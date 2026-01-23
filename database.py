"""
DB 연결/세션/베이스 설정 모듈.

- secrets.json에서 DB 접속 정보를 로드
- SQLAlchemy 엔진과 세션 팩토리를 생성
- 모델 베이스(Base)를 노출
"""

import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def load_database_url() -> str:
    """secrets.json에서 MySQL 접속 문자열을 구성."""

    secrets_path = Path(__file__).with_name("secrets.json")
    if not secrets_path.exists():
        raise RuntimeError("secrets.json 파일이 없습니다.")

    with secrets_path.open("r", encoding="utf-8") as file:
        secrets = json.load(file)

    user = secrets.get("user")
    password = secrets.get("password")
    host = secrets.get("host", "localhost")
    port = secrets.get("port", 3306)
    db_name = secrets.get("db_name", "yolo_trash")
    charset = secrets.get("charset", "utf8mb4")

    if not user or not password:
        raise RuntimeError("secrets.json에 user/password가 필요합니다.")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset={charset}"


# secrets.json 기반 DB URL
DATABASE_URL = load_database_url()

# 커넥션 풀 엔진 생성 (끊어진 커넥션 자동 복구)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 요청 단위로 사용할 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy 모델 베이스
Base = declarative_base()
