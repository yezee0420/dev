# Docs Sync Rules

코드와 문서를 항상 동기화하기 위한 규칙. 이 프로젝트의 문서는 장식이 아니라 진실 소스입니다.

## 원칙

**코드 변경이 문서 주제와 겹치면, 같은 턴에 해당 MD를 함께 업데이트한다.** 다음 턴으로 미루지 않는다.

## 주제 ↔ 파일 매핑

| 코드에서 이런 변경을 하면 | 같은 턴에 이 MD도 업데이트 |
|---|---|
| DB 마이그레이션 / 테이블 구조 변경 | `docs/db-schema.md` |
| 새 화면·플로우 / 온보딩 수정 | `docs/onboarding-flow.md` |
| 구독 카탈로그 추가·가격 변경 | `app/data/seed-subscriptions.json` + `updated_at` |
| 카테고리 신설 | `app/data/seed-subscriptions.json` + (UI면) `onboarding-flow.md` |
| BM·가격 정책 변경 | `docs/business-model.md` |
| Phase 전환·주요 태스크 완료 | `docs/state/progress.md` |
| 새 규칙·의사결정 | `docs/rules/*.md` + `CLAUDE.md` 라우팅 표 |
| 새 외부 서비스·API 도입 | `README.md`의 기술 스택 표 + 해당 규칙 파일 |
| 기술 스택 변경 | `README.md` + `docs/roadmap.md` (해당 Phase) |

## 체크리스트 (변경 커밋 전)

1. 이 변경은 위 매핑 중 어디에 해당하는가?
2. 해당 MD가 지금 상태를 올바르게 반영하는가?
3. `docs/state/progress.md`의 체크박스·다음 할 일이 여전히 유효한가?
4. `CLAUDE.md` 라우팅 표에 새 주제가 추가돼야 하는가?

## 모순이 발견되면

- 현재 코드 상태를 진실로 보고 문서를 수정. 그 반대가 아님.
- 단, 코드 버그로 보이는 모순이면 사용자에게 확인 후 결정.

## 안 해도 되는 것

- 소소한 변수명 변경, 포매팅, 주석 수정은 문서 동기화 불필요.
- 내부 구현 디테일(함수 시그니처 등)은 문서에 복제하지 않음. 문서는 "무엇을/왜"만.
