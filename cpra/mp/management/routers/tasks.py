from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from cpra.mp.management.controllers.clickup_controller import ClickUpController
from cpra.mp.management.dependencies import (
    get_current_active_admin,
    get_current_active_user,
)
from cpra.mp.management.models.db_models import User as DBUser
from cpra.mp.management.models.request_models import Task as RequestTask
from cpra.mp.management.models.request_models import TaskUpdate as RequestTaskUpdate
from cpra.mp.management.models.response_models import Task as ResponseTask

router = APIRouter(prefix="/tasks")


@router.get("/", response_model=list[ResponseTask])
async def get_tasks(
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
    tags: Optional[List[str]] = Query([]),
    statuses: Optional[List[str]] = Query([]),
):
    # Tags need to be separated into "general" and "data_dimension" tags.
    separated_tags = {"general": [], "data_dimension": {}}

    for tag in tags:
        if ":" in tag:
            data_dimension_key, value = tag.split(":")
            if data_dimension_key not in separated_tags:
                separated_tags["data_dimension"][data_dimension_key] = [tag]
            else:
                separated_tags["data_dimension"][data_dimension_key].append(tag)
        else:
            separated_tags["general"].append(tag)

    # Once they've been separated, determine which group of tags to send for filtering
    # For simplicity, try to use either the scenario_id or model_group_id tags if they exist
    tags_to_filter = []
    if "scenario_id" in separated_tags["data_dimension"]:
        tags_to_filter.extend(separated_tags["data_dimension"]["scenario_id"])
    elif "model_group_id" in separated_tags["data_dimension"]:
        tags_to_filter.extend(separated_tags["data_dimension"]["model_group_id"])
    else:
        tags_to_filter.extend(separated_tags["general"])

    params = {}
    if tags_to_filter:
        params["tags[]"] = tags_to_filter

    if statuses:
        params["statuses[]"] = statuses

    print(params)
    try:
        tasks = ClickUpController().task_bulk_get(params)
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="ClickUp Task could not be found.")

    tasks_to_return = []
    for task in tasks:
        # Unique tags for this task
        task_tags = {tag.get("name") for tag in task.get("tags", [])}

        # Validation criteria is that there needs to exist at least one tag from each unique data_dimension
        # and at least one tag from the general
        # Essentially, each "group" is OR'd and then they're all AND'd together.
        # Naive solution is to iterate over each data_dimension and general and perform intersection checks
        # If there is an intersection, then we're good, otherwise fail out
        if not set(separated_tags["general"]).intersection(task_tags):
            continue

        or_fail = False
        for _, tag_group in separated_tags["data_dimension"].items():
            if not set(tag_group).intersection(task_tags):
                or_fail = True
                break

        if or_fail:
            continue

        tasks_to_return.append(task)

    return tasks_to_return


# GET /management/v1/tasks/10001
@router.get("/{task_id}", response_model=ResponseTask)
async def get_task(
    task_id: int,
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    # Get Task from ClickUp
    try:
        task = ClickUpController().task_get(task_id)
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="ClickUp Task could not be found.")

    return task


@router.post("/", response_model=ResponseTask)
async def create_task(
    task: RequestTask,
    current_user: Annotated[DBUser, Depends(get_current_active_admin)],
):
    task_data = task.model_dump()

    try:
        task = ClickUpController().task_create(task_data)
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="Could not create ClickUp Task")

    return task


@router.put("/{task_id}", response_model=ResponseTask)
async def update_task(
    task_id: int,
    request_task: RequestTaskUpdate,
    current_user: Annotated[DBUser, Depends(get_current_active_admin)],
):
    # Get Task from ClickUp
    try:
        task_data = request_task.model_dump()
        updated_task = ClickUpController().task_update(task_id, task_data)
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="Could not update ClickUp Task")

    return updated_task


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: Annotated[DBUser, Depends(get_current_active_admin)],
):
    try:
        ClickUpController().task_delete(task_id)
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="Failed to delete ClickUp Task")

    return {"success": True}
