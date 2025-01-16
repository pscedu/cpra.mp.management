from datetime import timedelta
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from cpra.mp.management.database import engine
from cpra.mp.management.dependencies import get_current_active_user, get_current_user
from cpra.mp.management.models.db_models import User
from cpra.mp.management.settings import settings
from cpra.mp.management.controllers.token_controllers import create_token

COOKIE_NAME = "clickup_oauth_temp_token"

router = APIRouter(prefix="/clickup")


@router.get("/", response_class=RedirectResponse)
async def clickup_login(
    current_user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
    response: Response
):
    # Set a cookie containing a dedicated access token that will be
    # read on callback.
    data = {"sub": current_user.username}
    cookie_token = create_token(data=data, expires_delta=timedelta(minutes=15))
    response.set_cookie(key=COOKIE_NAME, value=cookie_token)

    clickup_settings = settings.clickup_settings
    # Redirect the user to ClickUp's authorization URL
    return f"{clickup_settings.authorization_url}?client_id={clickup_settings.client_id}&redirect_uri={request.url_for("clickup_callback")}&response_type=code"


@router.get("/callback", response_class=RedirectResponse)
async def clickup_callback(code: str, request: Request):
    # Determine the current user from the cookie token.
    current_user = get_current_active_user(
        get_current_user(request.cookies.get(COOKIE_NAME))
    )

    # Exchange the authorization code for an access token
    clickup_settings = settings.clickup_settings
    token_response = requests.post(
        clickup_settings.token_url,
        data={
            "client_id": clickup_settings.client_id,
            "client_secret": clickup_settings.client_secret,
            "code": code,
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
            },
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

        return f"{clickup_settings.portal_redirect_uri}?status=success"
    else:
        error_detail = token_response.json()
        raise HTTPException(status_code=token_response.status_code, detail=error_detail)
