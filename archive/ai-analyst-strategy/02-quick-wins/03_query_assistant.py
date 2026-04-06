"""
반복 질의 반자동 대응 시스템
==============================
자주 받는 질문을 분류 → SQL 자동 생성 → 검증 → 답변 초안

사용법:
    python 03_query_assistant.py "이번 달 VIP 고객 수익률 알려줘"
"""

import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import pandas as pd

# ──────────────────────────────────────────────
# 1. 설정
# ──────────────────────────────────────────────

CONFIG = {
    "db_path": os.getenv("ANALYTICS_DB", "analytics.db"),
    "output_dir": Path("query_logs"),
    "llm_api_key": os.getenv("LLM_API_KEY", ""),
    "llm_model": os.getenv("LLM_MODEL", "gpt-4o"),
}

# ──────────────────────────────────────────────
# 2. 질문 유형 분류 및 SQL 매핑
# ──────────────────────────────────────────────

QUERY_PATTERNS = {
    "수익률": {
        "keywords": ["수익률", "리턴", "return", "성과"],
        "sql_template": dedent("""\
            SELECT
                {segment_filter}
                product_type,
                AVG(return_rate) AS avg_return,
                MIN(return_rate) AS min_return,
                MAX(return_rate) AS max_return,
                COUNT(*) AS count
            FROM portfolio_performance pp
            JOIN customers c ON pp.customer_id = c.customer_id
            WHERE pp.date BETWEEN :start_date AND :end_date
            {where_clause}
            GROUP BY {group_by}
            ORDER BY avg_return DESC
        """),
        "answer_template": "{period} 기준 {segment} 평균 수익률은 {avg_return}%이며, 상품별로는 {details}입니다.",
    },
    "고객수": {
        "keywords": ["고객 수", "고객수", "계좌", "활성", "신규"],
        "sql_template": dedent("""\
            SELECT
                customer_segment,
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active,
                SUM(CASE WHEN created_date >= :start_date THEN 1 ELSE 0 END) AS new_this_period
            FROM customers
            WHERE 1=1 {where_clause}
            GROUP BY customer_segment
            ORDER BY total DESC
        """),
        "answer_template": "{period} 기준 {segment} 고객 현황: 총 {total}명 (활성 {active}명, 신규 {new}명)",
    },
    "캠페인": {
        "keywords": ["캠페인", "마케팅", "프로모션", "이벤트"],
        "sql_template": dedent("""\
            SELECT
                campaign_name,
                target_count,
                response_count,
                ROUND(response_count * 100.0 / NULLIF(target_count, 0), 2) AS response_rate,
                conversion_count,
                ROUND(conversion_count * 100.0 / NULLIF(response_count, 0), 2) AS conversion_rate,
                total_revenue
            FROM campaign_results
            WHERE start_date >= :start_date AND end_date <= :end_date
            {where_clause}
            ORDER BY total_revenue DESC
        """),
        "answer_template": "{period} 캠페인 성과: {campaign_name} 응답률 {response_rate}%, 전환율 {conversion_rate}%, 매출 {revenue}",
    },
    "이탈": {
        "keywords": ["이탈", "churn", "해지", "탈퇴", "휴면"],
        "sql_template": dedent("""\
            SELECT
                customer_segment,
                COUNT(*) AS churned,
                AVG(tenure_months) AS avg_tenure,
                AVG(last_aum) AS avg_last_aum,
                AVG(trade_count_last_3m) AS avg_trades
            FROM churn_events
            WHERE churn_date BETWEEN :start_date AND :end_date
            {where_clause}
            GROUP BY customer_segment
            ORDER BY churned DESC
        """),
        "answer_template": "{period} 이탈 현황: {segment} {churned}명 (평균 보유기간 {tenure}개월, 평균 자산 {aum}만원)",
    },
}

SEGMENT_MAP = {
    "vip": "c.customer_segment = 'VIP'",
    "일반": "c.customer_segment = '일반'",
    "프리미엄": "c.customer_segment = '프리미엄'",
    "법인": "c.customer_segment = '법인'",
}

PERIOD_PATTERNS = {
    r"이번\s*달": "this_month",
    r"지난\s*달": "last_month",
    r"이번\s*주": "this_week",
    r"지난\s*주": "last_week",
    r"올해": "this_year",
    r"작년|지난\s*해": "last_year",
    r"최근\s*(\d+)\s*일": "last_n_days",
}

