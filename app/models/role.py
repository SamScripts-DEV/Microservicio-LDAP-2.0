from pydantic import BaseModel
from typing import Optional, List

class RoleAssignment(BaseModel):
    role_global: Optional[str] = None
    role_local: Optional[str] = None
    area: Optional[str] = None
    users: List[str]


