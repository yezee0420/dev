# Git Workflow

## 기본 원칙

- 메인 브랜치: `main`.
<<<<<<< HEAD
- 일상 작업은 피처 브랜치에서 하고 `/git-ship`으로 main에 병합.
- 작은 변경(문서 오타, 사소한 수정)은 main에 직접 커밋 가능.
=======
- 이 레포의 ship 흐름은 **터미널 `gitship` 커맨드**가 담당 (사용자 셸에 이미 설치됨). Claude의 `/git-ship` 슬래시 커맨드는 **이 레포에서 쓰지 않음**.
>>>>>>> b8d83c31 (Add 프로젝트 한 줄 and 라우팅 — 상황별 읽을 md and 새 규칙·결정이 생겼을 때)
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

<<<<<<< HEAD
## `/git-ship` 사용

- `/git-ship` — 커밋 메시지 선택 (auto / 직접 입력).
- `/git-ship -y` — auto 메시지로 바로 진행.
- 동작 순서: status → 메시지 결정 → stage+commit → pull rebase → push → (피처 브랜치면) main 병합·푸시 → 요약.
- 명령 정의: `~/.claude/commands/git-ship.md`.
=======
## 터미널 `gitship` 흐름 (이 레포)

1. 코드 변경 후 사용자가 터미널에서 `gitship` 실행.
2. 자동으로: commit → `ship/YYYYMMDD-HHMMSS` 브랜치 생성 → 원격 push → GitHub에서 PR 자동 열림.
3. GitHub에서 PR 확인·머지.
4. 로컬 `git pull`로 `main` 동기화.

과거 커밋 로그(#54, #55, #56, #57 등)가 모두 이 흐름의 결과물.

## Claude가 Git 조작할 때

- `git add`, `git commit`까지만 수행. `git push` 이후는 사용자가 `gitship`으로.
- `git reset --hard`, `git stash pop`, `--force` 계열은 **사용자 승인 후에만**. 2026-04-21 실제 사고 — Claude의 /git-ship + 터미널 gitship이 동시 실행돼 stash 충돌·로컬 파일 일부 손실 (ship 브랜치에서 복구 완료).
- 다른 레포(터미널 `gitship` 없는 곳)에서는 `/git-ship` 슬래시 커맨드 사용 가능.
>>>>>>> b8d83c31 (Add 프로젝트 한 줄 and 라우팅 — 상황별 읽을 md and 새 규칙·결정이 생겼을 때)

## 훅 실패 시

1. 원인 메시지 확인.
2. 실제 이슈 수정 (린트·테스트·타입).
3. 다시 stage + 새 커밋. **절대 `--amend`로 숨기지 않기.**
