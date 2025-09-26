from fastapi import APIRouter, HTTPException, Query
from app.models.role import RoleAssignment
from app.services.role_service import RoleService
from loguru import logger
from typing import Optional

router = APIRouter()
role_service = RoleService()

@router.post("/assign-roles")
async def assign_roles(role_assignment: RoleAssignment):
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


@router.delete("/remove-role/{email}")
async def remove_role(email: str, role_type: str, role_name: str, area: Optional[str] = Query(None)):

    try:
        if role_type not in ["role_global", "role_local"]:
            raise HTTPException(status_code=400, detail="Invalid role type")
        
        success = role_service.remove_role_from_user(email, role_type, role_name)
        return {"success": success}
        
    except Exception as e:
        logger.error(f"Error removing role: {e}")
        raise HTTPException(status_code=500, detail=str(e))