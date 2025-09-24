from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import json
from app.services.jwt_service import jwt_service

async def decrypt_jwt_middleware(request: Request, call_next):

    if request.method in ["POST", "PUT", "PATCH"]:
        try: 
            body = await request.body()
            if body:
                json_data = json.loads(body.decode())

                if "token" in json_data:
                    decrypted_data = jwt_service.decrypt_payload(json_data["token"])

                    new_body = json.dumps(decrypted_data).encode()

                    async def receive():
                        return {"type": "http.request", "body": new_body}
                    
                    request._receive = receive

        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Error decrypting payload: {str(e)}"},
            )
    response = await call_next(request)
    return response
