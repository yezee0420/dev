# BugoAlert — 부고 알림 서비스

네이버 뉴스에서 부고 기사를 매시간 자동 크롤링하여 **핵심인물(key_person)** 중심의 구조화된 데이터를 추출하고, 웹 대시보드에서 검색·조회하며, 즐겨찾기 키워드 매칭 시 이메일 알림을 발송합니다.

> **핵심 철학**: "어느 회사의 누구와 관련된 누가 돌아가셨는가?"를 빠르게 파악하는 것이 목적입니다. 고인보다 **조문 대상(핵심인물)** 이 더 중요한 정보입니다.

---

## 주요 기능

- **자동 크롤링** — 매시간 네이버 뉴스 검색 API로 최대 1,000건 수집 (10페이지×100건), 비부고 기사 자동 필터링
- **스마트 파싱** — 12개 이상의 제목 패턴 + 본문 파싱 (고인: `이름(향년 N세) 씨 별세`, `이름씨 별세` 지원) → 핵심인물/소속/직급/관계/고인/장례식장/호실/발인/연락처 추출
- **중복 제거·병합** — `(고인, 핵심인물)`당 1개 레코드, 동일 부고 여러 기사는 raw_text 합쳐 병합, 품질 보정(본인상 제거·장례식장 통일 등). 상세: [docs/DEDUP_MERGE_LOGIC.md](docs/DEDUP_MERGE_LOGIC.md)
- **실시간 검색** — HTMX 기반 키워드 검색 (핵심인물, 소속, 고인, 장례식장 등)
- **즐겨찾기 알림** — 키워드 등록 시 매칭되는 부고 발생하면 이메일 자동 발송
- **화환 주문** — 조문 화환 협력업체 연동 (stub)

---

## 파싱 성능

| 항목 | 수치 |
|------|------|
| 1회 크롤링 수집량 | 최대 1,000건 (10페이지×100건, 네이버 API start 1~1000 제한) |
| 네이버 뉴스 중 부고 기사 식별 | 비부고 자동 필터링 |
| 핵심인물(key_person) 추출 | 제목 패턴 12개 이상 |
| 고인(deceased_name) 파싱 | `이름(향년 N세) 씨 별세`, `이름씨 별세` 패턴 지원 |
| 발인일 표시 | `9일` → `3월 9일` (월 자동 보완) |
| 비부고 쓰레기 기사 유입 | **0건** |

### 지원하는 제목 패턴 예시

```
[부고] 설명환(포스코DX 그룹장)씨 모친상
[부고] 이한울 씨(시사IN PD) 조부상
[부고]핀포인트뉴스 신홍범 대표 부친상
[부고종합·6일] 서승권 한화오션 안전총괄 전무 장모상 등
[부고]김성령(배우)·김성경(방송인)씨 모친상
[부고] 이명구(전 태경그룹 부회장)씨 별세
[부고] LG전자 중국 칭다오칠러 남상철 법인장 장인상
```

---

## 사전 준비

