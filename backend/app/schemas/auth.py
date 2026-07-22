from pydantic import BaseModel


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerifyResponse(BaseModel):
    valid: bool
