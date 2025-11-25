from fastapi import APIRouter, HTTPException, Query, Depends
from app.middleware.decrypt_jwt import decrypt_request
from app.models.role import RoleAssignment, RoleUpdateRequest
from app.services.role_service import RoleService
from loguru import logger
from typing import Optional

router = APIRouter()
role_service = RoleService()

@router.post("/assign-roles")
async def assign_roles(payload: dict = Depends(decrypt_request)):

    role_assignment = RoleAssignment(**payload)

    try:
        if not role_assignment.role_global and not role_assignment.role_local:
            raise HTTPException(status_code=400, detail="At least one role type must be provided")
        
        if not role_assignment.users:
            raise HTTPException(status_code=400, detail="At least one user must be provided")
        
        if role_assignment.role_local and not role_assignment.area:
            raise HTTPException(status_code=400, detail="Area must be provided for local roles")
        
        result = role_service.assign_roles(role_assignment)
        return result
        
    except Exception as e:
        logger.error(f"Error in assign_roles endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/update-role')
async def update_role(payload: dict = Depends(decrypt_request)):
    role_update = RoleUpdateRequest(**payload)

    try:
        if role_update.role_type not in ["role_global", "role_local"]:
            raise HTTPException(status_code=400, detail="Invalid role type")
        
        if role_update.role_type == "role_local" and not role_update.area:
            raise HTTPException(status_code=400, detail="Area must be provided for local roles")
        
        success = role_service.update_role_name(
            role_type=role_update.role_type,
            old_role_name=role_update.old_role_name,
            new_role_name=role_update.new_role_name,
            area=role_update.area
        )

        return {
            "success": success,
            "message": f"{role_update.role_type} name updated successfully"
            }
    
    except Exception as e:
        logger.error(f"Error updating role: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/remove-role/{email}")
async def remove_role(email: str, role_type: str, role_name: str, area: Optional[str] = Query(None)):

    try:
        if role_type not in ["role_global", "role_local"]:
            raise HTTPException(status_code=400, detail="Invalid role type")
        
        success = role_service.remove_role_from_user(email, role_type, role_name, area)
        return {"success": success}
        
    except Exception as e:
        logger.error(f"Error removing role: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.delete("/delete-role-group")
async def delete_role_group(role_type: str, role_name: str, area: Optional[str] = None):
    try:
        success = role_service.delete_role_group(role_type, role_name, area)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error deleting role group: {e}")
        raise HTTPException(status_code=500, detail=str(e))