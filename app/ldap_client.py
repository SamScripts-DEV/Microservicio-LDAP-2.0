from ldap3 import Server, Connection, ALL
from app.config import settings
from loguru import logger


class LDAPClient:
    def __init__(self):
        logger.info(f"Connecting to LDAP in {settings.LDAP_HOST}:{settings.LDAP_PORT}")
        self.server = Server(settings.LDAP_HOST, port=settings.LDAP_PORT, get_info=ALL)
        self._connect()


    def _connect(self):
        try:
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
                raise Exception("Failed to bind to LDAP server")
        except Exception as e:
            logger.error(f"LDAP connection error: {e}")
            raise
    

    def ensure_connection(self):
        try:
            if not self.conn.bound:
                logger.warning("LDAP connection lost, reconnecting...")
                self._connect()
        except Exception as e:
            logger.error(f"LDAP reconnection error: {e}")
            raise


    def entry_exists(self, dn: str):
        try:
            self.ensure_connection()
            self.conn.search(search_base=dn, search_filter='(objectClass=*)', search_scope='BASE')
            return len(self.conn.entries) > 0
        except Exception as e:
            logger.error(f"LDAP search error for DN {dn}: {e}")
            raise


    def search(self, base_dn: str, search_filter: str, search_scope='SUBTREE') -> list:
        try:
            self.ensure_connection()
            self.conn.search(search_base=base_dn, search_filter=search_filter, search_scope='SUBTREE')
            return self.conn.entries
        except Exception as e:
            logger.error(f"LDAP search error: base={base_dn}, filter={search_filter}, error={e}")
            raise


    def add_entry(self, dn: str, object_classes: list, attributes: dict):
        try:
            self.ensure_connection()
            logger.debug(f"Adding entry: {dn}")
            logger.debug(f"Object classes: {object_classes}")
            logger.debug(f"Attributes: {attributes}")
            
            self.conn.add(dn, object_classes, attributes)
            if not self.conn.result['description'] == 'success':
                raise Exception(f"Error adding entry: {self.conn.result}")
            logger.info(f"Entry added successfully: {dn}")
        except Exception as e:
            logger.error(f"Error adding entry {dn}: {e}")
            raise


    def modify_entry(self, dn: str, changes: dict):

        try:
            self.ensure_connection()
            logger.debug(f"Modifying entry: {dn}")
            logger.debug(f"Changes: {changes}")
            

            ldap_changes = {}
            for attr, value in changes.items():
                if value is not None:
                    ldap_changes[attr] = [('MODIFY_REPLACE', value)]
            
            self.conn.modify(dn, ldap_changes)
            if not self.conn.result['description'] == 'success':
                raise Exception(f"Error modifying entry: {self.conn.result}")
            logger.info(f"Entry modified successfully: {dn}")
        except Exception as e:
            logger.error(f"Error modifying entry {dn}: {e}")
            raise


    def delete_entry(self, dn: str):
        try:
            self.ensure_connection()
            logger.debug(f"Deleting entry: {dn}")
            
            self.conn.delete(dn)
            if not self.conn.result['description'] == 'success':
                raise Exception(f"Error deleting entry: {self.conn.result}")
            logger.info(f"Entry deleted successfully: {dn}")
        except Exception as e:
            logger.error(f"Error deleting entry {dn}: {e}")
            raise


    def bind_as_user(self, user_dn: str, password: str) -> bool:
        try:
            logger.debug(f"Attempting bind as user: {user_dn}")
            
            # Crear conexión temporal para autenticación
            user_conn = Connection(self.server, user=user_dn, password=password, auto_bind=True)
            is_authenticated = user_conn.bound
            
            if is_authenticated:
                logger.debug(f"Bind successful for: {user_dn}")
                user_conn.unbind()  # Cerrar la conexión temporal
            else:
                logger.debug(f"Bind failed for: {user_dn}")
            
            return is_authenticated
        except Exception as e:
            logger.debug(f"Bind error for user {user_dn}: {e}")
            return False


    def create_ou(self, ou_dn: str):
        try:
            self.ensure_connection()
            ou_name = ou_dn.split(',')[0].split('=')[1]
            self.conn.add(ou_dn, ['organizationalUnit', 'top'], {'ou': ou_name})
            if not self.conn.result['description'] == 'success':
                raise Exception(f"Error creating OU: {self.conn.result}")
            logger.info(f"OU created successfully: {ou_dn}")
        except Exception as e:
            logger.error(f"LDAP error creating OU {ou_dn}: {e}")
            raise
        

    def create_entry(self, user_dn: str, attrs: dict):
        try:
            self.ensure_connection()
            logger.debug(f"Creating user: {user_dn}")
            logger.debug(f"Attributes: {attrs}")
            
            self.conn.add(user_dn, attrs['objectClass'], attrs)
            if not self.conn.result['description'] == 'success':
                raise Exception(f"Error creating user: {self.conn.result}")
            logger.success(f"User created successfully: {user_dn}")
        except Exception as e:
            logger.error(f"Error creating user {user_dn}: {e}")
            raise

        
    def test_connection(self):
        try:
            self.ensure_connection()
            return self.conn.bound
        except Exception as e:
            logger.error(f"LDAP connection test error: {e}")
            return False
    



ldap_client = LDAPClient()
