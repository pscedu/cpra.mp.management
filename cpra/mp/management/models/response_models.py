from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseResponseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class Token(BaseResponseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str


class User(BaseResponseModel):
    id: int
    username: str
    email: str | None = None
    full_name: str | None = None
    clickup_id: str | None = None
    disabled: bool


class SimulationRun(BaseResponseModel):
    id: int
    model_group_id: str
    scenario_id: str
    status: str
    simulation_run_type: str
    clickup_data: dict


class Task(BaseResponseModel):
    id: str
    name: str
    description: str
    status: dict
    assignees: list
    tags: list
    url: str
    creator: dict
    date_created: str
    date_updated: str
    date_closed: str | None = None
    comments: list | None = []


class CommentCreate(BaseResponseModel):
    id: int


class Comment(CommentCreate):
    comment_text: str
    user: dict
    assignee: dict | None = None
    date: str
