# BugoAlert — 부고 알림 서비스

네이버 뉴스에서 부고 기사를 매시간 자동 크롤링하여 **핵심인물(key_person)** 중심의 구조화된 데이터를 추출하고, 웹 대시보드에서 검색·조회하며, 즐겨찾기 키워드 매칭 시 이메일 알림을 발송합니다.

> **핵심 철학**: "어느 회사의 누구와 관련된 누가 돌아가셨는가?"를 빠르게 파악하는 것이 목적입니다. 고인보다 **조문 대상(핵심인물)** 이 더 중요한 정보입니다.

---

## 주요 기능

- **자동 크롤링** — 매시간 네이버 뉴스 검색 API로 100건 수집, 비부고 기사 자동 필터링
- **스마트 파싱** — 12개 이상의 제목 패턴 + 본문 파싱으로 핵심인물/소속/직급/관계/고인/장례식장/호실/발인/연락처 추출
- **중복 제거** — `key_person|relationship` 기반 dedup (deceased_name 제외) + 소프트 매칭, 동일 부고는 빈 필드 보충만
- **실시간 검색** — HTMX 기반 키워드 검색 (핵심인물, 소속, 고인, 장례식장 등)
- **즐겨찾기 알림** — 키워드 등록 시 매칭되는 부고 발생하면 이메일 자동 발송
- **화환 주문** — 조문 화환 협력업체 연동 (stub)

---

## 파싱 성능

| 항목 | 수치 |
|------|------|
| 네이버 뉴스 100건 중 부고 기사 식별 | ~83건 (비부고 17건 필터링) |
| 핵심인물(key_person) 추출 성공률 | **100%** (미파싱 0건) |
| 중복 제거 후 고유 부고 | ~39건 (나머지는 보충 merge) |
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
uvicorn app.main:app --reload --port 8000
```

서버 시작 시 자동으로:
- DB 테이블 생성
- 첫 크롤링 즉시 실행
- 브라우저에서 `http://localhost:8000` 자동 열기

---

## 페이지 구조

| 페이지 | 경로 | 설명 |
|--------|------|------|
| 대시보드 | `/` | 최신 부고 목록 + 크롤링 상태 패널 + 수동 크롤링 버튼 |
| 검색 | `/search` | 실시간 키워드 검색 (HTMX) |
| 상세 | `/obituary/{id}` | 핵심인물/고인/장례 정보 + 기사 원문 |
| 즐겨찾기 | `/favorites` | 알림 키워드 등록/관리 (HTMX CRUD) |
| 화환 주문 | `/flower/order/{id}` | 협력업체 안내 (stub) |

### API 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /api/crawl-now` | 수동 크롤링 즉시 실행 |
| `GET /api/crawl-status` | 크롤링 상태 JSON 반환 |

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
├── (mdc 규칙은 dev/.cursor/rules/ 에 있음 — 워크스페이스 루트만 적용됨)
│   bugo-backend-agent.mdc, bugo-parser-agent.mdc, bugo-dedup-agent.mdc,
│   bugo-notification-agent.mdc, bugo-ui-agent.mdc
└── app/
    ├── main.py               FastAPI 앱 엔트리포인트
    ├── config.py              Pydantic 설정 (.env)
    ├── database.py            SQLAlchemy 엔진/세션
    ├── models.py              ORM 모델 (Obituary, Favorite, NotificationLog)
    ├── crawler/
    │   ├── naver_api.py       네이버 검색 API 호출
    │   ├── scraper.py         기사 본문 스크래핑
    │   └── parser.py          제목/본문 정규식 파싱 (핵심 파일)
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

## 향후 계획

- [ ] 카카오톡/SMS/앱 푸시 알림 채널 추가
- [ ] 즐겨찾기 키워드 유형별 분류 (인물/회사/기관)
- [ ] 화환 주문 협력업체 연동 및 결제
- [ ] PostgreSQL 마이그레이션 (운영 환경)
- [ ] Docker 컨테이너화 및 CI/CD
- [ ] 파싱 정확도 모니터링 대시보드
