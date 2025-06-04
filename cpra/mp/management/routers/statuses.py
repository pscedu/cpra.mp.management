from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from cpra.mp.management.controllers.clickup_controller import ClickUpController
from cpra.mp.management.controllers.user_controllers import (
    get_translated_clickup_users,
    get_users_by_ids,
)
from cpra.mp.management.dependencies import get_current_active_user
from cpra.mp.management.models.db_models import User as DBUser
from cpra.mp.management.models.request_models import Comment as RequestComment
from cpra.mp.management.models.request_models import Task as RequestTask
from cpra.mp.management.models.request_models import TaskUpdate as RequestTaskUpdate
from cpra.mp.management.models.response_models import Task as ResponseTask

router = APIRouter(prefix="/statuses")


@router.get("/", response_model=dict)
async def get_tasks(
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    return ClickUpController().status_bulk_get()
