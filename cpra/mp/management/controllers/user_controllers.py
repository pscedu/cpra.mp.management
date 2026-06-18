from typing import Union

from sqlmodel import Session, func, select

from cpra.mp.management.database import engine
from cpra.mp.management.models.db_models import User


def get_user(user_info: dict) -> Union[User, None]:
    username = user_info.get("username")
    email = user_info.get("email")
    with Session(engine) as session:
        user = session.exec(
            select(User).where(func.lower(User.email) == func.lower(email))
        ).first()
        if not user:
            user = session.exec(
                select(User).where(func.lower(User.username) == func.lower(username))
            ).first()

    return user


def get_translated_clickup_users(clickup_users: list[dict], cached_clickup_user_mapping: dict):
    translated_users = []
    remapped_clickup_users = {}

    for clickup_user in clickup_users:
        clickup_id = int(clickup_user["id"])

        # If the clickup_id has already been matched, return that mapping
        if cached_mapping := cached_clickup_user_mapping.get(clickup_id):
            translated_users.append(cached_mapping)

        # Otherwise, we will want to try to look it up
        else:
            remapped_clickup_users[clickup_id] = clickup_user

    # We found all of clickup users from the cache
    if len(remapped_clickup_users) == 0:
        return translated_users

    # Get the list of the users that exist internally
    internal_users = get_users_by_clickup_ids(list(remapped_clickup_users.keys()))

    # Iterate over the list of internal users
    for internal_user in internal_users:
        # Pop the matching entries from remapped_clickup_users
        remapped_clickup_users.pop(internal_user.clickup_id, None)

        # Add the user to the cache, and add it to the translated_users list
        cached_clickup_user_mapping[internal_user.clickup_id] = internal_user
        translated_users.append(internal_user)

    for clickup_id, clickup_user in remapped_clickup_users.items():
        cached_clickup_user_mapping[clickup_id] = clickup_user
        translated_users.append(clickup_user)

    return translated_users


def get_users_by_clickup_ids(clickup_ids) -> Union[list[User], list]:
    with Session(engine) as session:
        return session.exec(select(User).where(User.clickup_id.in_(clickup_ids))).all()


def get_users_by_ids(user_ids) -> Union[list[User], None]:
    with Session(engine) as session:
        return session.exec(select(User).where(User.id.in_(user_ids))).all()
