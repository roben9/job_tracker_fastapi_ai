from fastapi import FastAPI, Depends
from app.core.config import settings
from datetime import datetime
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from sqlalchemy import text

from app.api import auth, users

app = FastAPI(title=settings.app_name)
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/")
async def home():
    return {"message": "Welcome to the Job Tracker API"}


@app.get("/health")
async def health(db: Annotated[AsyncSession, Depends(get_db)]):
    await db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "ok"}


@app.get("/about")
async def about():
    return {"app": "Job Tracker", "version": "1.0"}


async def get_time():
    return datetime.now().strftime("%H:%M:%S")


@app.get("/time")
async def show_time(now: Annotated[str, Depends(get_time)]):
    # get the current time as text , like 14:35:20
    return {"time": now}


@app.get("/greeting")
async def greeting(now: Annotated[str, Depends(get_time)]):
    # the same line copied again
    return {"message": f"Hello,it is {now}"}
