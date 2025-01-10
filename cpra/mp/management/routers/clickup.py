from typing import Annotated

import requests
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlmodel import Session

from cpra.mp.management.database import engine
from cpra.mp.management.dependencies import get_current_active_user
from cpra.mp.management.models.db_models import User
from cpra.mp.management.settings import settings

router = APIRouter(prefix="/clickup/oauth")


@router.get("/")
async def clickup_oauth_get_auth_url(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    clickup_settings = settings.clickup_settings
    # Redirect the user to ClickUp's authorization URL
    clickup_oauth_url = f"{clickup_settings.authorization_url}?client_id={clickup_settings.client_id}&redirect_uri={clickup_settings.redirect_uri}&response_type=code"
    return {"clickup_oauth_url": clickup_oauth_url}


@router.post("/")
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

        # TODO: Change what we return here. Front-end doesn't need this information.
        return {"access_token": access_token}
    else:
        error_detail = token_response.json()
        raise HTTPException(status_code=token_response.status_code, detail=error_detail)
