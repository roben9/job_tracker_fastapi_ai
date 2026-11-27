from pydantic import BaseModel


# this is what we send back after a successful login
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
