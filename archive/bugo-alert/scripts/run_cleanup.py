#!/usr/bin/env python3
"""데이터 정리 수동 실행.

실행: cd bugo-alert && PYTHONPATH=. python scripts/run_cleanup.py
옵션: --dry-run (DB 변경 없이 변경 예정만 출력)
"""

import sys
from app.deduplication import run_cleanup

dry_run = "--dry-run" in sys.argv
result = run_cleanup(dry_run=dry_run)
print(f"병합 {result['merged']}건, 삭제 {result['deleted']}건, 보정 {result['corrected']}건")
if result.get("changes"):
    for c in result["changes"][:50]:
        print(f"  - {c}")
    if len(result["changes"]) > 50:
        print(f"  ... 외 {len(result['changes']) - 50}건")
