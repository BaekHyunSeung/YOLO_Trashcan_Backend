# YOLO Trashcan Backend

쓰레기통/대시보드/탐지 수신용 백엔드 서버입니다.

### 서버 사용 초기 환경 구성
## 가상환경 생성

```bash
python -m venv .venv
```

## 가상환경 활성화

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Windows CMD:

```bat
.venv\Scripts\activate.bat
```

macOS / Linux:

```bash
source .venv/bin/activate
```

## 패키지 설치

```bash
pip install -r requirements.txt
```

가상환경이 활성화된 상태에서 패키지를 설치하세요.

## 서버 실행

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

실제 실행 호스트/포트는 `.env`의 `APP_HOST`, `APP_PORT` 값을 우선 사용합니다.

## 환경 변수(.env)

`.env`에 DB 접속 정보, 서버 실행 정보, 이미지 저장 경로, 기본 쓰레기 타입 정보를 설정해야 합니다.

```
DB_USER=
DB_PW=
DB_IP=localhost
DB_PORT=3306
DB_NAME=yolo_trash
APP_HOST=0.0.0.0
APP_PORT=8000
ALLOWED_ORIGINS=http://localhost:5173
IMAGE_PATH=
WASTE_TYPE_1=MetalCan
WASTE_TYPE_2=PetBottle
WASTE_TYPE_3=Plastic
WASTE_TYPE_4=Styrofoam
CLASS_ID_TO_WASTE_TYPE_ID=0:1,1:2,2:3,3:4
```

- `DB_USER`, `DB_PW`, `DB_IP`, `DB_PORT`, `DB_NAME`: DB 접속 정보
- `APP_HOST`: FastAPI 서버 실행 호스트
- `APP_PORT`: FastAPI 서버 실행 포트
- `ALLOWED_ORIGINS`: CORS 허용 프론트 주소
- `IMAGE_PATH`: 디텍션 업로드 이미지를 저장할 상위 디렉터리 경로
- `WASTE_TYPE_{id}`: `wastetype` 테이블에 동기화할 쓰레기 타입 이름
- `CLASS_ID_TO_WASTE_TYPE_ID`: YOLO `class_id`와 `waste_type_id`를 직접 매핑하는 선택 설정
- `WASTE_TYPE_5=GlassBottle`처럼 새 타입을 추가하면 서버 시작 시 자동 반영됩니다.
- `.env`에서 빠진 타입은 서버 시작 시 `wastetype.is_active=False`로 비활성화됩니다.
- 기본 매핑은 `class_id = waste_type_id - 1`입니다.
- `CLASS_ID_TO_WASTE_TYPE_ID`를 비워두면 기본 매핑 규칙이 적용됩니다.

## startup 동작

서버 시작 시 아래 순서로 초기화가 진행됩니다.

1. `SQLModel.metadata.create_all()`로 전체 테이블 생성 확인
2. `.env`의 `WASTE_TYPE_{id}` 설정 기준으로 `wastetype` 동기화
3. `.env`에 있는 타입은 활성화, 없는 기존 타입은 비활성화

즉 startup이 정상 완료되어야:
- 테이블 구조 보정
- 쓰레기 타입 기준 데이터 동기화
- API 정상 실행

이 함께 완료됩니다.

## CORS 설정

- 허용할 프론트 주소는 `.env`의 `ALLOWED_ORIGINS`에서 관리합니다.
- 현재 프로젝트는 로그인/세션 인증을 사용하지 않으므로 `allow_credentials=False`로 설정합니다.
- 현재 코드는 `ALLOWED_ORIGINS` 한 개 값을 리스트로 감싸서 사용합니다.

