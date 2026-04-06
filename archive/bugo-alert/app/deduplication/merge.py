"""동일 부고 레코드 병합 — raw_text 합침, Case 3b 장례식장 풍부화."""

from __future__ import annotations

import json
import re
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import Obituary, NotificationLog
from app.crawler.parser import make_dedup_key

RAW_TEXT_MAX = 15000
RAW_MERGE_SEP = "\n\n---\n\n"


def _richness(obit: Obituary) -> int:
    """데이터 풍부도 점수."""
    return sum(
        1
        for f in ["key_person", "deceased_name", "funeral_hall", "organization"]
        if getattr(obit, f, None)
    )


def _richness_hall(obit: Obituary) -> int:
    """장례식장·호실·연락처 풍부도."""
    base = sum(
        1 for f in ["funeral_hall", "room_number", "contact"] if getattr(obit, f, None)
    )
    hall = getattr(obit, "funeral_hall", None) or ""
    if "장례식장" in hall or "국화원" in hall or "백합원" in hall:
        base += 1
    return base


def _normalize_relationship(rel: str | None) -> str | None:
    """형님상 → 형제상 정규화."""
    if not rel:
        return rel
    return rel.replace("형님상", "형제상").strip() or None


def _merge_funeral_hall(rows: list[Obituary]) -> tuple[str | None, str | None]:
    """Case 3b: 병원명 + 상세장소(국화원 등) + 호실 조합.

    예: 대구의료원 + 국화원장례식장 301호실 → 대구의료원 국화원장례식장 301호실
    """
    halls: list[str] = []
    rooms: list[str] = []
    for r in rows:
        h = (r.funeral_hall or "").strip()
        if h:
            halls.append(h)
        if r.room_number:
            rooms.append(r.room_number.strip())

    if not halls:
        return None, rooms[0] if rooms else None

    # 병원/의료원명 추출 (예: 대구의료원, 연세대 세브란스병원)
    hospital_pattern = re.compile(
        r"([가-힣A-Za-z0-9\s]+(?:병원|의료원|대학교|대학))"
    )
    # 상세장소 (국화원, 백합원, 장례식장 등)
    detail_pattern = re.compile(
        r"([가-힣A-Za-z0-9\s]*(?:국화원|백합원|장례식장|추모관)[\s\d호실]*)?"
    )

    hospital = ""
    detail = ""
    for h in halls:
        m = hospital_pattern.search(h)
        if m:
            cand = m.group(1).strip()
            if len(cand) > len(hospital):
                hospital = cand
        if "국화원" in h or "백합원" in h or "장례식장" in h:
            # 상세 부분 추출 (병원명 제외)
            rest = h
            if hospital:
                rest = rest.replace(hospital, "").strip()
            if rest and len(rest) > len(detail):
                detail = rest

    if hospital and detail:
        result = f"{hospital} {detail}".strip()
    elif halls:
        result = max(halls, key=len)
    else:
        result = ""

    room = max(rooms, key=len) if rooms else None
    return result or None, room


def _merge_raw_texts(rows: list[Obituary]) -> str:
    """여러 raw_text를 출처별 합침."""
    parts = []
    seen_urls = set()
    for r in rows:
        url = r.source_url or ""
        text = (r.raw_text or "").strip()
        if not text:
            continue
        if url in seen_urls:
            parts.append(text)
        else:
            seen_urls.add(url)
            parts.append(f"[출처: {url}]\n{text}")
    merged = RAW_MERGE_SEP.join(parts)
    return merged[:RAW_TEXT_MAX] if len(merged) > RAW_TEXT_MAX else merged


def _merge_source_urls(rows: list[Obituary]) -> str:
    """병합된 모든 URL JSON 배열."""
    urls = []
    seen = set()
    for r in rows:
        u = r.source_url
        if u and u not in seen:
            seen.add(u)
            urls.append(u)
    return json.dumps(urls, ensure_ascii=False) if urls else ""


