from fastapi import Depends
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS
from config import APP_NAME
from database.bootstrap import initialize_database

# Registra todos os models antes de criar as tabelas.
import models

from api.dependencies import require_coach
from api.origin_guard import origin_guard_middleware
from api.routers import athletes
from api.routers import admin
from api.routers import auth
from api.routers import evaluations
from api.routers import goals
from api.routers import integrations
from api.routers import ipt
from api.routers import invitations
from api.routers import profiles
from api.routers import student
from api.routers import trainings


initialize_database()


app = FastAPI(
    title=f"{APP_NAME} API",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        *ALLOWED_ORIGINS,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(
    origin_guard_middleware,
)


app.include_router(
    auth.router,
    prefix="/api",
)

app.include_router(
    admin.router,
    prefix="/api",
)

app.include_router(
    integrations.router,
    prefix="/api",
)

app.include_router(
    student.router,
    prefix="/api",
)

app.include_router(
    goals.router,
    prefix="/api",
)

app.include_router(
    invitations.router,
    prefix="/api",
)

app.include_router(
    profiles.router,
    prefix="/api",
)

app.include_router(
    athletes.router,
    prefix="/api",
    dependencies=[
        Depends(require_coach),
    ],
)

app.include_router(
    evaluations.router,
    prefix="/api",
)

app.include_router(
    trainings.router,
    prefix="/api",
    dependencies=[
        Depends(require_coach),
    ],
)


app.include_router(
    ipt.router,
    prefix="/api",
    dependencies=[
        Depends(require_coach),
    ],
)

@app.get("/health")
def health():

    return {
        "status": "ok",
    }
