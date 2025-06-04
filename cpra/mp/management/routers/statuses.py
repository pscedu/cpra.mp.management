from typing import Annotated

from fastapi import APIRouter, Depends

from cpra.mp.management.controllers.clickup_controller import ClickUpController
from cpra.mp.management.dependencies import get_current_active_user
from cpra.mp.management.models.db_models import User as DBUser

router = APIRouter(prefix="/statuses")


@router.get("/", response_model=dict)
async def get_tasks(
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    return ClickUpController().status_bulk_get()
