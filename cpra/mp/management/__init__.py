from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
import requests
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError, PyJWTError
from pydantic import BaseModel

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

fake_users_db = {
    "jpuerto": {
        "username": "jpuerto",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "disabled": False,
    }
}

# ClickUp Settings
client_id = "0D2C3KLO7ETCTIBR72Z6885TJYZ9JN4W"
client_secret = "Y7FKKTVWY49OP5HZ8IENCGNXP9M5J5JFIZLVPKTJZ9ZJCADN5RGMDESOZMMWM1FX"
redirect_uri = "http://localhost:5000/management/v1/clickup/callback"
authorization_base_url = "https://app.clickup.com/api"
token_url = "https://app.clickup.com/api/v2/oauth/token"

# ClickUp API token
api_token = "pk_89208365_SJ9TK5B5CCFAU13DD68WDH6GGXGSSY1W"
# api_token = '82415788_78820e51167b40f8aa2e20575000f6e39a3c511d3333cce1214c56c8edf6f18e'

# The headers, including the authorization token
headers = {"Authorization": api_token, "Content-Type": "application/json"}


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/management/v1/tokens/")


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    clickup_id: str | None = None
    clickup_access_token: str | None = None


def verify_password(password):
    # This will be replaced by LDAP
    return True


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return User(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password):
        return False
    return user


def create_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.get("/")
async def home():
    return "Welcome to the Management API!"


@app.get("/management/v1/clickup/oauth/")
async def clickup_oauth_get_auth_url(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    # Redirect the user to ClickUp's authorization URL
    clickup_oauth_url = f"{authorization_base_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    return {"clickup_oauth_url": clickup_oauth_url}


@app.post("/management/v1/clickup/oauth/")
async def clickup_oauth_post_oauth_code(
    current_user: Annotated[User, Depends(get_current_active_user)],
    oauth_code: str,
):
    # Exchange the authorization code for an access token
    token_response = requests.post(
        token_url,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": oauth_code,
            "redirect_uri": redirect_uri,
        },
    )

    if token_response.status_code == 200:
        access_token = token_response.json().get("access_token")
        # We update the user with the click_up access token
        return {"access_token": access_token}
    else:
        error_detail = token_response.json()
        raise HTTPException(status_code=token_response.status_code, detail=error_detail)


@app.get("/management/v1/clickup/callback/")
async def clickup_oauth_callback(request: Request):
    # Get the authorization code from the callback query parameters
    oauth_code = request.query_params.get("code")
    if not oauth_code:
        raise HTTPException(status_code=400, detail="Authorization code not found.")
    else:
        return {"oauth_code": oauth_code}


@app.post("/management/v1/tokens/")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_token(
        data={"sub": user.username}, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@app.post("/management/v1/tokens/refresh/", response_model=Token)
async def refresh_access_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = get_user(fake_users_db, username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    # Generate new access token
    access_token = create_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_token(
        data={"sub": user.username}, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
