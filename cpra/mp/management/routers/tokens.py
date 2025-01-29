from datetime import timedelta
from typing import Annotated
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Body, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from jwt import PyJWTError
from sqlmodel import Session

from cpra.mp.management.controllers.token_controllers import create_token, get_token
from cpra.mp.management.controllers.user_controllers import get_user
from cpra.mp.management.database import engine
from cpra.mp.management.models.response_models import Token
from cpra.mp.management.settings import settings

router = APIRouter(prefix="/login")


@router.get("/", response_class=RedirectResponse)
async def oidc_login(request: Request):
    ci_logon_settings = settings.ci_logon_settings
    metadata = requests.get(ci_logon_settings.server_metadata_url).json()
    authorization_endpoint = metadata.get("authorization_endpoint")
    params = {
        "client_id": ci_logon_settings.client_id,
        "response_type": "code",
        "scope": ci_logon_settings.scope,
        "redirect_uri": request.url_for("oidc_callback"),
    }
    return f"{authorization_endpoint}?{urlencode(params, doseq=True)}"


@router.get("/callback", response_class=RedirectResponse)
async def oidc_callback(code: str, request: Request):
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
            "code": code,
            "redirect_uri": request.url_for("oidc_callback"),
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

    # Find user based on email
    user = get_user(userinfo)
    if not user:
        # If user is not found with email return error
        # TODO: Change to add user once white-list expectation is changed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found based on user info",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if userinfo.get("idp_name") != "ACCESS":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unexpected Identity Provider used. Please use ACCESS Identity Provider.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Make sure user has username/name set.
    if not user.username or not user.full_name:
        # If there's no username/name, then lets set the username and full name
        user.username = userinfo.get("email")
        user.full_name = userinfo.get("name")
        with Session(engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)

    params = {
        "access_token": create_token(
            user,
            "access",
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        ),
        "refresh_token": create_token(
            user,
            "refresh",
            expires_delta=timedelta(days=settings.refresh_token_expire_days),
        ),
        "token_type": "bearer"
    }
    return f"{ci_logon_settings.portal_redirect_uri}?{urlencode(params, doseq=True)}"


@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: Annotated[str, Body(embed=True)]):
    try:
        payload = get_token(refresh_token)
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if username is None or token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = get_user({"username": username})
    if not user or user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    
    # Generate new access token
    access_token = create_token(
        user,
        "access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return Token(access_token=access_token, refresh_token=None, token_type="bearer")
