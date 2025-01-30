from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from cpra.mp.management.database import engine
from cpra.mp.management.dependencies import (
    get_current_active_admin,
    get_current_active_user,
)
from cpra.mp.management.models.db_models import User as DB_User
from cpra.mp.management.models.request_models import User as RequestUser
from cpra.mp.management.models.response_models import User as ResponseUser

router = APIRouter(prefix="/users")


@router.get("/", response_model=list[ResponseUser])
async def get_user_list(
    current_user: Annotated[DB_User, Depends(get_current_active_user)],
):
    with Session(engine) as session:
        users = session.exec(select(DB_User)).all()
        return users


@router.get("/current_user", response_model=ResponseUser)
async def get_current_user(
    current_user: Annotated[DB_User, Depends(get_current_active_user)],
):
    return current_user


@router.get("/{user_id}", response_model=ResponseUser)
async def get_user(
    user_id: int,
    current_user: Annotated[DB_User, Depends(get_current_active_user)],
):
    with Session(engine) as session:
        user = session.get(DB_User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user


@router.put("/current_user", response_model=ResponseUser)
async def update_current_user(
    request_user: RequestUser,
    current_user: Annotated[DB_User, Depends(get_current_active_user)],
):
    with Session(engine) as session:
        user_data = request_user.model_dump(exclude_unset=True)
        if "role" in user_data:
            del user_data["role"]

        current_user.sqlmodel_update(user_data)
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
        return current_user


@router.put("/{user_id}", response_model=ResponseUser)
# TODO: Add permission checking. IE, only allowed if the current user is an admin.
async def update_user(
    user_id: int,
    request_user: RequestUser,
    current_user: Annotated[DB_User, Depends(get_current_active_admin)],
):
    with Session(engine) as session:
        user = session.get(DB_User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = request_user.model_dump(exclude_unset=True)
        user.sqlmodel_update(user_data)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
