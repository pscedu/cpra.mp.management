from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyQuery, OAuth2PasswordBearer

from cpra.mp.management.controllers.token_controllers import get_valid_token_payload
from cpra.mp.management.controllers.user_controllers import get_user
from cpra.mp.management.models.request_models import RoleTypes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/management/login/", auto_error=False)
query_scheme = APIKeyQuery(name="access_token", auto_error=False)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class TokenUser:
    def __init__(
        self, token_type: str = "access", user_active: bool = True, user_role: str = None
    ):
        self.token_type = token_type
        self.user_active = user_active
        self.user_role = user_role

    def __call__(
        self,
        bearer_token: str = Depends(oauth2_scheme),
        query_token: str = Depends(query_scheme),
    ):
        payload = get_valid_token_payload(bearer_token or query_token, self.token_type)
        if payload is None:
            raise credentials_exception

        user = get_user(user_info={"username": payload.get("sub")})
        if not user:
            raise credentials_exception

        if self.user_active and user.disabled:
            raise HTTPException(status_code=400, detail="Inactive user")

        if self.user_role and user.role != self.user_role:
            raise HTTPException(
                status_code=400,
                detail=f"Only users with the role {str(self.user_role)} can use this endpoint",
            )

        return user


get_current_active_user = TokenUser()
get_current_active_admin = TokenUser(user_role=RoleTypes.admin)
get_refresh_user = TokenUser(token_type="refresh")
