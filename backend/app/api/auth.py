from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from app.schemas.user import UserCreate, UserOut
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.models.user import User
from app.schemas.token import Token

from fastapi.security import OAuth2PasswordRequestForm

# http://127.0.0.1:8000/auth/singup
# in the url (/auth) is the prefix
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    # we will make the email in lower case , because for the database it is different emails but in real world it is not
    email = user_in.email.lower()
    # look for an existing user with the same email
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email already exists!!!"
        )
    hashed = await run_in_threadpool(hash_password, user_in.password)
    user = User(email=email, hashed_password=hashed, full_name=user_in.full_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    email = form_data.username.lower()

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    login_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password!",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        raise login_error

    # the wrong password
    if not await run_in_threadpool(
        verify_password, form_data.password, user.hashed_password
    ):
        raise login_error

    # email and password are correct
    return Token(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )
