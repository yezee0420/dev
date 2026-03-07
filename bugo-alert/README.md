# BugoAlert — 부고 알림 서비스

네이버 뉴스에서 부고 기사를 매시간 크롤링하여 구조화된 데이터(소속/직급/관계/고인명/장례식장/호실/발인/연락처)를 추출하고, 웹 대시보드에서 검색·조회하며, 즐겨찾기 키워드 매칭 시 이메일 알림을 발송합니다.

## 사전 준비

1. [Naver Developers](https://developers.naver.com/)에서 애플리케이션 등록 → **검색 API** 사용 설정 → Client ID / Secret 복사
2. 이메일 알림을 사용하려면 Gmail 앱 비밀번호 생성 (Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호)

## 설치 및 실행

```bash
cd bugo-alert

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 열어 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 등을 입력

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

브라우저에서 http://localhost:8000 접속

## 주요 기능

| 페이지 | 경로 | 설명 |
|--------|------|------|
| 대시보드 | `/` | 최신 부고 목록 |
| 검색 | `/search` | 실시간 키워드 검색 (HTMX) |
| 상세 | `/obituary/{id}` | 부고 상세 정보 + 기사 원문 |
| 즐겨찾기 | `/favorites` | 키워드 등록/관리, 매칭 알림 |
| 화환 주문 | `/flower/order/{id}` | 협력업체 안내 (stub) |
| 수동 크롤링 | `/api/crawl-now` | 즉시 크롤링 실행 (디버그용) |

## 기술 스택

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, APScheduler
- **Frontend**: Jinja2, HTMX, Tailwind CSS (CDN)
- **DB**: SQLite (→ PostgreSQL 마이그레이션 가능)
- **알림**: SMTP 이메일 (aiosmtplib)
- **크롤링**: httpx, BeautifulSoup4