1. **네이버 API 키 발급**
   - [Naver Developers](https://developers.naver.com/) → 애플리케이션 등록 → **검색 API** 사용 설정 → Client ID / Secret 복사

2. **이메일 알림** (선택)
   - Gmail 앱 비밀번호 생성: Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호

---

## 설치 및 실행

```bash
cd bugo-alert

# 가상환경 생성 & 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 입력

# 서버 실행 (자동으로 브라우저 열림)
uvicorn app.main:app --reload --port 8001
```

서버 시작 시 자동으로:
- DB 테이블 생성
- 첫 크롤링 즉시 실행
- 브라우저 자동 열기 (이미 열려 있으면 기존 탭 포커스)

**데이터 정리 수동 실행** (크롤링 직후 자동 실행되며, 필요 시 수동 호출):
```bash
cd bugo-alert && PYTHONPATH=. python scripts/run_cleanup.py
# --dry-run: DB 변경 없이 변경 예정만 출력
```

---

## 페이지 구조

| 페이지 | 경로 | 설명 |
|--------|------|------|
| 대시보드 | `/` | 최신 부고 목록 + 크롤링 상태(시작시간/소요시간/API호출/실패사유) + 수동 크롤링 버튼 |
| 검색 | `/search` | 실시간 키워드 검색 (HTMX) |
| 상세 | `/obituary/{id}` | 핵심인물/고인/장례 정보 + 기사 원문 |
| 즐겨찾기 | `/favorites` | 알림 키워드 등록/관리 (HTMX CRUD) |
| 화환 주문 | `/flower/order/{id}` | 협력업체 안내 (stub) |

### API 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /api/crawl-now` | 수동 크롤링 즉시 실행 (asyncio.Lock 보호) |
| `GET /api/crawl-status` | 크롤링 상태 JSON |
| `GET /api/cleanup-now` | 데이터 정리 수동 실행 (중복 제거·병합·품질 보정) |
| `GET /health` | 헬스체크 (DB 연결 확인) |

---

## 데이터 모델 (key_person 중심)

```
Obituary
├── key_person        핵심인물 (조문 대상) ← 가장 중요
├── organization      소속 (회사/기관)
├── position          직급/직위
├── relationship      관계 (모친상, 부친상 등)
├── deceased_name     고인명
├── deceased_age      고인 나이
├── funeral_hall      장례식장
├── room_number       호실
├── funeral_date      발인일
├── funeral_time      발인시간
├── contact           연락처
├── related_persons   관계자 목록
├── dedup_key         중복 제거 키 (UNIQUE)
└── raw_text          기사 원문 (5000자)
```

---

## 프로젝트 구조

```
bugo-alert/
├── .env.example              환경변수 템플릿
├── requirements.txt          Python 의존성
├── README.md
├── TODO.md                   수정 이력 및 미처리 항목 상세
├── migrate_dedup.py          기존 DB 중복 정리 일회성 스크립트
└── app/
    ├── main.py               FastAPI 앱 엔트리포인트
    ├── config.py              Pydantic 설정 (.env)
    ├── database.py            SQLAlchemy 엔진/세션
    ├── models.py              ORM 모델 (Obituary, Favorite, NotificationLog)
    ├── crawler/
    │   ├── naver_api.py       네이버 검색 API 호출
    │   ├── scraper.py         기사 본문 스크래핑
    │   └── parser.py          제목/본문 정규식 파싱 (핵심 파일)
    ├── deduplication/        데이터 정리 (중복 제거, 병합, 품질 보정)
    │   ├── merge.py           동일 부고 병합 (raw_text 합침)
    │   ├── quality.py         품질 보정
    │   └── run.py             run_cleanup() 파이프라인
    ├── scheduler/
    │   └── jobs.py            크롤링 파이프라인 + 즐겨찾기 매칭
    ├── notifications/
    │   ├── base.py            BaseNotifier 추상 클래스
    │   └── email_sender.py    SMTP 이메일 알림
    ├── routers/
    │   ├── obituaries.py      부고 목록/검색/상세
    │   ├── favorites.py       즐겨찾기 CRUD
    │   └── flower_order.py    화환 주문
    └── templates/
        ├── base.html          공통 레이아웃
        ├── index.html         대시보드
        ├── search.html        검색
        ├── detail.html        상세
        ├── favorites.html     즐겨찾기
        ├── flower_order.html  화환 주문
        └── partials/
            ├── obituary_table.html   검색 결과 파셜
            └── favorites_list.html   즐겨찾기 목록 파셜
```

**Cursor mdc 규칙:** 워크스페이스 루트(`dev/.cursor/rules/`)에 `bugo-backend-agent`, `bugo-parser-agent`, `bugo-dedup-agent`, `bugo-notification-agent`, `bugo-ui-agent`가 있음. 하위 프로젝트 `.cursor/rules/`는 적용되지 않음.

**네이버 API:** 일 25,000회 제한. 1회 크롤링≈10호출 → 약 2,500회 크롤링/일 가능.

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, APScheduler |
| Frontend | Jinja2, HTMX 2.0, Tailwind CSS (CDN) |
| DB | SQLite (WAL 모드) |
| 알림 | SMTP 이메일 (aiosmtplib) |
| 크롤링 | httpx, BeautifulSoup4, 네이버 검색 API |
| 설정 | pydantic-settings (.env) |

---

## 환경변수

| 변수 | 설명 | 필수 |
|------|------|------|
| `NAVER_CLIENT_ID` | 네이버 API Client ID | **필수** |
| `NAVER_CLIENT_SECRET` | 네이버 API Client Secret | **필수** |
| `SMTP_HOST` | SMTP 서버 | 선택 |
| `SMTP_PORT` | SMTP 포트 (기본 587) | 선택 |
| `SMTP_USER` | SMTP 사용자 | 선택 |
| `SMTP_PASSWORD` | SMTP 비밀번호 | 선택 |
| `SMTP_FROM` | 발신자 이메일 | 선택 |
| `CRAWL_INTERVAL_MINUTES` | 크롤링 주기 (기본 60) | 선택 |
| `DATABASE_URL` | DB 경로 (기본 sqlite:///bugo.db) | 선택 |

---

## 수정 이력 및 미처리 항목

### ✅ 완료된 수정

| 항목 | 설명 |
|------|------|
| source_url 스킵 | 이미 본 URL은 스크래핑 건너뜀 (`_URLCache` LRU, 최대 50,000건) |
| 페이지네이션 | start 파라미터로 최대 1,000건 수집 (10페이지×100건) |
| race condition | `/api/crawl-now`에 `asyncio.Lock()` 적용 |
| 메모리 누수 | URL 캐시 LRU로 오래된 항목 자동 제거 |
| 404 처리 | 상세/화환/즐겨찾기 존재하지 않을 때 `HTTPException(404)` |
| 입력 검증 | 즐겨찾기 키워드 1~200자, 이메일 형식 검증 |
| API 키 검증 | 미설정/플레이스홀더 시 크롤링 조기 반환 |
| N+1 쿼리 | `_match_favorites` 단일 IN 쿼리로 변경 |
| 검색 쿼리 | `_search_query` 한 번만 호출 후 재사용 |
| `.gitignore` | `.env`, `*.db`, `__pycache__/` 등 추가 |
| `/health` | DB 연결 확인 헬스체크 엔드포인트 |

### ⏳ 미처리 항목

| 심각도 | 항목 | 설명 |
|--------|------|------|
| **Critical** | CSRF 미적용 | POST/DELETE 폼에 CSRF 토큰 없음 |
| **Medium** | 스크래퍼 예외 처리 | `except Exception`이 너무 broad → 디버깅 어려움 |
| **Medium** | 이메일 발송 실패 재시도 | `status="failed"`만 기록, 재발송 로직 없음 |
| **Low** | `datetime.utcnow` deprecated | `datetime.now(timezone.utc)`로 변경 권장 |
| **Low** | `crawl_interval_minutes` 검증 | 0 이하/과도한 값 입력 시 검증 없음 |
| **Low** | LOG_LEVEL 환경변수 | 로그 레벨을 환경변수로 제어 불가 |
| **Missing** | Rate limiting | `/api/crawl-now`, `/favorites/add` 등에 rate limit 없음 |

자세한 내용: `TODO.md` 참고.

---

## 향후 계획

- [ ] 카카오톡/SMS/앱 푸시 알림 채널 추가
- [ ] 즐겨찾기 키워드 유형별 분류 (인물/회사/기관)
- [ ] 화환 주문 협력업체 연동 및 결제
- [ ] PostgreSQL 마이그레이션 (운영 환경)
- [ ] Docker 컨테이너화 및 CI/CD
- [ ] 파싱 정확도 모니터링 대시보드
