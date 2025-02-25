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
from cpra.mp.management.settings import settings

import requests as http_r
import json

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
        # ClickUp creation
        headers = {
            'Authorization': settings.clickup_settings.api_token,
            'Content-Type': 'application/json'
        }
        list_id = settings.clickup_settings.list_id
        template_id = settings.clickup_settings.simulation_run_type_template_id_mapping[simulation_run.simulation_run_type]
        task_name = f"{simulation_run.model_group} {simulation_run.scenario}"
        task_url = f"{settings.clickup_settings.base_api_url}/list/{list_id}/taskTemplate/{template_id}"

        # The data for the task you want to create
        task_data = {
            'name': task_name,
            'tags': [simulation_run.simulation_run_type]
        }

        # Make the POST request to create the task
        response = http_r.post(task_url, headers=headers, data=json.dumps(task_data))

        # Check the response status code
        if response.status_code == 200:
            response = response.json()
            task = response.get('task', {})
        else:
            print('Failed to create task')
            print('Response:', response.json())

        print(task)

        # TODO: ValueError: "SimulationRun" object has no field "clickup_id"
        simulation_run_data = simulation_run.model_dump()
        simulation_run_data["clickup_id"] = task.get('id')

        db_simulation_run = DBSimulationRun(**simulation_run_data)
        session.add(db_simulation_run)
        session.commit()
        session.refresh(db_simulation_run)
        return db_simulation_run


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
