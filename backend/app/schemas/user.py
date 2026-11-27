# Emailstr is for validated emails, Field is for allowing us to add the conditions
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
import uuid


# this is what the user will send us
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)


# this is for the response
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    full_name: str
    created_at: datetime
