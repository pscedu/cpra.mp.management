import uvicorn
from fastapi import FastAPI

from cpra.mp.management.database import create_all
from cpra.mp.management.routers import clickup, login, users

app = FastAPI(root_path="/management/v1")

app.include_router(clickup.router)
app.include_router(login.router)
app.include_router(users.router)


@app.get("/")
async def home():
    return "Welcome to the Management API!"


create_all()
uvicorn.run(app, host="0.0.0.0", port=5000)
