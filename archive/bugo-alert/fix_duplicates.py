"""중복 제거 및 오파싱 수정 스크립트.

실행: python fix_duplicates.py

로직:
  1. 같은 source_url 중복 → 풍부한 데이터 가진 1건만 유지
  2. 주종석(id=22) 삭제 — 주수영(id=23)과 동일 부고(같은 고인·장례식장)
  3. 권봉금(id=21) — 본문에서 김영규 모친상으로 재파싱
  4. 윤호상(id=42,52) — 같은 URL 중복, 1건만 유지
  5. key_person == deceased_name 삭제 (같은 고인에 다른 key 있는 경우만)
  6. 같은 (deceased, key_person, funeral_hall) 중복 제거
  6b. 같은 (deceased, key_person) 중복 제거 — hall 표기 달라도 동일 부고면 1건만 유지
  7. 복수 부고 기사 장례식장 오매칭 보정
  8. org/pos 비정상 레코드 재파싱 보정
  9. 같은 고인 레코드의 장례식장·호실·연락처 통일
  10. deceased_name/key_person/funeral_hall/relationship 빈칸 보정 (재파싱)
  11. 품질 최저 레코드 삭제 (deceased·key 둘 다 없고 복구 불가 시)
"""

from __future__ import annotations

import re
from collections import defaultdict

from app.database import SessionLocal, init_db
from app.models import Obituary, NotificationLog
from app.crawler.parser import parse_obituary, parse_obituary_multi, _clean_funeral_hall, _get_block_containing_deceased

init_db()
db = SessionLocal()

changes = []


def _richness(obit: Obituary) -> int:
    """데이터 풍부도 점수."""
    return sum(
        1
        for f in ["key_person", "deceased_name", "funeral_hall", "organization"]
        if getattr(obit, f, None)
    )


def _richness_hall(obit: Obituary) -> int:
    """장례식장·호실·연락처 풍부도 점수 (통일 기준 선정용)."""
    base = sum(
        1 for f in ["funeral_hall", "room_number", "contact"] if getattr(obit, f, None)
    )
    # '장례식장' 포함 표기 우선 (연세대 세브란스병원 장례식장 > 신촌세브란스병원)
    hall = getattr(obit, "funeral_hall", None) or ""
    if "장례식장" in hall:
        base += 1
    return base


def _extract_composite_block_hall_contact(block: str) -> tuple[str | None, str | None]:
    """복수 부고 블록에서 장례식장·연락처 추출.

    '=6일 오전3시 신촌세브란스병원 발인 9일 (02)2227-7500' 형식.
    '신촌세브란스병원'은 '장례식장' 없이 쓴 경우도 처리.
    """
    # =N일 ... 뒤의 장소 (병원/의료원/장례식장 포함)
    hall_match = re.search(
        r"=\d+일[^=]*?"
        r"(?P<hall>[가-힣A-Za-z0-9\s]+(?:병원|의료원|장례식장|장[례레]식장))",
        block,
    )
    hall = hall_match.group("hall").strip() if hall_match else None
    if hall:
        hall = re.sub(r"^[\s=,]*\d*일?\s*(?:오[전후]\s*\d+시(?:\s*\d+분)?|오전|오후)?\s*", "", hall).strip()
        hall = _clean_funeral_hall(hall)
    # 전화번호
    phone_match = re.search(r"\(?\d{2,3}-\d{3,4}-\d{4}\)?", block)
    contact = phone_match.group(0).strip("()") if phone_match else None
    return (hall, contact)


def _get_block_for_key_person(raw_text: str, key_person: str) -> str | None:
    """raw에서 key_person이 포함된 ▲ 블록을 반환."""
    if not raw_text or not key_person:
        return None
    blocks = re.split(r"\n?[▲△◇◆]", raw_text)
    key_clean = key_person.replace(" ", "").strip()
    for b in blocks:
        if not b.strip():
            continue
        # 블록 내 이름(소속) 관계상 또는 이름씨 관계상 패턴에서 이름 추출
        for m in re.finditer(
            r"([가-힣]{2,5})\s*(?:\([^)]+\))?\s*[·\s]*씨?\s*[가-힣]+상", b
        ):
            name = m.group(1).strip()
            if name == key_clean or name.replace(" ", "") == key_clean:
                return b
        # 단순 이름 포함
        if key_clean in b.replace(" ", ""):
            return b
    return None


