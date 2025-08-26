from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: str
    firstName: str #si
    lastName: str  #si
    nationalId: str  #si
    email: str  #si
    username: str #si
    password: str   #si
    phone: str  #si
    active: bool
    city: str
    country: str
    address: Optional[str] = None   #si
    role: Optional[str] = None   #para el sistema en si
    department: Optional[str] = None   #si
    tower: Optional[str] = None    #si
    position: Optional[str] = None   #si
    imageUrl: Optional[str] = None
    createdAt: Optional[datetime] = None



