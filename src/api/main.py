from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import APP_NAME
from database.database import create_database

# Registra todos os models.
import models

from api.routers import athletes
from api.routers import auth
from api.routers import evaluations
from api.routers import integrations
from api.routers import invitations
from api.routers import strava


create_database()


app = FastAPI(
    title=f"{APP_NAME} API",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://runcore.tailf3239d.ts.net",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    auth.router,
    prefix="/api",
)

app.include_router(
    athletes.router,
    prefix="/api",
)

app.include_router(
    evaluations.router,
    prefix="/api",
)

app.include_router(
    invitations.router,
    prefix="/api",
)

app.include_router(
    integrations.router,
    prefix="/api",
)

app.include_router(
    strava.router,
    prefix="/api",
)

@app.get("/health")
def health():

    return {
        "status": "ok",
    }