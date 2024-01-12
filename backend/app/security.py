from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

def get_bearer():
    return HTTPBearer(auto_error=False)

def get_access_token(
        auth_header: HTTPAuthorizationCredentials | None = Depends(get_bearer) 
) -> str:
    if auth_header is None:
        raise HTTPException(
            status_code=401,
            detail="Not Authorized",
        )
    return auth_header.credentials
