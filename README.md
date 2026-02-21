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

- 저장 트리거: 디텍션 수신(`/detect/result`) 처리 중 에러 발생 시 자동 저장
- 보조 필드: `trashcan_id`를 찾을 수 없는 경우를 위해 로그에 `camera_id`도 함께 저장
- 시간 필드 규칙
  - `occurred_at`: 요청에 값이 있으면 사용, 없거나 파싱 실패면 서버 현재 시간
  - `created_at`: DB에 로그가 저장된 시각
  - `last_occurred_at`: 동일 에러가 반복될 때 마지막 발생 시각
- 중복 처리: 동일 에러가 1분 이내 반복되면 새 로그 대신 `repeat_count` 증가
- 조회: `/dashboard/trashcans/error/{trashcan_id}?limit=50` (최신순)
- 조회 제한: 기본 50건, 최대 200건
- 관련 문서: `API.md`의 대시보드 로그 섹션 참고

## 연결 상태 관리

- 기준 데이터: `is_online`, `last_connected_at`
- 온라인 처리
  - 디텍션 수신(`/detect/result`) 시 `is_online=True`, `last_connected_at=현재시간`
  - 연결 테스트 성공 시 `is_online=True`, `last_connected_at=현재시간`
- 오프라인 처리
  - 연결 테스트 실패 시 `is_online=False`
  - `last_connected_at`가 5분 이상 경과하면 자동으로 `is_online=False`
- 연결 테스트 방식
  - `server_url`에 저장된 라즈베리파이 사설 IP로 **ping** 테스트 (포트/경로 미사용)

## 쓰레기통 등록 주의사항

쓰레기통 등록 시 `server_url`로 연결 테스트를 수행합니다. 연결이 실패하면 등록이 중단됩니다.
