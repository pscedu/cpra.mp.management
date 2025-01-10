from datetime import datetime, timedelta, timezone
from typing import Annotated, Union
from urllib.parse import urlencode

import jwt
import requests
from fastapi import Depends, FastAPI, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError, PyJWTError
from pydantic import BaseModel
from sqlmodel import Session, select

from cpra.mp.management.database import engine
from cpra.mp.management.settings import settings
from cpra.mp.management.db_models import User

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/management/v1/tokens/")


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


def get_user(user_info: dict) -> Union[User, None]:
    username = user_info.get("username")
    email = user_info.get("email")
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            user = session.exec(select(User).where(User.username == username)).first()

    return user


def create_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(user_info={"username": username})
    if not user:
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
    oauth_code: Annotated[str, Body(embed=True)],
):
    # Exchange the authorization code for an access token
    clickup_settings = settings.clickup_settings
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
        current_user.clickup_access_token = access_token
        # We also need to introspect the clickup user id
        introspect_response = requests.get(
            f"{clickup_settings.base_api_url}/user",
            headers={
                "accept": "application/json",
                "Authorization": f"{access_token}",
            }
        )

        # TODO: Add checks and responses for failure cases
        #   - Access token GET fails
        #   - Introspection fails

        if introspect_response.status_code == 200:
            introspect_data = introspect_response.json()
            current_user.clickup_id = introspect_data.get("user", {}).get("id")
            with Session(engine) as session:
                session.add(current_user)
                session.commit()

        # TODO: Change what we return here. Front-end doesn't need this information.
        return {"access_token": access_token}
    else:
        error_detail = token_response.json()
        raise HTTPException(status_code=token_response.status_code, detail=error_detail)


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
    oauth_code: Annotated[str, Body(embed=True)],
) -> Token:
    print("hello world?")
    print(oauth_code)
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
        userinfo_response = requests.post(userinfo_endpoint, data={"access_token": access_token})
        if userinfo_response.status_code == 200:
            userinfo = userinfo_response.json()
        else:
            raise HTTPException(
                status_code=userinfo_response.status_code,
                detail=userinfo_response.json(),
            )
    else:
        raise HTTPException(status_code=token_response.status_code, detail=token_response.json())

    user = get_user(userinfo)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found based on user info",
            headers={"WWW-Authenticate": "Bearer"},
        )

    data = {"sub": user.username}
    access_token = create_token(
        data=data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = create_token(
        data=data,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@app.post("/management/v1/tokens/refresh/", response_model=Token)
async def refresh_access_token(refresh_token: Annotated[str, Body(embed=True)]):
    try:
        payload = jwt.decode(
            refresh_token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = get_user({"username": username})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    data = {"sub": user.username}
    # Generate new access token
    access_token = create_token(
        data=data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = create_token(
        data=data,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user
