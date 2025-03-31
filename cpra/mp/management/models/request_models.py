from enum import Enum

from pydantic import BaseModel


class RoleTypes(str, Enum):
    user = "user"
    admin = "admin"


class StatusTypes(str, Enum):
    backlog = "backlog"
    in_progress = "in progress"
    done = "done"


class TaskTypes(str, Enum):
    bug = "bug"
    narrative = "narrative"


class SimulationRunTypes(str, Enum):
    icm = "ICM"
    adcirc = "ADCIRC"
    clara = "CLARA"


class User(BaseModel):
    username: str
    full_name: str | None = None
    disabled: bool | None = False
    role: RoleTypes | None = RoleTypes.user


class SimulationRun(BaseModel):
    model_group: str
    scenario: str
    status: StatusTypes | None = StatusTypes.backlog
    simulation_run_type: SimulationRunTypes | None = SimulationRunTypes.icm


class SimulationRunUpdate(BaseModel):
    status: StatusTypes | None = None


class Task(BaseModel):
    name: str
    tags: list[TaskTypes]
    description: str | None = None
    assignees: list[int] | None = None
    status: StatusTypes | None = StatusTypes.backlog


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    assignees: list[int] | None = None
    status: StatusTypes | None = None
