"""부고 기사 본문에서 구조화된 정보를 추출한다.

일반적인 부고 기사 형식:
  제목: [부고] 이름(소속 직급) 씨 관계상
  본문: ▲고인명(향년 만 NN세)씨 별세, 누구씨 관계상, ... =날짜,
        OO병원 장례식장 N호실, 발인 N일 오전/오후 N시. 전화번호
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedObituary:
    deceased_name: Optional[str] = None
    age: Optional[str] = None
    organization: Optional[str] = None
    position: Optional[str] = None
    relationship: Optional[str] = None
    mourner_name: Optional[str] = None
    funeral_hall: Optional[str] = None
    room_number: Optional[str] = None
    funeral_date: Optional[str] = None
    funeral_time: Optional[str] = None
    contact: Optional[str] = None
    remarks: Optional[str] = None


# ---------------------------------------------------------------------------
# 정규식 패턴
# ---------------------------------------------------------------------------

# 제목: [부고] 홍길동(삼성전자 부사장) 씨 장인상
_RE_TITLE = re.compile(
    r"\[부고\]\s*(?P<name>[가-힣]{2,5})"
    r"\((?P<affiliation>[^)]+)\)"
    r"\s*씨\s*(?P<relation>[가-힣]+상)",
)

# 제목 변형: [부고] 홍길동(삼성전자 부사장)씨 장인상 (공백 없음)
_RE_TITLE_ALT = re.compile(
    r"\[부고\]\s*(?P<name>[가-힣]{2,5})"
    r"\((?P<affiliation>[^)]+)\)씨\s*(?P<relation>[가-힣]+상)",
)

# 본문: ▲ 또는 △ 로 시작하는 개별 부고 항목
_RE_ENTRY_SPLIT = re.compile(r"[▲△]")

# 고인: 이효원(향년 만 88세)씨 별세
_RE_DECEASED = re.compile(
    r"(?P<name>[가-힣]{2,5})\(향년\s*(?:만\s*)?(?P<age>\d+세?)\)씨?\s*별세"
)

# 이름(소속 직급)씨 관계상
_RE_PERSON_ORG = re.compile(
    r"(?P<name>[가-힣]{2,5})\((?P<org>[^)]+)\)[\s·]*씨?\s*(?P<relation>[가-힣]+상)"
)

# 이름씨 관계상 (소속 없음)
_RE_PERSON_SIMPLE = re.compile(
    r"(?P<name>[가-힣]{2,5})씨\s*(?P<relation>[가-힣]+상)"
)

# 장례식장 + 호실
_RE_FUNERAL_HALL = re.compile(
    r"(?P<hall>[가-힣A-Za-z\s]+(?:병원|의료원|대학교?|센터)?[\s]*장례식장)\s*"
    r"(?P<room>(?:특?\d+호실|[가-힣]+\d*호실|VIP\s*\d*호?))?",
)

# 발인
_RE_FUNERAL_DATE = re.compile(
    r"발인\s*(?P<date>\d{1,2}일)?\s*(?P<time>오[전후]\s*\d{1,2}시)?",
)

# 전화번호
_RE_PHONE = re.compile(r"\d{2,3}-\d{3,4}-\d{4}")


def _split_org_position(affiliation: str) -> tuple[str, str]:
    """'삼성전자 부사장' → ('삼성전자', '부사장')"""
    parts = affiliation.rsplit(maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return affiliation.strip(), ""


def parse_title(title: str) -> ParsedObituary:
    result = ParsedObituary()
    m = _RE_TITLE.search(title) or _RE_TITLE_ALT.search(title)
    if m:
        result.mourner_name = m.group("name")
        org, pos = _split_org_position(m.group("affiliation"))
        result.organization = org
        result.position = pos
        result.relationship = m.group("relation")
    return result


def parse_body(body: str) -> list[ParsedObituary]:
    """본문에서 하나 이상의 부고 정보를 추출한다."""
    entries = _RE_ENTRY_SPLIT.split(body)
    if len(entries) <= 1:
        entries = [body]

    results: list[ParsedObituary] = []

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        p = ParsedObituary()

        dm = _RE_DECEASED.search(entry)
        if dm:
            p.deceased_name = dm.group("name")
            p.age = dm.group("age")

        persons = _RE_PERSON_ORG.findall(entry)
        if persons:
            first = persons[0]
            if not p.deceased_name:
                p.mourner_name = first[0]
            p.organization = p.organization or first[1]
            org, pos = _split_org_position(first[1])
            p.organization = org
            p.position = pos
            p.relationship = p.relationship or first[2]

        if not p.relationship:
            sm = _RE_PERSON_SIMPLE.search(entry)
            if sm:
                p.relationship = sm.group("relation")
                if not p.mourner_name:
                    p.mourner_name = sm.group("name")

        hm = _RE_FUNERAL_HALL.search(entry)
        if hm:
            p.funeral_hall = hm.group("hall").strip()
            p.room_number = (hm.group("room") or "").strip() or None

        fm = _RE_FUNERAL_DATE.search(entry)
        if fm:
            p.funeral_date = (fm.group("date") or "").strip() or None
            p.funeral_time = (fm.group("time") or "").strip() or None

        phones = _RE_PHONE.findall(entry)
        if phones:
            p.contact = phones[0]

        if p.deceased_name or p.mourner_name or p.funeral_hall:
            results.append(p)

    return results


def parse_obituary(title: str, body: str) -> list[ParsedObituary]:
    """제목+본문을 종합하여 파싱 결과를 반환한다."""
    title_info = parse_title(title)
    body_results = parse_body(body)

    if not body_results:
        if title_info.mourner_name or title_info.organization:
            return [title_info]
        return []

    for result in body_results:
        # 제목에서 추출한 상주 소속/직급이 가장 정확하므로 우선 적용
        if title_info.mourner_name:
            result.mourner_name = result.mourner_name or title_info.mourner_name
            if title_info.organization:
                result.organization = title_info.organization
            if title_info.position:
                result.position = title_info.position
        else:
            if not result.organization and title_info.organization:
                result.organization = title_info.organization
            if not result.position and title_info.position:
                result.position = title_info.position
        if not result.relationship and title_info.relationship:
            result.relationship = title_info.relationship

    return body_results
