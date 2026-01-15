"""Pydantic schemas for authentication."""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """Schema for login request."""

    username: str = Field(..., min_length=1, max_length=80, description="Username")
    password: str = Field(..., min_length=1, description="Password")


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=3, max_length=80, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    display_name: str | None = Field(
        default=None, max_length=100, description="Display name"
    )
    is_admin: bool = Field(default=False, description="Admin status")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username contains only safe characters."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username must contain only letters, numbers, underscores, and hyphens"
            )
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""

    email: EmailStr | None = Field(default=None, description="Email address")
    display_name: str | None = Field(
        default=None, max_length=100, description="Display name"
    )
    avatar_url: str | None = Field(
        default=None, max_length=500, description="Avatar URL"
    )
    bio: str | None = Field(default=None, max_length=500, description="Bio")
    is_admin: bool | None = Field(default=None, description="Admin status")
    is_active: bool | None = Field(default=None, description="Active status")


class PasswordChange(BaseModel):
    """Schema for changing password (user changing their own password)."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password"
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class AdminPasswordReset(BaseModel):
    """Schema for admin resetting another user's password.

    Unlike PasswordChange, this only requires the new password since
    admins don't need to know the user's current password.
    """

    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password"
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    username: str
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    is_admin: bool
    is_active: bool
    created_at: str | None = None
    last_login: str | None = None


class ThemePreferences(BaseModel):
    """Schema for updating user theme preferences."""

    theme_preference: str | None = Field(
        default=None, description="Theme name (dark, light, midnight)"
    )
    page_accents: dict | None = Field(
        default=None, description="Page-specific accent colors"
    )

    @field_validator("theme_preference")
    @classmethod
    def validate_theme(cls, v: str | None) -> str | None:
        """Validate theme is one of the allowed values."""
        if v is not None:
            allowed_themes = {"dark", "light", "midnight"}
            if v not in allowed_themes:
                raise ValueError(f"Theme must be one of: {', '.join(allowed_themes)}")
        return v

    @field_validator("page_accents")
    @classmethod
    def validate_accents(cls, v: dict | None) -> dict | None:
        """Validate page accents have valid structure."""
        if v is not None:
            allowed_pages = {"dashboard", "devices", "services", "automation"}
            allowed_colors = {
                "red", "pink", "grape", "violet", "indigo", "blue", "cyan",
                "teal", "green", "lime", "yellow", "orange", "purple"
            }
            for page, color in v.items():
                if page not in allowed_pages:
                    raise ValueError(f"Invalid page: {page}")
                if color not in allowed_colors:
                    raise ValueError(f"Invalid color: {color}")
        return v
