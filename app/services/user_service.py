from app.models.user import User
from app.ldap_client import LDAPClient
from loguru import logger
from typing import Optional, Dict, Any
from app.config import settings


class UserService:
    def __init__(self):
        self.ldap = LDAPClient()
        self.base_dn = settings.BASE_DN
        self.users_ou = "ou=users"


    def ensure_ou(self, ou_name: str, parent_dn: str) -> str:
        ou_name = ou_name.lower()
        ou_dn = f"ou={ou_name},{parent_dn}"
        if not self.ldap.entry_exists(ou_dn):
            self.ldap.create_ou(ou_dn)
        return ou_dn


    def build_user_dn(self, user: User) -> str:
        return (
            f"uid={user.email},ou={user.city.lower()},ou={user.province.lower()},ou={user.country.lower()},ou=users,{self.base_dn}"
        )


    def build_user_attrs(self, user: User) -> dict:
        attrs = {
            "objectClass": ["inetOrgPerson", "organizationalPerson", "person", "top"],
            "uid": user.email,
            "cn": f"{user.firstName} {user.lastName}",
            "givenName": user.firstName,
            "sn": user.lastName,
            "mail": user.email,
            "employeeNumber": user.id,
        }
        if hasattr(user, 'active'):
            attrs["description"] = "ACTIVE" if user.active else "INACTIVE"
        if user.address:
            attrs["postalAddress"] = user.address
        if user.department:
            attrs["departmentNumber"] = user.department
        if user.area:
            attrs["physicalDeliveryOfficeName"] = user.area
        if user.position:
            attrs["title"] = user.position
        if user.phone:
            attrs["telephoneNumber"] = user.phone
        if user.imageUrl and user.imageUrl.startswith(("http://", "https://")):
            attrs["labeledURI"] = user.imageUrl
        if user.password:
            attrs["userPassword"] = user.password
        
        return attrs
    

    def create_user(self, user: User) -> str:

        try:
            logger.info(f"Creating user: {user.email}")
            users_dn = self.ensure_ou("users", self.base_dn)
            country_dn = self.ensure_ou(user.country, users_dn)
            province_dn = self.ensure_ou(user.province, country_dn)
            city_dn = self.ensure_ou(user.city, province_dn)

            user_dn = self.build_user_dn(user)
            attrs = self.build_user_attrs(user)

            if self.ldap.entry_exists(user_dn):
                raise Exception(f"User already exists: {user_dn}")
            
            self.ldap.create_entry(user_dn, attrs)
            logger.success(f"User created successfully: {user.email}")
            return user_dn

        except Exception as e:
            logger.error(f"Error creating user {user.email}: {e}")
            raise

    
    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Getting user: {email}")
            
            search_filter = f"(uid={email})"
            entries = self.ldap.search(base_dn=self.base_dn, search_filter=search_filter)
            
            if entries:
                user_entry = entries[0]
                description = user_entry.description.value if hasattr(user_entry, 'description') else "ACTIVE"
                is_active = description == "ACTIVE"
                user_data = {
                    "email": user_entry.uid.value if hasattr(user_entry, 'uid') else email,
                    "firstName": user_entry.givenName.value if hasattr(user_entry, 'givenName') else "",
                    "lastName": user_entry.sn.value if hasattr(user_entry, 'sn') else "",
                    "id": user_entry.employeeNumber.value if hasattr(user_entry, 'employeeNumber') else "",
                    "active": is_active,
                    "address": user_entry.postalAddress.value if hasattr(user_entry, 'postalAddress') else "",
                    "department": user_entry.departmentNumber.value if hasattr(user_entry, 'departmentNumber') else "",
                    "area": user_entry.physicalDeliveryOfficeName.value if hasattr(user_entry, 'physicalDeliveryOfficeName') else "",
                    "position": user_entry.title.value if hasattr(user_entry, 'title') else "",
                    "phone": user_entry.telephoneNumber.values if hasattr(user_entry, 'telephoneNumber') else [],
                    "imageUrl": user_entry.labeledURI.value if hasattr(user_entry, 'labeledURI') else "",
                    "dn": user_entry.entry_dn
                }
                logger.success(f"User found: {email}")
                return user_data
            
            logger.warning(f"User not found: {email}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user {email}: {e}")
            raise


    def update_user(self, email: str, user_data: Dict[str, Any]) -> str:
            try:
                logger.info(f"Updating user: {email}")
                existing_user = self.get_user(email)
                if not existing_user:
                    raise Exception(f"User not found: {email}")
                
                user_dn = existing_user["dn"]
                ldap_changes = {}
                field_mapping = {
                    "firstName": "givenName",
                    "lastName": "sn", 
                    "address": "postalAddress",
                    "department": "departmentNumber",
                    "area": "physicalDeliveryOfficeName",
                    "position": "title",
                    "phone": "telephoneNumber",
                    "imageUrl": "labeledURI",
                    "password": "userPassword",
                    "active": "description"
                }
                
                for field, ldap_attr in field_mapping.items():
                    if field in user_data and user_data[field] is not None:  
                        if field == "active":
                            ldap_changes[ldap_attr] = "ACTIVE" if user_data[field] else "INACTIVE"
                        else:
                            ldap_changes[ldap_attr] = user_data[field]
                
                if "firstName" in user_data or "lastName" in user_data:
                    first_name = user_data.get("firstName", existing_user["firstName"])
                    last_name = user_data.get("lastName", existing_user["lastName"])
                    ldap_changes["cn"] = f"{first_name} {last_name}"
                
                if ldap_changes:
                    self.ldap.modify_entry(user_dn, ldap_changes)
                    logger.success(f"User updated successfully: {email}")
                else:
                    logger.info(f"No changes to apply for user: {email}")
                
                return user_dn
                
            except Exception as e:
                logger.error(f"Error updating user {email}: {e}")
                raise


    def delete_user(self, email: str) -> bool:
        try:
            logger.info(f"Soft deleting user: {email}")
            
            soft_delete_data = {"active": False}
            self.update_user(email, soft_delete_data)
            
            logger.success(f"User soft deleted successfully: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error soft deleting user {email}: {e}")
            raise

    def hard_delete_user(self, email: str) -> bool:
        try:
            logger.info(f"Hard deleting user: {email}")
            existing_user = self.get_user(email)
            if not existing_user:
                raise Exception(f"User not found: {email}")
            
            user_dn = existing_user["dn"]
            
            self.ldap.delete_entry(user_dn)
            logger.success(f"User hard deleted successfully: {email}")
            
            return True
        except Exception as e:
            logger.error(f"Error hard deleting user {email}: {e}")
            raise

    def reactivate_user(self, email: str) -> bool:

        try:
            logger.info(f"Reactivating user: {email}")
            
            reactivate_data = {"active": True}
            self.update_user(email, reactivate_data)
            
            logger.success(f"User reactivated successfully: {email}")
            return True
        
        except Exception as e:
            logger.error(f"Error reactivating user {email}: {e}")
            raise
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        try:
            logger.info(f"Authenticating user: {email}")
            
            user_data = self.get_user(email)
            if not user_data:
                logger.warning(f"User not found for authentication: {email}")
                return {"success": False, "message": "User not found"}
            
            user_dn = user_data["dn"]
            is_authenticated = self.ldap.bind_as_user(user_dn, password)
            
            if is_authenticated:
                logger.success(f"Authentication successful for: {email}")
                return {
                    "success": True, 
                    "message": "Authentication successful",
                    "user": user_data
                }
            else:
                logger.warning(f"Authentication failed for: {email}")
                return {"success": False, "message": "Invalid credentials"}
                
        except Exception as e:
            logger.error(f"Error authenticating user {email}: {e}")
            return {"success": False, "message": "Authentication error"}


