from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from app.schemas.user import UserOut
from app.core.security import decode_token

router = APIRouter(prefix="/users", tags=["users"])

# read the token from the authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.get("/me", response_model=UserOut)
async def get_my_profile(token: Annotated[str, Depends(oauth2_scheme)]):
    print("my profile endpoint")
    user_id = decode_token(token, "access")
