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
```json
{
  "total_objects": 120,
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
```json
[
  { "trashcan_name": "A", "fill_status": "포화" }
]
```

### 통계 차트
- `GET /dashboard/charts?period=week|month|year`
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

### 미연결 쓰레기통 목록
- `GET /dashboard/trashcan/unconnected`
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

### 미연결 쓰레기통 로그 수신
- `POST /dashboard/trashcan/unconnected/{trashcan_id}/log`
```json
{ "status_code": 500, "message": "Model error", "occurred_at": "2026-02-09T14:10:00Z" }
```
```json
{ "saved": true }
```

### 미연결 쓰레기통 로그 조회
- `GET /dashboard/trashcan/unconnected/{trashcan_id}/log?limit=50`
```json
{
  "trashcan_id": 1,
  "logs": [
    { "trashcan_id": 1, "status_code": 500, "message": "Model error", "occurred_at": "2026-02-09T14:10:00Z" }
  ]
}
```

---

## 쓰레기통 목록

### 목록 조회
- `GET /trashcans_list/trashcans?offset=0&limit=20`

### 정렬
- `GET /trashcans_list/sorting?sort_by=collected|free_capacity|fill_rate|is_online&order=asc|desc&city=&name=&offset=0&limit=20`

### 검색
- `GET /trashcans_list/search?city=&name=&offset=0&limit=20`

---

## 쓰레기통 상세

### 상세 조회
- `GET /trashcans_detail/{trashcan_id}`
- Alias: `GET /trashcans_list/{trashcan_id}`

### 연결 테스트
- `GET /trashcans_detail/{trashcan_id}/connection-test`
- Alias: `GET /trashcans_list/{trashcan_id}/connection-test`

### 쓰레기 상세 데이터
- `GET /trashcans_detail/{trashcan_id}/waste-detail`
- Alias: `GET /trashcans_list/{trashcan_id}/waste-detail`

---

## 쓰레기통 관리

### 목록
- `GET /management/trashcans`

### 상태 확인
- `GET /management/trashcans/{trashcan_id}/health`

### 수정
- `PUT /management/trashcans`

### 삭제
- `DELETE /management/trashcans/{trashcan_id}`

### 복구
- `PUT /management/trashcans/{trashcan_id}/recover`

### 생성
- `POST /management/trashcans`

---

## 지도

### 지도 좌표 조회
- `GET /map/trashcans`
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
```json
{
  "camera_id": "CAM_01",
  "frame_id": "frame_001",
  "detections": [
    { "class_id": 0, "bbox": [0, 0, 10, 10], "score": 0.98 }
  ],
  "timestamp": "2026-02-09T14:10:00Z"
}
```
