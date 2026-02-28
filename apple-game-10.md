# 사과 합 10 게임 - 완전 재현용 명세

이 문서를 AI나 개발자에게 전달하고 **"이 명세대로 apple-game-10.html 파일을 만들어 줘"** 라고 요청하면 동일한 게임을 만들 수 있습니다.

---

## 사용법

1. 아래 "전체 소스 코드" 섹션의 HTML을 복사해 `apple-game-10.html` 파일로 저장
2. 또는 AI에게 이 md 파일 전체를 전달하고 "아래 소스 코드로 apple-game-10.html 파일을 생성해 줘" 요청

---

## 게임 설명

### 게임 규칙 요약

| 항목 | 내용 |
|------|------|
| 그리드 | Lv1: 3x3, 레벨업 시 4x4, 5x5 |
| 숫자 | 1~9 (0 제외) |
| 선택 방식 | 마우스/터치 드래그로 상하좌우 인접한 사과만 스네이크처럼 이어서 선택 |
| 제거 조건 | 선택한 사과들의 합 = 10 |
| 점수 | 사과 개수×5 (2칸=10점, 3칸=15점, 4칸=20점) |
| 채우기 | 제거된 칸에 새 사과 즉시 배치 |
| 승리 | 레벨별 목표 점수 도달 (20점 간격) |
| 패배 | 리프레시 2번 사용 후에도 조합이 없을 때 |

### 점수

- 합 10 성공 시: **사과 개수 × 5점**
- 2칸 → 10점, 3칸 → 15점, 4칸 → 20점

### 유효한 조합 (합 10)

- 2칸: 1+9, 2+8, 3+7, 4+6, 5+5
- 3칸: 1+2+7, 1+3+6, 1+4+5, 2+3+5, 2+4+4
- 4칸: 1+2+3+4

### 리프레시

- 레벨당 2번 사용 가능
- 조합을 찾지 못했을 때 보드를 새로 섞음
- 2번 모두 사용 후에도 조합이 없으면 게임 오버

### 보드 설계

- 초기 보드와 제거 후 리필 시 **최소 1개의 유효 조합**이 항상 존재하도록 생성
- createBoard: 인접 경로에 합 10 조합 시드
- fillCells: 랜덤 시도 후 실패 시 시드로 보장

### 레벨 시스템

| 레벨 | 그리드 | 목표 점수 |
|------|--------|-----------|
| 1 | 3x3 | 20 |
| 2 | 4x4 | 40 |
| 3 | 4x4 | 60 |
| 4 | 5x5 | 80 |
| 5 | 5x5 | 100 |
| 6+ | 5x5 | 100 + 20×(레벨-5) |

### UI/UX

- **사과 아이콘**: CSS로 만든 단순한 사과 모양 (빨간 그라데이션 + 초록 잎), 숫자는 흰색
- **선택 표시**: 흰색·주황색 이중 테두리, 1.1배 확대, 주황색 그림자
- **드래그**: 선택 자국 없음 (user-select, user-drag 비활성화)
- **효과음**: 합 10 성공 시 짧은 비프음 (523Hz, 0.2초)
- **플로팅 점수**: 사과 제거 시 획득 점수(+10, +15, +20)가 제거 위치에서 위로 떠오르며 표시
- **모바일**: 터치 지원

### 기술 스택

- 단일 HTML (CSS, JS 인라인)
- Noto Sans KR 폰트 (Google Fonts)
- Web Audio API (효과음)

---

