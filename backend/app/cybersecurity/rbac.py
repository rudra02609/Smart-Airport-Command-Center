"""
Role-Based Access Control (RBAC) for Smart Airport Command Center.
Defines roles, permissions, and an in-memory user store.
"""

from enum import Enum
from pydantic import BaseModel
from typing import Optional
from app.core.security import get_password_hash, verify_password


class Role(str, Enum):
    """User roles with hierarchical access levels."""
    ADMIN = "admin"        # Full access to all endpoints
    OPERATOR = "operator"  # Access to prediction and alert APIs
    VIEWER = "viewer"      # Read-only access (health, security status)


# Role hierarchy for permission checking
ROLE_HIERARCHY = {
    Role.ADMIN: 3,
    Role.OPERATOR: 2,
    Role.VIEWER: 1
}


class UserInDB(BaseModel):
    """User model stored in the in-memory database."""
    username: str
    hashed_password: str
    role: Role
    full_name: str
    disabled: bool = False


# In-memory user store with default users
# In production, this would be replaced with a real database
users_db: dict[str, UserInDB] = {
    "admin": UserInDB(
        username="admin",
        hashed_password=get_password_hash("admin123"),
        role=Role.ADMIN,
        full_name="Airport Administrator"
    ),
    "operator": UserInDB(
        username="operator",
        hashed_password=get_password_hash("operator123"),
        role=Role.OPERATOR,
        full_name="Airport Operator"
    ),
    "viewer": UserInDB(
        username="viewer",
        hashed_password=get_password_hash("viewer123"),
        role=Role.VIEWER,
        full_name="Airport Viewer"
    )
}


def get_user(username: str) -> Optional[UserInDB]:
    """Retrieve a user from the in-memory store."""
    return users_db.get(username)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user by username and password."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if user.disabled:
        return None
    return user


def has_permission(user_role: Role, required_role: Role) -> bool:
    """Check if a user role meets the minimum required role."""
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)
