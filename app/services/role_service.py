from app.ldap_client import LDAPClient
from app.models.role import RoleAssignment
from loguru import logger
from typing import Optional, Dict, Any, List
from ldap3 import MODIFY_ADD, MODIFY_REPLACE, BASE

class RoleService:
    def __init__(self):
        self.ldap = LDAPClient()
        self.base_dn = "dc=sonda,dc=org"
    
    def assign_roles(self, role_assigment: RoleAssignment) -> Dict[str, Any]:
        try:
            logger.info(f"Assigning roles: {role_assigment.users}")

            results = []
            for email in role_assigment.users:
                try:
                    user_dn = self._find_user_dn(email)
                    if not user_dn:
                        results.append({
                            "email": email,
                            "success": False,
                            "message": "User not found"
                        })
                        continue

                    if role_assigment.rol_local:
                        if not role_assigment.area:
                            results.append({
                                "email": email,
                                "success": False,
                                "message": "Area is required for local roles"
                            })
                            continue

                        if not self._validate_user_area(user_dn, role_assigment.area):
                            results.append({
                                "email": email,
                                "success": False,
                                "message": f"User does not belong to area {role_assigment.area}"
                            })

                    if role_assigment.rol_global:
                        self._assign_role_to_user(user_dn, "rol_global", role_assigment.rol_global)

                    if role_assigment.rol_local:
                        self._assign_role_to_user(user_dn, "rol_local", role_assigment.rol_local)

                    results.append({
                        "email": email,
                        "success": True,
                        "message": "Roles assigned successfully"
                    })

                except Exception as e:
                    logger.error(f"Error assigning roles to {email}: {e}")
                    results.append({
                        "email": email,
                        "success": False,
                        "message": str(e)
                    })
            logger.success(f"Role assignment completed for {len(role_assigment.users)} users")
            return {
                "success": True,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error in role assignment: {e}")
            raise

    def _validate_user_area(self, user_dn: str, required_area: str) -> bool:
        try:
            search_filter = "(objectClass=*)"
            entries = self.ldap.search(base_dn=user_dn, search_filter=search_filter)
            if entries and hasattr(entries[0], "physicalDeliveryOfficeName"):
                user_area = getattr(entries[0], "physicalDeliveryOfficeName")
                if hasattr(user_area, 'value'):
                    user_area_value = user_area.value
                else:
                    user_area_value = str(user_area)
                
                return user_area_value.lower() == required_area.lower()
            return False
        except Exception as e:
            logger.error(f"Error validating user area for {user_dn}: {e}")
            return False
                
    

    def _find_user_dn(self, email:str) -> str | None:
        try: 
            search_filter = f"(uid={email})"
            entries = self.ldap.search(base_dn=self.base_dn, search_filter=search_filter)

            if entries:
                return entries[0].entry_dn
            return None
            
        except Exception as e:
            logger.error(f"Error finding user DN for {email}: {e}")
            return None

    def _assign_role_to_user(self, user_dn: str, role_type: str, role_name: str):
        try:
            current_roles = self._get_user_roles(user_dn, role_type)

            if role_name in current_roles:
                logger.info(f"Role {role_name} already exists for user {user_dn}")
                return
            current_roles.append(role_name)

            changes = {role_type: (MODIFY_REPLACE, current_roles)}
            self.ldap.modify_entry(user_dn, changes)
            logger.success(f"Role {role_name} assigned to user {user_dn}")

        except Exception as e:
            logger.error(f"Error assigning role {role_name} to user {user_dn}: {e}")
            raise
    
    def _get_user_roles(self, user_dn: str, role_type: str) -> List[str]:
        try:
            search_filter = "(objectClass=*)"
            entries = self.ldap.search(base_dn=user_dn, search_filter=search_filter, search_scope=BASE)
            if entries and hasattr(entries[0], role_type):
                role_attr = getattr(entries[0], role_type)
                if hasattr(role_attr, 'values'):
                    return list(role_attr.values)
                elif role_attr:
                    return [str(role_attr)]
            
            return []
        except Exception as e:
            logger.error(f"Error getting user roles for {user_dn}: {e}")
            return []
        
    def get_user_roles(self, email: str) -> Dict[str, Any]:
        try:
            user_dn = self._find_user_dn(email)
            if not user_dn:
                return {
                    "rol_global": [],
                    "rol_local": []
                }
            
            global_roles = self._get_user_roles(user_dn, "rol_global")
            local_roles =self._get_user_roles(user_dn, "rol_local")

            return {
                "rol_global": global_roles,
                "rol_local": local_roles

            }
        except Exception as e:
            logger.error(f"Error getting roles for user {email}: {e}")
            raise


    def remove_role_from_user(self, email: str, role_type: str, role_name: str) -> bool:
        try:
            user_dn = self._find_user_dn(email)
            if not user_dn:
                raise Exception(f"User not found: {email}")
            
            current_roles = self._get_user_roles(user_dn, role_type)

            if role_name not in current_roles:
                logger.info(f"Role {role_name} does not exist for user {user_dn}")
                return False
            
            current_roles.remove(role_name)

            changes = {role_type: (MODIFY_REPLACE, current_roles)}
            self.ldap.modify_entry(user_dn, changes)

            logger.success(f"Role {role_name} removed from user {user_dn}")
            return True
        except Exception as e:
            logger.error(f"Error removing role {role_name} from user {email}: {e}")
            raise