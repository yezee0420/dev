# Progress — 현재 진행 상황

> **단일 진실 소스 (Single Source of Truth).** 사용자가 "지금 어떤 단계야?" 물으면 이 파일을 읽고 답한다. 작업을 마치거나 Phase를 전환할 때 즉시 업데이트한다.

- **마지막 업데이트**: 2026-04-21
- **현재 Phase**: Phase 1 (Web MVP + 소셜 로그인) — UI 작업 중
- **현재 Sub-task**: 온보딩 Step 2 (구독 + 고정비 입력 병합 화면) 완성 — 검색/인기 칩/카테고리 아코디언/요금제 모달/고정비 프리셋 칩+인라인 폼/커스텀 고정비/내 항목 탭. 다음: Step 3 (직접 추가 폼).

## 한눈에 보기

| Phase | 상태 | 비고 |
|---|---|---|
| **0 — 기획** | 🟢 완료 | Supabase·OAuth 앱 등록은 사용자 작업 — Phase 1 내부에서 연결 |
| **1 — Web MVP + 소셜 로그인** | 🟡 진행 중 | 랜딩·로그인·구독 선택 완성, 직접 추가 폼 착수 예정 |
| 2 — 분석·캘린더 + 브랜드명 확정 | ⚪ 대기 | |
| 3 — 알림 | ⚪ 대기 | |
| 4 — Switch & Save / 수익화 | ⚪ 대기 | |
| 5 — 앱 (Expo) | ⚪ 대기 | |
| 6+ — 오픈뱅킹·B2B2C | ⚪ 장기 | |

범례: 🟢 완료 · 🟡 진행 중 · 🔵 블로커 · ⚪ 대기

## Phase 0 상세

- [x] 프로젝트 폴더 `monthlybills/` 생성
- [x] `README.md`, `docs/roadmap.md`, `docs/business-model.md`, `docs/db-schema.md`, `docs/onboarding-flow.md`
- [x] `data/seed-subscriptions.json` (31 서비스)
- [x] `/git-ship` 슬래시 커맨드 (글로벌, `~/.claude/commands/`)
- [x] `CLAUDE.md` 라우터 + `docs/rules/` 규칙 시스템
- [x] `docs/state/progress.md` (이 파일)

## Phase 1 상세 (진행 중)

- [x] `app/` Next.js 16 부트스트랩 (TS + Tailwind v4 + App Router + Turbopack)
- [x] `npm install` (428 패키지)
- [x] 랜딩 페이지 `app/page.tsx` — 온보딩 플로우 [0]
- [x] 로그인 페이지 스텁 `app/login/page.tsx` — 온보딩 플로우 [1]
- [x] 메타데이터 · 한글 폰트 · `lang="ko"` 셋업
- [x] `next.config.ts`에 `devIndicators: false` (화면 좌하단 개발 인디케이터 숨김)
- [x] merge conflict 마커 오염 복구 (PR #60 머지 후 발생한 마커를 수동 해결)
- [ ] Supabase 프로젝트 생성 + Kakao/Naver 개발자 앱 등록 (사용자 작업)
- [ ] Supabase 클라이언트 (`@supabase/ssr`) + OAuth 실동작
- [x] 온보딩 Step 2 — 구독 선택 (카테고리 아코디언, seed JSON) — `app/app/onboarding/subscriptions/page.tsx`
- [x] 온보딩 Step 4 — 고정비 입력 (Step 2 화면 하단에 병합, 프리셋 칩 6개 + 커스텀 추가)
- [x] seed JSON을 `app/data/`로 이동 (Turbopack이 Next 프로젝트 외부 import 차단)
- [ ] 온보딩 Step 3 — 직접 추가 폼
- [ ] 대시보드 — 상단 월/연 총합 + 리스트
- [ ] 구독/고정비 CRUD
- [ ] 배포 (Vercel)

## 다음 할 일 (Top 3)

1. **직접 추가 폼 (Step 3)** — `/onboarding/custom` 루트. 서비스명·카테고리·금액·주기·결제일, 여러 개 누적 가능, skip 버튼.
2. **고정비 입력 (Step 4)** — `/onboarding/fixed-costs` 루트 (칩 + 금액 인라인 입력, skip 버튼).
3. **대시보드 (Step 5)** — `/dashboard` 루트, 상단 월/연 총합 카드 + 구독·고정비 리스트. localStorage로 Supabase 전까지 임시 저장.

## 블로커 / 외부 의존

- Kakao Developers / Naver Developers 앱 등록 — 사용자가 직접 가입 필요.
- Supabase 프로젝트 생성 — 사용자 계정 필요.
- 향후 카카오 알림톡 사업자 심사 (Phase 3).
