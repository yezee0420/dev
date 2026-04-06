"""품질 보정 — 빈 필드 보충, 본인상 제거, 장례식장 오매칭, org/pos 보정 등."""

from __future__ import annotations

import re
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import Obituary, NotificationLog
from app.crawler.parser import (
    parse_obituary,
    parse_body,
    _clean_funeral_hall,
    _get_block_containing_deceased,
)

# deceased_name 오파싱 블랙리스트 — 직급/직위/기타 (사람 이름 아님)
# 세로: "74세로 별세" 오매칭, 이사/전무/의원: 직급, 션닷컴전무: org+직급
DECEASED_BLACKLIST = frozenset({
    "이사", "전무", "의원", "세로", "경영본부장", "주식회사", "호실", "션닷컴전무",
})


def _richness(obit: Obituary) -> int:
    return sum(
        1 for f in ["key_person", "deceased_name", "funeral_hall", "organization"]
        if getattr(obit, f, None)
    )


def _richness_hall(obit: Obituary) -> int:
    base = sum(
        1 for f in ["funeral_hall", "room_number", "contact"] if getattr(obit, f, None)
    )
    hall = getattr(obit, "funeral_hall", None) or ""
    if "장례식장" in hall:
        base += 1
    return base


def _get_block_for_key_person(raw_text: str, key_person: str) -> str | None:
    """raw에서 key_person이 포함된 ▲ 블록을 반환."""
    if not raw_text or not key_person:
        return None
    blocks = re.split(r"\n?[▲△◇◆▶]", raw_text)
    key_clean = key_person.replace(" ", "").strip()
    for b in blocks:
        if not b.strip():
            continue
        for m in re.finditer(
            r"([가-힣]{2,5})\s*(?:\([^)]+\))?\s*[·\s]*씨?\s*[가-힣]+상", b
        ):
            name = m.group(1).strip()
            if name == key_clean or name.replace(" ", "") == key_clean:
                return b
        if key_clean in b.replace(" ", ""):
            return b
    return None


def _extract_composite_block_hall_contact(block: str) -> tuple[str | None, str | None]:
    hall_match = re.search(
        r"=\d+일[^=]*?"
        r"(?P<hall>[가-힣A-Za-z0-9\s]+(?:병원|의료원|장례식장|장[례레]식장))",
        block,
    )
    hall = hall_match.group("hall").strip() if hall_match else None
    if hall:
        hall = re.sub(
            r"^[\s=,]*\d*일?\s*(?:오[전후]\s*\d+시(?:\s*\d+분)?|오전|오후)?\s*",
            "", hall
        ).strip()
        hall = _clean_funeral_hall(hall)
    phone_match = re.search(r"\(?\d{2,3}-\d{3,4}-\d{4}\)?", block)
    contact = phone_match.group(0).strip("()") if phone_match else None
    return (hall, contact)


def _is_bad_org_pos(val: str | None) -> bool:
    if not val:
        return False
    return "씨(" in val or "pos=" in val or "(" in val[:3]


_HALL_SYNONYM_GROUPS = [
    {"연세대 세브란스병원 장례식장", "연세대 세브란스병원", "신촌세브란스병원"},
]


def _hall_same_venue(a: str, b: str) -> bool:
    if not a or not b:
        return False
    a, b = a.strip(), b.strip()
    for group in _HALL_SYNONYM_GROUPS:
        if a in group and b in group:
            return True
    return False


def _normalize_relationship(rel: str | None) -> str | None:
    """형님상 → 형제상."""
    if not rel:
        return rel
    return rel.replace("형님상", "형제상").strip() or None


def step1_source_url_dedup(db: Session) -> list[str]:
    """같은 source_url 중복 → 1건만 유지."""
    changes = []
    by_url = defaultdict(list)
    for r in db.query(Obituary).all():
        if r.source_url:
            by_url[r.source_url].append(r)

    for url, rows in by_url.items():
        if len(rows) <= 1:
            continue
        rows.sort(key=_richness, reverse=True)
        keep, *remove = rows
        for r in remove:
            db.query(NotificationLog).filter(NotificationLog.obituary_id == r.id).update(
                {"obituary_id": keep.id}, synchronize_session="fetch"
            )
            changes.append(f"URL 중복 삭제 id={r.id} (id={keep.id} 유지)")
            db.delete(r)
    db.flush()
    return changes


