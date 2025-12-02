from fastapi import APIRouter, HTTPException, Depends, Query
from app.middleware.decrypt_jwt import decrypt_request
from app.models.organizational_group import OrgGroupAssignment, OrgGroupUpdateRequest
from app.services.organizational_group_service import OrganizationalGroupService
from loguru import logger

router = APIRouter()
org_group_service = OrganizationalGroupService()

@router.post("/assign-organizational-group")
async def assign_organizational_group(payload: dict = Depends(decrypt_request)):

    try:
        org_group = OrgGroupAssignment(**payload)
        
        if not org_group.users:
            raise HTTPException(status_code=400, detail="At least one user must be provided")
        
        result = org_group_service.assign_organizational_group(org_group)
        return result
        
    except Exception as e:
        logger.error(f"Error in assign_organizational_group endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.put("/update-organizational-group")
async def update_organizational_group(payload: dict = Depends(decrypt_request)):
    try:
        org_group_update = OrgGroupUpdateRequest(**payload)
        success = org_group_service.update_organizational_group(org_group_update)

        return{
            "success": success,
            "message": "Organizational group updated successfully" 
        }
    
    except Exception as e:
        logger.error(F"Error updating organizational group: {e}")
        raise HTTPException(status_code=500, detail=str(e))


    
@router.delete("/remove-user-from-organizational-group/{email}")
async def remove_user_from_org_group(
    email: str,
    group_name: str = Query(..., description="Nombre del grupo organizacional"),
    hierarchy_level: int = Query(..., description="Nivel jerárquico del grupo organizacional")
):
    try:
        success = org_group_service.remove_user_from_org_group(
            email=email,
            group_name=group_name,
            hierarchy_level=hierarchy_level
        )

        return {"success": success, "message": "User removed from organizational group successfully"}

    
    except Exception as e:
        logger.error(f"Error removing user from organizational group: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    