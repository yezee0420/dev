"""
이상탐지 + AI 원인분석 파이프라인
==================================
거래/고객행동 지표 이상치를 탐지하고, AI가 1차 원인 후보를 제시한다.

사용법:
    python 02_anomaly_detection.py --target trades --lookback 30 --date 2026-03-04
"""

import argparse
import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from textwrap import dedent

import numpy as np
import pandas as pd

# ──────────────────────────────────────────────
# 1. 설정
# ──────────────────────────────────────────────

CONFIG = {
    "db_path": os.getenv("ANALYTICS_DB", "analytics.db"),
    "output_dir": Path("anomaly_reports"),
    "llm_api_key": os.getenv("LLM_API_KEY", ""),
    "llm_model": os.getenv("LLM_MODEL", "gpt-4o"),
    "alert_webhook": os.getenv("ALERT_WEBHOOK", ""),
}

METRIC_DEFINITIONS = {
    "trades": {
        "query": dedent("""\
            SELECT
                date,
                total_volume,
                total_amount,
                unique_customers,
                avg_order_size,
                buy_ratio,
                foreign_ratio
            FROM daily_trade_metrics
            WHERE date BETWEEN :start_date AND :end_date
            ORDER BY date
        """),
        "monitor_cols": ["total_volume", "total_amount", "unique_customers", "avg_order_size"],
        "context_cols": ["buy_ratio", "foreign_ratio"],
    },
    "customers": {
        "query": dedent("""\
            SELECT
                date,
                new_accounts,
                dormant_activations,
                churn_count,
                avg_login_frequency,
                complaint_count,
                nps_score
            FROM daily_customer_metrics
            WHERE date BETWEEN :start_date AND :end_date
            ORDER BY date
        """),
        "monitor_cols": ["new_accounts", "churn_count", "complaint_count", "nps_score"],
        "context_cols": ["dormant_activations", "avg_login_frequency"],
    },
    "market": {
        "query": dedent("""\
            SELECT
                date,
                kospi_close,
                kospi_volume,
                kosdaq_close,
                vix,
                usd_krw,
                bond_yield_3y
            FROM daily_market
            WHERE date BETWEEN :start_date AND :end_date
            ORDER BY date
        """),
        "monitor_cols": ["kospi_close", "kospi_volume", "vix", "usd_krw"],
        "context_cols": ["kosdaq_close", "bond_yield_3y"],
    },
}

ANALYSIS_PROMPT = dedent("""\
    당신은 증권사의 시니어 리스크 애널리스트입니다.

    아래 이상치가 탐지되었습니다. 가능한 원인 후보 3가지와 각각의 대응 권고를 제시하세요.

    ## 탐지 결과
    - 지표: {metric_name}
    - 탐지일: {detection_date}
    - 관측값: {observed_value}
    - 기대범위: {expected_range}
    - 편차 크기: {deviation}σ

    ## 최근 {lookback}일 추이
    {trend_summary}

    ## 동일 시점 맥락 지표
    {context_data}

    ## 답변 형식
    1. [원인 후보 1]: 설명 → 권고 액션
    2. [원인 후보 2]: 설명 → 권고 액션
    3. [원인 후보 3]: 설명 → 권고 액션
    긴급도: 상/중/하
""")


# ──────────────────────────────────────────────
# 2. 데이터 수집
# ──────────────────────────────────────────────

def fetch_metrics(target: str, end_date: str, lookback: int) -> pd.DataFrame:
    """지정된 지표 데이터를 DB에서 조회."""
    start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=lookback)).strftime("%Y-%m-%d")
    defn = METRIC_DEFINITIONS[target]

    conn = sqlite3.connect(CONFIG["db_path"])
    try:
        df = pd.read_sql_query(defn["query"], conn, params={"start_date": start_date, "end_date": end_date})
    finally:
        conn.close()

    return df


# ──────────────────────────────────────────────
# 3. 이상탐지 엔진 (다중 방법론)
# ──────────────────────────────────────────────

