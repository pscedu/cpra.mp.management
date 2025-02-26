from typing import Annotated
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from cpra.mp.management.database import engine
from cpra.mp.management.dependencies import get_current_active_user, query_scheme
from cpra.mp.management.models.db_models import User as DBUser
from cpra.mp.management.models.response_models import User as ResponseUser
from cpra.mp.management.settings import settings

router = APIRouter(prefix="/clickup")


@router.get("/", response_class=RedirectResponse)
async def clickup_login(
    request: Request,
    # Include current user dependency to verify token.
    current_user: DBUser = Depends(get_current_active_user),
    query_token: str = Depends(query_scheme),
):
    clickup_settings = settings.clickup_settings
    passthrough_params = {"access_token": query_token}
    # Redirect the user to ClickUp's authorization URL
    params = {
        "client_id": clickup_settings.client_id,
        "redirect_uri": f"{request.url_for('clickup_callback')}?{urlencode(passthrough_params)}",
        "response_type": "code",
    }
    return f"{clickup_settings.authorization_url}?{urlencode(params)}"


@router.get("/callback", response_class=RedirectResponse)
async def clickup_callback(
    request: Request,
    code: str,
    current_user: DBUser = Depends(get_current_active_user),
):
    # Exchange the authorization code for an access token
    clickup_settings = settings.clickup_settings
    token_response = requests.post(
        clickup_settings.token_url,
        data={
            "client_id": clickup_settings.client_id,
            "client_secret": clickup_settings.client_secret,
            "code": code,
            "redirect_uri": request.url_for("clickup_callback"),
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
                "Authorization": f"Bearer {access_token}",
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

                params = {"clickup_id": current_user.clickup_id, "status": "success"}
                return f"{clickup_settings.portal_redirect_uri}?{urlencode(params)}"
    else:
        error_detail = token_response.json()
        raise HTTPException(status_code=token_response.status_code, detail=error_detail)


@router.put("/disconnect", response_model=ResponseUser)
async def clickup_disconnect(
    request: Request,
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    current_user.clickup_access_token = None
    current_user.clickup_id = None
    with Session(engine) as session:
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
        return current_user
