"""기존 DB의 중복 부고 레코드를 정리하는 일회성 마이그레이션 스크립트.

실행: python migrate_dedup.py

동작:
  1. 모든 dedup_key를 NULL로 초기화 (UNIQUE 충돌 방지)
  2. 새 로직(key_person|relationship)으로 dedup_key 재계산
  3. 같은 키의 중복 그룹을 병합 (정보 보충 후 중복 삭제)
  4. 남은 레코드에 새 dedup_key 할당
"""

from __future__ import annotations

from collections import defaultdict

from app.database import SessionLocal, init_db
from app.models import Obituary, NotificationLog
from app.crawler.parser import ParsedObituary, make_dedup_key

MERGE_FIELDS = (
    "deceased_name", "deceased_age", "funeral_hall", "room_number",
    "funeral_date", "funeral_time", "contact", "related_persons",
    "organization", "position",
)


def _richness_score(obit: Obituary) -> int:
    score = 0
    for fld in MERGE_FIELDS:
        if getattr(obit, fld, None):
            score += 1
    return score


def _recalc_key(obit: Obituary) -> str | None:
    p = ParsedObituary(
        key_person=obit.key_person,
        relationship=obit.relationship,
        deceased_name=obit.deceased_name,
    )
    return make_dedup_key(p)


def main() -> None:
    init_db()
    db = SessionLocal()

    # 1) 모든 dedup_key를 NULL로 초기화 → UNIQUE 충돌 방지
    db.query(Obituary).update({"dedup_key": None}, synchronize_session="fetch")
    db.commit()
    print("dedup_key 전체 NULL 초기화 완료")

    # 2) 새 dedup_key 계산 + 그룹핑
    all_obits: list[Obituary] = db.query(Obituary).order_by(Obituary.id).all()
    print(f"총 레코드 수: {len(all_obits)}")

    groups: dict[str, list[Obituary]] = defaultdict(list)
    no_key_ids: list[int] = []

    for obit in all_obits:
        new_key = _recalc_key(obit)
        if new_key:
            groups[new_key].append(obit)
        else:
            no_key_ids.append(obit.id)

    dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"중복 그룹 수: {len(dup_groups)}")
    print(f"dedup_key 없는 레코드: {len(no_key_ids)}")

    deleted_count = 0

    # 3) 중복 그룹 병합: 가장 풍부한 레코드 유지, 나머지 삭제
    for key, obits in dup_groups.items():
        obits.sort(key=_richness_score, reverse=True)
        primary = obits[0]

        for secondary in obits[1:]:
            for fld in MERGE_FIELDS:
                if not getattr(primary, fld, None) and getattr(secondary, fld, None):
                    setattr(primary, fld, getattr(secondary, fld))

            db.query(NotificationLog).filter(
                NotificationLog.obituary_id == secondary.id
            ).update({"obituary_id": primary.id}, synchronize_session="fetch")

            db.delete(secondary)
            deleted_count += 1

    db.flush()
    db.commit()
    print(f"중복 병합 완료: {deleted_count}개 레코드 삭제")

    # 4) 남은 레코드에 새 dedup_key 할당
    remaining = db.query(Obituary).order_by(Obituary.id).all()
    updated_count = 0
    for obit in remaining:
        new_key = _recalc_key(obit)
        obit.dedup_key = new_key
        updated_count += 1

    db.commit()
    db.close()

    print(f"dedup_key 갱신: {updated_count}건")
    print(f"최종 레코드 수: {len(remaining)}")
    print("마이그레이션 성공.")


if __name__ == "__main__":
    main()
