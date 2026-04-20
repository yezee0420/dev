# Git Workflow

## 기본 원칙

- 메인 브랜치: `main`.
- 일상 작업은 피처 브랜치에서 하고 `/git-ship`으로 main에 병합.
- 작은 변경(문서 오타, 사소한 수정)은 main에 직접 커밋 가능.
- 커밋은 작고 의미 단위로. 한 커밋에 여러 주제 섞기 금지.

## 커밋 메시지

- 제목: 영어, 명령형, 72자 이하. Conventional Commit 느슨하게 따름 (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:` 등).
- 본문: 필요 시에만. WHY 중심. 한국어 OK.
- 마지막 줄:
  ```
  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  ```
- 예시:
  ```
  feat: add subscription picker with category accordion

  - 레퍼런스 이미지 기반 카테고리별 아코디언 UI
  - seed JSON에서 is_popular 태그로 상단 칩 구성

  Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
  ```

## 금지

- `git push --force`, `--force-with-lease` (사용자 명시 요청 시에만).
- `git commit --no-verify` / `--no-gpg-sign` (훅 실패는 원인 수정).
- `git commit --amend` (새 커밋 만들기).
- `git reset --hard`, `git checkout .` (사용자 확인 없이).
- `.env*`, `*credential*`, 키 파일 커밋.

## `/git-ship` 사용

- `/git-ship` — 커밋 메시지 선택 (auto / 직접 입력).
- `/git-ship -y` — auto 메시지로 바로 진행.
- 동작 순서: status → 메시지 결정 → stage+commit → pull rebase → push → (피처 브랜치면) main 병합·푸시 → 요약.
- 명령 정의: `~/.claude/commands/git-ship.md`.

## 훅 실패 시

1. 원인 메시지 확인.
2. 실제 이슈 수정 (린트·테스트·타입).
3. 다시 stage + 새 커밋. **절대 `--amend`로 숨기지 않기.**
