# git-ship & git-check

Git 워크플로우를 한 줄 명령어로 자동화하는 커스텀 CLI 도구.

## 개요

| 명령어 | 설명 |
|--------|------|
| `git-ship` | add → commit → pull → push → PR → merge 를 한 번에 |
| `git-check` | 리모트 변경사항 확인 + pull |

---

## 요구사항

- **Git** (2.x 이상)
- **GitHub CLI** (`gh`) — PR 생성 및 머지에 필요
- **Bash** (4.x 이상)
- **Python 3** — AI 커밋 메시지 생성에 필요
- macOS / Linux 지원 (zsh, bash 모두 호환)

---

## 설치

### 1. 스크립트 다운로드

```bash
mkdir -p ~/.local/bin
cp git-commands/git-ship ~/.local/bin/git-ship
cp git-commands/git-check ~/.local/bin/git-check
chmod +x ~/.local/bin/git-ship ~/.local/bin/git-check
```

### 2. PATH 등록

**zsh** (`~/.zshrc`) 또는 **bash** (`~/.bashrc`):

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 3. GitHub CLI 인증

```bash
brew install gh
gh auth login
```

### 4. (선택) AI 커밋 메시지 활성화

[Anthropic Console](https://console.anthropic.com/settings/keys)에서 API 키 발급 후:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

`~/.zshrc` 또는 `~/.bashrc`에 추가하면 영구 적용.

### 5. 설치 확인

```bash
git-ship --help
git-check --help
```

---

## git-ship

코드 변경 → 리모트 푸시 → PR → 머지까지 한 번에 수행.

### 사용법

```bash
git-ship                    # 자동 커밋 메시지 (선택 프롬프트)
git-ship -y                 # 자동 커밋 메시지 (프롬프트 없이 바로)
git-ship -m "feat: 로그인"   # 직접 커밋 메시지 지정
git-ship --no-pr            # push까지만 (PR/merge 스킵)
git-ship --no-merge         # PR 생성까지만 (merge 스킵)
git-ship --dry-run          # 실행하지 않고 미리보기
```

### 워크플로우

```
[1] Branch     main이면 자동으로 ship/YYYYMMDD-HHMMSS 브랜치 생성
[2] Stage      git add -A
[3] Commit     AI 요약 or 사용자 입력
[4] Sync       git pull --rebase → git push -u origin
[5] PR         gh pr create
[6] Merge      gh pr merge --squash → main 복귀
```

### 옵션

| 옵션 | 설명 |
|------|------|
| `-y`, `--yes` | 자동 커밋 메시지, 프롬프트 스킵 |
| `-m`, `--message <msg>` | 커밋 메시지 직접 지정 |
| `--no-pr` | PR 생성 및 머지 스킵 (push까지만) |
| `--no-merge` | PR 생성 후 머지 스킵 |
| `--dry-run` | 실제 실행 없이 미리보기 |

### 커밋 메시지 생성

| 방식 | 조건 | 예시 |
|------|------|------|
| **AI (Claude Sonnet)** | `ANTHROPIC_API_KEY` 설정됨 | `improve merge flow with auto-merge fallback for CI checks` |
| **Fallback** | API 키 없거나 호출 실패 | `update 2 files — git-commands/git-ship` |
| **수동** | `-m` 옵션 사용 | 사용자가 직접 입력한 메시지 |

---

## git-check

리모트에 새 커밋이 있는지 확인하고 pull.

### 사용법

```bash
git-check              # fetch + 변경 확인 + 자동 pull (기본)
git-check --peek       # 확인만 (pull 안 함)
git-check dev          # 특정 브랜치 기준으로 비교
```

### 옵션

| 옵션 | 설명 |
|------|------|
| `--peek` | 확인만, pull 하지 않음 |
| `<branch>` | 비교할 리모트 브랜치 지정 (기본: main/master) |

---

## 자동 에러 처리 & 방어 기능

### git-ship

| 상황 | 자동 처리 |
|------|----------|
| **main에서 실행** | `ship/YYYYMMDD-HHMMSS` 브랜치 자동 생성 후 작업 |
| **변경사항 없음** | 자동으로 원래 브랜치 복귀 + 임시 브랜치 삭제 |
| **ship/* 잔여 브랜치에서 실행 + 변경 없음** | main으로 복귀 + 잔여 브랜치 삭제 |
| **detached HEAD 상태** | 자동으로 default branch로 checkout 후 진행 |
| **default branch 감지 실패** | `origin/main` → `origin/master` 순서로 fallback |
| **AI 커밋 메시지 실패** | API 키 없음 / 타임아웃 / 에러 시 자동으로 fallback 방식 사용 |
| **PR 이미 존재** | 중복 생성하지 않고 기존 PR URL 표시 |
| **즉시 merge 실패 (CI 체크 대기)** | `--auto` 플래그로 자동 머지 예약 (체크 통과 시 자동 머지) |
| **auto-merge도 실패** | PR URL 표시 + 수동 머지 안내 |
| **gh CLI 미설치** | 에러 메시지 + 설치 명령어 안내 |
| **gh 미인증** | 에러 메시지 + `gh auth login` 안내 |
| **git repo 밖에서 실행** | "Not inside a git repository" 에러 |
| **pull 시 충돌** | `--rebase --autostash`로 자동 stash 후 rebase 시도 |
| **push non-fast-forward 거절** | 자동으로 `git pull --rebase` 후 재시도 |
| **unpushed 커밋만 있을 때** | 새 커밋 없이 push만 수행 (main이면 PR/merge 스킵) |

### git-check

| 상황 | 자동 처리 |
|------|----------|
| **리모트에 변경 없음** | "Up to date" 메시지 |
| **리모트에 새 커밋 있음** | 커밋 목록 표시 + 자동 pull (기본) |
| **로컬에만 있는 커밋** | 로컬 ahead 커밋 수 표시 |
| **fetch 실패** | 에러 메시지 출력 |

---

## API 키 관련

- Anthropic API 키는 **만료 기한 없음** (직접 삭제하지 않는 한 영구 유효)
- 계정 크레딧 소진 시 AI 호출 실패 → **자동 fallback** (git-ship 동작에 영향 없음)
- 키 없이도 git-ship 정상 동작 (fallback 방식으로 커밋 메시지 생성)

---

## 제거

```bash
rm ~/.local/bin/git-ship ~/.local/bin/git-check
```

`~/.zshrc` (또는 `~/.bashrc`)에서 PATH 줄과 `ANTHROPIC_API_KEY` 줄을 제거.
