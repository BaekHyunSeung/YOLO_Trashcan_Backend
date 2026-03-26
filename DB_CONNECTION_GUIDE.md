# DB 연결 가이드

## 개요

이 프로젝트는 현재 `MariaDB/MySQL + aiomysql + SQLModel` 조합을 기준으로 DB에 연결한다.

핵심 파일:
- `db/db.py`
- `main.py`
- `README.md`

현재 연결 문자열:

```python
DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PW}@{DB_IP}:{DB_PORT}/{DB_NAME}"
```

즉 현재 프로젝트는 기본적으로:
- DB 종류: MySQL/MariaDB
- 비동기 드라이버: `aiomysql`
- ORM/모델: `SQLModel`, `SQLAlchemy`

---

## 1. 현재 프로젝트의 DB 연결 방식

`db/db.py`에서 `.env` 값을 읽어 DB 엔진을 생성한다.

사용하는 환경변수:
- `DB_USER`
- `DB_PW`
- `DB_IP`
- `DB_PORT`
- `DB_NAME`

예시:

```env
DB_USER=yolo_user
DB_PW=1234
DB_IP=127.0.0.1
DB_PORT=3306
DB_NAME=yolo_trash
```

동작 방식:
- 서버 시작 전에 `.env`를 읽음
- 필수 환경변수가 하나라도 없으면 예외 발생
- 연결 문자열을 생성하고 비동기 엔진 생성
- 각 API 요청마다 세션을 열고 사용 후 닫음

---

## 2. 서버 시작 시 DB에서 일어나는 일

`main.py`의 startup 단계에서 아래 순서로 동작한다.

1. 전체 테이블 생성 확인
2. `wastetype.is_active` 컬럼 존재 여부 확인
3. 없으면 컬럼 추가
4. `.env` 기준으로 `wastetype` 동기화

즉 DB 연결이 정상이어야 startup이 완료되고 서버가 정상 실행된다.

DB 연결이 실패하면:
- 테이블 생성 실패
- `wastetype` 동기화 실패
- FastAPI startup 실패
- 서버 실행 중단

---

## 3. MariaDB 접속이 막히는 대표 원인

DB 접속 문제는 대부분 백엔드 코드가 아니라 MariaDB 서버 설정 문제다.

대표 원인 3가지:

1. `bind-address`
- DB가 외부 TCP 접속을 듣지 않음

2. 사용자 계정 권한
- 계정이 `localhost`에서만 접속 가능
- 특정 호스트만 허용됨

3. 방화벽
- `3306` 포트가 막혀 있음

---

## 4. 같은 컴퓨터인데도 접속이 막힐 수 있는 이유

같은 컴퓨터라도 MariaDB는 접속 호스트를 다르게 판단할 수 있다.

예:
- `localhost`
- `127.0.0.1`
- `192.168.x.x`

이 값들은 DB 입장에서 서로 다른 호스트처럼 취급될 수 있다.

즉 같은 컴퓨터여도:
- `user@localhost`
- `user@127.0.0.1`
- `user@%`

의 권한이 다를 수 있어서 접속 에러가 날 수 있다.

그래서 같은 PC에서만 쓸 때도 `.env`의 `DB_IP`를 명확히 맞추는 것이 중요하다.

권장:

```env
DB_IP=127.0.0.1
DB_PORT=3306
```

---

## 5. MariaDB 기본 세팅 방법

### 5-1. bind-address 설정

MariaDB 설정 파일에서:

```ini
bind-address = 0.0.0.0
```

보통 설정 파일 위치 예시:
- `/etc/mysql/mariadb.conf.d/50-server.cnf`
- `/etc/mysql/my.cnf`
- `/etc/my.cnf`

수정 후 재시작:

```bash
sudo systemctl restart mariadb
```

의미:
- DB가 외부에서 들어오는 TCP 연결도 받을 수 있도록 설정

### 5-2. 사용자 권한 설정

예시:

```sql
CREATE USER 'yolo_user'@'%' IDENTIFIED BY '비밀번호';
GRANT ALL PRIVILEGES ON yolo_trash.* TO 'yolo_user'@'%';
FLUSH PRIVILEGES;
```

더 안전하게 특정 IP만 허용하는 예시:

```sql
CREATE USER 'yolo_user'@'192.168.0.15' IDENTIFIED BY '비밀번호';
GRANT ALL PRIVILEGES ON yolo_trash.* TO 'yolo_user'@'192.168.0.15';
FLUSH PRIVILEGES;
```

