"""
주간/월간 리포트 자동화 파이프라인
===================================
SQL 결과 → 시각화 → AI 요약문 초안 → 검증 → 최종 보고서

사용법:
    python 01_report_automation.py --report weekly --date 2026-03-04
"""

import argparse
import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from textwrap import dedent

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ──────────────────────────────────────────────
# 1. 설정
# ──────────────────────────────────────────────

CONFIG = {
    "db_path": os.getenv("ANALYTICS_DB", "analytics.db"),
    "output_dir": Path("reports"),
    "llm_api_key": os.getenv("LLM_API_KEY", ""),
    "llm_model": os.getenv("LLM_MODEL", "gpt-4o"),
}

REPORT_QUERIES = {
    "weekly": {
        "summary": dedent("""\
            SELECT
                date,
                total_aum,
                net_inflow,
                active_customers,
                trade_volume
            FROM daily_metrics
            WHERE date BETWEEN :start_date AND :end_date
            ORDER BY date
        """),
        "top_products": dedent("""\
            SELECT
                product_name,
                SUM(revenue) AS total_revenue,
                COUNT(DISTINCT customer_id) AS customers,
                AVG(return_rate) AS avg_return
            FROM product_performance
            WHERE date BETWEEN :start_date AND :end_date
            GROUP BY product_name
            ORDER BY total_revenue DESC
            LIMIT 10
        """),
        "risk_alerts": dedent("""\
            SELECT
                alert_type,
                COUNT(*) AS count,
                AVG(severity) AS avg_severity
            FROM risk_alerts
            WHERE date BETWEEN :start_date AND :end_date
            GROUP BY alert_type
            ORDER BY count DESC
        """),
    },
    "monthly": {
        "summary": dedent("""\
            SELECT
                DATE(date, 'start of month') AS month,
                SUM(net_inflow) AS monthly_inflow,
                AVG(total_aum) AS avg_aum,
                SUM(trade_volume) AS monthly_volume,
                AVG(active_customers) AS avg_customers
            FROM daily_metrics
            WHERE date BETWEEN :start_date AND :end_date
            GROUP BY month
        """),
        "segment_analysis": dedent("""\
            SELECT
                customer_segment,
                COUNT(*) AS customers,
                AVG(aum) AS avg_aum,
                AVG(trade_count) AS avg_trades,
                SUM(CASE WHEN churned = 1 THEN 1 ELSE 0 END) AS churned
            FROM customer_snapshot
            WHERE snapshot_date = :end_date
            GROUP BY customer_segment
        """),
    },
}

SUMMARY_PROMPT_TEMPLATE = dedent("""\
    당신은 증권사 데이터분석팀의 시니어 애널리스트입니다.
    아래 데이터를 바탕으로 {report_type} 리포트 요약문을 작성하세요.

    ## 작성 규칙
    1. 핵심 지표 변동을 먼저 서술 (전주/전월 대비 증감률 포함)
    2. 주목할 이상치나 트렌드 변화를 2~3개 지적
    3. 마지막에 권고안 3가지 (보수/중립/공격) 제시
    4. 전체 분량: 400자 이내
    5. 숫자에는 반드시 단위 표기

    ## 데이터
    {data_json}

    ## 전주/전월 비교 데이터
    {comparison_json}
""")


# ──────────────────────────────────────────────
# 2. 데이터 수집
# ──────────────────────────────────────────────

def get_date_range(report_type: str, ref_date: str) -> tuple[str, str]:
    """리포트 유형별 조회 기간 산출."""
    ref = datetime.strptime(ref_date, "%Y-%m-%d")
    if report_type == "weekly":
        start = ref - timedelta(days=ref.weekday())
        end = start + timedelta(days=6)
    else:
        start = ref.replace(day=1)
        next_month = (start + timedelta(days=32)).replace(day=1)
        end = next_month - timedelta(days=1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def fetch_data(report_type: str, start_date: str, end_date: str) -> dict[str, pd.DataFrame]:
    """SQL 쿼리를 실행해 데이터프레임 딕셔너리로 반환."""
    queries = REPORT_QUERIES[report_type]
    results = {}

    conn = sqlite3.connect(CONFIG["db_path"])
    try:
        params = {"start_date": start_date, "end_date": end_date}
        for name, query in queries.items():
            results[name] = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()

    return results


# ──────────────────────────────────────────────
# 3. 시각화
# ──────────────────────────────────────────────

def create_weekly_charts(data: dict[str, pd.DataFrame], output_dir: Path) -> list[Path]:
    """주간 리포트용 차트 생성."""
    charts = []

    if "summary" in data and not data["summary"].empty:
        df = data["summary"]
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("AUM 추이", "순유입", "활성고객", "거래량"),
        )
        fig.add_trace(go.Scatter(x=df["date"], y=df["total_aum"], name="AUM"), row=1, col=1)
        fig.add_trace(go.Bar(x=df["date"], y=df["net_inflow"], name="순유입"), row=1, col=2)
        fig.add_trace(go.Scatter(x=df["date"], y=df["active_customers"], name="활성고객"), row=2, col=1)
        fig.add_trace(go.Bar(x=df["date"], y=df["trade_volume"], name="거래량"), row=2, col=2)
        fig.update_layout(title_text="주간 핵심 지표", showlegend=False, height=600)

        path = output_dir / "weekly_summary.html"
        fig.write_html(str(path))
        charts.append(path)

    if "top_products" in data and not data["top_products"].empty:
        df = data["top_products"]
        fig = px.bar(
            df, x="product_name", y="total_revenue",
            color="avg_return", title="상위 상품 매출 및 수익률",
            labels={"total_revenue": "매출(억원)", "avg_return": "평균수익률(%)"},
        )
        path = output_dir / "top_products.html"
        fig.write_html(str(path))
        charts.append(path)

    return charts