def _is_bad_org_pos(val: str | None) -> bool:
    """org/pos가 비정상 파싱인지 판별 (예: '씨(' 포함)."""
    if not val:
        return False
    return "씨(" in val or "pos=" in val or "(" in val[:3]


# 장례식장 동의어: 같은 장소를 가리키는 표기들 (더 풍부한 표기 우선)
_HALL_SYNONYM_GROUPS = [
    {"연세대 세브란스병원 장례식장", "연세대 세브란스병원", "신촌세브란스병원"},
]


def _hall_same_venue(a: str, b: str) -> bool:
    """두 장례식장 표기가 같은 장소인지."""
    if not a or not b:
        return False
    a, b = a.strip(), b.strip()
    for group in _HALL_SYNONYM_GROUPS:
        if a in group and b in group:
            return True
    return False


# 1. 같은 source_url 중복 → 1건만 유지
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
        changes.append(f"중복 삭제 id={r.id} (url 중복, id={keep.id} 유지)")
        db.delete(r)

db.flush()

# 2. 주종석(id=22) — 주수영(id=23)과 동일 부고
r22 = db.query(Obituary).filter(Obituary.id == 22).first()
r23 = db.query(Obituary).filter(Obituary.id == 23).first()
if r22 and r23 and r22.deceased_name == r23.deceased_name == "주종석":
    db.query(NotificationLog).filter(NotificationLog.obituary_id == 22).update(
        {"obituary_id": 23}, synchronize_session="fetch"
    )
    db.delete(r22)
    changes.append("중복 삭제 id=22 (주종석, 주수영 id=23과 동일 부고)")

# 3. 권봉금(id=21) — 본문에서 김영규 모친상으로 재파싱
r21 = db.query(Obituary).filter(Obituary.id == 21).first()
if r21 and r21.key_person == "권봉금":
    parsed = parse_obituary(r21.title, r21.raw_text or "")
    if parsed and parsed.key_person == "김영규":
        r21.key_person = parsed.key_person
        r21.organization = parsed.organization
        r21.position = parsed.position
        r21.relationship = parsed.relationship
        r21.deceased_name = parsed.deceased_name or r21.deceased_name
        changes.append(
            f"권봉금 id=21 수정: key_person=김영규, org={parsed.organization}, pos={parsed.position}, rel={parsed.relationship}"
        )

# 4. 윤호상 — key_person 보충 (같은 URL 중복은 1에서 처리됨)
for r in db.query(Obituary).filter(Obituary.deceased_name == "윤호상").all():
    if not r.key_person and r.title:
        parsed = parse_obituary(r.title, r.raw_text or "")
        if parsed and parsed.key_person:
            r.key_person = parsed.key_person
            r.organization = parsed.organization
            r.position = parsed.position
            r.relationship = parsed.relationship or "별세"
            changes.append(f"윤호상 id={r.id} 수정: key_person={parsed.key_person}")

db.flush()

# 10. deceased_name/key_person/funeral_hall/relationship 빈칸 보정 (5·6·6b·9 이전에 실행)
for r in db.query(Obituary).filter(Obituary.raw_text.isnot(None)).all():
    if not r.title:
        continue
    parsed = parse_obituary(r.title, r.raw_text or "")
    if not parsed:
        continue
    updated = []
    if not r.deceased_name and parsed.deceased_name:
        r.deceased_name = parsed.deceased_name
        updated.append("deceased_name")
    if not r.key_person and parsed.key_person:
        r.key_person = parsed.key_person
        updated.append("key_person")
    if not r.funeral_hall and parsed.funeral_hall:
        r.funeral_hall = parsed.funeral_hall
        updated.append("funeral_hall")
    if not r.room_number and parsed.room_number:
        r.room_number = parsed.room_number
        updated.append("room_number")
    if not r.relationship and parsed.relationship:
        r.relationship = parsed.relationship
        updated.append("relationship")
    if not r.contact and parsed.contact:
        r.contact = parsed.contact
        updated.append("contact")
    if updated:
        changes.append(f"빈칸 보정 id={r.id}: {', '.join(updated)}")

db.flush()

# 5. key_person == deceased_name 삭제 (같은 고인에 다른 key 있는 경우만)
by_deceased = defaultdict(list)
for r in db.query(Obituary).filter(Obituary.deceased_name.isnot(None)).all():
    by_deceased[r.deceased_name].append(r)

