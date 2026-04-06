#!/usr/bin/env python3
"""고인 데이터 품질 감사 — BEFORE/AFTER 표 출력.

실행: cd bugo-alert && PYTHONPATH=. python scripts/audit_deceased_report.py
옵션: --apply — cleanup 실행 후 AFTER 표 (기본은 BEFORE만)
"""

import sys
from collections import defaultdict

from app.database import SessionLocal
from app.models import Obituary


def _norm(s: str | None) -> str:
    if s is None:
        return ""
    return (s or "").strip()


def _fetch_rows(db):
    return db.query(Obituary).all()


def _analyze(rows):
    """분석 결과 dict 반환."""
    no_deceased = [r for r in rows if not _norm(r.deceased_name)]
    has_deceased = [r for r in rows if _norm(r.deceased_name)]
    by_deceased = defaultdict(list)
    for r in has_deceased:
        by_deceased[_norm(r.deceased_name)].append(r)

    # 블랙리스트 (quality.py와 동일)
    BLACKLIST = {"이사", "전무", "의원", "세로", "경영본부장", "주식회사", "호실", "션닷컴전무"}
    bad_deceased = [r for r in has_deceased if _norm(r.deceased_name) in BLACKLIST]

    # (deceased, key_person) 중복
    dup_pairs = []
    for d, recs in by_deceased.items():
        by_kp = defaultdict(list)
        for r in recs:
            by_kp[_norm(r.key_person) or "(없음)"].append(r)
        for kp_val, recs2 in by_kp.items():
            if len(recs2) > 1:
                dup_pairs.append((d, kp_val, recs2))

    # (deceased, None) 중복
    no_key = [r for r in has_deceased if not _norm(r.key_person)]
    by_deceased_no_key = defaultdict(list)
    for r in no_key:
        by_deceased_no_key[_norm(r.deceased_name)].append(r)
    dup_no_key = [(d, recs) for d, recs in by_deceased_no_key.items() if len(recs) > 1]

    return {
        "total": len(rows),
        "no_deceased": no_deceased,
        "bad_deceased": bad_deceased,
        "dup_pairs": dup_pairs,
        "dup_no_key": dup_no_key,
    }


def _table(name, headers, rows, fmt=None):
    """표 형식 출력."""
    if fmt is None:
        fmt = lambda r: r
    lines = [f"\n### {name}", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows[:50]:
        lines.append("| " + " | ".join(str(x) for x in fmt(r)) + " |")
    if len(rows) > 50:
        lines.append(f"| ... 외 {len(rows) - 50}건 |")
    return "\n".join(lines)


def main():
    apply_cleanup = "--apply" in sys.argv
    db = SessionLocal()

    # BEFORE
    rows_before = _fetch_rows(db)
    before = _analyze(rows_before)

    if apply_cleanup:
        from app.deduplication import run_cleanup
        result = run_cleanup(db=db, dry_run=False)
        db.expire_all()  # refresh
        rows_after = _fetch_rows(db)
        after = _analyze(rows_after)
    else:
        after = None

    # 출력
    print("=" * 80)
    print("고인(deceased_name) 데이터 품질 감사")
    print("=" * 80)
    print(f"\n총 레코드: BEFORE {before['total']}" + (f" → AFTER {after['total']}" if after else ""))

    # 1. deceased 없음
    print(_table(
        "1. deceased_name 없음",
        ["id", "key_person", "funeral_hall", "raw_preview"],
        before["no_deceased"],
        fmt=lambda r: (r.id, (r.key_person or "-")[:15], (r.funeral_hall or "-")[:20], (r.raw_text or "")[:30].replace("\n", " ") + "..."),
    ))
    if after and len(after["no_deceased"]) != len(before["no_deceased"]):
        print(f"\n**AFTER**: {len(after['no_deceased'])}건 (변경 {len(after['no_deceased']) - len(before['no_deceased']):+d})")

    # 2. 오파싱(블랙리스트)
    print(_table(
        "2. deceased 오파싱 (직급/직위 블랙리스트)",
        ["id", "deceased", "key_person", "funeral_hall"],
        before["bad_deceased"],
        fmt=lambda r: (r.id, r.deceased_name, (r.key_person or "-")[:15], (r.funeral_hall or "-")[:25]),
    ))
    if after:
        print(f"\n**AFTER**: {len(after['bad_deceased'])}건 (변경 {len(after['bad_deceased']) - len(before['bad_deceased']):+d})")

    # 3. (deceased, key_person) 중복
    print(_table(
        "3. 같은 (deceased, key_person) 중복 — 병합 대상",
        ["deceased", "key_person", "건수", "id 목록"],
        before["dup_pairs"],
        fmt=lambda r: (r[0][:12], r[1][:15], len(r[2]), [x.id for x in r[2]]),
    ))
    if after:
        print(f"\n**AFTER**: {len(after['dup_pairs'])}건 (변경 {len(after['dup_pairs']) - len(before['dup_pairs']):+d})")

    # 4. (deceased, None) 중복
    print(_table(
        "4. 같은 deceased, key_person 없음 중복",
        ["deceased", "건수", "id 목록"],
        before["dup_no_key"],
        fmt=lambda r: (r[0][:15], len(r[1]), [x.id for x in r[1]]),
    ))
    if after:
        print(f"\n**AFTER**: {len(after['dup_no_key'])}건 (변경 {len(after['dup_no_key']) - len(before['dup_no_key']):+d})")

    db.close()
    if apply_cleanup:
        print(f"\n\ncleanup 결과: 병합 {result['merged']}건, 삭제 {result['deleted']}건, 보정 {result['corrected']}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
