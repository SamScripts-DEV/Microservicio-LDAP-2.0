from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from app.middleware.decrypt_jwt import decrypt_request
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
def create_user_route(payload: dict = Depends(decrypt_request)):   
    user = User(**payload)
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
def update_user_route(email: str, payload: dict = Depends(decrypt_request)):
    user_data = UpdatedUserRequest(**payload)
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
    
@router.get("/health", response_model=HealthCheckResponse, summary="Health Check")
def health_check_route():
    try:
        ldap_status = user_service.ldap.test_connection()
        status_str = "healthy" if ldap_status else "unhealthy"
        http_status = status.HTTP_200_OK if ldap_status else status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(
            status_code=http_status,
            content=HealthCheckResponse(
                status=status_str,
                ldap_connection=ldap_status
            ).dict()
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=HealthCheckResponse(
                status="unhealthy",
                ldap_connection=False,
                error=str(e)
            ).dict()
        )        

    