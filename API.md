# API 문서

## 공통
- Base URL: `http://<APP_HOST>:<APP_PORT>`
- 기본 응답 형식: JSON
- 시간 포맷: ISO 8601
- 서버 실행 주소와 CORS 허용 주소는 `.env` 기준으로 결정됩니다.
- 이미지 조회 API는 JSON이 아닌 파일 바이너리를 반환합니다.

에러 응답 기본 형식:
```json
{ "detail": "에러 메시지" }
```

자주 나오는 실패 코드:
- `400`: 직접 검증하는 잘못된 요청
- `404`: 조회 대상 없음
- `422`: FastAPI/Pydantic 검증 실패
- `500`: 처리 중 예외

주의:
- 일부 관리 API는 실패 시 HTTP 에러를 던지지 않고, `200 OK`와 함께 `created: false`, `updated: false` 같은 결과 JSON을 반환합니다.
- 쓰레기통 상세/대시보드 조회 계열은 없는 대상을 조회하면 `404`를 반환하는 경우가 있습니다.

### 디텍션·수신 관련 환경 변수 (`.env`)
| 변수 | 기본 | 설명 |
|------|------|------|
| `DETECTION_CONFIDENCE_THRESHOLD` | `0.25` | 검출 `score`가 이보다 낮으면 저장 대상에서 제외 |
| `DETECTION_MIN_INTERVAL_SECONDS` | `0` | 같은 `camera_id`로 최소 이 간격(초)마다만 DB 등록. `0`이면 제한 없음. 간격 미달 요청은 본문 무시 후 `204` |
| `IMAGE_PATH` | `.` | 디텍션 이미지 저장 루트 |

---

## 대시보드

### 전체 탐지 요약
- `GET /dashboard/detections`
- 활성(`is_active=True`) 쓰레기 타입만 집계합니다.

성공 응답:
```json
{
  "total_objects": 120,
  "total_events": 10,
  "items_by_type": {
    "MetalCan": 30,
    "PetBottle": 25,
    "Plastic": 50,
    "Styrofoam": 15
  }
}
```

실패 경우:
- `500`: DB 조회 등 서버 내부 오류

### 수거 필요 쓰레기통
- `GET /dashboard/trashcans/full`
- `fill_rate`는 `current_volume / trashcan_capacity * 100`으로 계산하고, 응답에서는 최대 `100.0`으로 제한합니다.

성공 응답:
```json
[
  {
    "trashcan_id": 1,
    "trashcan_name": "A",
    "fill_rate": 95.0
  }
]
```

실패 경우:
- `500`: DB 조회 등 서버 내부 오류

### 통계 차트
- `GET /dashboard/charts`
- Query:
  - `period`: `week | month | year` (기본 `week`)
  - `start_date`: `YYYY-MM-DD` 형식, 자유 기간 조회 시작일
  - `end_date`: `YYYY-MM-DD` 형식, 자유 기간 조회 종료일
- `start_date`, `end_date`를 둘 다 보내면 자유 기간 조회로 처리되고 `period`는 무시됩니다.
- 활성(`is_active=True`) 쓰레기 타입만 집계합니다.

요청 예시:
```text
/dashboard/charts?period=week
/dashboard/charts?start_date=2026-03-01&end_date=2026-03-31
```

성공 응답:
```json
{
  "period": "custom",
  "start_date": "2026-03-01",
  "end_date": "2026-03-31",
  "total_count": 120,
  "items_by_type": {
    "MetalCan": 30,
    "PetBottle": 25
  },
  "items_by_city": {
    "서울": 60,
    "부산": 40
  }
}
```

실패 경우:
- `400`: `start_date`, `end_date` 중 하나만 보낸 경우
- `400`: `start_date > end_date`
- `422`: `period`가 `week|month|year` 외의 값인 경우
- `422`: 날짜 형식이 잘못된 경우
- `500`: DB 조회 등 서버 내부 오류

