import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cpra.mp.management.database import create_all
from cpra.mp.management.routers import clickup, login, simulation_runs, users, tasks
from cpra.mp.management.settings import settings

app = FastAPI(root_path="/v1/management")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clickup.router)
app.include_router(login.router)
app.include_router(users.router)
app.include_router(simulation_runs.router)
app.include_router(tasks.router)


@app.get("/")
async def home():
    return "Welcome to the Management API!"


create_all()
uvicorn.run(app, host="0.0.0.0", port=5000)
