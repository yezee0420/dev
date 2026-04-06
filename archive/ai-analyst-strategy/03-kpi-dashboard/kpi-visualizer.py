"""
AI 성과 KPI 시각화 대시보드
==============================
weekly-kpi-tracker.csv를 읽어 진행 상황을 시각화한다.

사용법:
    python kpi-visualizer.py
    python kpi-visualizer.py --output dashboard.html
"""

import argparse
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def load_kpi_data(csv_path: str = "weekly-kpi-tracker.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    for col in ["AI적용전", "AI적용후", "절감량", "절감률(%)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def create_time_savings_chart(df: pd.DataFrame) -> go.Figure:
    """시간 절감 추이 차트."""
    speed = df[df["카테고리"] == "속도"].copy()
    if speed.empty:
        return go.Figure()

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=speed["지표명"].unique()[:3],
        shared_yaxes=True,
    )

    for i, metric in enumerate(speed["지표명"].unique()[:3]):
        subset = speed[speed["지표명"] == metric]
        col = i + 1
        fig.add_trace(
            go.Bar(
                x=subset["주차"], y=subset["AI적용전"],
                name="적용 전", marker_color="#ef4444",
                showlegend=(i == 0),
            ),
            row=1, col=col,
        )
        fig.add_trace(
            go.Bar(
                x=subset["주차"], y=subset["AI적용후"],
                name="적용 후", marker_color="#22c55e",
                showlegend=(i == 0),
            ),
            row=1, col=col,
        )

    fig.update_layout(
        title_text="시간 절감 추이 (AI 적용 전/후)",
        barmode="group",
        height=400,
    )
    return fig


def create_quality_chart(df: pd.DataFrame) -> go.Figure:
    """품질 지표 추이."""
    quality = df[df["카테고리"] == "품질"].copy()
    if quality.empty:
        return go.Figure()

    fig = go.Figure()
    for metric in quality["지표명"].unique():
        subset = quality[quality["지표명"] == metric]
        fig.add_trace(go.Scatter(
            x=subset["주차"], y=subset["AI적용후"],
            mode="lines+markers",
            name=metric,
        ))

    fig.update_layout(
        title_text="품질 지표 추이",
        yaxis_title="값",
        height=400,
    )
    return fig


def create_business_impact_chart(df: pd.DataFrame) -> go.Figure:
    """비즈니스 영향 지표."""
    biz = df[df["카테고리"] == "비즈니스"].copy()
    if biz.empty:
        return go.Figure()

    fig = go.Figure()
    for metric in biz["지표명"].unique():
        subset = biz[biz["지표명"] == metric]
        values = subset["AI적용후"].fillna(0)
        fig.add_trace(go.Bar(x=subset["주차"], y=values, name=metric))

    fig.update_layout(
        title_text="비즈니스 영향 지표 (누적)",
        barmode="stack",
        height=400,
    )
    return fig


def create_adoption_chart(df: pd.DataFrame) -> go.Figure:
    """팀 확산 지표."""
    adopt = df[df["카테고리"] == "확산"].copy()
    if adopt.empty:
        return go.Figure()

    fig = go.Figure()
    for metric in adopt["지표명"].unique():
        subset = adopt[adopt["지표명"] == metric]
        values = subset["AI적용후"].fillna(0).cumsum()
        fig.add_trace(go.Scatter(
            x=subset["주차"], y=values,
            mode="lines+markers+text",
            text=values.astype(int).astype(str),
            textposition="top center",
            name=metric,
        ))

    fig.update_layout(
        title_text="팀 확산 지표 (누적)",
        height=400,
    )
    return fig


def create_summary_scorecard(df: pd.DataFrame) -> str:
    """핵심 KPI 요약 HTML 카드."""
    latest = df.groupby("지표명").last().reset_index()

    total_saved_hours = latest[latest["카테고리"] == "속도"]["절감량"].sum()
    avg_quality_improvement = latest[latest["카테고리"] == "품질"]["절감률(%)"].mean()
    total_biz_impact = latest[latest["카테고리"] == "비즈니스"]["AI적용후"].sum()
    total_adoption = latest[latest["카테고리"] == "확산"]["AI적용후"].sum()

    def safe(val):
        return f"{val:.1f}" if pd.notna(val) else "-"

    return f"""
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin:20px 0;">
        <div style="background:#1e293b; color:white; padding:20px; border-radius:12px; text-align:center;">
            <div style="font-size:14px; opacity:0.7;">총 시간 절감</div>
            <div style="font-size:32px; font-weight:bold; color:#22c55e;">{safe(total_saved_hours)}h</div>
        </div>
        <div style="background:#1e293b; color:white; padding:20px; border-radius:12px; text-align:center;">
            <div style="font-size:14px; opacity:0.7;">품질 개선률</div>
            <div style="font-size:32px; font-weight:bold; color:#3b82f6;">{safe(avg_quality_improvement)}%</div>
        </div>
        <div style="background:#1e293b; color:white; padding:20px; border-radius:12px; text-align:center;">
            <div style="font-size:14px; opacity:0.7;">비즈니스 임팩트</div>
            <div style="font-size:32px; font-weight:bold; color:#f59e0b;">{safe(total_biz_impact)}건</div>
        </div>
        <div style="background:#1e293b; color:white; padding:20px; border-radius:12px; text-align:center;">
            <div style="font-size:14px; opacity:0.7;">팀 활용 건수</div>
            <div style="font-size:32px; font-weight:bold; color:#a855f7;">{safe(total_adoption)}건</div>
        </div>
    </div>
    """


def build_dashboard(csv_path: str, output_path: str):
    """전체 대시보드를 HTML로 생성."""
    df = load_kpi_data(csv_path)

    scorecard_html = create_summary_scorecard(df)
    charts = [
        create_time_savings_chart(df),
        create_quality_chart(df),
        create_business_impact_chart(df),
        create_adoption_chart(df),
    ]

    chart_htmls = []
    for chart in charts:
        if chart.data:
            chart_htmls.append(chart.to_html(full_html=False, include_plotlyjs=False))

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>AI 성과 KPI 대시보드</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background: #0f172a; color: white; margin: 0; padding: 20px; }}
        h1 {{ text-align: center; margin-bottom: 8px; }}
        .subtitle {{ text-align: center; opacity: 0.6; margin-bottom: 24px; }}
        .chart-container {{ background: #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>AI 성과 KPI 대시보드</h1>
    <div class="subtitle">증권사 데이터분석팀 | 주간 업데이트</div>
    {scorecard_html}
    {''.join(f'<div class="chart-container">{ch}</div>' for ch in chart_htmls)}
    <div class="subtitle">마지막 업데이트: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}</div>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"대시보드 생성 완료: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KPI 대시보드 생성")
    parser.add_argument("--csv", default="weekly-kpi-tracker.csv")
    parser.add_argument("--output", default="dashboard.html")
    args = parser.parse_args()

    build_dashboard(args.csv, args.output)