SQL_GENERATION_PROMPT = dedent("""\
    당신은 증권사 데이터베이스 전문가입니다.

    ## 질문
    {question}

    ## 데이터베이스 스키마
    {schema}

    ## 규칙
    1. 반드시 SELECT 문만 작성 (DML/DDL 금지)
    2. 날짜 필터는 :start_date, :end_date 파라미터 사용
    3. 고객 세그먼트 필터가 필요하면 WHERE 절에 추가
    4. 결과가 너무 많으면 LIMIT 100 추가
    5. 숫자는 ROUND 처리

    ## SQL
""")


# ──────────────────────────────────────────────
# 3. 질문 파서
# ──────────────────────────────────────────────

class QueryParser:
    """자연어 질문을 분류하고 파라미터를 추출."""

    def classify(self, question: str) -> str | None:
        question_lower = question.lower()
        for qtype, defn in QUERY_PATTERNS.items():
            if any(kw in question_lower for kw in defn["keywords"]):
                return qtype
        return None

    def extract_segment(self, question: str) -> str | None:
        question_lower = question.lower()
        for seg_name, _ in SEGMENT_MAP.items():
            if seg_name in question_lower:
                return seg_name
        return None

    def extract_period(self, question: str) -> tuple[str, str]:
        today = datetime.now()
        for pattern, period_type in PERIOD_PATTERNS.items():
            match = re.search(pattern, question)
            if match:
                if period_type == "this_month":
                    start = today.replace(day=1).strftime("%Y-%m-%d")
                    end = today.strftime("%Y-%m-%d")
                elif period_type == "last_month":
                    first = today.replace(day=1)
                    last_month_end = first - __import__("datetime").timedelta(days=1)
                    start = last_month_end.replace(day=1).strftime("%Y-%m-%d")
                    end = last_month_end.strftime("%Y-%m-%d")
                elif period_type == "this_week":
                    start = (today - __import__("datetime").timedelta(days=today.weekday())).strftime("%Y-%m-%d")
                    end = today.strftime("%Y-%m-%d")
                elif period_type == "this_year":
                    start = f"{today.year}-01-01"
                    end = today.strftime("%Y-%m-%d")
                elif period_type == "last_n_days":
                    days = int(match.group(1))
                    start = (today - __import__("datetime").timedelta(days=days)).strftime("%Y-%m-%d")
                    end = today.strftime("%Y-%m-%d")
                else:
                    start = today.replace(day=1).strftime("%Y-%m-%d")
                    end = today.strftime("%Y-%m-%d")
                return start, end

        start = today.replace(day=1).strftime("%Y-%m-%d")
        return start, today.strftime("%Y-%m-%d")

    def parse(self, question: str) -> dict:
        qtype = self.classify(question)
        segment = self.extract_segment(question)
        start_date, end_date = self.extract_period(question)

        return {
            "original": question,
            "type": qtype,
            "segment": segment,
            "start_date": start_date,
            "end_date": end_date,
        }


# ──────────────────────────────────────────────
# 4. SQL 생성 및 실행
# ──────────────────────────────────────────────

def build_sql(parsed: dict) -> str | None:
    """파싱 결과를 바탕으로 SQL 생성. 템플릿 매칭 우선, 실패 시 LLM 사용."""
    qtype = parsed["type"]
    if not qtype or qtype not in QUERY_PATTERNS:
        return generate_sql_with_llm(parsed)

    template = QUERY_PATTERNS[qtype]["sql_template"]

    where_clause = ""
    if parsed["segment"] and parsed["segment"] in SEGMENT_MAP:
        where_clause = f"AND {SEGMENT_MAP[parsed['segment']]}"

    segment_filter = "c.customer_segment," if parsed["segment"] else ""
    group_by = "c.customer_segment, product_type" if parsed["segment"] else "product_type"

    sql = template.format(
        where_clause=where_clause,
        segment_filter=segment_filter,
        group_by=group_by,
    )

    return sql.strip()


def generate_sql_with_llm(parsed: dict) -> str:
    """템플릿에 매핑되지 않는 질문은 LLM으로 SQL 생성."""
    # from openai import OpenAI
    # client = OpenAI(api_key=CONFIG["llm_api_key"])
    # ...
    return f"-- LLM 생성 SQL (API 연동 필요)\n-- 원본 질문: {parsed['original']}"


