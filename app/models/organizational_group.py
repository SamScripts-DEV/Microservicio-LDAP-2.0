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
    old_group_name: str
    new_group_name: str
    old_hierarchy_level: int
    new_hierarchy_level: int
    group_type: Literal['CONTAINER', 'LEADERSHIP', 'OPERATIONAL']