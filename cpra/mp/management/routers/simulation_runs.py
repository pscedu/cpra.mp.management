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
):
    simulation_runs_to_return = []
    # TODO: Optimization to use the bulk GET endpoint and search based on tags.
    # This will not support having very many Simulation Runs.
    with Session(engine) as session:
        simulation_runs = session.exec(select(DBSimulationRun)).all()
        for simulation_run in simulation_runs:
            # Get simulation runs from ClickUp
            try:
                task = ClickUpController().task_get(
                    simulation_run.clickup_id, include_subtasks=True
                )
            except Exception as e:
                print(repr(e))
                raise HTTPException(
                    status_code=500, detail="ClickUp SimulationRun could not be found."
                )
            simulation_run_data = simulation_run.model_dump()
            simulation_run_data["clickup_data"] = task
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
