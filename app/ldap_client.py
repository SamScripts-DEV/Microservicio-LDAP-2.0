from ldap3 import Server, Connection, ALL
from app.config import settings
from loguru import logger


class LDAPClient:
    def __init__(self):
        logger.info(f"Connecting to LDAP in {settings.LDAP_HOST}:{settings.LDAP_PORT}")
        self.server = Server(settings.LDAP_HOST, port=settings.LDAP_PORT, get_info=ALL)
        self.conn = Connection(
            self.server,
            user=settings.LDAP_BIND_DN,
            password=settings.LDAP_PASSWORD,
            auto_bind=True
        )
        if self.conn.bound:
            logger.success("Connected to LDAP successfully")
        else:
            logger.error("Error connecting to LDAP")

    def entry_exists(self, dn: str):
        self.conn.search(search_base=dn, search_filter='(objectClass=*)', search_scope='BASE')
        return len(self.conn.entries) > 0
    
    def create_ou(self, ou_dn: str):
        self.conn.add(ou_dn, ['organizationalUnit', 'top'], {'ou': ou_dn.split(',')[0].split('=')[1]})
        if not self.conn.result['description'] == 'success':
            raise Exception(f"Error creating OU: {self.conn.result}")

    def create_entry(self, user_dn: str, attrs: dict):
        self.conn.add(user_dn, attrs['objectClass'], attrs)
        if not self.conn.result['description'] == 'success':
            raise Exception(f"Error creating user: {self.conn.result}")

    def test_connection(self):
        return self.conn.bound


ldap_client = LDAPClient()