def step2_fill_blank_fields(db: Session) -> list[str]:
    """빈 필드 보충 (재파싱)."""
    changes = []
    for r in db.query(Obituary).filter(Obituary.raw_text.isnot(None)).all():
        if not r.title:
            continue
        parsed = parse_obituary(r.title, r.raw_text or "")
        if not parsed:
            continue
        updated = []
        for fld, val in [
            ("deceased_name", parsed.deceased_name),
            ("key_person", parsed.key_person),
            ("funeral_hall", parsed.funeral_hall),
            ("room_number", parsed.room_number),
            ("relationship", _normalize_relationship(parsed.relationship) if parsed.relationship else None),
            ("contact", parsed.contact),
        ]:
            if val and not getattr(r, fld, None):
                setattr(r, fld, val)
                updated.append(fld)
        if updated:
            changes.append(f"빈칸 보정 id={r.id}: {', '.join(updated)}")
    db.flush()
    return changes


def step2a_fill_deceased_from_body(db: Session) -> list[str]:
    """deceased 없음 → 본문(parse_body) + 제목 직접 파싱으로 보충."""
    changes = []
    _re_title_starse = re.compile(r"(?P<name>[가-힣]{2,5})\s*씨\s*별세")
    for r in db.query(Obituary).filter(
        Obituary.deceased_name.is_(None) | (Obituary.deceased_name == ""),
    ).all():
        dn = None
        source = None
        body_info = {}
        raw = (r.raw_text or "").strip()
        if raw:
            body_info = parse_body(raw)
            dn = body_info.get("deceased_name")
            if dn:
                source = "본문"
        if not dn and r.title:
            m = _re_title_starse.search(r.title)
            if m:
                dn = m.group("name").strip()
                source = "제목"
        if not dn and raw and r.title:
            parsed = parse_obituary(r.title, raw)
            if parsed and parsed.deceased_name:
                dn = parsed.deceased_name
                source = "parse_obituary"
        if not dn or (dn or "").strip() in DECEASED_BLACKLIST:
            continue
        r.deceased_name = (dn or "").strip()
        if body_info.get("deceased_age"):
            r.deceased_age = body_info["deceased_age"]
        if not r.key_person and body_info.get("key_person"):
            r.key_person = body_info["key_person"]
            r.organization = body_info.get("organization")
            r.position = body_info.get("position")
            r.relationship = _normalize_relationship(body_info.get("relationship"))
        changes.append(f"고인 보정 id={r.id}: ({source}) → '{r.deceased_name}'")
    db.flush()
    return changes


def step2b_fix_bad_deceased(db: Session) -> list[str]:
    """deceased_name 오파싱 보정 — 블랙리스트(직급/직위)에 있으면 재파싱."""
    changes = []
    for r in db.query(Obituary).filter(
        Obituary.deceased_name.isnot(None),
        Obituary.raw_text.isnot(None),
    ).all():
        dn = (r.deceased_name or "").strip()
        if dn not in DECEASED_BLACKLIST:
            continue
        parsed = parse_obituary(r.title or "", r.raw_text or "")
        if parsed and parsed.deceased_name and parsed.deceased_name.strip() not in DECEASED_BLACKLIST:
            old = r.deceased_name
            r.deceased_name = parsed.deceased_name
            r.deceased_age = parsed.deceased_age or r.deceased_age
            if not r.key_person and parsed.key_person:
                r.key_person = parsed.key_person
                r.organization = parsed.organization or r.organization
                r.position = parsed.position or r.position
                r.relationship = _normalize_relationship(parsed.relationship) or r.relationship
            changes.append(f"고인 보정 id={r.id}: '{old}' → '{r.deceased_name}'")
        elif parsed and parsed.key_person and parsed.key_person.strip() not in DECEASED_BLACKLIST:
            # "이름 직급 별세" 형식: key_person이 실제 고인(본인상)
            old = r.deceased_name
            r.deceased_name = parsed.key_person
            r.deceased_age = parsed.deceased_age or r.deceased_age
            if not r.key_person:
                r.key_person = parsed.key_person
                r.organization = parsed.organization or r.organization
                r.position = parsed.position or r.position
                r.relationship = "본인상"
            changes.append(f"고인 보정 id={r.id}: '{old}' → '{r.deceased_name}' (본인상)")
        else:
            r.deceased_name = None
            r.deceased_age = None
            changes.append(f"고인 보정 id={r.id}: '{dn}' 제거 (재파싱 실패)")
    db.flush()
    return changes