class AnomalyDetector:
    """Z-score, IQR, 이동평균 기반 이상탐지."""

    def __init__(self, z_threshold: float = 2.5, iqr_multiplier: float = 1.5, ma_window: int = 7):
        self.z_threshold = z_threshold
        self.iqr_multiplier = iqr_multiplier
        self.ma_window = ma_window

    def detect_zscore(self, series: pd.Series) -> pd.Series:
        mean, std = series.mean(), series.std()
        if std == 0:
            return pd.Series(False, index=series.index)
        z = (series - mean) / std
        return z.abs() > self.z_threshold

    def detect_iqr(self, series: pd.Series) -> pd.Series:
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - self.iqr_multiplier * iqr
        upper = q3 + self.iqr_multiplier * iqr
        return (series < lower) | (series > upper)

    def detect_ma_deviation(self, series: pd.Series) -> pd.Series:
        ma = series.rolling(window=self.ma_window, min_periods=3).mean()
        ma_std = series.rolling(window=self.ma_window, min_periods=3).std()
        ma_std = ma_std.replace(0, np.nan)
        deviation = (series - ma) / ma_std
        return deviation.abs() > self.z_threshold

    def detect(self, df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        """여러 컬럼에 대해 이상탐지 실행. 2개 이상 방법에서 탐지되면 이상치로 확정."""
        results = []
        for col in columns:
            if col not in df.columns:
                continue
            series = df[col].astype(float)
            z = self.detect_zscore(series)
            iqr = self.detect_iqr(series)
            ma = self.detect_ma_deviation(series)

            vote = z.astype(int) + iqr.astype(int) + ma.astype(int)
            anomaly_mask = vote >= 2

            if anomaly_mask.any():
                mean, std = series.mean(), series.std()
                for idx in anomaly_mask[anomaly_mask].index:
                    deviation = (series[idx] - mean) / std if std > 0 else 0
                    results.append({
                        "date": df.loc[idx, "date"] if "date" in df.columns else str(idx),
                        "metric": col,
                        "value": series[idx],
                        "mean": round(mean, 4),
                        "std": round(std, 4),
                        "deviation_sigma": round(abs(deviation), 2),
                        "methods": {
                            "zscore": bool(z[idx]),
                            "iqr": bool(iqr[idx]),
                            "moving_avg": bool(ma[idx]),
                        },
                        "vote_count": int(vote[idx]),
                    })

        return pd.DataFrame(results)


# ──────────────────────────────────────────────
# 4. AI 원인 분석
# ──────────────────────────────────────────────

def analyze_anomaly(anomaly: dict, df: pd.DataFrame, target: str, lookback: int) -> str:
    """이상치에 대해 AI 원인 분석을 요청."""
    defn = METRIC_DEFINITIONS[target]
    col = anomaly["metric"]

    trend = df[["date", col]].tail(lookback).to_dict(orient="records")
    context = {}
    for ctx_col in defn["context_cols"]:
        if ctx_col in df.columns:
            row = df[df["date"] == anomaly["date"]]
            if not row.empty:
                context[ctx_col] = row[ctx_col].values[0]

    prompt = ANALYSIS_PROMPT.format(
        metric_name=col,
        detection_date=anomaly["date"],
        observed_value=anomaly["value"],
        expected_range=f"{anomaly['mean'] - 2*anomaly['std']:.2f} ~ {anomaly['mean'] + 2*anomaly['std']:.2f}",
        deviation=anomaly["deviation_sigma"],
        lookback=lookback,
        trend_summary=json.dumps(trend[-10:], ensure_ascii=False, default=str),
        context_data=json.dumps(context, ensure_ascii=False, default=str),
    )

    # --- LLM API 호출 ---
    # from openai import OpenAI
    # client = OpenAI(api_key=CONFIG["llm_api_key"])
    # response = client.chat.completions.create(
    #     model=CONFIG["llm_model"],
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.2,
    # )
    # return response.choices[0].message.content

    return f"[원인분석 초안 - {col} / {anomaly['date']}]\n프롬프트 길이: {len(prompt)}자\n(API 연동 후 자동 생성)"


# ──────────────────────────────────────────────
# 5. 알림
# ──────────────────────────────────────────────

def send_alert(anomalies_df: pd.DataFrame, analyses: list[str]):
    """Slack/Teams 웹훅으로 이상탐지 알림 전송."""
    if not CONFIG["alert_webhook"] or anomalies_df.empty:
        return

    message = f"🚨 이상탐지 알림: {len(anomalies_df)}건\n\n"
    for _, row in anomalies_df.iterrows():
        message += f"• {row['metric']} ({row['date']}): {row['value']:.2f} ({row['deviation_sigma']}σ)\n"

    # import requests
    # requests.post(CONFIG["alert_webhook"], json={"text": message})
    print(f"[알림] {message}")


# ──────────────────────────────────────────────
# 6. 메인 실행
# ──────────────────────────────────────────────

def run_detection(target: str, end_date: str, lookback: int = 30):
    """전체 이상탐지 파이프라인 실행."""
    output_dir = CONFIG["output_dir"] / f"{target}_{end_date}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] 데이터 수집: {target} (최근 {lookback}일)")
    df = fetch_metrics(target, end_date, lookback)
    print(f"  - {len(df)}행 로드")

    print("[2/4] 이상탐지 실행")
    detector = AnomalyDetector()
    monitor_cols = METRIC_DEFINITIONS[target]["monitor_cols"]
    anomalies = detector.detect(df, monitor_cols)
    print(f"  - {len(anomalies)}건 탐지")

    if anomalies.empty:
        print("  ✓ 이상치 없음")
        return output_dir

    anomalies.to_csv(output_dir / "anomalies.csv", index=False, encoding="utf-8-sig")

    print("[3/4] AI 원인 분석")
    analyses = []
    for _, row in anomalies.iterrows():
        analysis = analyze_anomaly(row.to_dict(), df, target, lookback)
        analyses.append(analysis)
        print(f"  - {row['metric']} ({row['date']}): 분석 완료")

    report_lines = ["# 이상탐지 보고서\n", f"대상: {target} | 기준일: {end_date}\n"]
    for i, (_, row) in enumerate(anomalies.iterrows()):
        report_lines.append(f"\n## {i+1}. {row['metric']} ({row['date']})")
        report_lines.append(f"- 관측값: {row['value']:.4f}")
        report_lines.append(f"- 편차: {row['deviation_sigma']}σ")
        report_lines.append(f"- 탐지방법: {row['methods']}\n")
        report_lines.append(analyses[i])

    (output_dir / "anomaly_report.md").write_text("\n".join(report_lines), encoding="utf-8")

    print("[4/4] 알림 전송")
    send_alert(anomalies, analyses)

    print(f"완료 → {output_dir}")
    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="이상탐지 파이프라인")
    parser.add_argument("--target", choices=list(METRIC_DEFINITIONS.keys()), default="trades")
    parser.add_argument("--lookback", type=int, default=30)
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()

    run_detection(args.target, args.date, args.lookback)