# ──────────────────────────────────────────────
# 4. AI 요약 생성
# ──────────────────────────────────────────────

def generate_summary(report_type: str, data: dict[str, pd.DataFrame], comparison: dict | None = None) -> str:
    """LLM API를 호출해 리포트 요약문 초안 생성."""
    data_json = {k: v.to_dict(orient="records") for k, v in data.items()}
    comp_json = json.dumps(comparison or {}, ensure_ascii=False)

    prompt = SUMMARY_PROMPT_TEMPLATE.format(
        report_type="주간" if report_type == "weekly" else "월간",
        data_json=json.dumps(data_json, ensure_ascii=False, default=str),
        comparison_json=comp_json,
    )

    # --- LLM API 호출 (OpenAI 호환) ---
    # 실제 환경에서는 아래 주석을 해제하고 API 키를 설정
    #
    # from openai import OpenAI
    # client = OpenAI(api_key=CONFIG["llm_api_key"])
    # response = client.chat.completions.create(
    #     model=CONFIG["llm_model"],
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.3,
    #     max_tokens=800,
    # )
    # return response.choices[0].message.content

    return f"[AI 요약 초안 - 프롬프트 길이: {len(prompt)}자]\n{prompt[:200]}...\n\n(실제 API 연동 후 자동 생성됩니다)"


# ──────────────────────────────────────────────
# 5. 검증
# ──────────────────────────────────────────────

def validate_report(data: dict[str, pd.DataFrame], summary_text: str) -> list[str]:
    """리포트 수치 검증. 불일치 항목을 리스트로 반환."""
    issues = []

    if "summary" in data and not data["summary"].empty:
        df = data["summary"]
        for col in ["total_aum", "net_inflow", "trade_volume"]:
            if col in df.columns and df[col].isnull().any():
                issues.append(f"[경고] {col}에 NULL 값 존재 ({df[col].isnull().sum()}건)")

        if "net_inflow" in df.columns:
            extreme = df[df["net_inflow"].abs() > df["net_inflow"].std() * 3]
            if not extreme.empty:
                issues.append(f"[주의] 순유입 3σ 초과 이상치: {extreme['date'].tolist()}")

    if not summary_text or len(summary_text) < 50:
        issues.append("[오류] AI 요약문이 비어있거나 너무 짧습니다")

    return issues


# ──────────────────────────────────────────────
# 6. 메인 실행
# ──────────────────────────────────────────────

def run_report(report_type: str, ref_date: str):
    """전체 파이프라인 실행."""
    start_date, end_date = get_date_range(report_type, ref_date)
    output_dir = CONFIG["output_dir"] / f"{report_type}_{end_date}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/5] 데이터 수집: {start_date} ~ {end_date}")
    data = fetch_data(report_type, start_date, end_date)
    for name, df in data.items():
        print(f"  - {name}: {len(df)}행")

    print("[2/5] 시각화 생성")
    if report_type == "weekly":
        charts = create_weekly_charts(data, output_dir)
    else:
        charts = []
    print(f"  - 차트 {len(charts)}개 생성")

    print("[3/5] AI 요약 생성")
    summary = generate_summary(report_type, data)
    summary_path = output_dir / "summary.md"
    summary_path.write_text(summary, encoding="utf-8")

    print("[4/5] 검증")
    issues = validate_report(data, summary)
    if issues:
        print("  ⚠ 검증 이슈:")
        for issue in issues:
            print(f"    {issue}")
    else:
        print("  ✓ 검증 통과")

    print(f"[5/5] 완료 → {output_dir}")

    metadata = {
        "report_type": report_type,
        "period": f"{start_date} ~ {end_date}",
        "generated_at": datetime.now().isoformat(),
        "data_rows": {k: len(v) for k, v in data.items()},
        "charts": [str(c) for c in charts],
        "validation_issues": issues,
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="리포트 자동화 파이프라인")
    parser.add_argument("--report", choices=["weekly", "monthly"], default="weekly")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()

    run_report(args.report, args.date)
