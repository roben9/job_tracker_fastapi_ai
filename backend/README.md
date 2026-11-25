<!--

1- uv init [name of the project] --no-package --python 3.14

-------------------------------------------------------------------------------------------------------------

2- uv add "fastapi[standard]"

-------------------------------------------------------------------------------------------------------------

3- we will add this to the buttom of pyproject.toml:
[tool.fastapi]
entrypoint ="app.main:app"

-------------------------------------------------------------------------------------------------------------

4- after this we can run the server with:
uv run fastapi dev

-------------------------------------------------------------------------------------------------------------

5- we need docker to be running

-------------------------------------------------------------------------------------------------------------

6.1- outside our backend folder we will create a compose.yaml

            services:
                db:
                    image: postgres:18-trixie
                    environment:
                    POSTGRES_USER: jobtracker
                    POSTGRES_PASSWORD: 123456789
                    POSTGRES_DB: jobtracker_db
                    ports:
                    - "127.0.0.1:5433:5432"
                    volumes:
                    - pgdata:/var/lib/postgresql

            volumes:
                pgdata:

6.2 - run: docker compose up -d
6.3 - to check it is responding run : docker compose exec db psql -U [username in the compose.yaml] -d [db name in the compose.yaml]
and then this : SELECT version();

-------------------------------------------------------------------------------------------------------------

7- we need a .env file to put our info in it (!!!!!!!!!!!!!!!!!! and make sure to add it to the .gitignore)
and inside the .env we will put all the details inside the compose.yaml
in this project it was:
POSTGRES_USER=jobtracker
POSTGRES_PASSWORD=123456789
POSTGRES_DB=jobtracker_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
and if there was a LLM_API_Key , it will be here also

-------------------------------------------------------------------------------------------------------------

8.1- next to the main.py we will create **init**.py
8.2- we will create a folder named "core" : inside it we need : - **init**.py - config.py \* the both (**init.py**) is for connecting the whole modules in python together
-- now inside the config.py we will write everything we want to control in our project like this:
---------using the pydantic library-------
from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
model_config = SettingsConfigDict(env_file=".env") # if u change this app_name it is what will be shown in the doc swagger
app_name: str = "Job Tracker"

            # Database details
            postgres_user: str
            postgres_password: str
            postgres_db: str
            postgres_host: str = "localhost"
            postgres_port: int = 5433
            # if we are using an api from an llm
            # gemini_api_key: str

         # this code here is for exporting it so we will use it in the main.py
         settings = Settings()

-------------------------------------------------------------------------------------------------------------

9- now in the main.py:

     from fastapi import FastAPI
     from app.core.config import settings

     app = FastAPI(title=settings.app_name)

    # now we can create our first entrypoint
    @app.get("/")
    async def home():
        return {"message": "Welcome to the Job Tracker API"}

-------------------------------------------------------------------------------------------------------------

10.1- after this we need to start connection with the database , with sqlalchemy:
    uv add "sqlalchemy[asyncio]" asyncpg

10.2- after we add the sqlalchemy, in the config.py after the configuration we aill add this:

        dialect+driver://username:password@host:port/database
        postgresql+asyncpg://jobtracker:123456789@localhost:5433/jobtracker_db
        but we use URL from sqlalchemy:

    from sqlalchemy import URL

    @property
    def database_url(self) -> URL:
        database_url = URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )
        return database_url
     # the property let us call the function without the () so it will return this:
        postgresql+asyncpg://jobtracker:***@localhost:5433/jobtracker_db

-------------------------------------------------------------------------------------------------------------

11.1- we will create a folder in the app folder we call it "db" , it will have session.py (for the connection with the database) , inside it we will create the engine, the engine manages our database connections
****************************************
!!!!!!!! let's translate , the engine manage the connection , but we work through sessions , and the session is one piece of work with the database , and it lasts for one request
and why it matters????
let's say you send a 200$ to your friends account , the money leave your account , and in the middle something went wrong ..........the money is gone!!!! NO, everything will be cancelled and like nothing happend
-and each user with each request will hae one session
- the session does not hold the connection , it borrows the connection from the engine when it want to talk to the database and gives it back when it's done
- and ofcourse we are not going to create a session for every user manually , we will create a factory that with every press of the button it will create a session
****************************************

11.2- we will add for the session.py:
    from sqlalchemy.ext.asyncio import async_sessionmaker
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    # expire_on_commit=false ----}something you add for async applications,normally after saving sqlalchemy
    forgets the value and reloads them the next time we read them ......in async code , the automatic reload
    causes an error , that is why we turn it off, (expire_on_commit=False)

-------------------------------------------------------------------------------------------------------------

