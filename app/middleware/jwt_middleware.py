from fastapi import Request
from fastapi.responses import JSONResponse
import json
from app.services.jwt_service import jwt_service

async def decrypt_jwt_middleware(request: Request, call_next):
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body_bytes = await request.body()
            if body_bytes:
                json_data = json.loads(body_bytes.decode())

                if "token" in json_data:
                    decrypted_data = jwt_service.decrypt_payload(json_data["token"])
                    for key in ["iat", "exp"]:
                        decrypted_data.pop(key, None)
                    print("Decrypted Data:", decrypted_data)

                    new_body = json.dumps(decrypted_data).encode("utf-8")

                    # Este receive devuelve el body una sola vez y luego vacío
                    async def receive():
                        nonlocal new_body
                        if new_body:
                            b = new_body
                            new_body = b""
                            return {
                                "type": "http.request",
                                "body": b,
                                "more_body": False,
                            }
                        return {"type": "http.request", "body": b"", "more_body": False}

                    request._receive = receive
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"Error decrypting payload: {str(e)}",
                },
            )

    response = await call_next(request)
    return response
