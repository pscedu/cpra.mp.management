from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

from cpra.mp.management.models.db_models import User
from cpra.mp.management.settings import settings


def create_token(user: User, token_type: str, expires_delta: timedelta | None = None) -> str:
    to_encode = {"sub": user.username, "type": token_type}

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def get_token_payload(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def get_valid_token_payload(token: str, token_type: str = "access") -> bool:
    """Check whether a token is valid and is of the expected type.
    If so, return its payload."""
    if token is None:
        return None
    try:
        payload = get_token_payload(token)
    except InvalidTokenError:
        return None

    if payload.get("sub") is None or payload.get("type") != token_type:
        return None

    return payload
