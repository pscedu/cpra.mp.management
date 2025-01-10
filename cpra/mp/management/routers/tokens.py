from fastapi import APIRouter, Body, HTTPException, status
from cpra.mp.management.settings import settings
import requests
from urllib.parse import urlencode
from typing import Annotated
from cpra.mp.management.models.response_models import Token
from cpra.mp.management.controllers.user_controllers import get_user
from cpra.mp.management.controllers.token_controllers import create_token, get_token
from datetime import timedelta
from jwt import PyJWTError

router = APIRouter(
    prefix="/tokens"
)


@router.get("/")
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


@router.post("/", response_model=Token)
async def login_for_access_token(
    oauth_code: Annotated[str, Body(embed=True)],
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


@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: Annotated[str, Body(embed=True)]):
    try:
        payload = get_token(refresh_token)
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