for deceased, rows in by_deceased.items():
    has_other_key = any(
        r.key_person and r.key_person != deceased for r in rows
    )
    if not has_other_key:
        continue
    for r in rows:
        if r.key_person == deceased:
            db.query(NotificationLog).filter(
                NotificationLog.obituary_id == r.id
            ).delete(synchronize_session="fetch")
            changes.append(
                f"중복 삭제 id={r.id} (key_person==deceased '{deceased}', 같은 고인에 다른 key 있음)"
            )
            db.delete(r)

db.flush()

# 6. 같은 (deceased, key_person, funeral_hall) 중복 제거
by_triple = defaultdict(list)
for r in db.query(Obituary).all():
    if r.deceased_name and r.key_person:
        key = (r.deceased_name, r.key_person, r.funeral_hall or "")
        by_triple[key].append(r)

for (deceased, kp, hall), rows in by_triple.items():
    if len(rows) <= 1:
        continue
    rows.sort(key=_richness, reverse=True)
    keep, *remove = rows
    for r in remove:
        db.query(NotificationLog).filter(NotificationLog.obituary_id == r.id).update(
            {"obituary_id": keep.id}, synchronize_session="fetch"
        )
        changes.append(
            f"중복 삭제 id={r.id} ({deceased}·{kp}·{hall or '(장례식장 없음)'}, id={keep.id} 유지)"
        )
        db.delete(r)

db.flush()

# 6b. 같은 (deceased, key_person) 중복 제거 — hall 표기 달라도 동일 부고면 1건만 유지
# 장례식장·호실·연락처가 풍부한 쪽을 유지 (대시보드 표시 품질 우선)
by_deceased_key = defaultdict(list)
for r in db.query(Obituary).all():
    if r.deceased_name and r.key_person:
        by_deceased_key[(r.deceased_name, r.key_person)].append(r)

for (deceased, kp), rows in by_deceased_key.items():
    if len(rows) <= 1:
        continue
    rows.sort(key=lambda r: (_richness_hall(r), _richness(r)), reverse=True)
    keep, *remove = rows
    for r in remove:
        db.query(NotificationLog).filter(NotificationLog.obituary_id == r.id).update(
            {"obituary_id": keep.id}, synchronize_session="fetch"
        )
        changes.append(
            f"중복 삭제 id={r.id} ({deceased}·{kp} 동일 부고, id={keep.id} 유지)"
        )
        db.delete(r)

db.flush()

# 7. 복수 부고 기사 장례식장 오매칭 보정
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
    # 현재 hall이 이 블록의 hall과 다르면 보정 (다른 블록 것을 잘못 가져온 경우)
    # 단, 같은 장소 동의어(연세대/신촌세브란스 등)면 덮어쓰지 않음
    # 현재 표기가 더 풍부하면(장례식장 포함) 덮어쓰지 않음
    current = (r.funeral_hall or "").strip()
    if current and hall and current != hall and not _hall_same_venue(current, hall):
        if "장례식장" in current and "장례식장" not in hall:
            continue  # 현재가 더 풍부한 표기면 유지
        r.funeral_hall = hall
        if contact:
            r.contact = contact
        changes.append(
            f"복수 부고 보정 id={r.id} ({r.key_person}): funeral_hall '{current}' → '{hall}'"
        )

db.flush()

# 8. org/pos 비정상 레코드 재파싱 보정
# key_person(소속 직급) 관계상 패턴으로 블록/본문에서 직접 추출 (parse_obituary는 복수 부고에서 잘못된 인물 추출 가능)
_RE_KEY_ORG_POS = re.compile(
    r"(?P<name>[가-힣]{2,5})\s*씨?\s*\((?P<affil>[^)]+)\)\s*[·\s]*(?P<rel>[가-힣]+상)"
)


def _extract_org_pos_for_key(text: str, key_person: str) -> tuple[str | None, str | None, str | None]:
    """text에서 key_person에 해당하는 org, pos, rel 추출."""
    if not key_person or not text:
        return (None, None, None)
    key_clean = key_person.replace(" ", "").strip()
    for m in _RE_KEY_ORG_POS.finditer(text):
        name = m.group("name").replace(" ", "").strip()
        if name != key_clean:
            continue
        affil = m.group("affil").strip()
        rel = m.group("rel")
        # affil 분리: "전 네슬레코리아 본부장" → org=네슬레코리아, pos=전 본부장
        # "전 헌법재판소장" → org=None, pos=전 헌법재판소장 (직급만 있는 경우)
        parts = affil.split()
        if len(parts) >= 3 and parts[0] in ("전", "前"):
            org = parts[1]
            pos = " ".join([parts[0]] + parts[2:])
        elif len(parts) == 2 and parts[0] in ("전", "前"):
            org = None
            pos = affil
        elif len(parts) >= 2:
            org = parts[0]
            pos = " ".join(parts[1:])
        else:
            org = None
            pos = affil
        return (org or None, pos or None, rel)
    return (None, None, None)


