from fastapi import APIRouter, HTTPException
from app.models.user import User
from app.services.user_service import UserService

router = APIRouter()
user_service = UserService()

@router.post("/create-user")
def create_user_route(user: User):
    try:
        dn = user_service.create_user(user)
        return {"dn": dn}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    