from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from cpra.mp.management.database import engine
from cpra.mp.management.dependencies import get_current_active_user
from cpra.mp.management.models.db_models import User as DB_User
from cpra.mp.management.models.response_models import User as ResponseUser

router = APIRouter(prefix="/users")


@router.get("/", response_model=list[ResponseUser])
async def get_user(
    current_user: Annotated[DB_User, Depends(get_current_active_user)],
):
    with Session(engine) as session:
        users = session.exec(select(DB_User)).all()
        return users
