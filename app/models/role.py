from pydantic import BaseModel
from typing import Optional, List

class RoleAssignment(BaseModel):
    rol_global: Optional[str] = None
    rol_local: Optional[str] = None
    users: List[str]


