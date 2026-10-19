"""认证相关请求模型"""
from pydantic import BaseModel, Field, field_validator
import re


class RegisterRequest(BaseModel):
    account: str = Field(..., description="手机号或邮箱")
    nickname: str = Field(..., min_length=2, max_length=16)
    password: str = Field(..., min_length=8, max_length=32)
    confirm_password: str
    agree: bool = True

    @field_validator("account")
    @classmethod
    def validate_account(cls, v: str) -> str:
        if re.fullmatch(r"1[3-9]\d{9}", v) or re.fullmatch(r"[\w.+-]+@[\w-]+\.[\w.]+", v):
            return v
        raise ValueError("账号须为合法手机号或邮箱")


class LoginRequest(BaseModel):
    account: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    nickname: str
    user_id: int


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str
