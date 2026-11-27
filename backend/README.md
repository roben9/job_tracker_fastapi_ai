-- Active: 1790186618178@@127.0.0.1@3306

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

13- each route need a session so we will create a function for the session dependancies in the session.py:

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
        inside db folder we will create base.py and what we will write in it is one time only , and we use it to never write sql queries so we will use ORM
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

18- check that docker andthe database is running , and run this command:

    - uv run alembic revision --autogenerate -m "create users table"

    this mean:
        we are telling alembic to create a new migration file , and the (--autogenerate) tells alembic to work out the changes byitself,by comparing our models with the database, the (-m) create the users table with a message ("create users table") about what changes we have done

    so if you open the alembic/versions/1523125673_create_users_table
    and this is what  we call (THE MIGRATION FILE), you will see the comparing alembic did to get the right things for our table in the upgrade(), and in the downgrade() will see the undo of these changes

    - and to use the migration file, we will use the upgrade() with this command:
            -  uv run alembic upgrade head
      if it gave u this:
            INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
            INFO  [alembic.runtime.migration] Will assume transactional DDL.
            INFO  [alembic.runtime.migration] Running upgrade  -> 79db5bd516fc, create users table

      this means it worked!!!!!!!

    - let's see this table in the database , we have two ways:

        1- open pgadmin software and connect to ur database (with the details in the .env file , like username and password)
        ------------- servers----register----server...............

        2- or u can download the extension (sqltools) and its driver (@tag:sqltools-driver) get the postgres and else:
                - then connect your databse like the details in your .env file
                - so now it is connected and u can see it on the left panel
                - navigate to /schemas/public/tables/users and press right then(show table records)


-------------------------------------------------------------------------------------------------------------

19- now let's talk about hashing the password, we need to know:
        1- how to hash the password
        2- how to verify the hashed password

    in the core folder we will create security.py, we will have in it 2 functions , one to hash and one to verify.

    we have in python a library for that it is PWD for hashing, and it use an algorithm called Argon 2
    and this is the FASTAPI docs recommendation , because it is developed to be slow , for the security reasons , like if an attacker , beacuse the attacker will try billions of guesses , so this will be expensive for the attacker

    let's install it (again make sure u r in the backend folder):
        -     uv add "pwdlib[argon2]"

    and in the security.py:

            from pwdlib import PasswordHash
            # this is the main player
            password_hash = PasswordHash.recommended()  # this recommend will give the argon2

            # this for hashing the password
            def hash_password(password: str) -> str:
                return password_hash.hash(password)

            # this for verify the password
            def verify_password(password: str, hashed_password: str) -> bool:
                return password_hash.verify(password, hashed_password)

    *******but there is some issues:
             1- incoming data (password from the user)
             2- outgoing data (hashed from the server)

        - we fix this with SCHEMA
            - this is a pydantic class , it describe what data is allowed to come , and what data is allowed to go out (in django , it is like the serializers, which convert the model object to json format)
            - in FASTAPI , schema do the same thing

    how to do this????? inside the app folder we will create a new folder called schemas (as always we need to create in it a __init__.py):

        - inside , we will create a user.py for the models/user.py model , this file we will use this schema in the request and response lifecycle , it will not do anything with the database tables,here we will handle:
            1- what the user will send us when signing up (eg. should be 8 characters)
                in simple words:  "what are we expecting from the user"
                * so here , we should handle :
                    1- email
                    2- full name
                    3- hashed password

            2- what we will send the user:
                * we need to use some special things :
                    1-model config from the ConfigDict(from_attributes=True)
                        # becuase pydantic read details like this (user["email"]), but user is an alembic
                        object so it should read like this (user.email) {an attributes not dictionary}
                    2- the other columns in the user table: email,fullname,created_at


-------------------------------------------------------------------------------------------------------------

