# 증권사 데이터분석가 AI 인정 전략 키트

증권사 데이터분석팀에서 AI를 활용해 **단기 성과를 만들고, 팀 표준으로 확산**시키기 위한 실행 도구 모음.

## 구조

```
ai-analyst-strategy/
├── 01-task-audit/                    # 업무 점수화
│   ├── task-scoring-template.csv     # 업무별 AI 적용 우선순위 점수표
│   └── task-audit-guide.md           # 점수화 기준 및 사용법
├── 02-quick-wins/                    # 빠른 성과 3종
│   ├── 01_report_automation.py       # 리포트 자동화 파이프라인
│   ├── 02_anomaly_detection.py       # 이상탐지 + AI 원인분석
│   ├── 03_query_assistant.py         # 반복 질의 반자동 대응
│   └── requirements.txt              # Python 의존성
├── 03-kpi-dashboard/                 # 성과 측정
│   ├── weekly-kpi-tracker.csv        # 주간 KPI 기록 시트
│   ├── kpi-visualizer.py             # 대시보드 생성기
│   └── kpi-guide.md                  # 측정 기준 및 보고 팁
└── 04-team-playbook/                 # 팀 공유 플레이북
    ├── playbook.md                   # 전체 AI 활용 가이드
    └── prompt-templates/             # 프롬프트 템플릿 5종
        ├── 01-eda.md                 # 탐색적 데이터 분석
        ├── 02-report-summary.md      # 리포트 요약문
        ├── 03-hypothesis-generation.md # 가설 생성
        ├── 04-anomaly-interpretation.md # 이상탐지 해석
        └── 05-executive-briefing.md  # 경영진 보고
```

## 시작하기

### 1. 업무 점수화 (Day 1)

`01-task-audit/task-scoring-template.csv`를 열어 본인 업무로 교체하고, 상위 3개를 파일럿 과제로 선정.

### 2. 파이프라인 세팅 (Week 1)

```bash
cd 02-quick-wins
pip install -r requirements.txt
```

### 3. KPI 추적 시작 (Week 1~)

매주 금요일에 `03-kpi-dashboard/weekly-kpi-tracker.csv`를 업데이트.

```bash
cd 03-kpi-dashboard
python kpi-visualizer.py --output dashboard.html
```

### 4. 팀 공유 (Week 4~)

`04-team-playbook/playbook.md`를 팀 위키에 게시하고, 프롬프트 템플릿을 공유.

## 핵심 원칙

1. AI 출력은 초안 — 반드시 사람이 검증
2. 프롬프트는 코드 — 버전관리하고 개선
3. 성과는 숫자 — 시간/정확도/비즈니스 영향으로 측정
4. 민감정보 절대 금지 — 고객식별정보 입력 차단
