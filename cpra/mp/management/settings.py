import json
from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings


@lru_cache
def load_config(file_path: str):
    with open(file_path, "r") as f:
        return json.load(f)


class CILogonSettings(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str
    server_metadata_url: str = "https://cilogon.org/.well-known/openid-configuration"
    grant_type: str = "authorization_code"


class ClickUpSettings(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    authorization_url: str
    token_url: str
    api_token: str
    base_api_url: str


class Settings(BaseSettings):
    secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    jwt_algorithm: str
    ci_logon_settings: CILogonSettings
    clickup_settings: ClickUpSettings
    db_url: str
    debug: bool = True


settings = Settings(**load_config("config.json"))