def run_merge(db: Session) -> list[str]:
    """(deceased, key_person) 동일 레코드 병합 — raw_text 합침, Case 3b 풍부화."""
    changes = []
    by_key = defaultdict(list)
    for r in db.query(Obituary).all():
        if r.deceased_name and r.key_person:
            by_key[(r.deceased_name, r.key_person)].append(r)

    for (deceased, kp), rows in by_key.items():
        if len(rows) <= 1:
            continue
        rows.sort(key=lambda r: (_richness_hall(r), _richness(r)), reverse=True)
        keep, *remove = rows
        changes.extend(_merge_record(keep, remove, db))
    db.flush()

    # 같은 deceased, key_person 없음 중복 → 1건만 유지
    changes.extend(_merge_same_deceased_no_key(db))
    return changes


def _merge_same_deceased_no_key(db: Session) -> list[str]:
    """(deceased, None) 중복 — 풍부한 1건만 유지."""
    changes = []
    by_deceased = defaultdict(list)
    for r in db.query(Obituary).all():
        if r.deceased_name and not (r.key_person or "").strip():
            by_deceased[(r.deceased_name or "").strip()].append(r)

    for deceased, rows in by_deceased.items():
        if len(rows) <= 1:
            continue
        rows.sort(key=lambda r: (_richness_hall(r), _richness(r)), reverse=True)
        keep, *remove = rows
        for r in remove:
            db.query(NotificationLog).filter(NotificationLog.obituary_id == r.id).update(
                {"obituary_id": keep.id}, synchronize_session="fetch"
            )
            changes.append(f"병합 삭제 id={r.id} ({deceased}·key없음, id={keep.id} 유지)")
            db.delete(r)
    db.flush()
    return changes


def _merge_record(keep: Obituary, remove: list[Obituary], db: Session) -> list[str]:
    """keep에 remove들을 병합. NotificationLog 이전, remove 삭제."""
    changes = []
    all_rows = [keep] + remove

    # dedup_key UNIQUE 충돌 방지: remove를 먼저 삭제한 뒤 keep 업데이트
    for r in remove:
        db.query(NotificationLog).filter(NotificationLog.obituary_id == r.id).update(
            {"obituary_id": keep.id}, synchronize_session="fetch"
        )
        changes.append(f"병합 삭제 id={r.id} ({keep.deceased_name}·{keep.key_person}, id={keep.id} 유지)")
        db.delete(r)
    db.flush()

    # 필드 병합 (풍부한 값 우선)
    for fld in [
        "deceased_age", "related_persons", "room_number",
        "funeral_date", "funeral_time", "contact",
        "organization", "position", "relationship",
    ]:
        for r in all_rows:
            val = getattr(r, fld, None)
            if val and not getattr(keep, fld, None):
                if fld == "relationship":
                    val = _normalize_relationship(val)
                setattr(keep, fld, val)
                break

    # relationship 형님상 → 형제상
    if keep.relationship:
        keep.relationship = _normalize_relationship(keep.relationship)

    # Case 3b: 장례식장·호실 풍부하게 병합
    hall, room = _merge_funeral_hall(all_rows)
    if hall:
        keep.funeral_hall = hall
    if room and not keep.room_number:
        keep.room_number = room

    # funeral_date: 연도 포함 우선
    for r in all_rows:
        fd = r.funeral_date or ""
        if fd and "년" in fd and (not keep.funeral_date or "년" not in (keep.funeral_date or "")):
            keep.funeral_date = fd
            break
    if not keep.funeral_date:
        for r in all_rows:
            if r.funeral_date:
                keep.funeral_date = r.funeral_date
                break

    # funeral_time
    if not keep.funeral_time:
        for r in all_rows:
            if r.funeral_time:
                keep.funeral_time = r.funeral_time
                break

    # raw_text 병합
    keep.raw_text = _merge_raw_texts(all_rows)

    # source_urls (컬럼 있으면)
    try:
        urls_json = _merge_source_urls(all_rows)
        if urls_json:
            setattr(keep, "source_urls", urls_json)
    except Exception:
        pass

    # source_url: keep이 이미 가장 풍부한 레코드이므로 유지

    # dedup_key (다른 레코드가 이미 사용 중이면 None)
    for r in all_rows:
        dk = r.dedup_key
        if dk:
            existing = db.query(Obituary).filter(
                Obituary.dedup_key == dk, Obituary.id != keep.id
            ).first()
            keep.dedup_key = dk if not existing else None
            break

    return changes
