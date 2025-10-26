"""
Common dependencies for FastAPI dependency injection.
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.db import get_db
from app.config import settings

# Security
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Dependency to extract and validate JWT token.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        User information from JWT payload, or None if no token

    Raises:
        HTTPException: If token is invalid

    Example:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["sub"]}
    """
    if credentials is None:
        return None

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def require_auth(
    user: Optional[dict] = Depends(get_current_user)
) -> dict:
    """
    Dependency that requires authentication.

    Args:
        user: User from get_current_user dependency

    Returns:
        User information

    Raises:
        HTTPException: If user is not authenticated

    Example:
        @app.post("/admin")
        async def admin_route(user: dict = Depends(require_auth)):
            return {"message": "Admin access granted"}
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Re-export get_db for convenience
__all__ = ["get_db", "get_current_user", "require_auth"]
