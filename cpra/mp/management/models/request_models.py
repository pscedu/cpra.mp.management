from enum import Enum

from pydantic import BaseModel


class RoleTypes(str, Enum):
    user = "user"
    admin = "admin"


class User(BaseModel):
    username: str
    full_name: str | None = None
    disabled: bool | None = False
    role: RoleTypes | None = RoleTypes.user
