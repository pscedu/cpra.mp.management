from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from cpra.mp.management.controllers.clickup_controller import ClickUpController
from cpra.mp.management.dependencies import (
    get_current_active_user,
)
from cpra.mp.management.models.db_models import User as DBUser
from cpra.mp.management.models.request_models import Task as RequestTask
from cpra.mp.management.models.request_models import TaskUpdate as RequestTaskUpdate
from cpra.mp.management.models.request_models import Comment as RequestComment
from cpra.mp.management.models.response_models import Task as ResponseTask


from cpra.mp.management.controllers.user_controllers import get_users_by_ids, get_users_by_clickup_ids

router = APIRouter(prefix="/tasks")


@router.get("/", response_model=list[ResponseTask])
async def get_tasks(
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
    tags: Optional[List[str]] = Query([]),
    statuses: Optional[List[str]] = Query([]),
    get_comments: Optional[bool] = Query(False, alias="getComments"),
):
    # TODO: Add restriction for requiring tags, make it optional for now
    separated_tags = {}
    for tag in tags:
        if ":" in tag:
            data_dimension_key, value = tag.split(":")
            if data_dimension_key not in separated_tags:
                separated_tags[data_dimension_key] = [tag]
            else:
                separated_tags[data_dimension_key].append(tag)

    tags_to_filter = []
    if "scenario_id" in separated_tags:
        tags_to_filter.extend(separated_tags["scenario_id"])
    elif "model_group_id" in separated_tags:
        tags_to_filter.extend(separated_tags["model_group_id"])
    elif len(separated_tags) > 0:
        tags_to_filter.extend(separated_tags[next(iter(separated_tags))])

    params = {}
    if tags_to_filter:
        params["tags[]"] = tags_to_filter

    if statuses:
        params["statuses[]"] = statuses

    try:
        tasks = ClickUpController().task_bulk_get(params)
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="ClickUp Task could not be found.")

    tasks_to_return = []
    exclusion_tags = {"meta_type:simulation_run", "meta_type:subroutine"}
    for task in tasks:
        # Unique tags for this task
        task_tags = {tag.get("name") for tag in task.get("tags", [])}

        # Exclude tasks that contain an exclusion tag.
        if exclusion_tags.intersection(task_tags):
            continue

        if len(tags) > 0:
            # Validation criteria is that there needs to exist at least one tag from each unique data_dimension
            # and at least one tag from the general
            # Essentially, each "group" is OR'd and then they're all AND'd together.
            # Naive solution is to iterate over each data_dimension and general and perform intersection checks
            # If there is an intersection, then we're good, otherwise fail out
            or_fail = False
            for _, tag_group in separated_tags.items():
                if not set(tag_group).intersection(task_tags):
                    or_fail = True
                    break

            if or_fail:
                continue

        if get_comments:
            task["comments"] = ClickUpController().task_get_comments(task["id"])

        # Transformation routine
        # TODO:
        #   If the user does not exist in the DB, it should use the dict returned by ClickUp
        #   Place that logic into a controller rather than repeating it for every route
        #   For the bulk endpoint, cache the user information so that we don't hit the DB
        task['assignees'] = get_users_by_clickup_ids(assignee['id'] for assignee in task["assignees"])
        if len(creator := get_users_by_clickup_ids([task['creator']['id']])) > 0:
            task['creator'] = creator[0]

        tasks_to_return.append(task)

    return tasks_to_return


@router.get("/{task_id}", response_model=ResponseTask)
async def get_task(
    task_id: str,
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
    get_comments: Optional[bool] = Query(False, alias="getComments"),
):
    # Get Task from ClickUp
    try:
        task = ClickUpController().task_get(task_id)
        if get_comments:
            task["comments"] = ClickUpController().task_get_comments(task_id)

        # Transformation routine
        task['assignees'] = get_users_by_clickup_ids(assignee['id'] for assignee in task["assignees"])
        if len(creator := get_users_by_clickup_ids([task['creator']['id']])) > 0:
            task['creator'] = creator[0]
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="ClickUp Task could not be found.")

    return task


@router.post("/", response_model=ResponseTask)
async def create_task(
    task: RequestTask,
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    try:
        task_data = task.model_dump()

        if task_data['assignees']:
            task_data['assignees'] = [user.clickup_id for user in get_users_by_ids(task_data['assignees'])]
        task_data["tags"].append("meta_type:task")

        task = ClickUpController().task_create(task_data)

        # Transformation routine
        task['assignees'] = get_users_by_clickup_ids([assignee['id'] for assignee in task['assignees']])
        task['creator'] = current_user
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="Could not create ClickUp Task")

    return task


@router.put("/{task_id}", response_model=ResponseTask)
async def update_task(
    task_id: str,
    request_task: RequestTaskUpdate,
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    # Get Task from ClickUp
    try:
        task_data = request_task.model_dump()
        if task_data['assignees']:
            task_data['assignees'] = [user.clickup_id for user in get_users_by_ids(task_data['assignees'])]

        updated_task = ClickUpController().task_update(task_id, task_data)

        # Transformation routine
        updated_task['assignees'] = get_users_by_clickup_ids([assignee['id'] for assignee in updated_task['assignees']])
        if len(creator := get_users_by_clickup_ids([updated_task['creator']['id']])) > 0:
            updated_task['creator'] = creator[0]

    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="Could not update ClickUp Task")

    return updated_task


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    try:
        ClickUpController().task_delete(task_id)
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="Failed to delete ClickUp Task")

    return {"success": True}


@router.post("/{task_id}/comments", response_model=ResponseTask)
async def create_task_comment(
        task_id: str,
        comment: RequestComment,
        current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    comment_data = comment.model_dump()

    try:
        task = ClickUpController().task_get(task_id)
        ClickUpController().task_create_comment(task_id, comment_data)
        task["comments"] = ClickUpController().task_get_comments(task_id)

        # Transformation routine
        task['assignees'] = get_users_by_clickup_ids(assignee['id'] for assignee in task["assignees"])
        if len(creator := get_users_by_clickup_ids([task['creator']['id']])) > 0:
            task['creator'] = creator[0]
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="Could not create ClickUp Comment")

    return task
