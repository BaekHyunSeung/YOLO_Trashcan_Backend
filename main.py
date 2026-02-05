from fastapi import FastAPI
import uvicorn
from sqlalchemy import text
from sqlmodel import SQLModel

import db.entity
from db.db import engine, SessionDep
from routers.dashboard_router import dashboard
from routers.trashcan_list_router import trashcans_list
from routers.trashcan_management_router import management
from routers.trashcan_map_router import map
from routers.detections_router import detections

app = FastAPI()

app.include_router(dashboard)
app.include_router(management)
app.include_router(map)
app.include_router(trashcans_list)
app.include_router(detections)

if __name__== "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)