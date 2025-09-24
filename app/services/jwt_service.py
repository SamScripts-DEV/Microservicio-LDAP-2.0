import jwt
from datetime import datetime, timedelta
from app.config import settings
import json

class JWTService:
    SECRET_KEY = settings.JWT_SECRET_KEY
    ALGORITHM = "HS256"

    def encrypt_payload(self, data: dict) -> str:
        payload = {
            "data": data,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=30)  # Token válido por 30 minutos
        }
        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)
    
    def decrypt_payload(self, token:str) -> dict:
        try:
            decoded = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return decoded
        except jwt.ExpiredSignatureError:
            raise Exception("Encrypted payload has expired")
        except jwt.PyJWTError:
            raise Exception("Invalid encrypted payload")



jwt_service = JWTService()