def step3_remove_self_obituary(db: Session) -> list[str]:
    """본인상 제거: key_person == deceased_name, 같은 고인에 다른 key 있으면 삭제."""
    changes = []
    by_deceased = defaultdict(list)
    for r in db.query(Obituary).filter(Obituary.deceased_name.isnot(None)).all():
        by_deceased[r.deceased_name].append(r)

    for deceased, rows in by_deceased.items():
        has_other = any(r.key_person and r.key_person != deceased for r in rows)
        if not has_other:
            continue
        for r in rows:
            if r.key_person == deceased:
                db.query(NotificationLog).filter(
                    NotificationLog.obituary_id == r.id
                ).delete(synchronize_session="fetch")
                changes.append(
                    f"본인상 삭제 id={r.id} (key_person==deceased '{deceased}')"
                )
                db.delete(r)
    db.flush()
    return changes


def step4_fix_hall_mismatch(db: Session) -> list[str]:
    """복수 부고 기사 장례식장 오매칭 보정."""
    changes = []
    for r in db.query(Obituary).filter(Obituary.raw_text.isnot(None)).all():
        raw = r.raw_text or ""
        blocks = re.split(r"[▲△◇◆]", raw)
        if len([b for b in blocks if b.strip()]) < 2:
            continue
        block = _get_block_for_key_person(raw, r.key_person or "")
        if not block:
            continue
        hall, contact = _extract_composite_block_hall_contact(block)
        if not hall:
            continue
        current = (r.funeral_hall or "").strip()
        if current and hall and current != hall and not _hall_same_venue(current, hall):
            if "장례식장" in current and "장례식장" not in hall:
                continue
            r.funeral_hall = hall
            if contact:
                r.contact = contact
            changes.append(f"장례식장 보정 id={r.id}: '{current}' → '{hall}'")
    db.flush()
    return changes


def step5_fix_bad_org_pos(db: Session) -> list[str]:
    """org/pos 비정상 재파싱 보정."""
    _RE_KEY_ORG_POS = re.compile(
        r"(?P<name>[가-힣]{2,5})\s*씨?\s*\((?P<affil>[^)]+)\)\s*[·\s]*(?P<rel>[가-힣]+상)"
    )
    changes = []

    def _extract_org_pos(text: str, kp: str) -> tuple[str | None, str | None, str | None]:
        if not kp or not text:
            return (None, None, None)
        key_clean = kp.replace(" ", "").strip()
        for m in _RE_KEY_ORG_POS.finditer(text):
            name = m.group("name").replace(" ", "").strip()
            if name != key_clean:
                continue
            affil = m.group("affil").strip()
            rel = m.group("rel")
            parts = affil.split()
            if len(parts) >= 3 and parts[0] in ("전", "前"):
                org, pos = parts[1], " ".join([parts[0]] + parts[2:])
            elif len(parts) == 2 and parts[0] in ("전", "前"):
                org, pos = None, affil
            elif len(parts) >= 2:
                org, pos = parts[0], " ".join(parts[1:])
            else:
                org, pos = None, affil
            return (org or None, pos or None, rel)
        return (None, None, None)

    for r in db.query(Obituary).filter(Obituary.raw_text.isnot(None)).all():
        if not _is_bad_org_pos(r.organization) and not _is_bad_org_pos(r.position):
            continue
        raw = r.raw_text or ""
        blocks = re.split(r"[▲△◇◆]", raw)
        search_text = (
            _get_block_for_key_person(raw, r.key_person or "") or raw
            if len([b for b in blocks if b.strip()]) >= 2
            else raw
        )
        org, pos, rel = _extract_org_pos(search_text, r.key_person or "")
        if org and not _is_bad_org_pos(org):
            r.organization = org
        if pos and not _is_bad_org_pos(pos):
            r.position = pos
        if rel:
            r.relationship = _normalize_relationship(rel)
        if org or pos or rel:
            changes.append(f"org/pos 보정 id={r.id} ({r.key_person})")
    db.flush()
    return changes