12- let's talk about the Dependancy Injection:
"""
@app.get("/time")
async def show_time():
    # get the current time as text , like 14:35:20
    now = datetime.now().strftime("%H:%M:%S")
    return {"time": now}

@app.get("/greeting")
async def greeting():
    # the same line copied again
    now = datetime.now().strftime("%H:%M:%S")
    return {"message": f"Hello,it is {now}"}
"""
in this code :

Dependancy: time is dependancy
Injection: fastapi is providing the dependancy to a function

"""

so we will create a function that will get the time and then :

    from typing import Annotated
    from fastapi import Depends

    async def get_time():
        return datetime.now().strftime("%H:%M:%S")

                                               #note like : this is time
    @app.get("/time")         #Annotated [type,note]
    async def show_time(now: Annotated[str, Depends(get_time)]):
        # get the current time as text , like 14:35:20
        return {"time": now}

-------------------------------------------------------------------------------------------------------------

13- each route need a session so wwe will create a function for the session dependancies in the session.py:

            async def get_db():
                async with SessionLocal() as session:
                    yield session

- so now in the route , we will:
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.db.session import get_db
        from sqlalchemy import text

    ***** after this in every route we will create the session for the database like this(make sure docker
          container is working to connect to the database):

            @app.get("/health")
            async def health(db: Annotated[AsyncSession, Depends(get_db)]):
                await db.execute(text("SELECT 1"))
                return {"status": "healthy", "database": "ok"}

-------------------------------------------------------------------------------------------------------------

14- we need to change the compose.yaml so it won't haev the password and other things:

            services:
            db:
                image: postgres:18-trixie
                env_file:
                - ./backend/.env
                ports:
                - "127.0.0.1:5433:5432"
                volumes:
                - pgdata:/var/lib/postgresql

            volumes:
            pgdata:

now push the project to github

-------------------------------------------------------------------------------------------------------------

15- we will use alembic to modify and change things in our database like tables ......:
        inside db folder we will create base.py and what we will write is it we will right it one time only , and we use it to never write sql queries so we will use ORM
        - so we can create database tables with python classes:
            from sqlalchemy.orm import DeclarativeBase

            class Base(DeclarativeBase):
                pass

and why this only , because it will let us write a python class , and it will translate it to a sql query

-------------------------------------------------------------------------------------------------------------

16- now create a new folder named models inside it a __init__.py, now for each tables we will create a new file for it:
        import uuid
        from datetime import datetime
        from sqlalchemy import DateTime, String, func
        from sqlalchemy.orm import Mapped, mapped_column
        from app.db.base import Base

and in each one , we will create the shape of the table (blueprint) , but the alembic who will create the table , we only design the shape:

    class User(Base):
        __tablename__ = "users"             # the name of the table

        #    then the columns like this
        #    Mapped[the type]       mapped_column(the configuration)

        id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
        email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
        hashed_password: Mapped[str] = mapped_column(String(255))
        full_name: Mapped[str] = mapped_column(String(100))
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    but this is only the shape , the table is not created , we need to migrate!!!!!!

-------------------------------------------------------------------------------------------------------------

17- with alembic we create the tables ,
    BBBBBBBBEEEEEEEEEEEE AWARE!!!!!!!!!
    alembic create tables that are not existed yet , it can change or modify an existed table

    so let's install alembic(but remember to be inside the backend directory):
    - uv add alembic

    and then we have a setting up for it :

    - uv run alembic init -t async alembic -------------(alembic = this is the folder name)

    this will create a new folder named alembic , and inside it we will have some files and all we need is the env.py(and these changes will do it one time only for every new project):
    1- settings
    2- base
    3- where is the models


    where:
        line 10: from app.core.config import settings
                 from app.db.base import Base
                 import app.models  -----------------------when this is imported the __init__.py will
                                                            be called so this is why it is like this

        line 16: after the config=context.config:
            config.set_main_option(
                "sqlalchemy.url",
                settings.database_url.render_as_string(hide_password=False).replace("%", "%%"),
            ),

        line 32: the target_metadata:
            target_metadata = Base.metadata


    so we will go to the models/__init.py__:

    each model u create(i mean table) , we should import it in this specific __init__.py , beacuse alembic need to see all these models:

   - from app.models.user import User



     after every thing , we can try it with this :

       - uv run alembic current

       if it return this(it worked!!!!!) :
            INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
            INFO  [alembic.runtime.migration] Will assume transactional DDL.

-------------------------------------------------------------------------------------------------------------

18-

-------------------------------------------------------------------------------------------------------------

19-

-------------------------------------------------------------------------------------------------------------

20-

-------------------------------------------------------------------------------------------------------------

21-

-------------------------------------------------------------------------------------------------------------

22-

-------------------------------------------------------------------------------------------------------------

23-

-------------------------------------------------------------------------------------------------------------

24-

-------------------------------------------------------------------------------------------------------------

25-

-------------------------------------------------------------------------------------------------------------

26-

-------------------------------------------------------------------------------------------------------------













    -->
