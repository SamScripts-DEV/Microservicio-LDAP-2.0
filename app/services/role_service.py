from app.ldap_client import LDAPClient
from app.models.role import RoleAssignment
from loguru import logger
from typing import Optional, Dict, Any, List
from ldap3 import MODIFY_ADD, MODIFY_REPLACE, BASE
import re

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

                    if role_assigment.role_local:
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

                    if role_assigment.role_global:
                        self._assign_role_to_user(user_dn, "role_global", role_assigment.role_global)

                    if role_assigment.role_local:
                        self._assign_role_to_user(user_dn, "role_local", role_assigment.role_local, area=role_assigment.area)

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

    def _assign_role_to_user(self, user_dn: str, role_type: str, role_name: str, area: Optional[str] = None):
        group_dn = self._get_role_group_dn(role_type, role_name, area)
        self._ensure_role_group(group_dn, first_member_dn=user_dn)

        entries = self.ldap.search(base_dn=group_dn, search_filter="(objectClass=groupOfNames)", search_scope='BASE')
        if entries:
            group_entry = entries[0]
            members = set(group_entry.member.values) if hasattr(group_entry, 'member') else set()
            if user_dn not in members:
                members.add(user_dn)
                self.ldap.modify_entry(group_dn, {"member": list(members)})


    
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
        
    def get_user_roles(self, email: str) -> dict:
        user_dn = self._find_user_dn(email)
        if not user_dn:
            return {"roles": []}

        search_filter = f"(member={user_dn})"
        entries = self.ldap.search(base_dn=f"ou=roles,{self.base_dn}", search_filter=search_filter)
        roles = []
        for entry in entries:
            if hasattr(entry, "cn"):
                roles.append(entry.cn.value)
        return {"roles": roles}


    def remove_role_from_user(self, email: str, role_type: str, role_name: str, area: Optional[str] = None) -> bool:
        user_dn = self._find_user_dn(email)
        if not user_dn:
            raise Exception(f"User not found: {email}")
        group_dn = self._get_role_group_dn(role_type, role_name, area)
        entries = self.ldap.search(base_dn=group_dn, search_filter="(objectClass=groupOfNames)", search_scope='BASE')
        if entries:
            group_entry = entries[0]
            members = set(group_entry.member.values) if hasattr(group_entry, 'member') else set()
            if user_dn in members:
                members.remove(user_dn)
                self.ldap.modify_entry(group_dn, {"member": list(members)})
                return True
        return False

    
    def _get_role_group_dn(self, role_type: str, role_name:str, area: Optional[str] = None) -> str:
        role_name_norm = normalize_name(role_name)
        if role_type == "role_global":
            group_cn = f"{role_name_norm}_global"
        elif role_type == "role_local" and area:
            area_norm = normalize_name(area)
            group_cn = f"{role_name_norm}_{area_norm}"
        else:
            raise Exception ("Invalid role type or missing area for local role")
        return f"cn={group_cn},ou=roles,{self.base_dn}"
    
    def _ensure_role_group(self, group_dn:str, first_member_dn: Optional[str] = None):
        if not self.ldap.entry_exists(group_dn):
            roles_ou_dn = f"ou=roles,{self.base_dn}"
            if not self.ldap.entry_exists(roles_ou_dn):
                self.ldap.create_ou(roles_ou_dn)
            
            cn = group_dn.split(',')[0].split('=')[1]
            attrs = {
                "objectClass": ["groupOfNames", "top"],
                "cn": cn,
            }
            if first_member_dn:
                attrs["member"] = [first_member_dn]
            else:
                raise Exception("First member DN is required to create a new role group")
            self.ldap.create_entry(group_dn, attrs)





def normalize_name(name:str) -> str:
    name = name.lower()
    name = re.sub(r"[ /]+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name