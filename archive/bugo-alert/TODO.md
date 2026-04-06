# BugoAlert — 수정/개선 TODO

## ✅ 완료된 수정

### 크롤링

- **source_url 스킵**: 이미 DB에 있는 URL은 스크래핑 건너뜀 (`_URLCache` LRU, 최대 50,000건)
- **페이지네이션**: `start` 파라미터로 최대 1,000건 수집 (10페이지×100건)
- **API 키 검증**: 미설정/플레이스홀더 시 크롤링 조기 반환
- **네트워크 오류**: Timeout, ConnectError 시 해당 페이지에서 중단

### 안정성

- **race condition**: `/api/crawl-now`에 `asyncio.Lock()` 적용
- **메모리 누수**: URL 캐시 LRU로 오래된 항목 자동 제거
- **N+1 쿼리**: `_match_favorites`에서 NotificationLog 단일 IN 쿼리로 변경

### API/라우터

- **404 처리**: 상세/화환/즐겨찾기 존재하지 않을 때 `HTTPException(404)`
- **입력 검증**: 즐겨찾기 키워드 1~200자, 이메일 형식 검증
- **검색 쿼리**: `_search_query` 한 번만 호출 후 count/offset 재사용
- **`/health`**: DB 연결 확인 헬스체크 엔드포인트

### 기타

- **`.gitignore`**: `.env`, `*.db`, `__pycache__/` 등 추가
- **`source_url` 인덱스**: `ix_obituaries_source_url` 추가

---

## ⏳ 미처리 항목

### Critical

| 항목 | 설명 | 담당 |
|------|------|------|
| **CSRF 미적용** | POST/DELETE 폼에 CSRF 토큰 없음. 악의적 사이트에서 위조 가능 | UI/Backend |

### Medium

| 항목 | 설명 | 담당 |
|------|------|------|
| **스크래퍼 예외 처리** | `scraper.py`의 `except Exception`이 너무 broad → 디버깅 어려움 | Parser |
| **이메일 발송 실패 재시도** | `status="failed"`만 기록, 재발송 로직 없음 | Notification |

### Low

| 항목 | 설명 | 담당 |
|------|------|------|
| **`datetime.utcnow` deprecated** | Python 3.12+에서 `datetime.now(timezone.utc)` 권장 | Backend |
| **`crawl_interval_minutes` 검증** | 0 이하/과도한 값 입력 시 검증 없음 (`Field(ge=1, le=1440)`) | Backend |
| **LOG_LEVEL 환경변수** | 로그 레벨을 환경변수로 제어 불가 | Backend |

### Missing

| 항목 | 설명 | 담당 |
|------|------|------|
| **Rate limiting** | `/api/crawl-now`, `/favorites/add` 등에 rate limit 없음 | Backend |

---

## 참고

- 수정 시 해당 에이전트 규칙(`.cursor/rules/bugo-*-agent.mdc`)도 함께 업데이트
- `README.md`의 "수정 이력 및 미처리 항목" 섹션 동기화
