from fastapi import APIRouter, HTTPException
from app.models.user import (
    User,
    UserResponse,
    AuthRequest,
    AuthResponse,
    UpdatedUserRequest,
    ApiResponse,
    HealthCheckResponse
)
from app.services.user_service import UserService

router = APIRouter()
user_service = UserService()

@router.post("/create-user", response_model=ApiResponse, summary="Crear un nuevo usuario en LDAP")
def create_user_route(user: User):   
    try:
        dn = user_service.create_user(user)
        return ApiResponse(
            success=True,
            message="User created successfully",
            dn=dn
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/users/{email}", response_model=ApiResponse, summary="Obtener usuario")
def get_user_route(email: str):
    try:
        user_data = user_service.get_user(email)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        return ApiResponse(
            success=True,
            message= "User found",
            data=user_data
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.patch("/users/{email}", response_model=ApiResponse, summary="Actualizar usuario")
def update_user_route(email: str, user_data: UpdatedUserRequest):
    try:
        updated_data = {k: v for k, v in user_data.dict().items() if v is not None}

        if not updated_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        dn = user_service.update_user(email, updated_data)
        return ApiResponse(
            success=True,
            message="User updated successfully",
            dn=dn
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{email}", response_model=ApiResponse, summary="Desactivar usuario (soft delete)")
def delete_user_route(email: str):
    try:
        result = user_service.delete_user(email)
        return ApiResponse(
            success=True,
            message="User deactivated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{email}/hard", response_model=ApiResponse, summary="Eliminar usuario físicamente")
def hard_delete_user_route(email: str):
    try:
        result = user_service.hard_delete_user(email)
        return ApiResponse(
            success=True,
            message="User permanently deleted"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.patch("/users/{email}/reactivate", response_model=ApiResponse, summary="Reactivar usuario")
def reactivate_user_route(email: str):
    try:
        result = user_service.reactivate_user(email)
        return ApiResponse(
            success=True,
            message="User reactivated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/auth/validate", response_model=AuthResponse, summary="Autenticar usuario")
def authenticate_user_route(auth_request: AuthRequest):
    try:
        result= user_service.authenticate_user(auth_request.email, auth_request.password)
        return AuthResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/health", response_model=HealthCheckResponse, summary = "Health Check")
def health_check_route():
    try:
        ldap_status = user_service.ldap.test_connection()
        return HealthCheckResponse(
            status="healthy" if ldap_status else "unhealthy",
            ldap_connection=ldap_status
        )
    except Exception as e:
        return HealthCheckResponse(
            status="unhealthy",
            ldap_connection=False,
            error=str(e)
        )
        

    