from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = False
    clickup_id: str | None = None
    clickup_access_token: str | None = None
