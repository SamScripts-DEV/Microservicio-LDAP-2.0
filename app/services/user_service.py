from app.models.user import User
from app.ldap_client import LDAPClient

class UserService:
    def __init__(self):
        self.ldap = LDAPClient()
        self.base_dn = "dc=sonda,dc=org"
        self.users_ou = "ou=users"

    def ensure_ou(self, ou_name: str, parent_dn: str) -> str:
        """
        Verifica si la OU existe, si no la crea. Retorna el DN de la OU.
        """
        ou_name = ou_name.lower()
        ou_dn = f"ou={ou_name},{parent_dn}"
        if not self.ldap.entry_exists(ou_dn):
            self.ldap.create_ou(ou_dn)
        return ou_dn

    def build_user_dn(self, user: User) -> str:
        """
        Construye el DN del usuario según país y ciudad.
        """
        return (
            f"uid={user.email},ou={user.city.lower()},ou={user.country.lower()},ou=users,{self.base_dn}"
        )

    def build_user_attrs(self, user: User) -> dict:
        """
        Construye los atributos LDAP del usuario, mapeando los campos del modelo a atributos estándar.
        """
        attrs = {
            "objectClass": ["inetOrgPerson", "organizationalPerson", "person", "top"],
            "uid": user.email,
            "cn": f"{user.firstName} {user.lastName}",
            "sn": user.lastName,
            "mail": user.email,
            "employeeNumber": user.id,
        }
        if user.address:
            attrs["postalAddress"] = user.address
        if user.department:
            attrs["departmentNumber"] = user.department
        if user.tower:
            attrs["physicalDeliveryOfficeName"] = user.tower
        if user.position:
            attrs["title"] = user.position
        if user.phone:
            attrs["telephoneNumber"] = user.phone
        if user.imageUrl and user.imageUrl.startswith(("http://", "https://")):
            attrs["labeledURI"] = user.imageUrl
        # Otros campos pueden agregarse aquí según el esquema LDAP
        return attrs
    

    def create_user(self, user: User) -> str:
        """
        Crea las OU necesarias y el usuario en LDAP. Devuelve el DN o lanza excepción.
        """
        # 1. Verificar/crear OU Users
        users_dn = self.ensure_ou("users", self.base_dn)
        # 2. Verificar/crear OU país
        country_dn = self.ensure_ou(user.country, users_dn)
        # 3. Verificar/crear OU ciudad
        city_dn = self.ensure_ou(user.city, country_dn)

        # 4. Construir DN y atributos del usuario
        user_dn = self.build_user_dn(user)
        attrs = self.build_user_attrs(user)

        # 5. Crear usuario en LDAP
        if self.ldap.entry_exists(user_dn):
            raise Exception(f"User already exists: {user_dn}")
        self.ldap.create_entry(user_dn, attrs)

        # 6. Retornar DN
        return user_dn
