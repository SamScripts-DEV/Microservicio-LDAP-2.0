from fastapi import FastAPI
from app.routes.users import router as users_router
from app.routes.roles import router as roles_router
from app.middleware.jwt_middleware import decrypt_jwt_middleware

app = FastAPI(
    title="Microservicio de sincnización a LDAP",
    description="Microservicio para gestión de usuarios y sincronización con LDAP",
    version="2.0.0"

)





app.include_router(users_router, prefix="/api/v2/ldap", tags=["Users"])
app.include_router(roles_router, prefix="/api/v2/ldap", tags=["Roles"])

@app.get("/")
def root():
    return {
        "message": "Microservicio LDAP 2.0",
        "version": "2.0.0",
        "status": "running",
        "endpoints": "/api/v2/ldap",
        "supports_jwt_encryption": True
    }