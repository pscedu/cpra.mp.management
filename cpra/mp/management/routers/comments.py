from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException

from cpra.mp.management.controllers.clickup_controller import ClickUpController
from cpra.mp.management.controllers.user_controllers import get_users_by_clickup_ids
from cpra.mp.management.dependencies import get_current_active_user
from cpra.mp.management.models.db_models import User as DBUser
from cpra.mp.management.models.request_models import Comment as RequestComment
from cpra.mp.management.models.request_models import (
    CommentUpdate as RequestCommentUpdate,
)
from cpra.mp.management.models.response_models import Comment as ResponseComment

router = APIRouter(prefix="/comments")


@router.get("/{comment_id}/replies", response_model=List[ResponseComment])
async def get_comment_replies(
    comment_id: int,
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    try:
        replies = ClickUpController().comment_get_replies(comment_id)
        for reply in replies:
            for idx in ["user", "assignee"]:
                if (
                    reply[idx]
                    and len(internal_user := get_users_by_clickup_ids([reply[idx]["id"]])) > 0
                ):
                    reply[idx] = internal_user[0]
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="Could not get replies")

    return replies


@router.post("/{comment_id}/replies", response_model=ResponseComment)
async def create_reply(
    comment_id: int,
    reply: RequestComment,
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    comment_data = reply.model_dump()
    try:
        new_reply = ClickUpController().comment_create_reply(comment_id, comment_data)
        replies = ClickUpController().comment_get_replies(comment_id)
        for reply in replies:
            if int(new_reply["id"]) == int(reply["id"]):
                for idx in ["user", "assignee"]:
                    if (
                        reply[idx]
                        and len(internal_user := get_users_by_clickup_ids([reply[idx]["id"]])) > 0
                    ):
                        reply[idx] = internal_user[0]
                return reply
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="Could not create ClickUp reply")


@router.put("/{comment_id}")
async def update_comment(
    comment_id: int,
    request_comment: RequestCommentUpdate,
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    # Get Comment from ClickUp
    try:
        comment_data = request_comment.model_dump()
        ClickUpController().comment_update(comment_id, comment_data)
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="Could not update ClickUp Comment")

    return {"success": True}


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    try:
        ClickUpController().comment_delete(comment_id)
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="Failed to delete ClickUp Comment")

    return {"success": True}
