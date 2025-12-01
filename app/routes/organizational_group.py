from fastapi import APIRouter, HTTPException, Depends
from app.middleware.decrypt_jwt import decrypt_request
from app.models.organizational_group import OrgGroupAssignment
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