from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone
from typing import Annotated, Union

import jwt
import requests
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError, PyJWTError
from pydantic import BaseModel
from pydantic_settings import BaseSettings

import json


def load_config(file_path: str):
    with open(file_path, "r") as f:
        return json.load(f)


class CILogonSettings(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str
    server_metadata_url: str = "https://cilogon.org/.well-known/openid-configuration"
    grant_type: str = "authorization_code"


class ClickUpSettings(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    authorization_url: str
    token_url: str
    api_token: str


class Settings(BaseSettings):
    secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    jwt_algorithm: str
    ci_logon_settings: CILogonSettings
    clickup_settings: ClickUpSettings
    debug: bool = True


fake_users_db = {
    "jpuerto": {
        "username": "jpuerto",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "disabled": False,
    }
}
# Create an instance of Settings
settings = Settings(**load_config("config.json"))
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


def verify_password(password) -> bool:
    # This will be replaced by LDAP
    return True


def get_user(db, user_info: dict) -> Union[User, None]:
    # TODO: Update to actually use DB
    # Check based on username first and then use email
    return db["jpuerto"]


def authenticate_user(fake_db, user_info: dict, password: str) -> Union[User, bool]:
    user = get_user(fake_db, user_info)
    if not user:
        return False
    if not verify_password(password):
        return False
    return user


def create_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, user_info={"username": token_data.username})
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
    clickup_settings = settings.clickup_settings
    # Redirect the user to ClickUp's authorization URL
    clickup_oauth_url = f"{clickup_settings.authorization_url}?client_id={clickup_settings.client_id}&redirect_uri={clickup_settings.redirect_uri}&response_type=code"
    return {"clickup_oauth_url": clickup_oauth_url}


@app.post("/management/v1/clickup/oauth/")
async def clickup_oauth_post_oauth_code(
    current_user: Annotated[User, Depends(get_current_active_user)],
    oauth_code: str,
):
    # Exchange the authorization code for an access token
    clickup_settings = settings.clickup_config
    token_response = requests.post(
        clickup_settings.token_url,
        data={
            "client_id": clickup_settings.client_id,
            "client_secret": clickup_settings.client_secret,
            "code": oauth_code,
            "redirect_uri": clickup_settings.redirect_uri,
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


@app.get("/management/v1/tokens/")
async def get_oidc_login_url() -> str:
    ci_logon_settings = settings.ci_logon_settings
    metadata = requests.get(ci_logon_settings.server_metadata_url).json()
    authorization_endpoint = metadata.get("authorization_endpoint")
    params = {
        "client_id": ci_logon_settings.client_id,
        "response_type": "code",
        "scope": ci_logon_settings.scope,
        "redirect_uri": ci_logon_settings.redirect_uri,
    }
    redirect = f"{authorization_endpoint}?{urlencode(params, doseq=True)}"
    return redirect


@app.post("/management/v1/tokens/")
async def login_for_access_token(
    oauth_code: str,
) -> Token:
    ci_logon_settings = settings.ci_logon_settings
    metadata = requests.get(ci_logon_settings.server_metadata_url).json()

    # Get an access token using the oauth_code
    token_endpoint = metadata.get("token_endpoint")
    token_response = requests.post(
        token_endpoint,
        data={
            "grant_type": ci_logon_settings.grant_type,
            "client_id": ci_logon_settings.client_id,
            "client_secret": ci_logon_settings.client_secret,
            "code": oauth_code,
            "redirect_uri": ci_logon_settings.redirect_uri,
        },
    )

    if token_response.status_code == 200:
        access_token = token_response.json().get("access_token")

        # Get user information from CILogon using access token
        userinfo_endpoint = metadata.get("userinfo_endpoint")
        userinfo_response = requests.post(
            userinfo_endpoint, data={"access_token": access_token}
        )
        if userinfo_response.status_code == 200:
            userinfo = userinfo_response.json()
        else:
            raise HTTPException(
                status_code=userinfo_response.status_code,
                detail=userinfo_response.json(),
            )
    else:
        raise HTTPException(
            status_code=token_response.status_code, detail=token_response.json()
        )

    user = authenticate_user(fake_users_db, userinfo, "")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found based on user info",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.access_token_expires_minutes),
    )
    refresh_token = create_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@app.post("/management/v1/tokens/refresh/", response_model=Token)
async def refresh_access_token(refresh_token: str):
    try:
        payload = jwt.decode(
            refresh_token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = get_user(fake_users_db, {"username": username})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user"
        )

    # Generate new access token
    access_token = create_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.access_token_expires_minutes),
    )
    refresh_token = create_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
