"""Authentication schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .user import UserResponse


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    display_name: Optional[str] = Field(default=None, max_length=255)
    device_name: Optional[str] = Field(default=None, max_length=255)
    platform: Optional[str] = Field(default=None, max_length=64)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=255)
    device_name: Optional[str] = Field(default=None, max_length=255)
    platform: Optional[str] = Field(default=None, max_length=64)


class GoogleAuthRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_token: str = Field(min_length=1)
    device_name: Optional[str] = Field(default=None, max_length=255)
    platform: Optional[str] = Field(default=None, max_length=64)


class AppleAuthRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity_token: str = Field(min_length=1)
    authorization_code: str = Field(min_length=1)
    device_name: Optional[str] = Field(default=None, max_length=255)
    platform: Optional[str] = Field(default=None, max_length=64)


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=1)
    device_name: Optional[str] = Field(default=None, max_length=255)
    platform: Optional[str] = Field(default=None, max_length=64)


class LogoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=1)


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_token_expires_in: int
    refresh_token_expires_in: int
    user: UserResponse


class LogoutResponse(BaseModel):
    success: bool


class SessionRevocationResponse(BaseModel):
    success: bool
    revoked_count: int


class GoogleUserInfoResponse(BaseModel):
    sub: str
    email: EmailStr
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
