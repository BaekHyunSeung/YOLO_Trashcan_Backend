import os
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
from sqlmodel import SQLModel
from fastapi.middleware.cors import CORSMiddleware
import db.entity
from db.db import engine
from routers.dashboard_router import dashboard
from routers.trashcan_list_router import trashcans_list
from routers.trashcan_detail_router import trashcans_detail
from routers.trashcan_management_router import management
from routers.trashcan_map_router import map
from routers.detections_router import detections
from utils.waste_type_config import ensure_waste_type_schema, sync_waste_types

load_dotenv()

APP_HOST = os.getenv("APP_HOST")
APP_PORT = int(os.getenv("APP_PORT"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS")

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
#    await ensure_waste_type_schema(engine) 쓰레기타입 is_active 컬럼 추가
    await sync_waste_types(engine) # 쓰레기타입 is_active 컬럼 추가

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGINS],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard)
app.include_router(management)
app.include_router(map)
app.include_router(trashcans_list)
app.include_router(trashcans_detail)
app.include_router(detections)

if __name__ == "__main__":
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)