from pydantic import BaseModel
from enum import Enum


class RoleTypes(str, Enum):
    user = "user"
    admin = "admin"


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = False
    role: RoleTypes | None = RoleTypes.user
