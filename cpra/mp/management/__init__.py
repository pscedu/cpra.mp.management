from fastapi import FastAPI
from cpra.mp.management.routers import clickup, tokens
from cpra.mp.management.models import db_models

app = FastAPI(root_path="/management/v1")


app.include_router(clickup.router)
app.include_router(tokens.router)


@app.get("/")
async def home():
    return "Welcome to the Management API!"
