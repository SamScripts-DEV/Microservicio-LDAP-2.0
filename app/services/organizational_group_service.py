from app.ldap_client import LDAPClient
from app.models.organizational_group import OrgGroupAssignment
from loguru import logger
from typing import Optional, Dict, Any, List
from ldap3 import BASE
import re
from app.config import settings

class OrganizationalGroupService:
    def __init__(self):
        self.ldap = LDAPClient()
        self.base_dn = settings.BASE_DN
    
    def assign_organizational_group(self, org_group: OrgGroupAssignment) -> Dict[str, Any]:
        """Asigna un grupo organizacional a usuarios"""
        try:
            logger.info(f"Assigning organizational group '{org_group.group_name}' to users: {org_group.users}")

            results = []
            for email in org_group.users:
                try:
                    user_dn = self._find_user_dn(email)
                    if not user_dn:
                        results.append({
                            "email": email,
                            "success": False,
                            "message": "User not found"
                        })
                        continue

                    # Asignar grupo organizacional con hierarchy_chain
                    self._assign_org_group_to_user(
                        user_dn=user_dn,
                        group_name=org_group.group_name,
                        hierarchy_level=org_group.hierarchy_level,
                        group_type=org_group.group_type,
                        hierarchy_chain=[item.dict() for item in org_group.hierarchy_chain]
                    )

                    results.append({
                        "email": email,
                        "success": True,
                        "message": "Organizational group assigned successfully"
                    })

                except Exception as e:
                    logger.error(f"Error assigning org group to {email}: {e}")
                    results.append({
                        "email": email,
                        "success": False,
                        "message": str(e)
                    })
            
            logger.success(f"Organizational group assignment completed for {len(org_group.users)} users")
            return {
                "success": True,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error in organizational group assignment: {e}")
            raise

    def _find_user_dn(self, email: str) -> str | None:
        """Encuentra el DN de un usuario por email"""
        try: 
            search_filter = f"(uid={email})"
            entries = self.ldap.search(base_dn=self.base_dn, search_filter=search_filter)

            if entries:
                return entries[0].entry_dn
            return None
            
        except Exception as e:
            logger.error(f"Error finding user DN for {email}: {e}")
            return None

    def _assign_org_group_to_user(self, user_dn: str, group_name: str, hierarchy_level: int, group_type: str, hierarchy_chain: List[Dict]):
        """Asigna un grupo organizacional a un usuario"""
        group_dn = self._get_org_group_dn(group_name, hierarchy_level)
        self._ensure_org_group(group_dn, first_member_dn=user_dn)

        # Agregar usuario al grupo CN
        entries = self.ldap.search(base_dn=group_dn, search_filter="(objectClass=groupOfNames)", search_scope='BASE')
        if entries:
            group_entry = entries[0]
            members = set(group_entry.member.values) if hasattr(group_entry, 'member') else set()
            if user_dn not in members:
                members.add(user_dn)
                self.ldap.add_group_member(group_dn, user_dn)
                logger.info(f"[ORG_GROUP] User {user_dn} added to group {group_dn}")
        
        # Construir la jerarquía completa
        hierarchy_path = self._build_hierarchy_path(hierarchy_chain)
        logger.info(f"[ORG_GROUP] Jerarquía completa: {hierarchy_path}")
        
        # Actualizar businessCategory con la jerarquía completa
        try:
            changes = {
                "businessCategory": hierarchy_path,
                "employeeType": group_name
            }
            self.ldap.modify_entry(user_dn, changes)
            logger.success(f"[ORG_GROUP] ✓ Usuario actualizado con jerarquía: {hierarchy_path}")
        except Exception as e:
            logger.error(f"[ORG_GROUP] ✗ Error actualizando usuario: {e}")
            import traceback
            logger.error(f"[ORG_GROUP] Traceback: {traceback.format_exc()}")

    def _build_hierarchy_path(self, hierarchy_chain: List[Dict]) -> str:
        """Construye el path jerárquico completo"""
        sorted_chain = sorted(hierarchy_chain, key=lambda x: x.get('level', 0))
        path_parts = [f"{item['name']}({item['level']})" for item in sorted_chain]
        return " > ".join(path_parts)

    def _get_user_business_categories(self, user_dn: str) -> List[str]:
        """Obtiene los grupos organizacionales del usuario desde businessCategory"""
        try:
            entries = self.ldap.search(user_dn, "(objectClass=*)", search_scope='BASE')
            if entries and hasattr(entries[0], "businessCategory"):
                return list(entries[0].businessCategory.values)
            return []
        except Exception as e:
            logger.warning(f"Could not get businessCategory for {user_dn}: {e}")
            return []

    def _get_org_group_dn(self, group_name: str, hierarchy_level: int) -> str:
        """Genera el DN del grupo organizacional"""
        group_name_norm = normalize_name(group_name)
        group_cn = f"{group_name_norm}_{hierarchy_level}"
        return f"cn={group_cn},ou=organizational_groups,{self.base_dn}"
    
    def _ensure_org_group(self, group_dn: str, first_member_dn: Optional[str] = None):
        """Asegura que el grupo organizacional exista"""
        if not self.ldap.entry_exists(group_dn):
            org_groups_ou_dn = f"ou=organizational_groups,{self.base_dn}"
            if not self.ldap.entry_exists(org_groups_ou_dn):
                self.ldap.create_ou(org_groups_ou_dn)
            
            cn = group_dn.split(',')[0].split('=')[1]
            attrs = {
                "objectClass": ["groupOfNames", "top"],
                "cn": cn,
            }
            if first_member_dn:
                attrs["member"] = [first_member_dn]
            else:
                raise Exception("First member DN is required to create a new organizational group")
            self.ldap.create_entry(group_dn, attrs)
            logger.info(f"[ORG_GROUP] Created new organizational group: {group_dn}")


def normalize_name(name: str) -> str:
    """Normaliza nombres eliminando tildes y caracteres especiales"""
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u',
        'ñ': 'n', 'Ñ': 'n',
        'ü': 'u', 'Ü': 'u'
    }

    for old, new in replacements.items():
        name = name.replace(old, new)
    
    name = name.lower()
    name = re.sub(r"[ /]+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name