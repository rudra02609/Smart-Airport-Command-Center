"""
Authentication endpoints and dependency functions.
Handles login, token verification, and role-based access.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.core.security import create_access_token, decode_access_token
from app.cybersecurity.rbac import (
    UserInDB, Role, authenticate_user, get_user, has_permission
)
from app.cybersecurity.audit import audit_logger
from app.cybersecurity.anomaly_detection import anomaly_detector
from typing import Optional

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> UserInDB:
    """
    FastAPI dependency: Extract and verify the current user from JWT token.
    Raises 401 if token is missing or invalid.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please provide a valid token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = decode_access_token(token)
    if payload is None:
        audit_logger.log(
            user="unknown",
            action="authentication_failed",
            endpoint="token_validation",
            status="failed",
            details="Invalid or expired token presented"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    username: str = payload.get("sub")
    if username is None:
        audit_logger.log(
            user="unknown",
            action="authentication_failed",
            endpoint="token_validation",
            status="failed",
            details="Token missing subject claim"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = get_user(username)
    if user is None or user.disabled:
        audit_logger.log(
            user=username,
            action="authentication_failed",
            endpoint="token_validation",
            status="failed",
            details="User not found or disabled"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled."
        )
    
    return user


def require_role(*allowed_roles: Role):
    """
    FastAPI dependency factory: Require the current user to have one of the allowed roles.
    Usage: Depends(require_role(Role.ADMIN, Role.OPERATOR))
    """
    async def role_checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if current_user.role not in allowed_roles:
            audit_logger.log(
                user=current_user.username,
                action="authorization_failed",
                endpoint="rbac_check",
                status="failed",
                details=f"User role '{current_user.role.value}' denied; required one of: {', '.join(r.value for r in allowed_roles)}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(r.value for r in allowed_roles)}. Your role: {current_user.role.value}"
            )
        return current_user
    return role_checker


# Optional auth dependency - returns None if no token provided (for endpoints that work with or without auth)
async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[UserInDB]:
    """Get current user if authenticated, otherwise return None."""
    if token is None:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    username = payload.get("sub")
    if username is None:
        return None
    return get_user(username)


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    """
    Login endpoint. Accepts username and password, returns JWT token.
    
    **Default Users:**
    - admin / admin123 (Full access)
    - operator / operator123 (Prediction APIs)
    - viewer / viewer123 (Read-only)
    """
    client_ip = request.client.host if request and request.client else "unknown"
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        # Record the failed attempt for anomaly detection
        anomaly_detector.record_failed_login(client_ip)
        audit_logger.log(
            user=form_data.username,
            action="login",
            endpoint="/api/auth/login",
            status="failed",
            ip_address=client_ip,
            details="Invalid username or password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    
    audit_logger.log(
        user=user.username,
        action="login",
        endpoint="/api/auth/login",
        status="success",
        ip_address=client_ip,
        details=f"Role: {user.role.value}"
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role.value,
        "full_name": user.full_name
    }


@router.get("/me")
async def get_me(current_user: UserInDB = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    return {
        "username": current_user.username,
        "role": current_user.role.value,
        "full_name": current_user.full_name,
        "disabled": current_user.disabled
    }
