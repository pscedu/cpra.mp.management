from typing import Union

from sqlmodel import Session, select

from cpra.mp.management.database import engine
from cpra.mp.management.models.db_models import User


def get_user(user_info: dict) -> Union[User, None]:
    username = user_info.get("username")
    email = user_info.get("email")
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            user = session.exec(select(User).where(User.username == username)).first()

    return user