def execute_sql(sql: str, params: dict) -> pd.DataFrame:
    """SQL 실행 (읽기 전용)."""
    conn = sqlite3.connect(CONFIG["db_path"])
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    return df


# ──────────────────────────────────────────────
# 5. SQL 검증
# ──────────────────────────────────────────────

def validate_sql(sql: str) -> list[str]:
    """생성된 SQL의 안전성을 검증."""
    issues = []
    sql_upper = sql.upper()

    dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "EXEC", "EXECUTE"]
    for keyword in dangerous:
        if keyword in sql_upper.split():
            issues.append(f"[차단] 위험 키워드 감지: {keyword}")

    if "LIMIT" not in sql_upper and "GROUP BY" not in sql_upper:
        issues.append("[경고] LIMIT/GROUP BY 없음 - 대량 결과 가능성")

    if sql_upper.count("SELECT") > 3:
        issues.append("[주의] 서브쿼리가 많음 - 성능 확인 필요")

    return issues


# ──────────────────────────────────────────────
# 6. 답변 생성
# ──────────────────────────────────────────────

def format_answer(parsed: dict, df: pd.DataFrame) -> str:
    """결과 데이터프레임을 한국어 답변으로 변환."""
    if df.empty:
        return f"조회 기간({parsed['start_date']} ~ {parsed['end_date']})에 해당하는 데이터가 없습니다."

    qtype = parsed["type"]
    segment = parsed["segment"] or "전체"
    period = f"{parsed['start_date']} ~ {parsed['end_date']}"

    if qtype and qtype in QUERY_PATTERNS:
        template = QUERY_PATTERNS[qtype]["answer_template"]
        summary = df.head(5).to_dict(orient="records")
        return f"{template}\n\n상세:\n{json.dumps(summary, ensure_ascii=False, indent=2, default=str)}"

    return f"{period} 조회 결과:\n{df.to_string(index=False)}"


# ──────────────────────────────────────────────
# 7. 로깅
# ──────────────────────────────────────────────

def log_query(parsed: dict, sql: str, result_rows: int, answer: str):
    """질의 이력을 JSON Lines로 기록."""
    CONFIG["output_dir"].mkdir(parents=True, exist_ok=True)
    log_file = CONFIG["output_dir"] / "query_log.jsonl"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "question": parsed["original"],
        "type": parsed["type"],
        "segment": parsed["segment"],
        "period": f"{parsed['start_date']} ~ {parsed['end_date']}",
        "sql_length": len(sql),
        "result_rows": result_rows,
        "answer_preview": answer[:200],
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ──────────────────────────────────────────────
# 8. 메인 실행
# ──────────────────────────────────────────────

def handle_query(question: str) -> dict:
    """전체 질의 대응 파이프라인 실행."""
    print(f"\n질문: {question}")
    print("-" * 50)

    parser = QueryParser()
    parsed = parser.parse(question)
    print(f"[1/5] 질문 분류: {parsed['type'] or '미분류'}")
    print(f"  - 세그먼트: {parsed['segment'] or '전체'}")
    print(f"  - 기간: {parsed['start_date']} ~ {parsed['end_date']}")

    print("[2/5] SQL 생성")
    sql = build_sql(parsed)
    print(f"  - SQL 길이: {len(sql)}자")

    print("[3/5] SQL 검증")
    issues = validate_sql(sql)
    if issues:
        for issue in issues:
            print(f"  ⚠ {issue}")
        if any("[차단]" in i for i in issues):
            return {"error": "위험한 SQL이 감지되어 실행을 차단했습니다.", "issues": issues}
    else:
        print("  ✓ 검증 통과")

    print("[4/5] SQL 실행")
    params = {"start_date": parsed["start_date"], "end_date": parsed["end_date"]}
    try:
        df = execute_sql(sql, params)
        print(f"  - {len(df)}행 반환")
    except Exception as e:
        print(f"  ✗ 실행 실패: {e}")
        df = pd.DataFrame()

    print("[5/5] 답변 생성")
    answer = format_answer(parsed, df)
    print(f"\n답변:\n{answer}")

    log_query(parsed, sql, len(df), answer)

    return {
        "question": question,
        "parsed": parsed,
        "sql": sql,
        "result_rows": len(df),
        "answer": answer,
        "validation_issues": issues,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "이번 달 VIP 고객 수익률 알려줘"

    handle_query(question)
