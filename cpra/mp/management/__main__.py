import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cpra.mp.management.database import create_all
from cpra.mp.management.routers import clickup, login, simulation_runs, users

app = FastAPI(root_path="/v1/management")

origins = [
    "http://mpdp.coastal.la.gov",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clickup.router)
app.include_router(login.router)
app.include_router(users.router)
app.include_router(simulation_runs.router)


@app.get("/")
async def home():
    return "Welcome to the Management API!"


create_all()
uvicorn.run(app, host="0.0.0.0", port=5000)
