# Progress — 현재 진행 상황

> **단일 진실 소스 (Single Source of Truth).** 사용자가 "지금 어떤 단계야?" 물으면 이 파일을 읽고 답한다. 작업을 마치거나 Phase를 전환할 때 즉시 업데이트한다.

- **마지막 업데이트**: 2026-04-23
- **현재 Phase**: Phase 1 (Web MVP + 소셜 로그인) — UI 작업 중
- **현재 Sub-task**: Supabase 클라이언트·미들웨어·OAuth 콜백 + 카카오 로그인 버튼 활성화 완료. 다음: DB 스키마 마이그레이션 + localStorage→Supabase 병합.

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
- [x] Supabase 프로젝트 생성 (사용자 작업, 2026-04-23 완료)
- [x] Kakao 개발자 앱 등록 + REST 키 확보 (2026-04-23 완료, Naver는 Phase 1 후반으로 연기)
- [x] Supabase 클라이언트 (`@supabase/ssr`) — `app/lib/supabase/{client,server,middleware}.ts` + `app/middleware.ts` + `app/app/auth/callback/route.ts`
- [x] 로그인 페이지 카카오 버튼 실제 `signInWithOAuth` 연결 (`app/app/login/page.tsx`)
- [ ] Supabase 대시보드에서 Kakao provider 활성화 (REST 키 등록) — 사용자 작업
- [ ] 카카오 Developers에서 Supabase Redirect URL 등록 — 사용자 작업
- [x] 온보딩 Step 2 — 구독 선택 (카테고리 아코디언, seed JSON) — `app/app/onboarding/subscriptions/page.tsx`
- [x] 온보딩 Step 4 — 고정비 입력 (Step 2 화면 하단에 병합, 프리셋 칩 6개 + 커스텀 추가)
- [x] seed JSON을 `app/data/`로 이동 (Turbopack이 Next 프로젝트 외부 import 차단)
- [x] 온보딩 Step 3 — 직접 추가 폼 (`app/app/onboarding/custom/page.tsx`, 이름·카테고리·금액·주기·결제일 선택)
- [x] 대시보드 1차 — 월/연 총합 카드 + 구독·고정비·직접추가 섹션별 리스트 + 초기화 + FAB (`app/app/dashboard/page.tsx`)
- [ ] DB 스키마 마이그레이션 (`subscription_catalog`, `user_subscriptions`, `user_fixed_costs`, `user_custom_subscriptions`, `profiles`, `categories` + RLS)
- [ ] 로그인 성공 시 localStorage → Supabase 병합 로직
- [ ] 대시보드 고도화 — 카테고리 차트, 결제일 타임라인, 항목 편집(인라인)
- [ ] 구독/고정비 CRUD
- [ ] 배포 (Vercel)

## 다음 할 일 (Top 3)

1. **Supabase 대시보드 Kakao provider 활성화 + 카카오 Developers Redirect URL 등록** (사용자 작업). 이후 `/login`에서 카카오 버튼 눌러 실제 OAuth 왕복 확인.
2. **DB 스키마 마이그레이션** — `user_subscriptions`, `user_fixed_costs`, `user_custom_subscriptions`, `profiles` + RLS (`user_id = auth.uid()`).
3. **localStorage → Supabase 병합** — 로그인 성공(`/auth/callback`) 직후 localStorage 3개 키 읽어 DB insert, 완료 시 localStorage 클리어.

## 블로커 / 외부 의존

- Kakao Developers / Naver Developers 앱 등록 — 사용자가 직접 가입 필요.
- Supabase 프로젝트 생성 — 사용자 계정 필요.
- 향후 카카오 알림톡 사업자 심사 (Phase 3).
