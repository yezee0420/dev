# Progress — 현재 진행 상황

> **단일 진실 소스 (Single Source of Truth).** 사용자가 "지금 어떤 단계야?" 물으면 이 파일을 읽고 답한다. 작업을 마치거나 Phase를 전환할 때 즉시 업데이트한다.

- **마지막 업데이트**: 2026-04-21
- **현재 Phase**: Phase 1 (Web MVP + 소셜 로그인) — 부트스트랩 완료
- **현재 Sub-task**: Next.js 14 프로젝트 `app/`에 생성됨. 다음: `npm install` → 랜딩·로그인 페이지 UI 작업.

## 한눈에 보기

| Phase | 상태 | 비고 |
|---|---|---|
| **0 — 기획** | 🟢 완료 | (Supabase·OAuth 앱 등록은 사용자 작업 — Phase 1에서 연결) |
| **1 — Web MVP + 소셜 로그인** | 🟡 진행 중 | Next.js 부트스트랩 완료, UI 작업 시작 |
| 2 — 분석·캘린더 + 브랜드명 확정 | ⚪ 대기 | |
| 3 — 알림 | ⚪ 대기 | |
| 4 — Switch & Save / 수익화 | ⚪ 대기 | |
| 5 — 앱 (Expo) | ⚪ 대기 | |
| 6+ — 오픈뱅킹·B2B2C | ⚪ 장기 | |

범례: 🟢 완료 · 🟡 진행 중 · 🔵 블로커 · ⚪ 대기

## Phase 0 상세

- [x] 프로젝트 폴더 `monthlybills/` 생성
- [x] `README.md`
- [x] `docs/roadmap.md`
- [x] `docs/business-model.md`
- [x] `docs/db-schema.md`
- [x] `docs/onboarding-flow.md`
- [x] `data/seed-subscriptions.json` (31 서비스)
- [x] `/git-ship` 슬래시 커맨드
- [x] `CLAUDE.md` 라우터 + `docs/rules/` 규칙 시스템
- [x] `docs/state/progress.md` (이 파일)
- [ ] 와이어프레임 (코드 프로토타입으로 대체 예정 → Phase 1에 흡수)
- [ ] Supabase 프로젝트 생성
- [ ] Kakao Developers 앱 등록
- [ ] Naver Developers 앱 등록

## Phase 1 상세 (진행 중)

- [x] `app/` 디렉토리에 Next.js 14 부트스트랩 (TS + Tailwind + App Router + Turbopack)
- [ ] `npm install` (의존성 설치) ← **사용자 실행 필요 or 다음 턴에 실행**
- [ ] Supabase 클라이언트 설정 (`@supabase/ssr`)
- [ ] 로그인 페이지 (Kakao/Naver)
- [ ] 온보딩 Step 1 — 구독 카탈로그 선택 화면 (레퍼런스 이미지 기반)
- [ ] 온보딩 Step 2 — 직접 추가 폼
- [ ] 온보딩 Step 3 — 고정비 입력/skip
- [ ] 대시보드 — 상단 월/연 총합 + 리스트
- [ ] 구독/고정비 CRUD
- [ ] 배포 (Vercel)

## 다음 할 일 (Top 3)

1. **`cd app && npm install`** — 의존성 설치 (약 1–2분)
2. **랜딩 페이지 + 로그인 화면 UI** — 온보딩 플로우 [0], [1] 단계 (레퍼런스 이미지 기반, Tailwind)
3. **구독 선택 페이지 (Step 2)** — `data/seed-subscriptions.json` 읽어서 카테고리 아코디언 렌더링

## 블로커 / 외부 의존

- Kakao Developers / Naver Developers 앱 등록 — 사용자가 직접 가입 필요
- Supabase 프로젝트 생성 — 사용자 계정 필요
- 향후 카카오 알림톡 사업자 심사 (Phase 3)
