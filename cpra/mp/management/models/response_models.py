from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class User(BaseModel):
    id: int
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool

class SimulationRun(BaseModel):
    id: int
    model_group: str
    scenario: str
    status: str
    simulation_run_type: str
    clickup_data: dict
