# 2026-03-18 작업 정리

## 개요

오늘 작업은 크게 3가지였다.

1. 쓰레기 상세 조회 API에 페이지네이션과 종류별 조회 기능 추가
2. 서버 실행 설정과 CORS 설정을 `.env` 기반으로 정리
3. 쓰레기 타입(`wastetype`)을 `.env` 기준으로 동기화하고, 빠진 타입은 비활성화되도록 확장

---

## 1. 쓰레기 상세 조회 API 개선

대상:
- `routers/trashcan_detail_router.py`
- `service/trashcan_detail_service.py`
- `API.md`

변경 내용:
- `GET /trashcans_detail/{trashcan_id}/waste-detail`에 `offset`, `limit` 페이지네이션 적용
- `type_name` 필터를 추가해 전체 조회와 종류별 조회를 모두 지원
- 정렬 기준을 최신순으로 고정
  - `detected_at DESC`
  - `detection_id DESC`
  - `detail_id DESC`
- 응답에서 중복 성격이 강한 `items`, `page_count`는 제거

현재 요청 방식:
- 전체 조회: `/trashcans_detail/1/waste-detail?offset=0&limit=20`
- 종류별 조회: `/trashcans_detail/1/waste-detail?type_name=MetalCan&offset=0&limit=20`

현재 응답 핵심 필드:
- `trashcan_id`
- `type_name`
- `offset`
- `limit`
- `total_objects`
- `total_events`
- `items_by_type`

현재 `type_name`은 서버 시작 시 `.env`의 `WASTE_TYPE_{id}` 설정을 기반으로 동적으로 생성된 Enum 선택값을 사용한다.

---

## 2. 서버 실행 설정 `.env` 분리

대상:
- `main.py`
- `README.md`

변경 내용:
- 서버 실행 호스트와 포트를 `.env`에서 읽도록 변경
- CORS 허용 주소 목록도 `.env`에서 읽도록 변경
- 로그인/세션 기능이 없으므로 `allow_credentials=False`로 단순화

사용하는 환경변수:
- `APP_HOST`
- `APP_PORT`
- `ALLOWED_ORIGINS`

예시:

```env
APP_HOST=0.0.0.0
APP_PORT=8000
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174
```

의미:
- 실행 환경별로 코드 수정 없이 서버 주소와 포트를 바꿀 수 있음
- 프론트 허용 주소도 `.env`에서 관리 가능

---

## 3. `wastetype` 관리 방식 개선

대상:
- `db/entity.py`
- `service/waste_type_config.py`
- `service/detections_service.py`
- `routers/trashcan_detail_router.py`
- `service/dashboard_service.py`
- `service/trashcan_detail_service.py`
- `main.py`
- `README.md`

변경 내용:
- `wastetype`를 하드코딩 대신 `.env` 기반으로 관리하도록 변경
- 서버 시작 시 `.env`의 `WASTE_TYPE_{id}` 값을 읽어 `wastetype` 테이블과 동기화
- 기존에 없던 타입은 자동 생성
- 같은 ID의 이름이 바뀌면 `type_name` 갱신
- `.env`에서 빠진 타입은 삭제하지 않고 `is_active=False`로 비활성화

추가된 컬럼:
- `wastetype.is_active`

예시:

```env
WASTE_TYPE_1=MetalCan
WASTE_TYPE_2=PetBottle
WASTE_TYPE_3=Plastic
WASTE_TYPE_4=Styrofoam
```

새 타입 추가 예시:

```env
WASTE_TYPE_5=GlassBottle
```

동작 방식:
- 서버 시작 시 `wastetype`에 `id=5, type_name=GlassBottle, is_active=True`가 없으면 생성
- 기존 타입이 `.env`에서 사라지면 DB에서 삭제하지 않고 `is_active=False`로 전환
- 기존 탐지 이력은 그대로 유지됨

---

## 4. 탐지 매핑 설정화

대상:
- `service/detections_service.py`
- `service/waste_type_config.py`

변경 내용:
- 기존 `class_id -> type_name` 하드코딩 제거
- `.env` 기반 타입 설정을 통해 탐지 수신 시 쓰레기 타입을 결정하도록 변경
- 기본 규칙은 `class_id = waste_type_id - 1`
- 필요 시 `CLASS_ID_TO_WASTE_TYPE_ID`로 직접 지정 가능

예시:

```env
CLASS_ID_TO_WASTE_TYPE_ID=0:1,1:2,2:3,3:4
```

주의:
- 이 값은 필수는 아님
- YOLO `class_id` 순서와 `waste_type_id` 순서가 다를 때만 사용하면 됨

---

## 5. 조회/집계 로직 동적 타입 대응

대상:
- `service/dashboard_service.py` - 성진이 한테 이야기하기
- `service/trashcan_detail_service.py`

변경 내용:
- 기존 4개 타입 고정 딕셔너리 제거
- 타입 목록을 DB에서 읽어 동적으로 집계하도록 변경
- 따라서 타입이 추가되면 대시보드 집계와 상세 집계도 구조적으로 대응 가능

현재 정책:
- 집계 응답의 타입 목록은 DB 기준으로 생성됨
- 비활성 타입은 기존 이력 참조를 위해 DB에는 남아 있음

---

## 6. startup 처리 확장

대상:
- `main.py`
- `service/waste_type_config.py`

변경 내용:
- 서버 startup 시 아래 순서로 동작

1. 테이블 생성
2. `wastetype.is_active` 컬럼 존재 여부 확인
3. 없으면 컬럼 자동 추가
4. `.env` 기준으로 쓰레기 타입 동기화

의미:
- 별도 수동 SQL 없이 서버 시작만으로 기준 데이터와 스키마 일부를 보정할 수 있음

---

## 7. 문서 반영

대상:
- `README.md`
- `API.md`

반영 내용:
- `.env` 설정 방식 정리
- CORS 설정 방식 정리
- `WASTE_TYPE_{id}`와 `CLASS_ID_TO_WASTE_TYPE_ID` 설명 추가
- `.env`에서 빠진 타입 비활성화 정책 설명 추가
- 쓰레기 상세 조회 API의 페이지네이션/필터 설명 갱신

---

## 8. 최종 상태 요약

현재 프로젝트는 다음 방식으로 동작한다.

- 서버 호스트/포트/CORS는 `.env`로 관리
- 쓰레기 타입도 `.env` 기반으로 관리
- 서버 시작 시 `wastetype` 테이블과 자동 동기화
- `.env`에 없는 기존 타입은 삭제하지 않고 비활성화
- 상세 조회 API는 페이지네이션과 종류별 조회를 지원
- `type_name` 선택 목록은 서버 시작 시점의 `.env` 기준으로 생성됨

---

## 9. 주의사항

- `.env` 변경 사항은 서버 재시작 후 반영됨
- `type_name` 선택 목록도 서버 재시작 후 Swagger에 반영됨
- `is_active` 컬럼 추가는 startup 시 DB에 실제 반영됨
- DB 연결이 안 되면 startup 단계에서 동기화 작업도 실패할 수 있음