for r in db.query(Obituary).filter(Obituary.raw_text.isnot(None)).all():
    if not _is_bad_org_pos(r.organization) and not _is_bad_org_pos(r.position):
        continue
    raw = r.raw_text or ""
    # 복수 부고면 key_person 블록에서만 추출
    blocks = re.split(r"[▲△◇◆]", raw)
    if len([b for b in blocks if b.strip()]) >= 2:
        search_text = _get_block_for_key_person(raw, r.key_person or "") or raw
    else:
        search_text = raw
    org, pos, rel = _extract_org_pos_for_key(search_text, r.key_person or "")
    if org and not _is_bad_org_pos(org):
        r.organization = org
    if pos and not _is_bad_org_pos(pos):
        r.position = pos
    if rel:
        r.relationship = rel
    if org or pos or rel:
        changes.append(
            f"org/pos 보정 id={r.id} ({r.key_person}): org={r.organization}, pos={r.position}, rel={r.relationship}"
        )

db.flush()

# 9. 같은 고인 레코드의 장례식장·호실·연락처 통일
by_deceased_only = defaultdict(list)
for r in db.query(Obituary).filter(Obituary.deceased_name.isnot(None)).all():
    by_deceased_only[r.deceased_name].append(r)

for deceased, rows in by_deceased_only.items():
    if len(rows) < 2:
        continue
    # 가장 풍부한 hall/room/contact를 가진 레코드를 기준으로
    best = max(rows, key=_richness_hall)
    hall = best.funeral_hall
    room = best.room_number
    contact = best.contact
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
            changes.append(
                f"장례정보 통일 id={r.id} ({deceased}·{r.key_person}): {', '.join(updated)}"
            )

db.flush()

# 11a. 복수 부고 오매칭 삭제 — ▲ 블록 2개 이상일 때만, key_person이 해당 고인 블록에 없으면 삭제
rows_11a = db.query(Obituary).filter(
    Obituary.raw_text.isnot(None),
    Obituary.deceased_name.isnot(None),
    Obituary.key_person.isnot(None),
).all()
for r in list(rows_11a):
    raw = r.raw_text or ""
    blocks = re.split(r"\n?[▲△◇◆▶]", raw)
    if len([b for b in blocks if b.strip()]) < 2:
        continue  # 단일 부고 기사는 스킵
    block = _get_block_containing_deceased(raw, r.deceased_name or "")
    if block and r.key_person:
        kp_clean = r.key_person.replace(" ", "").strip()
        if kp_clean not in block.replace(" ", ""):
            db.query(NotificationLog).filter(NotificationLog.obituary_id == r.id).delete(
                synchronize_session="fetch"
            )
            changes.append(
                f"복수 부고 오매칭 삭제 id={r.id} ({r.deceased_name}·{r.key_person}, 다른 블록 인물)"
            )
            db.delete(r)

db.flush()

# 11. 품질 최저 레코드 삭제 — deceased·key 둘 다 없고 복구 불가 시에만
for r in list(db.query(Obituary).filter(
    Obituary.deceased_name.is_(None),
    Obituary.key_person.is_(None),
).all()):
    # funeral_hall·contact 있으면 유지 (재파싱 가능성)
    if r.funeral_hall or r.contact:
        continue
    raw = r.raw_text or ""
    if raw.strip():
        parsed = parse_obituary(r.title or "", raw)
        if parsed and (parsed.deceased_name or parsed.key_person):
            continue  # 재파싱으로 복구 가능하면 스킵 (10단계에서 이미 시도했으나 실패한 경우)
    # raw 없거나 재파싱으로도 deceased/key 추출 불가 → 삭제
    db.query(NotificationLog).filter(NotificationLog.obituary_id == r.id).delete(
        synchronize_session="fetch"
    )
    changes.append(f"품질 최저 삭제 id={r.id} (deceased·key 없음, 복구 불가)")
    db.delete(r)

db.commit()
db.close()

print("적용된 변경:")
for c in changes:
    print(f"  - {c}")
print(f"\n총 {len(changes)}건 변경 완료.")
