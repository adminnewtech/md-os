from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

SECRET_KEY = "md-os-dev-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12

security = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    sub: str
    role: str
    company_id: str
    workspace_id: str
    exp: int


class AuthContext(BaseModel):
    actor_id: str
    role: str
    company_id: str
    workspace_id: str


def create_access_token(
    actor_id: str,
    role: str,
    company_id: str,
    workspace_id: str,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": actor_id,
        "role": role,
        "company_id": company_id,
        "workspace_id": workspace_id,
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_auth_context(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthContext:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = creds.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        data = TokenPayload(**payload)
    except (JWTError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc

    return AuthContext(
        actor_id=data.sub,
        role=data.role,
        company_id=data.company_id,
        workspace_id=data.workspace_id,
    )