def step6_unify_same_deceased(db: Session) -> list[str]:
    """같은 고인 레코드의 장례식장·호실·연락처 통일."""
    changes = []
    by_deceased = defaultdict(list)
    for r in db.query(Obituary).filter(Obituary.deceased_name.isnot(None)).all():
        by_deceased[r.deceased_name].append(r)

    for deceased, rows in by_deceased.items():
        if len(rows) < 2:
            continue
        best = max(rows, key=_richness_hall)
        hall, room, contact = best.funeral_hall, best.room_number, best.contact
        if not hall and not room and not contact:
            continue
        for r in rows:
            updated = []
            if hall and (not r.funeral_hall or r.funeral_hall != hall):
                r.funeral_hall = hall
                updated.append("hall")
            if room and (not r.room_number or r.room_number != room):
                r.room_number = room
                updated.append("room")
            if contact and (not r.contact or r.contact != contact):
                r.contact = contact
                updated.append("contact")
            if updated:
                changes.append(f"장례정보 통일 id={r.id} ({deceased}·{r.key_person})")
    db.flush()
    return changes


def step7_remove_mismatched_multi(db: Session) -> list[str]:
    """복수 부고 오매칭 삭제 — key_person이 해당 고인 블록에 없으면 삭제."""
    changes = []
    for r in list(db.query(Obituary).filter(
        Obituary.raw_text.isnot(None),
        Obituary.deceased_name.isnot(None),
        Obituary.key_person.isnot(None),
    ).all()):
        raw = r.raw_text or ""
        blocks = re.split(r"\n?[▲△◇◆▶]", raw)
        if len([b for b in blocks if b.strip()]) < 2:
            continue
        block = _get_block_containing_deceased(raw, r.deceased_name or "")
        if block and r.key_person:
            kp_clean = r.key_person.replace(" ", "").strip()
            if kp_clean not in block.replace(" ", ""):
                db.query(NotificationLog).filter(
                    NotificationLog.obituary_id == r.id
                ).delete(synchronize_session="fetch")
                changes.append(
                    f"오매칭 삭제 id={r.id} ({r.deceased_name}·{r.key_person})"
                )
                db.delete(r)
    db.flush()
    return changes


def step8_remove_low_quality(db: Session) -> list[str]:
    """품질 최저 삭제 — deceased·key 둘 다 없고 복구 불가. deceased 없고 본문에 부고 내용 없으면 삭제."""
    changes = []
    _obit_keywords = ("별세", "부친상", "모친상", "장인상", "장모상", "시부상", "시모상", "조부상", "조모상")
    for r in list(db.query(Obituary).filter(Obituary.deceased_name.is_(None)).all()):
        # deceased·key 둘 다 없음
        if not (r.key_person or "").strip():
            if r.funeral_hall or r.contact:
                continue
            raw = (r.raw_text or "").strip()
            if raw:
                parsed = parse_obituary(r.title or "", raw)
                if parsed and (parsed.deceased_name or parsed.key_person):
                    continue
            db.query(NotificationLog).filter(NotificationLog.obituary_id == r.id).delete(
                synchronize_session="fetch"
            )
            changes.append(f"품질 최저 삭제 id={r.id} (deceased·key 없음)")
            db.delete(r)
            continue
        # key 있지만 deceased 없음 + 본문에 부고 키워드 없음 → 복구 불가
        raw = (r.raw_text or "").strip()
        if not raw or len(raw) < 100:
            continue
        if any(kw in raw for kw in _obit_keywords):
            continue
        # 본문이 기자명/메뉴 등만 있음
        db.query(NotificationLog).filter(NotificationLog.obituary_id == r.id).delete(
            synchronize_session="fetch"
        )
        changes.append(f"품질 최저 삭제 id={r.id} (deceased 없음, 본문 미수집)")
        db.delete(r)
    db.flush()
    return changes


def run_quality_fixes(db: Session) -> list[str]:
    """품질 보정 단계 순차 실행."""
    all_changes = []
    for step in [
        step1_source_url_dedup,
        step2_fill_blank_fields,
        step3_remove_self_obituary,
        step4_fix_hall_mismatch,
        step5_fix_bad_org_pos,
        step6_unify_same_deceased,
        step7_remove_mismatched_multi,
        step8_remove_low_quality,
    ]:
        all_changes.extend(step(db))
    return all_changes