### 미연결/에러 쓰레기통 목록
- `GET /dashboard/trashcans/error`
- 현재 오프라인 상태이거나 최근 1분 내 에러 로그가 있는 쓰레기통 목록을 반환합니다.
- `last_connected_at` 기준 5분 이상 수신/테스트가 없으면 `is_online=False`로 갱신될 수 있습니다.

성공 응답:
```json
[
  {
    "trashcan_id": 1,
    "trashcan_name": "A",
    "address_detail": "서울 강남구 ...",
    "last_connected_at": "2026-02-09T10:00:00"
  }
]
```

실패 경우:
- `500`: DB 조회 등 서버 내부 오류

### 쓰레기통 에러 로그 조회
- `GET /dashboard/trashcans/error/{trashcan_id}?limit=50`
- 디텍션 수신(`/detect/result`) 중 저장된 에러 로그를 조회합니다.
- **소프트 삭제(`is_deleted=True`)된 쓰레기통**이라도 PK가 DB에 있으면 조회 가능합니다 (삭제된 통에 쌓인 로그 확인용).
- 같은 에러가 1분 이내 반복되면 새 로그 대신 `repeat_count`가 증가합니다.
- `limit`: `1~200`, 기본 `50`

성공 응답:
```json
{
  "trashcan_id": 1,
  "logs": [
    {
      "trashcan_id": 1,
      "camera_id": 1,
      "status_code": 500,
      "message": "Model error",
      "occurred_at": "2026-02-09T14:10:00",
      "last_occurred_at": "2026-02-09T14:10:55",
      "repeat_count": 3,
      "created_at": "2026-02-09T14:10:05"
    }
  ]
}
```

실패 경우:
- `404`: 해당 PK의 `trashcan` 행이 **아예 없는** 경우 (잘못된 `trashcan_id`)
- `422`: `trashcan_id`가 정수가 아닌 경우
- `422`: `limit`가 `1~200` 범위를 벗어난 경우
- `500`: DB 조회 등 서버 내부 오류

### 미등록 camera 에러 로그 조회
- `GET /dashboard/trashcans/error/unregistered?limit=50`
- `camera_id`는 들어왔지만 **등록된 쓰레기통 PK가 없는** 경우 등, `trashcan_id`가 로그에 `null`로 남은 행을 조회합니다.
- (삭제된 쓰레기통에 대한 400 등은 `trashcan_id`가 채워져 있을 수 있어 이 목록과 겹치지 않을 수 있음.)
- `trashcan_id`는 `null`로 반환됩니다.
- `limit`: `1~200`, 기본 `50`

성공 응답:
```json
{
  "trashcan_id": null,
  "logs": [
    {
      "trashcan_id": null,
      "camera_id": 999,
      "status_code": 400,
      "message": "등록되지 않은 쓰레기통입니다. camera_id=999",
      "occurred_at": "2026-04-01T12:00:00",
      "last_occurred_at": "2026-04-01T12:00:00",
      "repeat_count": 1,
      "created_at": "2026-04-01T12:00:00"
    }
  ]
}
```

실패 경우:
- `422`: `limit`가 `1~200` 범위를 벗어난 경우
- `500`: DB 조회 등 서버 내부 오류

---

## 쓰레기통 목록

### 목록 조회
- `GET /trashcans_list/trashcans?offset=0&limit=20`
- 삭제되지 않은 쓰레기통만 조회합니다.
- `fill_rate`는 응답 시 최대 `100.0`으로 제한됩니다.

성공 응답:
```json
{
  "total": 100,
  "items": [
    {
      "trashcan_id": 1,
      "trashcan_name": "A",
      "address_detail": "서울 강남구 ...",
      "is_online": true,
      "fill_rate": 60.0,
      "total_collected": 120
    }
  ]
}
```