20- Store the User data:

    - we will hae a lot of routes , so we will create a folder in app folder , call it api
    - inside it create a file for the auth (singup,login,forget password......)
    - create the prefix for all the auth api like:
        router = APIRouter(prefix="/auth", tags=["auth"])

            *  http://127.0.0.1:8000/auth/singup
                # in the url (/auth) is the prefix

            * the tag, is for the docs , when u open the docs FASTAPI will create section called it auth (tags=["auth"]) and make every api belong to the auth inside this section

    - we will create the route:
    @router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
                # the endpoint , and then what is the response(will call UserOut) and the status code is 201 for creating
        # for every route we will add the db session as we talked before
    async def signup(user_in: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
        # first we need to hash the password , and we run it in another thread because argon2 will take time (as we said)
        hashed = await run_in_threadpool(hash_password, user_in.password)

        # put the user inputs in its fields (from app/models/user.py)
        user = User(email=user_in.email, hashed_password=hashed, full_name=user_in.full_name)

        # finally we need to stage it for saving
        # and the staging is because alembic do everything to the end OR....... nothing gonna be done

        db.add(user)  # this is just staging
        await db.commit()  # saving the data
        await db.refresh(user)
        # refreshing the user object so the id and the created_at will launch and be created

        # after this return , FASTAPI will call UserOut() and match the things in it with the data we provide
        # and notice there is no hash paassword in the UserOut , so the password won't be sent to the user
        return user

    - now after we create the api and the router, we should tell the main.py that there is more routes to take notice for :
        * after we create app = FastAPI(title=settings.app_name):
            app.include_router(auth.router)

    - try it in the docs and add a user and check the database , NICEEEEEEEEE!!!!!!!!!!!

-------------------------------------------------------------------------------------------------------------

21- there is 2 problems:

        1- when i enter an already existed email , the server will throw a 500 status code and the app crash
        2- when i enter the same email but in upper case(hello = HELLO) , the database sees it as different email but in real life on the web it is the same email

    * the fix :

        we will make every user input in the signup to lower case,and then we will go to the database and check there if this email is already exist , and then we will decide :
            1- throw an exception (like 409_conflict)
            2- make it pass and enter the database

                email = user_in.email.lower()
                result = await db.execute(select(User).where(User.email == email))
                if result.scalar_one_or_none():
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already exists!!!")

-------------------------------------------------------------------------------------------------------------

22- Tokens:

    we need :
        1- access token (expires in 30 minutes (the default))
        2- refresh token (expires in 7 days (the default))

    and we create and read them by a library called PYJWT (json web token), as always using uv (as always in the backend folder):
        - uv add pyjwt

    after this , we need to create the secret key,this is how, we have an utility in python named "secrets":
        - uv run python
            * in the python :
                import secrets
                print(secrets.token_hex(32))

    this will give u a key (generated locally, never generate it on a website)

    take this key and put it in the .env file:
        * SECRET_KEY=*****************************

    in the config.py(under the postgres config):
        secret_key: str

    *********** this key will sign those tokens , for security and maitainability , because this key will help your backend to know that this tokens are generated from our application , not modified

-------------------------------------------------------------------------------------------------------------

23- now for the tokens , in the config.py we will add this expiring time:
        access_token_expire_minutes: int = 30(the default we can change it)
        refresh_token_expire_days: int = 7(the default we can change it)

    * now we need 3 small function to create these 2 tokens,in the security.py:
    # subject says which user this token belongs to , so this will be the user ID
        1- create token
        2- create access token
        3- create refresh token

    * we will use the "HS256" ALGORITHM
    * and we add it to the utc for each user, not the local timezone, because utc is a thing every server understand it,and "timedelta" is the way for python to detect time in the right way
    * then we need a payload(some meta data we send it with the access token)
    * finally we need to sign the tokens with the SECRET_KEY with the JWT:
        - encode()
        - give it the payload
        - the secret key
        - the algorithm

    and then how to check if it worked:
        - uv run python
        - from app.core.security import create_access_token,create_refresh_token
        - print(create_access_token("1"))
    this will give u a token , go to : https://www.jwt.io/
    and put the token there and u will see the json breakdown of it


-------------------------------------------------------------------------------------------------------------

24- we will create a schema for the token in the schema folder token.py:
        inside it is : what we send back after a successful login,and the type: "bearer" mean(whoever hold it is the owner)
        and we will use something in FASTAPI called
    now in the OAuth2PasswordRequestForm.......it is a form data from the user (in our project we take form the user email and password and fullname)

    * now in the auth.py , we will create a new endpoint for the login API(OAuth2PasswordRequestForm):

        so we create a new API (/login)
        and we need 2 dependancies , the database session and the form_data so the email and the passowrd are comming from it
        ********* in the OAuth2PasswordRequestForm, it has (username , password) , but because in our project we are asking the user for his email , so ............. form_data.username == user.email

    * so we take a form_data (which is from python OAuth2......) and have the username and password
    * we will take the email (to lower case as previous) and see if it is in the database
    * if the email is not exist, raise an 401 error(not found user with this email)
    * if the email existed , check if the password is right?? the same thing in the threadpool (because the argon2 will take time)################we will use the verify_password we created earlier
    * if the email and the password correct , then create the tokens

-------------------------------------------------------------------------------------------------------------

25- let's create and end point to see the profile details:

    - in the api folder we will create a file named users.py:
        here we will create all the api for the users like get delete update .......

    simple as the other:
        - we will create the router
        - include it in the main.py app
        - create the endpoint

    - when we try it it will give a 500 error, because there is no access token in the request , and this is why we create the payload:
        * the backend send it to the frontend
        * when the frontend ask for something , they will provide the same payload with the request

    - the user have it when we send the token (encoded), and now when he ask for something , first thing we will o is to decode it
        * from the FASTAPI documentation, we will use the OAuthPasswordBearer (because our token is Bearer):
            ------ oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/auth/login") ------

    so go to security.py and create a decode_token() function:

        - it will take the payload and decode it
        - if there is no token then None
        - if the type of the payload is not "access" as we expected then None
        - else return the sub ( which is our user ID) :
            {
            "sub": "1",
            "type": "access",   -----------------------------------this is from the jwt.io
            "exp": 1795807398
            }

-------------------------------------------------------------------------------------------------------------

26-

-------------------------------------------------------------------------------------------------------------













    -->
