# Git Workflow

## 기본 원칙

- 메인 브랜치: `main`.
- 이 레포의 주 ship 흐름은 **터미널 `gitship` 커맨드** (사용자 셸에 설치됨).
- Claude의 `/git-ship` 슬래시 커맨드도 사용 가능. 다만 **터미널 `gitship`과 동시에 실행하지 않는다** — stash/rebase 충돌 위험 (2026-04-21 실제 사고).
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

## 터미널 `gitship` 흐름

1. 코드 변경 후 터미널에서 `gitship` 실행.
2. 자동으로: commit → `ship/YYYYMMDD-HHMMSS` 브랜치 생성 → 원격 push → GitHub에서 PR 자동 열림.
3. GitHub에서 PR 확인·머지.
4. 로컬에서 `git checkout main && git pull`로 `main` 동기화.

과거 커밋 로그 (`#54~#60` 등)가 모두 이 흐름의 결과물.

## Claude가 Git 조작할 때

- 기본: `git add`, `git commit`까지만 수행. `git push` 이후는 사용자가 결정.
- 사용자가 `/git-ship` 슬래시 커맨드를 명시적으로 호출하면 push·merge까지 진행 가능. **단, 그 세션에서 터미널 `gitship`을 쓰지 않을 때만.**
- 파괴적 작업(`reset --hard`, `stash pop` 등)은 **사용자 승인 후에만**.

## PR 머지 후 markers 오염 발견 시

GitHub 웹이 자동 머지 중 충돌을 마커(`<<<<<<<`, `=======`, `>>>>>>>`)로 표시하고 그대로 커밋하는 경우가 있음 (2026-04-21 사례).
1. 영향 파일에서 마커 수동 제거, 최종 내용 결정.
2. 새 커밋으로 수정 (`fix: resolve merge conflict markers from #NN`).
3. `gitship` 또는 직접 push.

## 훅 실패 시

1. 원인 메시지 확인.
2. 실제 이슈 수정 (린트·테스트·타입).
3. 다시 stage + 새 커밋. **절대 `--amend`로 숨기지 않기.**