실패 경우:
- `422`: `offset`, `limit`가 정수가 아닌 경우
- `500`: DB 조회 등 서버 내부 오류

### 정렬/검색
- `GET /trashcans_list/query`
- Query:
  - `sort_by`: `collected | free_capacity | is_online` (기본 `collected`)
  - `order`: `asc | desc` (기본 `desc`)
  - `city`: 도시명 부분 일치 필터
  - `name`: 쓰레기통 이름 부분 일치 필터
  - `offset`: 시작 위치 (기본 `0`)
  - `limit`: 조회 개수 (기본 `20`)

성공 응답:
```json
{
  "total": 100,
  "items": [
    {
      "trashcan_id": 1,
      "trashcan_name": "A",
      "address_detail": "서울 강남구 ...",
      "is_online": true,
      "total_collected": 120,
      "free_capacity": 40,
      "fill_rate": 60.0
    }
  ]
}
```

실패 경우:
- `422`: `sort_by`가 허용값이 아닌 경우
- `422`: `order`가 허용값이 아닌 경우
- `422`: `offset`, `limit`가 정수가 아닌 경우
- `500`: DB 조회 등 서버 내부 오류

---

## 쓰레기통 상세

### 상세 조회
- `GET /trashcans_detail/{trashcan_id}`
- 삭제되지 않은 쓰레기통만 조회합니다.

성공 응답:
```json
{
  "trashcan_id": 1,
  "trashcan_name": "A",
  "address_detail": "서울 강남구 ...",
  "is_online": true,
  "last_connected_at": "2026-02-09T10:00:00",
  "trashcan_capacity": 100,
  "current_volume": 60,
  "free_capacity": 40,
  "detect_items_response": {
    "total_objects": 120,
    "total_events": 10,
    "data": {
      "MetalCan": 30,
      "PetBottle": 25,
      "Plastic": 50,
      "Styrofoam": 15
    }
  }
}
```

실패 경우:
- `404`: 존재하지 않거나 삭제된 쓰레기통인 경우
- `422`: `trashcan_id`가 정수가 아닌 경우
- `500`: DB 조회 등 서버 내부 오류

### 연결 테스트
- `GET /trashcans_detail/{trashcan_id}/connection-test`
- `server_url`에 저장된 장치 주소로 ping 연결 테스트를 수행합니다.
- 성공 시 `is_online=True`, `last_connected_at=현재시간`으로 갱신됩니다.
- 실패 시 HTTP 에러가 아니라 상태 JSON을 반환합니다.

성공 응답:
```json
{
  "trashcan_id": 1,
  "status": "ok",
  "message": "Server is healthy"
}
```

실패 응답 예시:
```json
{
  "trashcan_id": 1,
  "status": "error",
  "message": "Failed to connect to server"
}
```

실패 경우:
- `200`: 쓰레기통이 없거나 `server_url`이 없으면 `status: "error"`, `message: "Server URL not found"`
- `200`: ping 실패 시 `status: "error"`, `message: "Failed to connect to server"`
- `422`: `trashcan_id`가 정수가 아닌 경우
- `500`: DB 처리 오류

### 쓰레기 상세 데이터
- `GET /trashcans_detail/{trashcan_id}/waste-detail`
- Query:
  - `type_name`: 선택한 쓰레기 타입 이름
  - `offset`: 시작 위치, 기본 `0`
  - `limit`: 조회 개수, 기본 `20`, 최대 `100`
- `type_name` 선택값은 서버 시작 시 `.env`의 `WASTE_TYPE_{id}` 기준으로 생성됩니다.
- 응답의 `image_path`는 이미지 조회 API 경로로 그대로 사용할 수 있습니다.

요청 예시:
```text
/trashcans_detail/1/waste-detail?offset=0&limit=20
/trashcans_detail/1/waste-detail?type_name=MetalCan&offset=0&limit=20
```

