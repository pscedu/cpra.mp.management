from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyQuery, OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from cpra.mp.management.controllers.token_controllers import get_token
from cpra.mp.management.controllers.user_controllers import get_user
from cpra.mp.management.models.db_models import User
from cpra.mp.management.models.request_models import RoleTypes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/management/login/", auto_error=False)
query_scheme = APIKeyQuery(name="access_token", auto_error=False)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    bearer_token: str = Depends(oauth2_scheme),
    query_token: str = Depends(query_scheme),
):
    token = bearer_token or query_token
    if token is None:
        raise credentials_exception
    try:
        payload = get_token(token)
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if username is None or token_type != "access":
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


async def get_current_active_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    if current_user.role != RoleTypes.admin:
        raise HTTPException(status_code=400, detail="Only admin users can use this endpoint")
    return current_user