### 5-3. 방화벽 설정

Ubuntu 기준:

```bash
sudo ufw allow 3306
sudo ufw status
```

---

## 6. 백엔드 코드로 해결 가능한 것과 불가능한 것

### 백엔드에서 바꿀 수 있는 것
- `DB_IP`
- `DB_PORT`
- `DB_USER`
- `DB_PW`
- `DB_NAME`
- 접속 문자열 형식
- 재시도 로직

### 백엔드에서 바꿀 수 없는 것
- MariaDB의 `bind-address`
- MariaDB 계정의 host 권한
- DB 서버 방화벽
- DB 서버가 연결을 듣지 않는 상태

즉 DB가 연결 자체를 안 받도록 설정되어 있으면, 백엔드 코드만 바꿔서는 해결할 수 없다.

---

## 7. 왜 환경을 옮길 때마다 문제가 반복될 수 있는가

새 Ubuntu/MariaDB 환경은 보통 기본 보안 설정이 다르다.

예를 들면:
- 어떤 환경은 `localhost`만 허용
- 어떤 환경은 `bind-address=127.0.0.1`
- 어떤 환경은 방화벽이 기본 활성화

그래서 DB 서버를 새로 세팅하거나 옮길 때:
- 백엔드 코드는 그대로여도
- DB 서버 정책이 달라서
- 접속 권한 문제가 반복될 수 있다

이건 비정상이 아니라 비교적 흔한 운영 이슈다.

---

## 8. 운영 관점 권장 방식

가장 현실적인 운영 방식은:

1. MariaDB 서버 초기 세팅을 표준화
2. `bind-address`, 사용자 권한, 방화벽 설정을 한 번에 맞춤
3. 백엔드는 `.env`만 바꿔서 연결

즉 환경을 옮길 때마다 백엔드를 고치는 게 아니라, DB 서버 초기 세팅 절차를 문서화해서 맞추는 것이 중요하다.

---

## 9. 다른 DB로 바꿀 수 있는가

가능은 하다.  
하지만 지금 프로젝트는 현재 MySQL/MariaDB 전용 연결 문자열을 사용하고 있다.

현재:

```python
mysql+aiomysql://...
```

즉 다른 DB를 쓰려면 최소한 아래를 바꿔야 한다.

1. DB 연결 문자열
2. 드라이버 패키지
3. DB별 SQL 차이

예시:

### PostgreSQL

```env
DATABASE_URL=postgresql+asyncpg://user:pw@host:5432/dbname
```

필요 패키지:

```bash
pip install asyncpg
```

### SQLite

```env
DATABASE_URL=sqlite+aiosqlite:///./test.db
```

필요 패키지:

```bash
pip install aiosqlite
```

주의:
- ORM 모델은 어느 정도 재사용 가능
- 하지만 `SHOW COLUMNS`, `ALTER TABLE ... BOOLEAN` 같은 일부 로직은 MariaDB 의존적일 수 있음

---

## 10. 이 프로젝트에서 MariaDB 의존적인 부분

현재 MariaDB/MySQL 의존성이 있는 부분:
- `db/db.py`의 `mysql+aiomysql`
- `requirements.txt`의 `aiomysql`
- `service/waste_type_config.py`의 `SHOW COLUMNS`
- `service/waste_type_config.py`의 `ALTER TABLE ... BOOLEAN`

즉 완전히 다른 DB로 옮기려면 단순히 `.env`만 바꾸는 것으로는 부족하고, 일부 코드 수정이 필요할 수 있다.

---

## 11. 문제 발생 시 체크리스트

DB 연결이 안 될 때는 아래 순서로 확인한다.

1. `.env`의 `DB_IP`, `DB_PORT`, `DB_USER`, `DB_PW`, `DB_NAME` 확인
2. DB 서버 프로세스 실행 상태 확인
3. `bind-address` 확인
4. 사용자 권한 확인
5. 방화벽 확인
6. 백엔드 실행 로그에서 에러 메시지 확인

대표 에러 의미:
- `Access denied for user`
  - 계정 권한 문제
- `Can't connect to MySQL server`
  - 포트, 방화벽, bind-address, IP 문제
- `Host is not allowed to connect`
  - 해당 호스트 접속 권한 없음

---

## 12. 한 줄 요약

이 프로젝트의 DB 연결 문제는 대부분 백엔드 코드보다 MariaDB 서버의 수신 설정, 사용자 권한, 방화벽 설정에서 발생하며, 백엔드 코드만으로는 우회할 수 없다.

