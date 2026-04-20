# monthlybills — Project Router

Claude Code가 이 레포에서 작업할 때 자동으로 읽는 마스터 라우터. **이 파일은 길게 쓰지 않고**, 상황별로 어떤 MD를 읽어야 하는지 안내만 합니다. 규칙·상태·결정 내용은 아래 링크된 파일에 저장하고, 항상 동기화합니다.

## 프로젝트 한 줄

구독 + 월 고정비 통합 관리 웹 서비스. 레포명 `monthlybills`, 서비스 브랜드명 미정 (Phase 2 끝에 확정).

## 라우팅 — 상황별 읽을 MD

| 사용자가 이런 걸 물으면/요청하면 | 먼저 이 파일을 읽어라 |
|---|---|
| "지금 어떤 단계야?", "진행률", "다음 뭐 해?" | [docs/state/progress.md](docs/state/progress.md) |
| 전체 계획·우선순위 재검토 | [docs/roadmap.md](docs/roadmap.md) |
| BM·수익화·가격·파트너 | [docs/business-model.md](docs/business-model.md) |
| DB·테이블·스키마 변경 | [docs/db-schema.md](docs/db-schema.md) |
| 화면 흐름·온보딩·UX 플로우 | [docs/onboarding-flow.md](docs/onboarding-flow.md) |
| 카피·문구·톤·UI 텍스트 | [docs/rules/ux-writing.md](docs/rules/ux-writing.md) |
| 커밋·브랜치·배포 워크플로 | [docs/rules/git-workflow.md](docs/rules/git-workflow.md) |
| 대화 언어·응답 길이·스타일 | [docs/rules/communication.md](docs/rules/communication.md) |
| 과거 결정·'이거 왜 이렇게 정했지?' | [docs/rules/decisions.md](docs/rules/decisions.md) |
| 코드/문서 동기화 규칙 | [docs/rules/docs-sync.md](docs/rules/docs-sync.md) |
| 구독 카탈로그·시드 데이터 | [data/seed-subscriptions.json](data/seed-subscriptions.json) |

## 핵심 불변 규칙 (항상 적용)

1. **대화·문서는 한국어, 코드는 영어.** (상세: `docs/rules/communication.md`)
2. **코드 변경이 문서 주제와 겹치면 같은 턴에 해당 MD도 업데이트한다.** (상세: `docs/rules/docs-sync.md`)
3. **진행 상황은 매 Phase 작업 완료·전환 시 `docs/state/progress.md`에 반영한다.** 사용자가 "지금 어떤 단계야?" 물으면 그 파일을 근거로 답한다.
4. **브랜드명 확정 전까지 서비스 이름은 "monthlybills (가제)"로 표기한다.** 임의의 브랜드명을 UI/문서에 쓰지 않는다.
5. **광고 수익화 제안 금지.** (이유·대안: `docs/rules/decisions.md`)
6. **예산 제약**: 초기 $0, 안정화 후 월 3만 원까지. 무료 티어·오픈소스 우선.
7. **커밋/배포는 `/git-ship`으로 통일.** (상세: `docs/rules/git-workflow.md`)

## 새 규칙·결정이 생겼을 때

1. 해당 주제의 `docs/rules/*.md`에 추가(없으면 새 파일 생성).
2. 위 "라우팅" 표에 한 줄 추가.
3. 필요시 "핵심 불변 규칙"에 반영(자주 적용되는 것만).
