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
- macOS / Linux 지원

---

## 설치

### 1. 스크립트 다운로드

```bash
# 설치 디렉토리 생성
mkdir -p ~/.local/bin

# 스크립트 복사
cp git-commands/git-ship ~/.local/bin/git-ship
cp git-commands/git-check ~/.local/bin/git-check

# 실행 권한 부여
chmod +x ~/.local/bin/git-ship ~/.local/bin/git-check
```

### 2. PATH 등록

셸 설정 파일에 아래 한 줄을 추가한다.

**zsh** (`~/.zshrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

**bash** (`~/.bashrc` 또는 `~/.bash_profile`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

변경 적용:
```bash
source ~/.zshrc   # 또는 source ~/.bashrc
```

### 3. GitHub CLI 인증 (PR/Merge 기능 사용 시)

```bash
brew install gh    # 설치 (macOS)
gh auth login      # GitHub 로그인
```

### 4. 설치 확인

```bash
git-ship --help
git-check --help
```

---

## 사용법

### git-ship

코드 변경 → 리모트 푸시 → PR → 머지까지 한 번에 수행.

```bash
git-ship                    # 자동 커밋 메시지 (선택 프롬프트)
git-ship -y                 # 자동 커밋 메시지 (프롬프트 없이 바로)
git-ship -m "feat: 로그인"   # 직접 커밋 메시지 지정
git-ship --no-pr            # push까지만 (PR/merge 스킵)
git-ship --no-merge         # PR 생성까지만 (merge 스킵)
git-ship --dry-run          # 실행하지 않고 미리보기
```

**워크플로우:**

```
[1] Branch     main이면 자동으로 ship/YYYYMMDD-HHMMSS 브랜치 생성
[2] Stage      git add -A
[3] Commit     자동 메시지 생성 또는 사용자 입력
[4] Sync       git pull --rebase → git push -u origin
[5] PR         gh pr create
[6] Merge      gh pr merge --squash → main 복귀
```

**옵션:**

| 옵션 | 설명 |
|------|------|
| `-y`, `--yes` | 자동 커밋 메시지, 프롬프트 스킵 |
| `-m`, `--message <msg>` | 커밋 메시지 직접 지정 |
| `--no-pr` | PR 생성 및 머지 스킵 (push까지만) |
| `--no-merge` | PR 생성 후 머지 스킵 |
| `--dry-run` | 실제 실행 없이 미리보기 |

---

### git-check

리모트에 새 커밋이 있는지 확인하고 pull.

```bash
git-check              # fetch + 변경 확인 + 자동 pull (기본)
git-check --peek       # 확인만 (pull 안 함)
git-check dev          # 특정 브랜치 기준으로 비교
```

**옵션:**

| 옵션 | 설명 |
|------|------|
| `--peek` | 확인만, pull 하지 않음 |
| `<branch>` | 비교할 리모트 브랜치 지정 (기본: main/master) |

---

## 제거

```bash
rm ~/.local/bin/git-ship ~/.local/bin/git-check
```

`~/.zshrc` (또는 `~/.bashrc`)에서 PATH 줄도 제거한다.
