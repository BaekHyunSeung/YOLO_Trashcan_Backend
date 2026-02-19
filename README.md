# YOLO Trashcan Backend

쓰레기통/대시보드/탐지 수신용 백엔드 서버입니다.

## 필수 설치 패키지

아래 패키지는 서버 실행에 필요합니다.

```bash
pip install fastapi uvicorn sqlmodel sqlalchemy aiomysql pydantic python-dotenv python-multipart
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

## 프로젝트 구조

```
.
├─ main.py                # FastAPI 진입점
├─ API.md                 # API 문서
├─ README.md              # 프로젝트 설명
├─ metadata.json          # 테스트용 메타데이터 샘플
├─ db/
│  ├─ db.py               # DB 세션/엔진
│  └─ entity.py           # SQLModel 엔티티
├─ models/
│  └─ request.py          # 요청/응답 모델
├─ routers/
│  ├─ dashboard_router.py         # 대시보드 API
│  ├─ detections_router.py        # 디텍션 수신 API
│  ├─ trashcan_detail_router.py   # 쓰레기통 상세 API
│  ├─ trashcan_list_router.py     # 쓰레기통 목록 API
│  ├─ trashcan_management_router.py # 쓰레기통 관리 API
│  └─ trashcan_map_router.py      # 지도 API
└─ service/
   ├─ dashboard_service.py
   ├─ detections_service.py
   ├─ trashcan_detail_service.py
   ├─ trashcan_list_service.py
   ├─ trashcan_management_service.py
   ├─ trashcan_map_service.py
   ├─ connection_utils.py
   └─ trashcan_status_utils.py    # 온라인 상태 갱신 유틸
```

## 에러 로그

디텍션 수신 처리 중 에러가 발생하면 `trashcan_error_log` 테이블에 자동 저장됩니다.
조회 API는 `API.md`의 대시보드 로그 섹션을 참고하세요.

`trashcan_id`를 찾을 수 없는 경우를 위해 로그에 `camera_id`도 함께 저장합니다.
동일 에러가 1분 이내 반복되면 새 로그 대신 `repeat_count`만 증가합니다.
로그 조회는 기본 50건이며 최대 200건까지 제한됩니다.
에러/미연결 쓰레기통 목록은 `/dashboard/trashcan/error`에서 조회합니다.
`last_connected_at` 기준 5분 이상 수신/테스트가 없으면 `is_online`이 False로 처리됩니다.
연결 테스트 성공 시 `is_online`, `last_connected_at`이 갱신됩니다.
기준 시간(5분)은 `service/trashcan_status_utils.py`에서 변경합니다.

## 쓰레기통 등록 주의사항

쓰레기통 등록 시 `server_url`로 연결 테스트를 수행합니다. 연결이 실패하면 등록이 중단됩니다.
