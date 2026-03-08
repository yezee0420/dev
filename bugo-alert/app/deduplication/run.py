"""데이터 정리 파이프라인 — 품질 보정 + 병합."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.deduplication.quality import (
    run_quality_fixes,
    step1_source_url_dedup,
    step2_fill_blank_fields,
    step2a_fill_deceased_from_body,
    step2b_fix_bad_deceased,
    step3_remove_self_obituary,
)
from app.deduplication.merge import run_merge

logger = logging.getLogger(__name__)


def _ensure_source_urls_column(db: Session) -> None:
    """source_urls 컬럼이 없으면 추가."""
    try:
        from sqlalchemy import text
        result = db.execute(text("PRAGMA table_info(obituaries)"))
        columns = [row[1] for row in result.fetchall()]
        if "source_urls" not in columns:
            db.execute(text("ALTER TABLE obituaries ADD COLUMN source_urls TEXT"))
            db.flush()
    except Exception:
        pass


def run_cleanup(db: Session | None = None, dry_run: bool = False) -> dict[str, Any]:
    """크롤링 후 데이터 정리 — 중복 제거, 병합, 품질 보정.

    처리 순서 (DEDUP_MERGE_LOGIC.md):
      1. source_url 중복 삭제
      2. 빈 필드 보충
      3. 본인상 제거
      4. (deceased, key_person) 동일 → 병합 (raw_text 합침, Case 3b 풍부화)
      5. 복수 부고 장례식장 오매칭 보정
      6. org/pos 비정상 보정
      7. 같은 고인 장례정보 통일
      8. 품질 최저 삭제

    Returns:
        {"merged": N, "deleted": M, "corrected": K, "changes": [...]}
    """
    own_db = db is None
    if own_db:
        init_db()
        db = SessionLocal()

    all_changes = []

    try:
        _ensure_source_urls_column(db)

        # 1. source_url 중복
        all_changes.extend(step1_source_url_dedup(db))

        # 2. 빈 필드 보충
        all_changes.extend(step2_fill_blank_fields(db))

        # 2a. deceased 없음 → 본문 직접 파싱 보충
        all_changes.extend(step2a_fill_deceased_from_body(db))

        # 2b. 고인 오파싱 보정 (직급/직위 블랙리스트)
        all_changes.extend(step2b_fix_bad_deceased(db))

        # 3. 본인상 제거
        all_changes.extend(step3_remove_self_obituary(db))

        # 4. (deceased, key_person) 병합
        merge_changes = run_merge(db)
        all_changes.extend(merge_changes)

        # 5~8. 나머지 품질 보정 (merge 제외)
        from app.deduplication.quality import (
            step4_fix_hall_mismatch,
            step5_fix_bad_org_pos,
            step6_unify_same_deceased,
            step7_remove_mismatched_multi,
            step8_remove_low_quality,
        )
        for step in [
            step4_fix_hall_mismatch,
            step5_fix_bad_org_pos,
            step6_unify_same_deceased,
            step7_remove_mismatched_multi,
            step8_remove_low_quality,
        ]:
            all_changes.extend(step(db))

        if not dry_run:
            db.commit()
        else:
            db.rollback()

        merged = sum(1 for c in all_changes if "병합 삭제" in c)
        deleted = sum(1 for c in all_changes if "삭제" in c and "병합" not in c)
        corrected = sum(1 for c in all_changes if "보정" in c or "통일" in c or "빈칸" in c)

        logger.info(
            "데이터 정리 완료: 병합 %d건, 삭제 %d건, 보정 %d건 (총 %d건 변경)",
            merged, deleted, corrected, len(all_changes),
        )

        return {
            "merged": merged,
            "deleted": deleted,
            "corrected": corrected,
            "total_changes": len(all_changes),
            "changes": all_changes,
        }
    finally:
        if own_db:
            db.close()


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    result = run_cleanup(dry_run=dry_run)
    print(f"병합 {result['merged']}건, 삭제 {result['deleted']}건, 보정 {result['corrected']}건")
    for c in (result.get("changes") or [])[:50]:
        print(f"  - {c}")
    if len(result.get("changes") or []) > 50:
        print(f"  ... 외 {len(result['changes']) - 50}건")
