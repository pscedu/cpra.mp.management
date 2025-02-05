from datetime import datetime, timedelta, timezone

import jwt

from cpra.mp.management.settings import settings
from cpra.mp.management.models.db_models import User


def create_token(
    user: User,
    token_type: str,
    expires_delta: timedelta | None = None
) -> str:
    to_encode = {"sub": user.username, "type": token_type}

    # TODO: This data probably should come from a separate endpoint
    # (e.g., /user/me).
    if token_type == "access":
        to_encode.update(
            {
                "name": user.full_name,
                "clickup": user.clickup_id,
                "email": user.email
            }
        )

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def get_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
