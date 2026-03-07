"""부고 기사에서 구조화된 정보를 추출한다.

핵심 원칙:
  1. 제목에서 key_person(핵심인물)을 추출 — 가장 신뢰할 수 있는 정보
  2. 본문의 ▲ 항목들은 한 건의 부고에 대한 관계자 나열 → 하나로 통합
  3. 제목에 [부고] 패턴이 없는 기사는 필터링
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedObituary:
    key_person: Optional[str] = None
    organization: Optional[str] = None
    position: Optional[str] = None
    deceased_name: Optional[str] = None
    deceased_age: Optional[str] = None
    relationship: Optional[str] = None
    related_persons: Optional[str] = None
    funeral_hall: Optional[str] = None
    room_number: Optional[str] = None
    funeral_date: Optional[str] = None
    funeral_time: Optional[str] = None
    contact: Optional[str] = None
    remarks: Optional[str] = None


# ---------------------------------------------------------------------------
# 전처리
# ---------------------------------------------------------------------------

def _clean_text(text: str) -> str:
    """HTML 엔티티 디코딩 + 불필요한 공백 정리."""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _strip_suffix(name: str) -> str:
    """이름 뒤의 '씨', '시', 공백 제거."""
    if not name:
        return name
    return re.sub(r"[\s]*씨$", "", name).strip()


def _take_first_name(name: str) -> str:
    """'이창연,이승연' → '이창연' (쉼표로 구분된 복수 이름 시 첫 번째만)."""
    if not name or "," not in name:
        return name
    return name.split(",")[0].strip()


# ---------------------------------------------------------------------------
# 부고 기사 여부 판별
# ---------------------------------------------------------------------------

_RE_BUGO_TITLE = re.compile(
    r"[\[<\(【〔]?\s*부고\s*[\]>\)】〕]|부고종합|부고\s*[·\-]"
)

_RE_RELATION_IN_TITLE = re.compile(r"씨?\s*(?:모친|부친|장인|장모|시부|시모|조부|조모|외조부|외조모|남편|부인|빙모|빙부)상")


def is_obituary_article(title: str) -> bool:
    """제목에서 부고 기사 여부를 판별한다."""
    title = _clean_text(title)
    if _RE_BUGO_TITLE.search(title):
        if _RE_RELATION_IN_TITLE.search(title) or "별세" in title:
            return True
        # [부고] 패턴은 있지만 관계상/별세가 없으면 제목 형식 추가 확인
        if re.search(r"[\[<\(【〔]\s*부고\s*[\]>\)】〕]", title):
            return True
    return False


# ---------------------------------------------------------------------------
# 제목 파싱 — key_person 추출 (가장 중요)
# ---------------------------------------------------------------------------

# 패턴1: [부고] 이름(소속 직급)씨 관계상
_RE_TITLE_P1 = re.compile(
    r"[\[<\(【〔]\s*부고\s*[\]>\)】〕]\s*"
    r"(?P<name>[가-힣]{2,5})\s*"
    r"\((?P<affil>[^)]+)\)\s*씨?\s*"
    r"(?P<rel>[가-힣]+상)"
)

# 패턴2: [부고] 이름 씨(소속 직급) 관계상 (씨가 괄호 앞, 씨 앞 공백 허용)
_RE_TITLE_P2 = re.compile(
    r"[\[<\(【〔]\s*부고\s*[\]>\)】〕]\s*"
    r"(?P<name>[가-힣]{2,5})\s*씨?\s*"
    r"\((?P<affil>[^)]+)\)\s*"
    r"(?P<rel>[가-힣]+상)"
)

# 패턴3: [부고] 소속 이름 직급 관계상 (괄호 없음)
_RE_TITLE_P3 = re.compile(
    r"[\[<\(【〔]\s*부고\s*[\]>\)】〕]\s*"
    r"(?P<affil>[가-힣A-Za-z0-9㈜·\s]+?)\s+"
    r"(?P<name>[가-힣]{2,5})\s+"
    r"(?P<position>[가-힣A-Za-z·]+(?:장|부장|국장|기자|PD|사원|대표|이사|위원|교수|총장|부총장|법인장|전무|상무|센터장|본부장|부국장|팀장|수석부사장|부구청장|부회장|회장|사장|부사장))\s+"
    r"(?P<rel>[가-힣]+상)\s*(?:등)?"
)

# 패턴3b: [부고]소속 이름 ...rest... 관계상 (]바로 뒤 소속, 공백 없이도 매칭)
_RE_TITLE_P3b = re.compile(
    r"[\[<\(【〔]\s*부고\s*[\]>\)】〕]\s*"
    r"(?P<affil>[가-힣A-Za-z0-9㈜·]+)\s+"
    r"(?P<name>[가-힣]{2,5})\s+"
    r"(?P<rest>.+?)\s+"
    r"(?P<rel>[가-힣]+상)"
)

# 패턴4: [부고] 이름(소속 직급) 관계상 (씨 없음)
_RE_TITLE_P4 = re.compile(
    r"[\[<\(【〔]\s*부고\s*[\]>\)】〕]\s*"
    r"(?P<name>[가-힣]{2,5})\s*"
    r"\((?P<affil>[^)]+)\)\s+"
    r"(?P<rel>[가-힣]+상)"
)

# 패턴5: [부고종합·날짜] 이름 소속 직급 관계상 등
_RE_TITLE_P5 = re.compile(
    r"[\[<\(【〔]\s*부고(?:종합)?[·\s]*[^】〕\]>\)]*[\]>\)】〕]\s*"
    r"(?P<name>[가-힣]{2,5})\s+"
    r"(?P<affil>[가-힣A-Za-z0-9㈜·\s]+?)\s+"
    r"(?P<position>[가-힣A-Za-z·]+(?:장|부장|국장|기자|대표|이사|위원|교수|총장|전무|상무|법인장|센터장|본부장|부국장|팀장|수석부사장|부구청장|부회장|회장|사장|부사장))\s+"
    r"(?P<rel>[가-힣]+상)\s*(?:등)?"
)

# 패턴5b: [부고종합] 이름(소속 직급) 관계상 등
_RE_TITLE_P5b = re.compile(
    r"[\[<\(【〔]\s*부고(?:종합)?[·\s]*[^】〕\]>\)]*[\]>\)】〕]\s*"
    r"(?P<name>[가-힣]{2,5})\s*"
    r"\((?P<affil>[^)]+)\)\s*"
    r"(?P<rel>[가-힣]+상)"
)


def _split_org_position(affiliation: str) -> tuple[str, str]:
    """'삼성전자 부사장' → ('삼성전자', '부사장')
       '전 헌법재판소장' → ('헌법재판소', '전 소장')  # 전 prefix 처리
       '오늘경제 대표, 前 시민의소리 대표' → 첫 번째 소속만 사용
    """
    affiliation = affiliation.strip()
    # 쉼표·전/前로 구분된 복수 소속 — 첫 번째만 사용
    if re.search(r"[,，]\s*(?:전|前)\s+", affiliation):
        affiliation = re.split(r"\s*[,，]\s*(?:전|前)\s+", affiliation)[0].strip()

    # "전 OOO" 패턴
    m_former = re.match(r"^전\s+(.+)$", affiliation)
    if m_former:
        inner = m_former.group(1)
        parts = inner.rsplit(maxsplit=1)
        if len(parts) == 2:
            return parts[0].strip(), f"전 {parts[1].strip()}"
        return "", f"전 {inner.strip()}"

    # "OO대학교 OO부 교수" 같은 긴 소속
    parts = affiliation.rsplit(maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return affiliation.strip(), ""


_KNOWN_POSITIONS = re.compile(
    r"^(?:(?:전\s+)?(?:안전총괄\s+)?(?:대표이사|대표|이사|전무|상무|부사장|사장|회장|부회장|"
    r"부장|국장|기자|PD|사원|위원|교수|총장|부총장|법인장|센터장|본부장|부국장|팀장|"
    r"수석부사장|부구청장|교육·연구부총장|그룹장).*)$"
)


def _split_rest_to_org_pos(rest: str) -> tuple[str, str]:
    """'한화오션 안전총괄 전무' → ('한화오션', '안전총괄 전무')
       '핀포인트뉴스 대표' → ('핀포인트뉴스', '대표')
    """
    parts = rest.split()
    if not parts:
        return "", ""

    # 뒤에서부터 직급에 해당하는 부분을 찾는다
    for i in range(len(parts)):
        candidate = " ".join(parts[i:])
        if _KNOWN_POSITIONS.match(candidate):
            org = " ".join(parts[:i]).strip()
            return org, candidate
        # 마지막 단어만 직급인지도 체크
        if _KNOWN_POSITIONS.match(parts[i]):
            org = " ".join(parts[:i]).strip()
            pos = " ".join(parts[i:]).strip()
            return org, pos

    return rest, ""


def parse_title(title: str) -> ParsedObituary:
    """제목에서 핵심인물(key_person), 소속, 직급, 관계를 추출한다."""
    title = _clean_text(title)
    result = ParsedObituary()

    for pattern in [_RE_TITLE_P1, _RE_TITLE_P2, _RE_TITLE_P4]:
        m = pattern.search(title)
        if m:
            result.key_person = _take_first_name(_strip_suffix(m.group("name")))
            affil = m.group("affil").strip().lstrip("(")
            org, pos = _split_org_position(affil)
            result.organization = org or None
            result.position = pos or None
            result.relationship = m.group("rel")
            return result

    for pattern in [_RE_TITLE_P3, _RE_TITLE_P5]:
        m = pattern.search(title)
        if m:
            result.key_person = _take_first_name(_strip_suffix(m.group("name")))
            result.organization = m.group("affil").strip() or None
            result.position = m.group("position").strip() or None
            result.relationship = m.group("rel")
            return result

    for pattern in [_RE_TITLE_P5b]:
        m = pattern.search(title)
        if m:
            result.key_person = _take_first_name(_strip_suffix(m.group("name")))
            affil = m.group("affil").strip()
            org, pos = _split_org_position(affil)
            result.organization = org or None
            result.position = pos or None
            result.relationship = m.group("rel")
            return result

    # 패턴 FALLBACK: [부고*] 이름 ...rest... 관계상 등? — rest에서 소속/직급 분리
    m_fb = re.search(
        r"[\[<\(【〔]\s*부고(?:종합)?[·\s]*[^】〕\]>\)]*[\]>\)】〕]\s*"
        r"(?P<name>[가-힣]{2,5})\s+"
        r"(?P<rest>.+?)\s+"
        r"(?P<rel>[가-힣]+상)\s*(?:등)?$",
        title.strip(),
    )
    if m_fb:
        rest = m_fb.group("rest").strip()
        org, pos = _split_rest_to_org_pos(rest)
        result.key_person = _take_first_name(_strip_suffix(m_fb.group("name")))
        result.organization = org or None
        result.position = pos or None
        result.relationship = m_fb.group("rel")
        return result

    # P3b: [부고]소속 이름 rest 관계상 (소속이 먼저, 이름 2-5자)
    m_3b = _RE_TITLE_P3b.search(title)
    if m_3b:
        rest = m_3b.group("rest").strip()
        _, pos = _split_rest_to_org_pos(rest)
        result.key_person = _take_first_name(_strip_suffix(m_3b.group("name")))
        result.organization = m_3b.group("affil").strip() or None
        result.position = pos or rest or None
        result.relationship = m_3b.group("rel")
        return result

    # 패턴6: [부고] 이름(소속)씨 별세 — key_person이 곧 고인
    m = re.search(
        r"[\[<\(]\s*부고\s*[\]>\)]\s*(?P<name>[가-힣]{2,5})\s*\((?P<affil>[^)]+)\)\s*씨?\s*별세",
        title,
    )
    if m:
        result.key_person = _take_first_name(_strip_suffix(m.group("name")))
        affil = m.group("affil").strip()
        org, pos = _split_org_position(affil)
        result.organization = org or None
        result.position = pos or None
        result.relationship = "별세"
        return result

    # 패턴6b: [부고] 이름 씨 별세 (소속 없음)
    m = re.search(r"[\[<\(]\s*부고\s*[\]>\)]\s*(?P<name>[가-힣]{2,5})\s*씨?\s*별세", title)
    if m:
        result.key_person = _take_first_name(_strip_suffix(m.group("name")))
        result.relationship = "별세"
        return result

    # 패턴7: [부고] 이름씨 관계상 (소속 없음)
    m = re.search(
        r"[\[<\(]\s*부고\s*[\]>\)]\s*"
        r"(?P<name>[가-힣]{2,5})\s*씨?\s+"
        r"(?P<rel>[가-힣]+상)",
        title,
    )
    if m:
        result.key_person = _take_first_name(_strip_suffix(m.group("name")))
        result.relationship = m.group("rel")
        return result

    # 패턴7b: [부고] 이름,이름 씨 관계상 (복수 이름, 소속 없음)
    m = re.search(
        r"[\[<\(]\s*부고\s*[\]>\)]\s*"
        r"(?P<name>[가-힣]{2,5}(?:,[가-힣]{2,5})+)\s*씨?\s+"
        r"(?P<rel>[가-힣]+상)",
        title,
    )
    if m:
        result.key_person = _take_first_name(_strip_suffix(m.group("name")))
        result.relationship = m.group("rel")
        return result

    # 패턴8: 이름(소속)·이름(소속) 씨 관계상 (복수 인물)
    m = re.search(
        r"(?P<name>[가-힣]{2,5})\s*\((?P<affil>[^)]+)\)[·\s]*(?:[가-힣]{2,5}\s*\([^)]+\)[·\s]*)*씨?\s*(?P<rel>[가-힣]+상)",
        title,
    )
    if m:
        result.key_person = _take_first_name(_strip_suffix(m.group("name")))
        affil = m.group("affil").strip()
        org, pos = _split_org_position(affil)
        result.organization = org or None
        result.position = pos or None
        result.relationship = m.group("rel")
        return result

    # 패턴9: [부고] 이름씨 (이름만 있는 경우)
    m = re.search(
        r"[\[<\(]\s*부고\s*[\]>\)]\s*(?P<name>[가-힣]{2,5})\s*씨?$",
        title.strip(),
    )
    if m:
        result.key_person = _take_first_name(_strip_suffix(m.group("name")))
        return result

    return result


# ---------------------------------------------------------------------------
# 본문 파싱 — 고인/장례식장/발인/연락처/관계자 추출 (모든 ▲를 하나로 통합)
# ---------------------------------------------------------------------------

# 고인: "이름(향년 N세) 씨 별세" 또는 "이름(xxx·향년 N세)씨 별세"
_RE_DECEASED = re.compile(
    r"(?P<name>[가-힣]{2,5})\s*\(\s*(?:[^)]*[·\s]+)?향년\s*(?:만\s*)?(?P<age>\d+세?)\s*\)\s*씨?\s*별세"
)
_RE_DECEASED_SIMPLE = re.compile(
    r"(?P<name>[가-힣]{2,5})\s*씨?\s*별세"
)
# 관계(고인씨·나이)상 — 모친(김용연씨·97)상, 부친(홍길동씨·80)상
_RE_DECEASED_REL = re.compile(
    r"(?:모친|부친|장인|장모|시부|시모|조부|조모|외조부|외조모|남편|부인|빙모|빙부)\s*"
    r"\(\s*(?P<name>[가-힣]{2,5})\s*씨\s*[··]\s*(?P<age>\d+)\s*\)\s*상"
)
# 이름씨(나이) N일 별세 — 윤태호씨(84) 27일 별세
_RE_DECEASED_DAY = re.compile(
    r"(?P<name>[가-힣]{2,5})\s*씨\s*\(\s*(?P<age>\d+)\s*\)\s*\d{1,2}\s*일\s*별세"
)
# ▲ 고인 : 이영재 또는 고인 : 이영재
_RE_DECEASED_LABEL = re.compile(
    r"[▲△]\s*고인\s*[=:]\s*(?P<name>[가-힣]{2,5})"
)

# 장례식장: '장레식장' 오타도 허용
_RE_FUNERAL_HALL = re.compile(
    r"(?P<hall>[가-힣A-Za-z\s]{2,}(?:병원|의료원|대학교?|센터|시민|농협|공원|빛고을|메모리얼|종합)\s*장[례레]식장|"
    r"[가-힣A-Za-z]+장[례레]식장)\s*"
    r"(?P<room>(?:특?\d+호실|[가-힣]+\d*호실|VIP\s*\d*호?|특실|\d+호))?"
)
# 빈소: / △빈소= 뒤의 장례식장 (본문에서 별도 검색용)
_RE_BINSO_PREFIX = re.compile(
    r"(?:빈소|△빈소)\s*[=:]\s*([^▲△]+?)(?=[▲△]|$)"
)

# 발인: "발인 3월 9일", "△발인=3월2일", "발인: 3월 1일", "▲ 발인 : 2026년 3월 1일"
# (월) 등 중간 괄호 허용, 2026년 등 연도 허용
_RE_FUNERAL_DATE = re.compile(
    r"발인\s*[=:]?\s*"
    r"(?:(?P<year>\d{4})\s*년\s*)?"
    r"(?:(?P<month>\d{1,2})월\s*)?"
    r"(?P<date>\d{1,2}일)?"
    r"\s*(?:\([^)]*\))?\s*"
    r"(?P<time>오[전후]\s*\d{1,2}시(?:\s*\d+분)?)?",
)

_RE_PHONE = re.compile(r"\d{2,3}-\d{3,4}-\d{4}")

# 관계자: 이름(소속 직급)씨 관계상 또는 이름씨 관계상
_RE_PERSON_WITH_ORG = re.compile(
    r"(?P<name>[가-힣]{2,5})\s*\((?P<org>[^)]+)\)\s*[·\s]*씨?\s*(?P<rel>[가-힣]+상)"
)
_RE_PERSON_SIMPLE = re.compile(
    r"(?P<name>[가-힣]{2,5})씨\s*(?P<rel>[가-힣]+상)"
)


def _extract_related_persons(text: str) -> list[str]:
    """본문에서 관계자 목록을 추출한다."""
    persons = []
    for m in _RE_PERSON_WITH_ORG.finditer(text):
        name = _strip_suffix(m.group("name"))
        org = m.group("org").strip()
        rel = m.group("rel")
        persons.append(f"{name}({org}) {rel}")

    for m in _RE_PERSON_SIMPLE.finditer(text):
        name = _strip_suffix(m.group("name"))
        rel = m.group("rel")
        entry = f"{name} {rel}"
        if entry not in " ".join(persons):
            persons.append(entry)

    return persons


def _clean_funeral_hall(hall: str) -> str:
    """장례식장 이름 앞뒤 쓰레기 문자 제거."""
    hall = re.sub(r"^[\s=,]*(?:일|분|시|오전|오후|빈소)+\s*", "", hall)
    hall = re.sub(r"^[\s=,]+", "", hall)
    return hall.strip()


def parse_body(body: str) -> dict:
    """본문 전체를 하나의 부고로 통합 파싱한다."""
    body = _clean_text(body)
    result = {}

    # 고인 (여러 패턴 순차 시도)
    dm = _RE_DECEASED.search(body)
    if dm:
        result["deceased_name"] = _strip_suffix(dm.group("name"))
        result["deceased_age"] = dm.group("age")
    else:
        dm_simple = _RE_DECEASED_SIMPLE.search(body)
        if dm_simple:
            result["deceased_name"] = _strip_suffix(dm_simple.group("name"))
        else:
            dm_rel = _RE_DECEASED_REL.search(body)
            if dm_rel:
                result["deceased_name"] = _strip_suffix(dm_rel.group("name"))
                result["deceased_age"] = dm_rel.group("age") + "세"
            else:
                dm_day = _RE_DECEASED_DAY.search(body)
                if dm_day:
                    result["deceased_name"] = _strip_suffix(dm_day.group("name"))
                    result["deceased_age"] = dm_day.group("age") + "세"
                else:
                    dm_label = _RE_DECEASED_LABEL.search(body)
                    if dm_label:
                        result["deceased_name"] = _strip_suffix(dm_label.group("name"))

    # 장례식장 + 호실
    hm = _RE_FUNERAL_HALL.search(body)
    if hm:
        hall = _clean_funeral_hall(hm.group("hall"))
        if hall:
            result["funeral_hall"] = hall
        room = (hm.group("room") or "").strip()
        if room:
            result["room_number"] = room
    else:
        # 빈소: / △빈소= 블록에서 재검색
        for m in _RE_BINSO_PREFIX.finditer(body):
            block = m.group(1)
            hm2 = _RE_FUNERAL_HALL.search(block)
            if hm2:
                hall = _clean_funeral_hall(hm2.group("hall"))
                if hall:
                    result["funeral_hall"] = hall
                room = (hm2.group("room") or "").strip()
                if room:
                    result["room_number"] = room
                break

    # 발인
    fm = _RE_FUNERAL_DATE.search(body)
    if fm:
        year = (fm.group("year") or "").strip()
        month = (fm.group("month") or "").strip()
        d = (fm.group("date") or "").strip()
        t = (fm.group("time") or "").strip()
        if d:
            parts = []
            if year:
                parts.append(f"{year}년")
            if month:
                parts.append(f"{month}월")
            parts.append(d)
            result["funeral_date"] = " ".join(parts)
        if t:
            result["funeral_time"] = t

    # 연락처
    phones = _RE_PHONE.findall(body)
    if phones:
        result["contact"] = phones[0]

    # 관계자 목록
    persons = _extract_related_persons(body)
    if persons:
        result["related_persons"] = " / ".join(persons)

    return result


# ---------------------------------------------------------------------------
# 통합 파싱
# ---------------------------------------------------------------------------

def parse_obituary(title: str, body: str) -> ParsedObituary | None:
    """제목+본문을 종합하여 하나의 ParsedObituary를 반환한다.
    부고가 아닌 기사면 None을 반환."""
    title = _clean_text(title)

    if not is_obituary_article(title):
        return None

    result = parse_title(title)
    body_info = parse_body(body) if body else {}

    # 본문 정보로 빈 필드 보충
    if not result.deceased_name:
        result.deceased_name = body_info.get("deceased_name")
    if not result.deceased_age:
        result.deceased_age = body_info.get("deceased_age")
    if not result.funeral_hall:
        result.funeral_hall = body_info.get("funeral_hall")
    if not result.room_number:
        result.room_number = body_info.get("room_number")
    if not result.funeral_date:
        result.funeral_date = body_info.get("funeral_date")
    if not result.funeral_time:
        result.funeral_time = body_info.get("funeral_time")
    if not result.contact:
        result.contact = body_info.get("contact")
    if not result.related_persons:
        result.related_persons = body_info.get("related_persons")

    return result


def _normalize_dedup(val: str | None) -> str:
    """중복 제거 키용 정규화: 공백 제거, '씨' 접미사 제거."""
    if not val:
        return ""
    val = val.strip()
    val = re.sub(r"\s+", "", val)
    val = re.sub(r"씨$", "", val)
    return val


def make_dedup_key(parsed: ParsedObituary) -> str | None:
    """중복 제거용 키를 생성한다. key_person + relationship 만 사용.

    deceased_name 은 기사마다 파싱 성공/실패가 달라
    같은 부고에 다른 키가 생성되는 문제를 일으키므로 제외한다.
    """
    kp = _normalize_dedup(parsed.key_person)
    rel = _normalize_dedup(parsed.relationship)
    if not kp:
        return None
    return f"{kp}|{rel}"
