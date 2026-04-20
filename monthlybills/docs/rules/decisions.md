# Decisions Log

이미 내린 결정과 이유. **같은 논의를 반복하지 않기 위해** 유지. 뒤집을 때는 이 파일에 갱신 기록 남기기.

## 2026-04-21

- **레포명**: `monthlybills`. 서비스 브랜드명은 Phase 2 끝에 따로 확정. UI/문서에 임의 브랜드명 쓰지 않기.
- **Phase 1에 소셜 로그인 포함** (Phase 1.5로 분리 X). 이유: 데이터 마이그레이션 복잡도 회피, Supabase 무료 티어로 비용 $0 유지.
- **기술 스택**: Next.js 16 App Router + TS + Tailwind v4 / Supabase(Auth+DB) / Vercel / Expo(앱). 이유: 무료 티어 커버, 카카오 OAuth 네이티브, 웹→앱 코드 재활용.
- **BM**: Freemium + Switch & Save 제휴. **광고 안 함**. 이유: 타겟이 "돈 관리 민감 유저"라 광고는 브랜드 훼손 + 역효과.
- **가격 가설**: Free / Plus ₩2,900/월 / Family ₩4,900/월. 전환율 3–5% 가정. Phase 4에서 검증.
- **알림 순서**: 웹푸시·이메일 → (MAU 200+) 카카오 알림톡. 이유: 초기 비용 0원 유지.
- **예산 원칙**: 초기 $0, 안정화 후 월 3만 원 상한. 무료 티어·오픈소스 우선.
- **레퍼런스 UI**: "내 구독 얼마" 앱 참고 (카테고리 아코디언, 인기 서비스 칩). 기능은 고정비까지 확장으로 차별화.
- **Git 워크플로**: 터미널 `gitship`이 주, Claude의 `/git-ship`은 보조 (필요 시 사용). **단 두 개를 같은 세션에서 동시 실행하지 않음.** 이유: 2026-04-21에 동시 실행으로 stash·rebase 충돌 발생, 로컬 일부 손실 (ship 브랜치에서 복구됨). PR #60 자동 머지 시 GitHub이 충돌 마커를 그대로 커밋하는 2차 문제도 발생.
- **Next.js dev 인디케이터 숨김**: `next.config.ts`의 `devIndicators: false`. 좌하단 N 아이콘을 꺼서 UI 디자인 시 방해 없애기. 다시 보려면 해당 줄을 주석 처리/true로 변경.
- **온보딩 Step 2 + Step 4 병합**: 구독 선택 화면(`/onboarding/subscriptions`) 하단에 고정비 입력 섹션을 함께 배치. 이유: 사용자 요청 + 플로우 1단계 감소로 60초 도달 목표에 유리. `/onboarding/fixed-costs`는 만들지 않음. 검증 시점: 대시보드 완성 후 스킵율/이탈률로 재확인.
- **seed JSON 위치**: `monthlybills/data/` → `monthlybills/app/data/`. 이유: Turbopack이 Next.js 프로젝트 외부 경로 import를 차단. `@/data/seed-subscriptions.json` 경로로 접근.

## 의사결정 템플릿 (새 결정 추가 시)

```
## YYYY-MM-DD
- **결정명**: 한 줄 요약
- **선택지**: A / B / (C)
- **선택**: X
- **이유**: 핵심 근거 2–3개
- **검증 시점**: 언제 뒤집을지 / 재검토할 트리거
```