## 전체 소스 코드

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>사과 합 10</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600&display=swap');

        * { margin: 0; padding: 0; box-sizing: border-box; }
        * { -webkit-user-select: none; user-select: none; -webkit-touch-callout: none; }

        body {
            font-family: 'Noto Sans KR', sans-serif;
            min-height: 100vh;
            background: #fafafa;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
            max-width: 340px;
            margin-bottom: 16px;
            font-size: 14px;
            font-weight: 600;
            color: #333;
        }

        .refresh-btn {
            font-family: inherit;
            font-size: 13px;
            padding: 6px 12px;
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 8px;
            cursor: pointer;
            color: #666;
        }
        .refresh-btn:hover:not(:disabled) { background: #f5f5f5; }
        .refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .grid-wrap {
            background: #fff;
            border-radius: 12px;
            padding: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }

        .grid {
            display: grid;
            gap: 8px;
        }

        .cell {
            -webkit-user-drag: none;
            user-drag: none;
            aspect-ratio: 1;
            min-width: 52px;
            min-height: 52px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: transform 0.15s;
        }
        .cell:hover { transform: scale(1.05); }

        .cell.selected .apple-icon {
            box-shadow: 0 0 0 4px #fff, 0 0 0 6px #c2410c, 0 4px 12px rgba(194,65,12,0.4);
            transform: scale(1.1);
        }

        .apple-icon {
            position: relative;
            width: 42px;
            height: 48px;
            transition: transform 0.15s, box-shadow 0.15s;
            background: linear-gradient(145deg, #e53935 0%, #c62828 100%);
            border-radius: 50% 50% 48% 48% / 55% 55% 45% 45%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .apple-icon::before {
            content: '';
            position: absolute;
            top: -5px;
            left: 50%;
            transform: translateX(-50%);
            width: 6px;
            height: 8px;
            background: #2e7d32;
            border-radius: 0 0 4px 4px;
        }

        .cell .num {
            font-size: 18px;
            font-weight: 800;
            color: #fff;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
            z-index: 1;
        }

        .modal {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
        }

        .modal-content {
            background: #fff;
            border-radius: 16px;
            padding: 32px;
            text-align: center;
            max-width: 320px;
        }

        .modal h2 { font-size: 20px; margin-bottom: 12px; color: #333; }
        .modal p { font-size: 14px; color: #666; margin-bottom: 20px; }
        .modal button {
            font-family: inherit;
            font-size: 15px;
            padding: 12px 24px;
            background: #c2410c;
            color: #fff;
            border: none;
            border-radius: 10px;
            cursor: pointer;
        }
        .modal button:hover { opacity: 0.9; }

        .hidden { display: none !important; }

        .floating-score {
            position: fixed;
            pointer-events: none;
            font-size: 24px;
            font-weight: 800;
            color: #c2410c;
            text-shadow: 0 0 4px #fff, 0 2px 4px rgba(0,0,0,0.3);
            z-index: 200;
            animation: floatUp 0.8s ease-out forwards;
        }
        @keyframes floatUp {
            0% { opacity: 1; transform: translate(-50%, -50%) scale(0.8); }
            30% { transform: translate(-50%, -80%) scale(1.2); }
            100% { opacity: 0; transform: translate(-50%, -150%) scale(1); }
        }
    </style>
</head>
<body>
    <div class="header">
        <span>Lv.<span id="level">1</span> <span id="score">0</span>/<span id="target">20</span></span>
        <button class="refresh-btn" id="refreshBtn">리프레시 <span id="refreshCount">2</span>/2</button>
    </div>

    <div class="grid-wrap">
        <div class="grid" id="grid"></div>
    </div>

    <div class="modal" id="startModal">
        <div class="modal-content">
            <h2>사과 합 10</h2>
            <p>상하좌우로 드래그해 사과를 스네이크처럼 이어 선택하세요.<br>합이 10이 되면 제거됩니다. 리프레시 2번 사용 가능.</p>
            <button id="startBtn">시작</button>
        </div>
    </div>

    <div class="modal hidden" id="gameOverModal">
        <div class="modal-content">
            <h2>게임 오버</h2>
            <p id="gameOverMsg">더 이상 만들 수 있는 조합이 없습니다.</p>
            <button id="retryBtn">다시 하기</button>
        </div>
    </div>

    <div class="modal hidden" id="levelClearModal">
        <div class="modal-content">
            <h2>레벨 클리어!</h2>
            <p id="levelClearMsg"></p>
            <button id="nextBtn">다음 레벨</button>
        </div>
    </div>

    <script>
        const LEVELS = [
            { grid: 3, maxNum: 9, target: 20 },
            { grid: 4, maxNum: 9, target: 40 },
            { grid: 4, maxNum: 9, target: 60 },
            { grid: 5, maxNum: 9, target: 80 },
            { grid: 5, maxNum: 9, target: 100 }
        ];

        const gridEl = document.getElementById('grid');
        const scoreEl = document.getElementById('score');
        const targetEl = document.getElementById('target');
        const levelEl = document.getElementById('level');
        const refreshBtn = document.getElementById('refreshBtn');
        const refreshCountEl = document.getElementById('refreshCount');

        let level = 0;
        let score = 0;
        let refreshesLeft = 2;
        let board = [];
        let isDragging = false;
        let selectedPath = [];
        let lastHoverCell = null;

        function getConfig() {
            return LEVELS[Math.min(level, LEVELS.length - 1)] || { ...LEVELS[LEVELS.length - 1], target: 100 + level * 20 };
        }

        function rand(min, max) {
            return Math.floor(Math.random() * (max - min + 1)) + min;
        }

        function playSuccessSound() {
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.frequency.value = 523;
                osc.type = 'sine';
                gain.gain.setValueAtTime(0.2, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
                osc.start(ctx.currentTime);
                osc.stop(ctx.currentTime + 0.2);
            } catch (_) {}
        }

        const COMBO_10 = [
            [1,9],[2,8],[3,7],[4,6],[5,5],
            [1,2,7],[1,3,6],[1,4,5],[2,3,5],[2,4,4],
            [1,2,3,4]
        ];

        function getCombosForMaxNum(maxNum) {
            return COMBO_10.filter(arr => arr.every(x => x >= 1 && x <= maxNum));
        }

        function getRandomAdjacentPath(n, len) {
            const total = n * n;
            for (let attempt = 0; attempt < 50; attempt++) {
                const path = [rand(0, total - 1)];
                const visited = new Set(path);
                for (let step = 0; step < len - 1; step++) {
                    const r = Math.floor(path[path.length - 1] / n), c = path[path.length - 1] % n;
                    const neighbors = [[r-1,c],[r+1,c],[r,c-1],[r,c+1]]
                        .filter(([nr,nc]) => nr >= 0 && nr < n && nc >= 0 && nc < n)
                        .map(([nr,nc]) => nr * n + nc)
                        .filter(i => !visited.has(i));
                    if (neighbors.length === 0) break;
                    const next = neighbors[rand(0, neighbors.length - 1)];
                    path.push(next);
                    visited.add(next);
                }
                if (path.length === len) return path;
            }
            return null;
        }

        function createBoard() {
            const { grid, maxNum } = getConfig();
            const total = grid * grid;
            const combos = getCombosForMaxNum(maxNum).filter(c => c.length >= 2 && c.length <= 4);
            for (let attempt = 0; attempt < 20; attempt++) {
                board = Array(total).fill(0).map(() => rand(1, maxNum));
                if (combos.length > 0) {
                    const combo = combos[rand(0, combos.length - 1)];
                    const path = getRandomAdjacentPath(grid, combo.length);
                    if (path) {
                        combo.forEach((num, i) => { board[path[i]] = num; });
                    }
                }
                if (hasValidMove()) return;
            }
            board = Array(total).fill(0).map(() => rand(1, maxNum));
            for (const combo of combos) {
                const path = getRandomAdjacentPath(grid, combo.length);
                if (path) {
                    combo.forEach((num, i) => { board[path[i]] = num; });
                    return;
                }
            }
        }

        function isAdjacent(i, j) {
            const n = getConfig().grid;
            const ri = Math.floor(i / n), ci = i % n;
            const rj = Math.floor(j / n), cj = j % n;
            return Math.abs(ri - rj) + Math.abs(ci - cj) === 1;
        }

        function hasValidMove() {
            const n = getConfig().grid;
            const total = n * n;
            function dfs(idx, sum, visited) {
                if (sum === 10) return true;
                if (sum > 10) return false;
                const r = Math.floor(idx / n), c = idx % n;
                const neighbors = [[r-1,c],[r+1,c],[r,c-1],[r,c+1]];
                for (const [nr, nc] of neighbors) {
                    if (nr < 0 || nr >= n || nc < 0 || nc >= n) continue;
                    const next = nr * n + nc;
                    if (visited.has(next)) continue;
                    visited.add(next);
                    if (dfs(next, sum + board[next], visited)) return true;
                    visited.delete(next);
                }
                return false;
            }
            for (let i = 0; i < total; i++) {
                if (dfs(i, board[i], new Set([i]))) return true;
            }
            return false;
        }

        function pathSum(indices) {
            let sum = 0;
            indices.forEach(i => { sum += board[i]; });
            return { sum, indices };
        }

        function fillCells(indices) {
            const { maxNum } = getConfig();
            for (let attempt = 0; attempt < 50; attempt++) {
                indices.forEach(i => { board[i] = rand(1, maxNum); });
                if (hasValidMove()) return;
            }
            const combos = getCombosForMaxNum(maxNum).filter(c => c.length >= 2 && c.length <= indices.length);
            if (combos.length > 0) {
                const combo = combos[rand(0, combos.length - 1)];
                combo.forEach((num, i) => { board[indices[i]] = num; });
                for (let i = combo.length; i < indices.length; i++) {
                    board[indices[i]] = rand(1, maxNum);
                }
            }
        }

        function render() {
            const { grid } = getConfig();
            const n = grid;
            gridEl.style.gridTemplateColumns = `repeat(${n}, 1fr)`;
            gridEl.innerHTML = '';
            board.forEach((val, i) => {
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.index = i;
                cell.innerHTML = `<div class="apple-icon"><span class="num">${val}</span></div>`;
                gridEl.appendChild(cell);
            });
        }

        function updateUI() {
            scoreEl.textContent = score;
            targetEl.textContent = getConfig().target;
            levelEl.textContent = level + 1;
            refreshCountEl.textContent = refreshesLeft;
            refreshBtn.disabled = refreshesLeft === 0;
        }

        function highlightPath(indices) {
            document.querySelectorAll('.cell').forEach(c => c.classList.remove('selected'));
            indices.forEach(i => {
                const cell = gridEl.querySelector(`[data-index="${i}"]`);
                if (cell) cell.classList.add('selected');
            });
        }

        function checkNoMoves() {
            if (!hasValidMove()) {
                if (refreshesLeft > 0) {
                    refreshBtn.focus();
                    showNoMovesNotice();
                } else {
                    document.getElementById('gameOverMsg').textContent = '리프레시를 모두 사용했고, 더 이상 조합이 없습니다.';
                    document.getElementById('gameOverModal').classList.remove('hidden');
                }
            } else {
                hideNoMovesNotice();
            }
        }

        function showNoMovesNotice() {
            let n = document.getElementById('noMovesNotice');
            if (!n) {
                n = document.createElement('div');
                n.id = 'noMovesNotice';
                n.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:10px 16px;border-radius:8px;font-size:13px;z-index:50;';
                document.body.appendChild(n);
            }
            n.textContent = '조합이 없습니다. 리프레시를 사용하세요.';
            n.classList.remove('hidden');
        }
        function hideNoMovesNotice() {
            const n = document.getElementById('noMovesNotice');
            if (n) n.classList.add('hidden');
        }

        function showFloatingScore(x, y, points) {
            const el = document.createElement('div');
            el.className = 'floating-score';
            el.textContent = '+' + points;
            el.style.left = x + 'px';
            el.style.top = y + 'px';
            document.body.appendChild(el);
            setTimeout(() => el.remove(), 800);
        }

        function tryRemove(pathIndices) {
            if (pathIndices.length === 0) return false;
            const { sum } = pathSum(pathIndices);
            if (sum === 10) {
                const points = 5 * pathIndices.length;
                const firstCell = gridEl.querySelector(`[data-index="${pathIndices[0]}"]`);
                if (firstCell) {
                    const rect = firstCell.getBoundingClientRect();
                    showFloatingScore(rect.left + rect.width / 2, rect.top + rect.height / 2, points);
                }
                playSuccessSound();
                score += points;
                fillCells(pathIndices);
                render();
                updateUI();
                if (score >= getConfig().target) {
                    hideNoMovesNotice();
                    document.getElementById('levelClearModal').classList.remove('hidden');
                    document.getElementById('levelClearMsg').textContent = `목표 ${getConfig().target}점 달성!`;
                } else {
                    checkNoMoves();
                }
                return true;
            }
            return false;
        }

        function doRefresh() {
            if (refreshesLeft <= 0) return;
            refreshesLeft--;
            createBoard();
            render();
            updateUI();
            hideNoMovesNotice();
            if (!hasValidMove()) {
                document.getElementById('gameOverMsg').textContent = '리프레시 후에도 조합이 없습니다.';
                document.getElementById('gameOverModal').classList.remove('hidden');
            }
        }

        function getEventTarget(e) {
            const t = e.touches ? e.touches[0] : e.changedTouches ? e.changedTouches[0] : e;
            return t ? document.elementFromPoint(t.clientX, t.clientY) : e.target;
        }

        function handleStart(e) {
            e.preventDefault?.();
            const target = getEventTarget(e);
            const i = parseInt(target.closest('.cell')?.dataset.index, 10);
            if (i < 0 || isNaN(i)) return;
            isDragging = true;
            selectedPath = [i];
            highlightPath(selectedPath);
        }

        function handleMove(e) {
            if (!isDragging || selectedPath.length === 0) return;
            e.preventDefault?.();
            const target = getEventTarget(e);
            const cell = target?.closest('.cell');
            if (!cell) return;
            lastHoverCell = cell;
            const i = parseInt(cell.dataset.index, 10);
            const last = selectedPath[selectedPath.length - 1];
            const idx = selectedPath.indexOf(i);
            if (idx >= 0) {
                selectedPath = selectedPath.slice(0, idx + 1);
            } else if (isAdjacent(last, i)) {
                selectedPath = [...selectedPath, i];
            }
            highlightPath(selectedPath);
        }

        function handleEnd(e) {
            if (!isDragging) return;
            tryRemove(selectedPath);
            lastHoverCell = null;
            document.querySelectorAll('.cell').forEach(c => c.classList.remove('selected'));
            isDragging = false;
            selectedPath = [];
        }

        gridEl.addEventListener('mousedown', handleStart);
        gridEl.addEventListener('mousemove', handleMove);
        gridEl.addEventListener('mouseup', handleEnd);
        gridEl.addEventListener('mouseleave', () => { if (isDragging) handleEnd({ target: null }); });

        gridEl.addEventListener('touchstart', handleStart, { passive: false });
        gridEl.addEventListener('touchmove', handleMove, { passive: false });
        gridEl.addEventListener('touchend', handleEnd, { passive: true });

        document.addEventListener('mouseup', () => { isDragging = false; selectedPath = []; });

        refreshBtn.addEventListener('click', doRefresh);

        document.getElementById('startBtn').addEventListener('click', () => {
            document.getElementById('startModal').classList.add('hidden');
            initGame();
        });

        document.getElementById('retryBtn').addEventListener('click', () => {
            document.getElementById('gameOverModal').classList.add('hidden');
            initGame();
        });

        document.getElementById('nextBtn').addEventListener('click', () => {
            document.getElementById('levelClearModal').classList.add('hidden');
            level++;
            initGame();
        });

        function initGame() {
            refreshesLeft = 2;
            score = 0;
            hideNoMovesNotice();
            createBoard();
            render();
            updateUI();
        }
    </script>
</body>
</html>
```

---

## AI 요청 예시

> "이 md 파일의 '전체 소스 코드' 섹션에 있는 HTML을 그대로 apple-game-10.html 파일로 생성해 줘. 추가 수정 없이 동일하게 만들어 줘."