## 목데이터
- 에지 모델이 보내는 `camera_id`와 동일한 `trashcan_id`를 가진 쓰레기통 데이터가 필요합니다.
- 쓰레기 종류 데이터는 `.env`의 `WASTE_TYPE_{id}` 설정을 기준으로 서버 시작 시 `wastetype` 테이블에 자동 동기화됩니다.
- `.env`에 없는 기존 타입은 삭제하지 않고 비활성화하여, 기존 탐지 이력 참조는 유지됩니다.
```
1: MetalCan
2: PetBottle
3: Plastic
4: Styrofoam
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
├─ service/
│  ├─ dashboard_service.py        # 대시보드 집계/통계 처리
│  ├─ detections_service.py       # 디텍션 저장/매핑 처리
│  ├─ trashcan_detail_service.py  # 쓰레기통 상세/이력 조회
│  ├─ trashcan_list_service.py    # 목록/검색/정렬 처리
│  ├─ trashcan_management_service.py # 관리(생성/수정/삭제) 처리
│  └─ trashcan_map_service.py     # 지도용 좌표 조회
└─ utils/
   ├─ connection_utils.py         # ping 연결 체크 유틸
   ├─ trashcan_status_utils.py    # 온라인 상태 갱신 유틸
   └─ waste_type_config.py        # 쓰레기 타입 설정/동기화 유틸
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

`class_id`는 기본적으로 `waste_type_id - 1` 규칙으로 타입에 매핑됩니다. 다른 순서를 사용하려면 `.env`의 `CLASS_ID_TO_WASTE_TYPE_ID`를 설정하면 됩니다.

## 이미지 저장 규칙

- 디텍션 업로드 시 전달된 이미지 파일은 서버 디스크에 저장됩니다.
- 실제 저장 경로의 상위 디렉터리는 `.env`의 `IMAGE_PATH`를 사용합니다.
- DB의 `image_path`에는 상대 경로 형식인 `detect_img/<파일명>`이 저장됩니다.
- 최종 저장 경로는 `IMAGE_PATH + detect_img/<파일명>` 조합으로 결정됩니다.
- `IMAGE_PATH`를 NULL처럼 상대 경로로 두면 프로젝트 폴더 기준으로 저장됩니다.
- 저장 파일명은 `{trashcan_id}_{detection_id}_{detected_at}_{uuid}` 형식을 사용합니다.
- 시간값은 파일명으로 안전하게 쓰기 위해 `YYYYMMDD_HHMMSS_mmm` 형식으로 저장됩니다.
- 마지막에는 중복 방지를 위한 8자리 UUID가 추가됩니다.

예시:

```text
IMAGE_PATH=
DB image_path=detect_img/1_296_20260327_141424_123_a1b2c3d4.jpg
실제 저장 경로=./프로젝트폴더/detect_img/1_296_20260327_141424_123_a1b2c3d4.jpg
```

## 에러 로그

- 저장 트리거: 디텍션 수신(`/detect/result`) 처리 중 에러 발생 시 자동 저장
- 보조 필드: `trashcan_id`를 찾을 수 없는 경우를 위해 로그에 `camera_id`도 함께 저장
- 미등록 `camera_id` 로그는 `trashcan_id=NULL` 상태로 저장되며 `/dashboard/trashcans/error/unregistered`에서 조회할 수 있습니다.
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

## 대시보드 집계 기준

- 대시보드의 전체 탐지 요약과 차트 집계는 `is_active=True`인 쓰레기 타입만 대상으로 계산합니다.
- 비활성 타입은 기존 탐지 이력을 위해 DB에 남아 있을 수 있지만, 대시보드 총계/차트 집계에서는 제외됩니다.
- 새 탐지 저장도 활성 타입만 반영됩니다.

## 포화도(`fill_rate`) 계산 기준

- 포화도는 `current_volume / trashcan_capacity * 100` 방식으로 계산합니다.
- `current_volume`은 디텍션 수신 시 감지된 객체 수만큼 누적됩니다.
- 내부 계산값은 100%를 넘을 수 있지만, API 응답으로 내려주는 `fill_rate` 값은 최대 `100.0`으로 제한합니다.

## 쓰레기통 등록 주의사항

쓰레기통 등록 시 `server_url`로 연결 테스트를 수행합니다. 연결이 실패하면 등록이 중단됩니다.