성공 응답:
```json
{
  "trashcan_id": 1,
  "type_name": null,
  "offset": 0,
  "limit": 20,
  "total_objects": 120,
  "total_events": 10,
  "items_by_type": {
    "MetalCan": [
      {
        "detail_id": 501,
        "detection_id": 100,
        "type_name": "MetalCan",
        "image_name": "1_100_20260327_141424_123_a1b2c3d4.jpg",
        "image_path": "detect_img/1_100_20260327_141424_123_a1b2c3d4.jpg",
        "detected_at": "2026-02-09T14:10:00"
      }
    ],
    "PetBottle": [],
    "Plastic": [],
    "Styrofoam": []
  }
}
```

실패 경우:
- `404`: 존재하지 않거나 삭제된 쓰레기통인 경우
- `422`: `trashcan_id`가 정수가 아닌 경우
- `422`: `type_name`이 허용된 Enum 값이 아닌 경우
- `422`: `offset < 0`인 경우
- `422`: `limit < 1` 또는 `limit > 100`인 경우
- `500`: DB 조회 등 서버 내부 오류

### 이미지 조회
- `GET /detect_img/{image_name:path}`
- `waste-detail` 응답의 `image_path` 값을 그대로 사용합니다.
- 예: `image_path`가 `detect_img/1_100_20260327_141424_123_a1b2c3d4.jpg`이면 요청은 `GET /detect_img/1_100_20260327_141424_123_a1b2c3d4.jpg`
- 서버는 `.env`의 `IMAGE_PATH`와 경로를 조합해 실제 파일을 반환합니다.
- 응답 형식은 파일 바이너리(`FileResponse`)입니다.

실패 경우:
- `404`: 파일이 없거나 허용된 이미지 경로 밖의 파일 접근인 경우
- `500`: 파일 응답 처리 중 서버 내부 오류

---

## 쓰레기통 관리

### 목록 조회
- `GET /management/trashcans`
- 삭제되지 않은 쓰레기통 목록을 반환합니다.

성공 응답:
```json
[
  {
    "trashcan_id": 1,
    "trashcan_name": "A",
    "address_detail": "서울 강남구 ...",
    "total_collected": 120
  }
]
```

실패 경우:
- `500`: DB 조회 등 서버 내부 오류

### 삭제된 쓰레기통 목록
- `GET /management/trashcans/deleted`

성공 응답:
```json
[
  {
    "trashcan_id": 2,
    "trashcan_name": "B",
    "address_detail": "서울 중구 ...",
    "total_collected": 10
  }
]
```

실패 경우:
- `500`: DB 조회 등 서버 내부 오류

### 상태 확인
- `GET /management/trashcans/{trashcan_id}/health`
- `trashcans_detail`의 연결 테스트와 같은 동작입니다.
- 실패 시 HTTP 에러가 아니라 상태 JSON을 반환합니다.

성공 응답:
```json
{
  "trashcan_id": 1,
  "status": "ok",
  "message": "Server is healthy"
}
```

실패 응답 예시:
```json
{
  "trashcan_id": 1,
  "status": "error",
  "message": "Server URL not found"
}
```

실패 경우:
- `200`: 쓰레기통이 없거나 `server_url`이 없으면 `status: "error"`
- `200`: ping 실패 시 `status: "error"`
- `422`: `trashcan_id`가 정수가 아닌 경우
- `500`: DB 처리 오류

### 생성
- `POST /management/trashcans`
- 등록 전 `server_url`로 ping 연결 테스트를 수행합니다.
- 연결 실패 시 HTTP 에러가 아니라 `created: false` JSON을 반환합니다.
- **`trashcan_id` (선택)**: 생략 시 DB 자동 증가. 지정 시 해당 PK로 행을 생성합니다. 디텍션의 `camera_id`와 동일한 값으로 맞추려면 장비 ID를 미리 넣어 등록하면 됩니다. 이미 사용 중인 PK(삭제된 행 포함)면 생성되지 않습니다.

