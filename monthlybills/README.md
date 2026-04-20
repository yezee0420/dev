# monthlybills

구독 서비스와 월 고정비(월세·관리비·통신비·대출이자·카드 연회비 등)를 한 곳에서 추적하고, 결제일 알림까지 자동화해주는 웹 서비스.

> **서비스 브랜드명은 아직 미정.** 레포명은 `monthlybills`로 고정, 브랜드는 Phase 2 진입 전에 따로 결정.

## 문제

- OTT, 음악, 배달, 쇼핑 멤버십, 클라우드, 독서 등 구독 수가 늘어나면서 "내가 매달 얼마 쓰는지" 체감이 안 됨
- 고정비(월세, 통신비, 보험, 카드 연회비)는 주기도 제각각이라 연 단위 합산이 더 안 됨
- 해지하고 싶은데 결제일을 놓쳐서 한 달 더 빠져나감

## 핵심 가치 제안

1. **한 화면에 월/연 총합** — 가입과 동시에 보여주는 첫 숫자
2. **갱신·결제일 알림** — 카카오톡/이메일/웹푸시 (카카오 알림톡은 Phase 3)
3. **"더 싼 요금제로 바꾸기" 제안** — Switch & Save (Phase 4, 수익화 연계)

## 현재 상태

- **Phase 0 (기획)** — 이 문서가 포함된 산출물 작성 중
- 개발자 1명, 초기 예산 $0, 안정화 후 월 3만 원선

## 기술 스택

| 레이어 | 선택 | 이유 |
|---|---|---|
| Web | Next.js 14 (App Router) + TypeScript | 앱 전환 시 로직 재사용, SEO/온보딩 SSR |
| Styling | Tailwind CSS | 레퍼런스 이미지 모바일 UI 빠른 재현 |
| Auth + DB | Supabase (Postgres + Auth) | 카카오 OAuth 네이티브 지원, 무료 티어로 Phase 1~2 커버 |
| Hosting | Vercel | 무료 티어, Next.js 네이티브 |
| 알림 | 웹푸시/이메일 → (Phase 3) 카카오 알림톡 (솔라피·알리고 경유) | 비용 0원부터 시작 |
| App | Expo (React Native) | Phase 5에서 웹 코드 재활용 |

## 디렉토리

```
monthlybills/
├── README.md              ← 지금 이 문서
├── docs/
│   ├── roadmap.md         ← 단계별 빌드 계획
│   ├── business-model.md  ← BM 가설 (freemium + switch&save)
│   ├── onboarding-flow.md ← 구독 선택 → 고정비 → 대시보드 UX
│   └── db-schema.md       ← 테이블·관계 설계
├── data/
│   └── seed-subscriptions.json  ← 카탈로그 초기 데이터
└── app/                   ← Next.js 14 (TS + Tailwind + App Router, 2026-04-21 부트스트랩)
```

## 바로 다음 할 일

1. Phase 0 문서 4종 + seed JSON 마무리 (← 지금)
2. 레퍼런스 이미지 기반 화면 와이어프레임 (Figma 또는 스케치)
3. Supabase 프로젝트 생성 + 카카오/네이버 개발자 앱 등록
4. `app/` 디렉토리에 Next.js 부트스트랩 → Phase 1 개발 시작
