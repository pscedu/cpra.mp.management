from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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
    SimulationRun as RequestSimulationRun,
)
from cpra.mp.management.models.request_models import (
    SimulationRunUpdate as RequestSimulationRunUpdate,
)
from cpra.mp.management.models.response_models import (
    SimulationRun as ResponseSimulationRun,
)

router = APIRouter(prefix="/simulation_runs")


@router.get("/", response_model=list[ResponseSimulationRun])
async def get_simulation_runs(
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
    tags: Optional[List[str]] = Query([]),
    statuses: Optional[List[str]] = Query([]),
):
    cu_controller = ClickUpController()
    separated_tags = {}
    for tag in tags:
        if tag.count(":") != 1:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid tag '{tag}'. Tags must contain exactly one colon (key:value).",
            )
        data_dimension_key = tag.split(":")[0]
        separated_tags.setdefault(data_dimension_key, []).append(tag)

    # The ClickUp tags[] filter is OR'd, so only one data dimension can be used to narrow the request.
    # Remaining dimensions (and meta_type) are enforced below. Simulation Runs and their Subroutine
    # subtasks are the only entries wanted, so with no usable dimension those two meta_types are requested.
    filter_key = next(
        (key for key in ("scenario_id", "model_group_id") if key in separated_tags),
        next((key for key in separated_tags if key != "meta_type"), None),
    )
    if filter_key:
        tags_to_filter = list(separated_tags[filter_key])
        if filter_key not in ("scenario_id", "model_group_id"):
            # Subroutines are only guaranteed to carry the scenario_id and model_group_id tags.
            tags_to_filter.append(ClickUpController.SUBROUTINE_TAG)
    else:
        tags_to_filter = [ClickUpController.SIMULATION_RUN_TAG, ClickUpController.SUBROUTINE_TAG]

    # Subtasks are returned as top level tasks by the bulk endpoint, they get nested back in below.
    # Statuses are filtered below instead of in the request, because a statuses[] filter would also
    # drop subtasks whose status differs from their parent's.
    params = {"subtasks": "true", "include_markdown_description": "true", "tags[]": tags_to_filter}

    try:
        tasks = cu_controller.task_bulk_get(params, list_key="simulation_runs")
    except Exception as e:
        print(repr(e))
        raise HTTPException(status_code=500, detail="ClickUp Simulation Runs could not be found.")

    status_filter = {status.lower() for status in statuses}
    tasks_by_clickup_id = {}
    subtasks_by_parent_id = {}
    for task in tasks:
        parent_id = task.get("parent")
        if parent_id:
            subtasks_by_parent_id.setdefault(parent_id, []).append(task)
            continue

        # Unique tags for this task
        task_tags = {tag.get("name") for tag in task.get("tags", [])}

        if ClickUpController.SIMULATION_RUN_TAG not in task_tags:
            continue

        if status_filter and task["status"]["status"].lower() not in status_filter:
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

        tasks_by_clickup_id[task["id"]] = task

    for clickup_id, task in tasks_by_clickup_id.items():
        task["subtasks"] = subtasks_by_parent_id.get(clickup_id, [])

    if not tasks_by_clickup_id:
        return []

    simulation_runs_to_return = []
    with Session(engine) as session:
        # Only fetch the DB rows that correspond to the ClickUp tasks that matched.
        simulation_runs = session.exec(
            select(DBSimulationRun).where(DBSimulationRun.clickup_id.in_(tasks_by_clickup_id))
        ).all()
        for simulation_run in simulation_runs:
            simulation_run_data = simulation_run.model_dump()
            simulation_run_data["clickup_data"] = tasks_by_clickup_id[simulation_run.clickup_id]
            simulation_runs_to_return.append(simulation_run_data)

        return simulation_runs_to_return


@router.get("/{simulation_run_id}", response_model=ResponseSimulationRun)
async def get_simulation_run(
    simulation_run_id: int,
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    with Session(engine) as session:
        simulation_run = session.get(DBSimulationRun, simulation_run_id)
        if not simulation_run:
            raise HTTPException(status_code=404, detail="Simulation Run not found")
        # Get simulation run from ClickUp
        try:
            task = ClickUpController().task_get(simulation_run.clickup_id, include_subtasks=True)
        except Exception as e:
            print(repr(e))
            raise HTTPException(
                status_code=500, detail="ClickUp Simulation Run could not be found."
            )

        simulation_run_data = simulation_run.model_dump()
        simulation_run_data["clickup_data"] = task
        return simulation_run_data


@router.post("/", response_model=ResponseSimulationRun)
async def create_simulation_run(
    simulation_run: RequestSimulationRun,
    current_user: Annotated[DBUser, Depends(get_current_active_admin)],
):
    with Session(engine) as session:
        try:
            task = ClickUpController().simulation_run_create(simulation_run)
        except Exception as e:
            print(repr(e))
            raise HTTPException(status_code=500, detail="Could not create ClickUp Simulation Run")
        simulation_run_data = simulation_run.model_dump()
        simulation_run_data["clickup_id"] = task.get("id")

        db_simulation_run = DBSimulationRun(**simulation_run_data)
        session.add(db_simulation_run)
        session.commit()
        session.refresh(db_simulation_run)
        simulation_run_data = db_simulation_run.model_dump()
        simulation_run_data["clickup_data"] = task
        return simulation_run_data


@router.put("/{simulation_run_id}", response_model=ResponseSimulationRun)
async def update_simulation_run(
    simulation_run_id: int,
    request_simulation_run: RequestSimulationRunUpdate,
    current_user: Annotated[DBUser, Depends(get_current_active_admin)],
):
    with Session(engine) as session:
        simulation_run = session.get(DBSimulationRun, simulation_run_id)
        if not simulation_run:
            raise HTTPException(status_code=404, detail="Simulation Run not found")

        try:
            task = ClickUpController().task_update(
                simulation_run.clickup_id, {"status": request_simulation_run.status}
            )
        except Exception as e:
            print(repr(e))
            raise HTTPException(status_code=500, detail="Could not update ClickUp Simulation Run")

        request_simulation_run_data = request_simulation_run.model_dump(exclude_unset=True)
        simulation_run.sqlmodel_update(request_simulation_run_data)
        session.add(simulation_run)
        session.commit()
        session.refresh(simulation_run)
        simulation_run_data = simulation_run.model_dump()
        simulation_run_data["clickup_data"] = task

        return simulation_run_data


@router.delete("/{simulation_run_id}")
async def delete_simulation_run(
    simulation_run_id: int,
    current_user: Annotated[DBUser, Depends(get_current_active_admin)],
):
    with Session(engine) as session:
        simulation_run = session.get(DBSimulationRun, simulation_run_id)
        if not simulation_run:
            raise HTTPException(status_code=404, detail="Simulation Run not found")
        try:
            ClickUpController().task_delete(simulation_run.clickup_id)
        except Exception as e:
            print(repr(e))
            raise HTTPException(status_code=500, detail="Failed to delete ClickUp Simulation Run")

        session.delete(simulation_run)
        session.commit()

        return {"success": True}
