from pydantic import BaseModel
from typing import Optional, List, Literal

class HierarchyChainItem(BaseModel):
    name: str
    level: int
    type: Literal['CONTAINER', 'LEADERSHIP', 'OPERATIONAL']

class OrgGroupAssignment(BaseModel):
    group_name: str
    group_type: Literal['CONTAINER', 'LEADERSHIP', 'OPERATIONAL']
    hierarchy_level: int
    area: Optional[str] = None
    container_group: Optional[str] = None
    hierarchy_chain: List[HierarchyChainItem]
    users: List[str]

class OrgGroupUpdateRequest(BaseModel):
    old_group_name: str  # Nombre actual del grupo
    old_hierarchy_level: int  # Nivel actual
    new_group_name: str  # Nuevo nombre
    new_hierarchy_level: int  # Nuevo nivel (puede ser el mismo)
    new_hierarchy_chain: List[HierarchyChainItem]  # Nueva jerarquía completa