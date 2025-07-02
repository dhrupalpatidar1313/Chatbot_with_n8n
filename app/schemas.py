from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Response Schemas
class MessageResponse(BaseModel):
    message: str

# Chat Schemas
class ChatMessageCreate(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: int
    session_id: str
    message: str
    response: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    session_name: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: str
    session_name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True