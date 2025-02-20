from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from cpra.mp.management.database import engine
from cpra.mp.management.dependencies import (
    get_current_active_admin,
    get_current_active_user,
)
from cpra.mp.management.models.db_models import User as DBUser, SimulationRun as DBSimulationRun
from cpra.mp.management.models.request_models import SimulationRun as RequestSimulationRun
from cpra.mp.management.models.response_models import SimulationRun as ResponseSimulationRun

router = APIRouter(prefix="/simulation_runs")


@router.get("/", response_model=list[ResponseSimulationRun])
async def get_simulation_runs(
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    with Session(engine) as session:
        simulation_runs = session.exec(select(DBSimulationRun)).all()
        return simulation_runs


@router.get("/{simulation_run_id}", response_model=ResponseSimulationRun)
async def get_simulation_run(
    simulation_run_id: int,
    current_user: Annotated[DBUser, Depends(get_current_active_user)],
):
    with Session(engine) as session:
        simulation_run = session.get(DBSimulationRun, simulation_run_id)
        if not simulation_run:
            raise HTTPException(status_code=404, detail="Simulation Run not found")
        return simulation_run


@router.post("/", response_model=ResponseSimulationRun)
async def create_simulation_run(
    simulation_run: RequestSimulationRun,
    current_user: Annotated[DBUser, Depends(get_current_active_admin)],
):
    with Session(engine) as session:
        simulation_run = DBSimulationRun.model_validate(simulation_run)
        session.add(simulation_run)
        session.commit()
        session.refresh(simulation_run)
        return simulation_run


@router.put("/{simulation_run_id}", response_model=ResponseSimulationRun)
async def update_simulation_run(
    simulation_run_id: int,
    request_simulation_run: RequestSimulationRun,
    current_user: Annotated[DBUser, Depends(get_current_active_admin)],
):
    with Session(engine) as session:
        simulation_run = session.get(DBUser, simulation_run_id)
        if not simulation_run:
            raise HTTPException(status_code=404, detail="Simulation Run not found")
        simulation_run_data = request_simulation_run.model_dump(exclude_unset=True)
        simulation_run.sqlmodel_update(simulation_run_data)
        session.add(simulation_run)
        session.commit()
        session.refresh(simulation_run)
        return simulation_run
