import json
from fastapi import Request, HTTPException
from app.services.jwt_service import jwt_service

async def decrypt_request(request: Request):
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Request vacío")

    try:
        data = json.loads(body.decode("utf-8"))
        print("Payload recibido:", data)
        if "token" not in data:
            raise HTTPException(status_code=422, detail="Falta campo 'token'")
        decrypted = jwt_service.decrypt_payload(data["token"])
        print("Payload desencriptado:", decrypted)
        for k in ["iat","exp"]:
            decrypted.pop(k, None)
        return decrypted
    except Exception as e:
        print("Error desencriptando:", e)
        raise HTTPException(status_code=422, detail=f"Error desencriptando payload: {str(e)}")