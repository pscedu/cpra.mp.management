from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from cpra.mp.management.controllers.clickup_controller import ClickUpController
from cpra.mp.management.database import engine
from cpra.mp.management.dependencies import (
    get_current_active_admin,
    get_current_active_user,
)
from cpra.mp.management.models.db_models import SimulationRun as DBSimulationRun
from cpra.mp.management.models.db_models import User as DBUser
from cpra.mp.management.models.request_models import (
    Task as RequestTask,
)
from cpra.mp.management.models.request_models import (
    TaskUpdate as RequestTaskUpdate,
)
from cpra.mp.management.models.response_models import (
    Task as ResponseTask,
)

router = APIRouter(prefix="/tasks")


# GET /management/v1/tasks/?task_id=1000&task_id=1001
# GET /management/v1/tasks?tags=progress_tracking_task&task_id=1000
# GET /management/v1/tasks?tags=bug&task_id=1000
# @router.get("/", response_model=list[ResponseTask])
# async def get_tasks(
#     current_user: Annotated[DBUser, Depends(get_current_active_user)],
# ):
#     tasks_to_return = []
#     # TODO: Optimization to use the bulk GET endpoint and search based on tags.
#     # This will not support having very many Tasks.
#     with Session(engine) as session:
#         # UPDATE
#         tasks = session.exec(select({})).all()
#         for task in tasks:
#             # Get Tasks from ClickUp
#             try:
#                 task = ClickUpController().task_get(task.clickup_id)
#             except Exception as e:
#                 print(repr(e))
#                 raise HTTPException(
#                     status_code=500, detail="ClickUp Task could not be found."
#                 )
#             task_data = task.model_dump()
#             task_data["clickup_data"] = task
#             tasks_to_return.append(task_data)
#         return tasks_to_return


# GET /management/v1/tasks/10001
# @router.get("/{task_id}", response_model=ResponseTask)
# async def get_task(
#     task_id: int,
#     current_user: Annotated[DBUser, Depends(get_current_active_user)],
# ):
#     # Get Task from ClickUp
#     try:
#         task = ClickUpController().task_get(task_id)
#     except Exception as e:
#         print(repr(e))
#         raise HTTPException(
#             status_code=500, detail="ClickUp Task could not be found."
#         )
#
#     task_data = task.model_dump()
#     task_data["clickup_data"] = task
#     return task_data



# POST /management/v1/tasks
# {
#     "task_id": 1000,
#     "tags": ["bug"],
#     "name": "Critical Error with Salinity",
#     "assignees": [1000, 1001]
# }
@router.post("/", response_model=ResponseTask)
async def create_task(
    task: RequestTask,
    current_user: Annotated[DBUser, Depends(get_current_active_admin)],
):
    with Session(engine) as session:
        # Check to make sure the simulation run id exists
        simulation_run = session.get(DBSimulationRun, task.simulation_run_id)
        if not simulation_run:
            raise HTTPException(status_code=404, detail="Associated Simulation Run not found")

    task_data = task.model_dump()
    # Need to add tags for model group + scenario, make tags required
    task_data["tags"].extend([simulation_run.model_group, simulation_run.scenario])
    try:
        clickup_task = ClickUpController().task_create(task_data)
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="Could not create ClickUp Task")

    clickup_task["simulation_run_id"] = simulation_run.id
    return clickup_task


# PUT /management/v1/tasks/1001
# {
#     "name": "New name",
# }
# @router.put("/{task_id}", response_model=ResponseTask)
# async def update_task(
#     task_id: int,
#     request_task: RequestTaskUpdate,
#     current_user: Annotated[DBUser, Depends(get_current_active_admin)],
# ):
#     with Session(engine) as session:
#         task = session.get(DBTask, task_id)
#         if not task:
#             raise HTTPException(status_code=404, detail="Task not found")
# 
#         try:
#             task = ClickUpController().task_update(
#                 task, request_task.status
#             )
#         except Exception as e:
#             print(repr(e))
#             raise HTTPException(status_code=500, detail="Could not update ClickUp Task")
# 
#         request_task_data = request_task.model_dump(exclude_unset=True)
#         task.sqlmodel_update(request_task_data)
#         session.add(task)
#         session.commit()
#         session.refresh(task)
#         task_data = task.model_dump()
#         task_data["clickup_data"] = task
# 
#         return task_data


# DELETE /management/v1/tasks/1001
@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: Annotated[DBUser, Depends(get_current_active_admin)],
):
    # TODO: Check whether this user created this task? Should any user be able to delete any task?
    with Session(engine) as session:
        try:
            ClickUpController().task_delete(task_id)
        except Exception as e:
            print(repr(e))
            raise HTTPException(status_code=500, detail="Failed to delete ClickUp Task")

        return {"success": True}
