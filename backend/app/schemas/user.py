from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str #no need to use EmailStr here since it's already validated in UserCreate
    username: str

    class Config:
        from_attributes = True #allows Pydantic to read data from SQLAlchemy models

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"