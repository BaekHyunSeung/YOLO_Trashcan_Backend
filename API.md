# API 문서

### 공통
- Base URL: `http://<host>:8000`
- 응답 형식: JSON
- 시간 포맷: ISO 8601
- 에러 형식
```json
{ "detail": "에러 메시지" }
```

### 에러 코드
- `400` 잘못된 요청
- `404` 리소스 없음
- `422` 파라미터 오류
- `500` 서버 오류

---

## 대시보드

### 전체 탐지 요약
- `GET /dashboard/detections`
Response:
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

### 수거 필요 쓰레기통
- `GET /dashboard/trashcans/full`
Response:
```json
[
  { "trashcan_id": 1, "trashcan_name": "A", "fill_rate": 95.00 }
]
```

### 통계 차트
- `GET /dashboard/charts?period=week|month|year`
Response:
```json
{
  "period": "week",
  "start_date": "2026-02-03",
  "end_date": "2026-02-09",
  "total_count": 120,
  "items_by_type": { "MetalCan": 30 },
  "items_by_city": { "서울": 60 }
}
```

### 미연결/에러 쓰레기통 목록
- `GET /dashboard/trashcans/error`
 - 현재 미연결 상태이거나 최근 1분 내 에러 로그가 있는 쓰레기통을 반환합니다.
 - `last_connected_at` 기준 5분 이상 수신/테스트가 없으면 `is_online`이 False로 처리됩니다.
Response:
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

### 쓰레기통 에러 로그 조회
- `GET /dashboard/trashcans/error/{trashcan_id}?limit=50`
 - 디텍션 수신(`/detect/result`) 중 에러 발생 시 자동 저장된 로그를 조회합니다.
 - 동일 에러가 1분 내 반복되면 `repeat_count`만 증가합니다.
 - `limit`: 1~200 (기본 50)
Response:
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

---

## 쓰레기통 목록

### 목록 조회
- `GET /trashcans_list/trashcans?offset=0&limit=20`
- 수거량 많은 순으로 기본 정렬
Response:
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
      "fill_rate": 60.00
    }
  ]
}
```

### 정렬/검색
- `GET /trashcans_list/query?sort_by=collected|free_capacity|is_online&order=asc|desc&city=&name=&offset=0&limit=20`
Request Params:
```text
sort_by: collected | free_capacity | is_online (기본 collected)
order: asc | desc (기본 desc)
city: 도시명 부분 일치 필터 (선택)
name: 쓰레기통 이름 부분 일치 필터 (선택)
offset: 페이지 시작 (기본 0)
limit: 페이지 크기 (기본 20)
```
sort_by 설명:
```
collected: 수거된 총 객체 수 기준 정렬
free_capacity: 여유 용량(= capacity - current_volume) 기준 정렬
is_online: 연결 상태 기준 정렬 (false < true)
```
Response:
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
      "fill_rate": 60.00
    }
  ]
}
```

### 검색
- `query` API에 `city`, `name` 파라미터를 함께 사용합니다.

---

## 쓰레기통 상세

### 상세 조회
- `GET /trashcans_detail/{trashcan_id}`
Response:
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

### 연결 테스트
- `GET /trashcans_detail/{trashcan_id}/connection-test`
 - `server_url`에 저장된 라즈베리파이 사설 IP로 ping 연결 테스트합니다. (포트/경로 미사용)
 - 성공 시 `is_online`, `last_connected_at`이 갱신됩니다.
Response:
```json
{
  "trashcan_id": 1,
  "status": "ok",
  "message": "Server is healthy"
}
```

### 쓰레기 상세 데이터
- `GET /trashcans_detail/{trashcan_id}/waste-detail`
Response:
```json
{
  "trashcan_id": 1,
  "total_objects": 120,
  "total_events": 10,
  "items_by_type": {
    "MetalCan": [
      {
        "detection_id": 100,
        "image_name": "img_001.jpg",
        "image_path": "detect_img/img_001.jpg",
        "detected_at": "2026-02-09T14:10:00"
      }
    ],
    "PetBottle": [],
    "Plastic": [],
    "Styrofoam": []
  }
}
```

---

## 쓰레기통 관리

### 목록
- `GET /management/trashcans`
Response:
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

### 삭제된 쓰레기통 목록
- `GET /management/trashcans/deleted`
Response:
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

### 상태 확인
- `GET /management/trashcans/{trashcan_id}/health`
 - `server_url`에 저장된 라즈베리파이 사설 IP로 ping 연결 테스트합니다. (포트/경로 미사용)
 - 성공 시 `is_online`, `last_connected_at`이 갱신됩니다.
Response:
```json
{ "trashcan_id": 1, "status": "ok", "message": "Server is healthy" }
```

### 수정
- `PUT /management/trashcans`
Request Body:
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
Response:
```json
{
  "updated": true,
  "trashcan_id": 1,
  "message": "Trashcan updated successfully"
}
```

### 삭제
- `DELETE /management/trashcans/{trashcan_id}`
Response:
```json
{ "deleted": true, "trashcan_id": 1, "message": "Trashcan deleted successfully" }
```

### 복구
- `PUT /management/trashcans/{trashcan_id}/recover`
Response:
```json
{ "recovered": true, "trashcan_id": 1, "message": "Trashcan recovered successfully" }
```

### 생성
- `POST /management/trashcans`
 - 등록 전 `server_url`(라즈베리파이 사설 IP)로 ping 연결 테스트를 수행합니다.
 - 실패 시 등록이 중단되고 실패 응답을 반환합니다.
Request Body:
```json
{
  "trashcan_name": "A",
  "trashcan_capacity": 100,
  "trashcan_city": "서울",
  "address_detail": "서울 강남구 ...",
  "trashcan_latitude": 37.0,
  "trashcan_longitude": 127.0,
  "server_url": "192.168.0.10"
}
```
Response:
```json
{
  "created": true,
  "trashcan_id": 1,
  "message": "Trashcan created successfully"
}
```
Response (연결 실패):
```json
{
  "created": false,
  "message": "Failed to connect to server"
}
```

---

## 지도

### 지도 좌표 조회
- `GET /map/trashcans`
Response:
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

---

## 탐지 결과 수신

### 탐지 결과 업로드
- `POST /detect/result`
- 요청: `multipart/form-data`
  - `file`: 이미지 파일
  - `metadata`: JSON 문자열
Request Body (metadata JSON 예시):
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
Response: `204 No Content`
에러 발생 시 해당 쓰레기통 로그가 DB에 자동 저장됩니다.
