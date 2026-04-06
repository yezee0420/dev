#!/usr/bin/env python3
"""고인(deceased_name) 데이터 품질 감사.

실행: cd bugo-alert && PYTHONPATH=. python scripts/audit_deceased.py
"""

import sys
from collections import defaultdict

from app.database import SessionLocal
from app.models import Obituary


def _norm(s: str | None) -> str:
    if s is None:
        return ""
    return (s or "").strip()


def main():
    db = SessionLocal()
    try:
        rows = db.query(Obituary).all()
    finally:
        db.close()

    # 1. deceased_name 없음
    no_deceased = [r for r in rows if not _norm(r.deceased_name)]
    # 2. deceased_name 있음
    has_deceased = [r for r in rows if _norm(r.deceased_name)]

    # 3. 고인별 그룹핑 (중복·분산 확인)
    by_deceased = defaultdict(list)
    for r in has_deceased:
        by_deceased[_norm(r.deceased_name)].append(r)

    # 4. 이상 패턴: 빈문자열, 공백만, 너무 짧음(1글자), 특수문자
    anomalies = []
    for r in rows:
        dn = _norm(r.deceased_name)
        if r.deceased_name is not None and not dn:
            anomalies.append((r, "deceased_name 공백/빈문자열"))
        elif dn and len(dn) == 1:
            anomalies.append((r, "deceased_name 1글자"))
        elif dn and any(c in dn for c in "()[]|·"):
            anomalies.append((r, "deceased_name 특수문자 포함"))

    # 5. key_person 없음 (고인만 있고 조문자 없음)
    no_key = [r for r in has_deceased if not _norm(r.key_person)]

    # 6. 본인상 의심 (key_person == deceased_name)
    self_obit = [
        r for r in has_deceased
        if _norm(r.key_person) and _norm(r.key_person) == _norm(r.deceased_name)
    ]

    # 7. 같은 (deceased, key_person) 중복
    dup_pairs = []
    for d, recs in by_deceased.items():
        by_kp = defaultdict(list)
        for r in recs:
            by_kp[_norm(r.key_person) or "(없음)"].append(r)
        for kp_val, recs2 in by_kp.items():
            if len(recs2) > 1:
                dup_pairs.append((d, kp_val, recs2))

    # 출력
    print("=" * 80)
    print("고인(deceased_name) 데이터 품질 감사")
    print("=" * 80)
    print(f"\n총 레코드: {len(rows)}")
    print(f"  - deceased_name 있음: {len(has_deceased)}")
    print(f"  - deceased_name 없음: {len(no_deceased)}")

    print("\n" + "-" * 80)
    print("1. deceased_name 없음 (NULL/빈칸) — BEFORE")
    print("-" * 80)
    if no_deceased:
        print(f"{'id':>6} | {'key_person':<20} | {'deceased':<12} | {'funeral_hall':<30} | raw_text")
        for r in sorted(no_deceased, key=lambda x: x.id)[:80]:
            raw_preview = (r.raw_text or "")[:40].replace("\n", " ")
            print(f"{r.id:>6} | {(r.key_person or '-'):<20} | {'(없음)':<12} | {(r.funeral_hall or '-')[:30]:<30} | {raw_preview}...")
        if len(no_deceased) > 80:
            print(f"... 외 {len(no_deceased) - 80}건")
    else:
        print("(없음)")

    print("\n" + "-" * 80)
    print("2. deceased_name 이상 패턴")
    print("-" * 80)
    if anomalies:
        for r, reason in anomalies[:30]:
            print(f"  id={r.id}: {reason} | deceased='{r.deceased_name}' | key={r.key_person}")
    else:
        print("(없음)")

    print("\n" + "-" * 80)
    print("3. key_person 없음 (고인만 있음)")
    print("-" * 80)
    if no_key:
        for r in sorted(no_key, key=lambda x: x.id)[:40]:
            print(f"  id={r.id}: deceased={r.deceased_name} | hall={r.funeral_hall}")
    else:
        print("(없음)")

    print("\n" + "-" * 80)
    print("4. 본인상 의심 (key_person == deceased_name)")
    print("-" * 80)
    if self_obit:
        for r in self_obit:
            others = [x for x in by_deceased.get(_norm(r.deceased_name), []) if x.id != r.id]
            has_other = any(_norm(x.key_person) != _norm(r.deceased_name) for x in others)
            print(f"  id={r.id}: deceased=key='{r.deceased_name}' | 같은고인 다른key 있음={has_other} | others={len(others)}")
    else:
        print("(없음)")

    print("\n" + "-" * 80)
    print("5. 같은 (deceased, key_person) 중복 — 병합 대상")
    print("-" * 80)
    if dup_pairs:
        for d, kp, recs in dup_pairs[:30]:
            ids = [r.id for r in recs]
            print(f"  ({d}, {kp}): {len(recs)}건 → id={ids}")
    else:
        print("(없음)")

    print("\n" + "-" * 80)
    print("6. 고인별 레코드 수 (2건 이상 = 같은 고인 여러 조문자)")
    print("-" * 80)
    multi = [(d, recs) for d, recs in by_deceased.items() if len(recs) >= 2]
    multi.sort(key=lambda x: -len(x[1]))
    for d, recs in multi[:25]:
        kps = [r.key_person for r in recs]
        print(f"  {d}: {len(recs)}건 | key_persons={kps[:5]}{'...' if len(kps)>5 else ''}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