요청 본문:
```json
{
  "trashcan_id": 42,
  "trashcan_name": "A",
  "trashcan_capacity": 100,
  "trashcan_city": "서울",
  "address_detail": "서울 강남구 ...",
  "trashcan_latitude": 37.0,
  "trashcan_longitude": 127.0,
  "server_url": "192.168.0.10"
}
```

`trashcan_id`를 쓰지 않을 때는 해당 필드를 빼면 됩니다.

추가 실패 응답 예시:
```json
{
  "created": false,
  "message": "trashcan_id가 이미 사용 중입니다."
}
```

성공 응답:
```json
{
  "created": true,
  "trashcan_id": 1,
  "message": "Trashcan created successfully"
}
```

실패 응답 예시:
```json
{
  "created": false,
  "message": "Failed to connect to server"
}
```

실패 경우:
- `200`: ping 실패 또는 연결 테스트 중 예외 발생 시 `created: false`
- `200`: 지정한 `trashcan_id`가 이미 존재하면 `created: false`, `message`에 사용 중 안내
- `422`: 요청 본문 누락/타입 오류
- `500`: DB 저장 오류

### 수정
- `PUT /management/trashcans`

요청 본문:
```json
{
  "trashcan_id": 1,
  "trashcan_name": "A",
  "trashcan_city": "서울",
  "address_detail": "서울 강남구 ...",
  "trashcan_latitude": 37.0,
  "trashcan_longitude": 127.0
}
```

성공 응답:
```json
{
  "updated": true,
  "trashcan_id": 1,
  "message": "Trashcan updated successfully"
}
```

실패 응답 예시:
```json
{
  "updated": false,
  "message": "Trashcan not found or deleted"
}
```

실패 경우:
- `200`: 대상이 없거나 삭제된 쓰레기통이면 `updated: false`
- `422`: 요청 본문 누락/타입 오류
- `500`: DB 저장 오류

### 삭제
- `DELETE /management/trashcans/{trashcan_id}`

성공 응답:
```json
{
  "deleted": true,
  "trashcan_id": 1,
  "message": "Trashcan deleted successfully"
}
```

실패 응답 예시:
```json
{
  "deleted": false,
  "message": "Trashcan not found or deleted"
}
```

실패 경우:
- `200`: 대상이 없거나 이미 삭제된 경우 `deleted: false`
- `422`: `trashcan_id`가 정수가 아닌 경우
- `500`: DB 저장 오류

### 복구
- `PUT /management/trashcans/{trashcan_id}/recover`

성공 응답:
```json
{
  "recovered": true,
  "trashcan_id": 1,
  "message": "Trashcan recovered successfully"
}
```

실패 응답 예시:
```json
{
  "recovered": false,
  "message": "Trashcan not found or not deleted"
}
```

실패 경우:
- `200`: 대상이 없거나 삭제 상태가 아니면 `recovered: false`
- `422`: `trashcan_id`가 정수가 아닌 경우
- `500`: DB 저장 오류

### 수거 처리
- `PUT /management/{trashcan_id}/collect`
- 해당 쓰레기통의 `current_volume`을 `0`으로 초기화합니다.

성공 응답:
```json
{
  "collected": true,
  "trashcan_id": 1,
  "current_volume": 0,
  "message": "Trashcan collected successfully"
}
```

실패 응답 예시:
```json
{
  "collected": false,
  "message": "Trashcan not found or deleted"
}
```

실패 경우:
- `200`: 대상이 없거나 삭제된 경우 `collected: false`
- `422`: `trashcan_id`가 정수가 아닌 경우
- `500`: DB 저장 오류

---

## 지도

### 지도 좌표 조회
- `GET /map/trashcans`
- 활성/삭제 쓰레기통을 분리해서 반환합니다.

