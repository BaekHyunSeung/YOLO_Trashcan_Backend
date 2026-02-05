import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
# 핵심: SQLAlchemy 것이 아니라 SQLModel의 비동기 세션을 가져와야 함
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Annotated, List
from fastapi import Depends

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PW = os.getenv("DB_PW")
DB_IP = os.getenv("DB_IP")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

missing = ['DB_USER', 'DB_PW', 'DB_IP', 'DB_PORT', 'DB_NAME']
for var in missing:
    if not os.getenv(var):
        raise ValueError(f"{var} 환경변수가 설정되지 않았습니다.")

DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PW}@{DB_IP}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True)

async def get_db():
    # sessionmaker에 SQLModel의 AsyncSession 클래스를 전달
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_db)]
