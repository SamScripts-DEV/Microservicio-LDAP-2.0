from pydantic import BaseModel
from typing import Optional, List

class RoleAssignment(BaseModel):
    role_global: Optional[str] = None
    role_local: Optional[str] = None
    area: Optional[str] = None
    users: List[str]

class RoleUpdateRequest(BaseModel):
    role_type: str
    old_role_name: str
    new_role_name: str
    area: Optional[str] = None


