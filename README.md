# YOLO Trashcan Backend

쓰레기통/대시보드/탐지 수신용 백엔드 서버입니다.

## 필수 설치 패키지

아래 패키지는 서버 실행에 필요합니다.

```bash
pip install fastapi uvicorn sqlmodel sqlalchemy aiomysql pydantic python-dotenv
```

## 환경 변수(.env)

`.env`에 DB 접속 정보를 설정해야 합니다.

```
DB_USER=
DB_PW=
DB_IP=localhost
DB_PORT=3306
DB_NAME=yolo_trash
```

## 초기 시드 데이터 세팅

`seed.sql`을 실행하면 `wastetype`과 테스트용 `trashcan` 3개가 생성됩니다.

```bash
mysql -u <USER> -p <DB_NAME> < seed.sql
```

## 서버 실행

```bash
python main.py
```

또는 개발용(자동 리로드):

```bash
python -m uvicorn main:app --reload
```

## API 문서

`API.md` 참고
