from enum import Enum

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseRequestModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class RoleTypes(str, Enum):
    user = "user"
    admin = "admin"


class SimulationRunTypes(str, Enum):
    icm = "ICM"
    adcirc = "ADCIRC"
    clara = "CLARA"


class User(BaseRequestModel):
    username: str
    full_name: str | None = None
    disabled: bool | None = False
    role: RoleTypes | None = RoleTypes.user


class SimulationRun(BaseRequestModel):
    model_group_id: str
    scenario_id: str
    status: str
    simulation_run_type: SimulationRunTypes | None = SimulationRunTypes.icm


class SimulationRunUpdate(BaseRequestModel):
    status: str | None = None


class Task(BaseRequestModel):
    name: str
    tags: list[str]
    description: str | None = None
    markdown_content: str | None = None
    assignees: list[int] | None = None
    status: str


class TaskUpdate(BaseRequestModel):
    name: str | None = None
    description: str | None = None
    markdown_content: str | None = None
    assignees: dict | None = None
    status: str | None = None
    tags: dict | None = None


class Comment(BaseRequestModel):
    comment: dict | list[dict] | None = None
    assignee: int | None = None
    notify_all: bool | None = False


class CommentUpdate(BaseRequestModel):
    comment_text: str
    assignee: int | None = None
    resolved: bool | None = False