성공 응답:
```json
{
  "active": [
    {
      "trashcan_id": 1,
      "trashcan_name": "A",
      "trashcan_latitude": 37.0,
      "trashcan_longitude": 127.0
    }
  ],
  "deleted": []
}
```

실패 경우:
- `500`: DB 조회 등 서버 내부 오류

---

## 탐지 결과 수신

### 탐지 결과 업로드
- `POST /detect/result`
- 요청 형식: `multipart/form-data`
- 필수 필드:
  - `file`: 이미지 파일
  - `metadata`: **유효한 JSON 문자열** (문법 오류 시 `422`, 쉼표 누락 등 주의)

#### `camera_id`와 쓰레기통
- `camera_id`는 DB의 **`trashcan.trashcan_id`(PK)** 와 동일한 값으로 조회합니다.
- 해당 PK의 행이 **없으면** `400`, 메시지: `등록되지 않은 쓰레기통입니다. camera_id=...`
- 행이 있으나 **`is_deleted=True`(소프트 삭제)** 이면 `400`, 메시지: `삭제된 쓰레기통입니다. trashcan_id=..., camera_id=...`
- 장비 ID를 미리 맞추려면 관리 API **`POST /management/trashcans`** 에서 선택 필드 **`trashcan_id`** 로 등록합니다.

#### 필터·저장 조건
- **`DETECTION_CONFIDENCE_THRESHOLD`**: 각 검출의 `score`가 임계값 미만이면 버립니다.
- **`DETECTION_MIN_INTERVAL_SECONDS`**: 같은 `camera_id`로 너무 자주 보내면 **DB에는 저장하지 않고** `204`만 반환 (에러 아님).
- 필터 후 **유효한 검출이 0개**이면 디텍션 행·이미지·`current_volume`/일별 통계 갱신 **없음** (`204`). 연결 상태(`is_online`) 갱신만 수행될 수 있습니다.
- `current_volume` 증가는 DB **`UPDATE ... SET current_volume = COALESCE(current_volume,0) + object_count`** 로 원자적 처리합니다.

#### 클래스 매핑·파일
- `class_id`는 기본적으로 `waste_type_id - 1` 규칙으로 매핑됩니다.
- 다른 매핑이 필요하면 `.env`의 `CLASS_ID_TO_WASTE_TYPE_ID`를 사용합니다.
- 업로드 이미지는 `IMAGE_PATH` 아래 `detect_img/<파일명>`으로 저장됩니다.
- DB의 `image_path`에는 상대 경로 `detect_img/<파일명>`이 저장됩니다.
- 저장 파일명 형식: `{trashcan_id}_{detection_id}_{YYYYMMDD_HHMMSS_mmm}_{uuid8}{suffix}`

`metadata` JSON 예시:
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

필드 사이에는 반드시 **쉼표**가 있어야 합니다. (잘못된 JSON은 `422`입니다.)

성공 응답:
- `204 No Content` (성공 저장, 간격으로 건너뜀, 검출 0으로 저장 생략 모두 동일하게 `204`일 수 있음)

실패 경우:
- `400`: 등록되지 않은 `camera_id`(PK 없음)
- `400`: 삭제된 쓰레기통(`is_deleted`)
- `422`: `metadata` JSON 파싱/스키마 검증 실패
- `422`: `file` 또는 `metadata` multipart 필드 누락
- `422`: `camera_id`, `class_id`, `bbox`, `score` 타입이 잘못된 경우
- `500`: 이미지 저장/DB 저장 등 서버 내부 예외

에러 로그 저장:
- `422`, `400`, `500` 계열 실패가 발생하면 가능한 경우 `trashcan_error_log`에 저장됩니다.
- `camera_id` 및 가능하면 `trashcan_id`가 함께 저장됩니다.
- **PK가 없는** `camera_id`만 `trashcan_id=null`로 남을 수 있습니다. 삭제된 쓰레기통의 경우 `trashcan_id`가 채워질 수 있습니다.
