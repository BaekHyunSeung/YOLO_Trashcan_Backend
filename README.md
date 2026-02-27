# YOLO Trashcan Backend

쓰레기통/대시보드/탐지 수신용 백엔드 서버입니다.

## 패키지 설치

```bash
pip install -r requirements.txt
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

## API 문서

`API.md` 참고

## 프로젝트 구조

```
.
├─ main.py                # FastAPI 진입점
├─ API.md                 # API 문서
├─ README.md              # 프로젝트 설명
├─ metadata.json          # 탐지 메타데이터 샘플
├─ requirements.txt       # 패키지 의존성 목록
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
   ├─ dashboard_service.py        # 대시보드 집계/통계 처리
   ├─ detections_service.py       # 디텍션 저장/매핑 처리
   ├─ trashcan_detail_service.py  # 쓰레기통 상세/이력 조회
   ├─ trashcan_list_service.py    # 목록/검색/정렬 처리
   ├─ trashcan_management_service.py # 관리(생성/수정/삭제) 처리
   ├─ trashcan_map_service.py     # 지도용 좌표 조회
   ├─ connection_utils.py         # ping 연결 체크 유틸
   └─ trashcan_status_utils.py    # 온라인 상태 갱신 유틸
```

## 메타데이터 형식

탐지 결과 업로드(`/detect/result`)의 `metadata`는 JSON 문자열이며, 형식은 아래와 같습니다.

```json
{
  "camera_id": 1,
  "frame_id": "frame_001",
  "detections": [
    { "class_id": 0, "bbox": [0, 0, 10, 10], "score": 0.98 }
  ],
  "timestamp": "2026-02-09T14:10:00Z"
}
```

- `camera_id`: 카메라(쓰레기통) 식별자
- `frame_id`: 프레임 식별자(선택)
- `detections`: 탐지 결과 목록
  - `class_id`: 클래스 ID
  - `bbox`: `[x1, y1, x2, y2]`
  - `score`: 신뢰도
- `timestamp`: ISO 8601 형식(선택)

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
