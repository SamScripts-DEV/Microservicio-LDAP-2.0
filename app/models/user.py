from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    id: str
    firstName: str #si
    lastName: str  #si
    nationalId: str  #si
    email: str  #si
    username: str #si
    password: str   #si
    phone: List[str]  #si
    active: bool
    city: str
    country: str
    province: str
    address: Optional[str] = None   #si
    roleGlobal: Optional[str] = None
    roleLocal: Optional[str] = None
    department: Optional[str] = None   #si
    area: Optional[str] = None    #si
    position: Optional[str] = None   #si
    imageUrl: Optional[str] = None
    createdAt: Optional[datetime] = None


#======MODELOS DE REPUESTA===========
class UserResponse(BaseModel):
    email: str
    firstName: str
    lastName: str
    id: str
    active: bool
    city: str
    address: str = ""
    department: str = ""
    area: str = ""
    position: str = ""
    phone: List[str] = []
    imageUrl: str = ""
    dn: str = ""

class AuthRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserResponse] = None

class UpdatedUserRequest(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    address: Optional[str] = None
    department: Optional[str] = None
    area: Optional[str] = None
    active: Optional[bool] = None
    position: Optional[str] = None
    phone: Optional[List[str]] = None
    imageUrl: Optional[str] = None
    password: Optional[str] = None


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    dn: Optional[str] = None

class HealthCheckResponse(BaseModel):
    status: str
    ldap_connection: bool
    error: Optional[str] = None