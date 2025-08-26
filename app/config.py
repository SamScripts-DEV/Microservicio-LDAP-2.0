import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    LDAP_HOST = os.getenv("LDAP_HOST", "ldap://localhost")
    LDAP_PORT = int(os.getenv("LDAP_PORT", "389"))
    LDAP_BIND_DN = os.getenv("LDAP_BIND_DN")
    LDAP_PASSWORD = os.getenv("LDAP_PASSWORD")
    BASE_DN = os.getenv("BASE_DN")
    JWT_SECRET = os.getenv("JWT_SECRET", "changeme")

settings = Settings()


