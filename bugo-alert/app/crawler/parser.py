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
from datetime import datetime
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
    """이름 뒤의 '씨', '님', '시', 공백 제거."""
    if not name:
        return name
    name = re.sub(r"[\s]*씨$", "", name).strip()
    name = re.sub(r"[\s]*님$", "", name).strip()
    return name


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

    # "전/前 OOO" 패턴
    m_former = re.match(r"^(?:전|前)\s+(.+)$", affiliation)
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
    r"부장|국장|기자|PD|사원|위원|교수|총장|부총장|법인장|센터장|본부장|부국장|팀장|초대단장|단장|"
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


# 패턴: 이름 소속 직급 별세[부고] — 신순심 리틀엔젤스 초대단장 별세[부고]
_RE_TITLE_STARSE = re.compile(
    r"(?P<name>[가-힣]{2,5})\s+(?P<rest>.+?)\s+별세\s*[\[<\(【〔]?\s*부고\s*[\]>\)】〕]?$"
)
# 패턴: [부고] A씨 남편(B 소속)상 — 고인=A, key_person=B
_RE_TITLE_DECEASED_SPOUSE = re.compile(
    r"[\[<\(【〔]\s*부고\s*[\]>\)】〕]\s*"
    r"(?P<deceased>[가-힣]{2,5})\s*씨\s+"
    r"(?P<rel>남편|부인)\s*\(\s*(?P<name>[가-힣]{2,5})\s*(?P<affil>[^)]*)\)\s*상"
)


def parse_title(title: str) -> ParsedObituary:
    """제목에서 핵심인물(key_person), 소속, 직급, 관계를 추출한다."""
    title = _clean_text(title)
    result = ParsedObituary()

    # [부고] A씨 남편(B)상 — 고인=A, key_person=B
    m_spouse = _RE_TITLE_DECEASED_SPOUSE.search(title)
    if m_spouse:
        result.deceased_name = _strip_suffix(m_spouse.group("deceased"))
        result.key_person = _take_first_name(_strip_suffix(m_spouse.group("name")))
        result.relationship = m_spouse.group("rel") + "상"
        affil = (m_spouse.group("affil") or "").strip()
        if affil:
            org, pos = _split_rest_to_org_pos(affil)
            result.organization = org or None
            result.position = pos or None
        return result

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

    # 패턴6a: 이름 소속 직급 별세[부고] — 신순심 리틀엔젤스 초대단장 별세[부고]
    # key_person=고인 본인 → 본인상
    m_starse = _RE_TITLE_STARSE.search(title.strip())
    if m_starse:
        result.key_person = _take_first_name(_strip_suffix(m_starse.group("name")))
        rest = m_starse.group("rest").strip()
        org, pos = _split_rest_to_org_pos(rest)
        result.organization = org or None
        result.position = pos or None
        result.relationship = "본인상"
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
        result.relationship = "본인상"
        return result

    # 패턴6b: [부고] 이름 씨 별세 (소속 없음)
    m = re.search(r"[\[<\(]\s*부고\s*[\]>\)]\s*(?P<name>[가-힣]{2,5})\s*씨?\s*별세", title)
    if m:
        result.key_person = _take_first_name(_strip_suffix(m.group("name")))
        result.relationship = "본인상"
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
# 관계(고인씨·나이)상 — 모친(김용연씨·97)상, 부친(홍길동씨·64세)상
_RE_DECEASED_REL = re.compile(
    r"(?:모친|부친|장인|장모|시부|시모|조부|조모|외조부|외조모|남편|부인|빙모|빙부)\s*"
    r"\(\s*(?P<name>[가-힣]{2,5})\s*씨\s*[·\-]\s*(?P<age>\d+세?)\s*\)\s*상"
)
# 관계(이름·나이) — 씨 없음: 조모(장경남·91세)
_RE_DECEASED_REL_NO_SSI = re.compile(
    r"(?:모친|부친|장인|장모|시부|시모|조부|조모|외조부|외조모)\s*"
    r"\(\s*(?P<name>[가-힣]{2,5})\s*[·\-]\s*(?P<age>\d+세?)\s*\)"
)
# 관계(이름씨)상 — 나이 없음: 부친(조창구씨)상
_RE_DECEASED_REL_SSI_ONLY = re.compile(
    r"(?:모친|부친|장인|장모|시부|시모|조부|조모|외조부|외조모|남편|부인|빙모|빙부)\s*"
    r"\(\s*(?P<name>[가-힣]{2,5})\s*씨\s*\)\s*상"
)
# 이름 ... N세의 나이로 별세했다 — 신순심 리틀엔젤스예술단 초대 단장이 지난 4일 89세의 나이로 별세했다
# (_RE_DECEASED_SIMPLE보다 먼저 적용해 '나이로 별세' 오매칭 방지)
_RE_DECEASED_NAIRO = re.compile(
    r"(?P<name>[가-힣]{2,5})\s+[^.]*?(?P<age>\d+세?)\s*의\s*나이로\s*별세했다"
)
# 이름(년도~년도) ... 향년 N세로 별세했다 — 황재형(1952~2026) 화백이 ... 향년 74세로 별세했다
# (_RE_DECEASED_SIMPLE '세로 별세' 오매칭 방지, 괄호 안 년도로 실제 고인만 매칭)
_RE_DECEASED_HYANGNYON_RO = re.compile(
    r"(?P<name>[가-힣]{2,5})\s*\(\s*\d{4}\s*~?\s*\d{4}\s*\)\s*[^.]*?향년\s*(?P<age>\d+세?)\s*로\s*별세했다"
)
# 이름씨(나이) N일 별세 — 윤태호씨(84) 27일 별세
_RE_DECEASED_DAY = re.compile(
    r"(?P<name>[가-힣]{2,5})\s*씨\s*\(\s*(?P<age>\d+)\s*\)\s*\d{1,2}\s*일\s*별세"
)
# ▲ 고인 : 이영재 또는 고인 : 이영재
_RE_DECEASED_LABEL = re.compile(
    r"[▲△]\s*고인\s*[=:]\s*(?P<name>[가-힣]{2,5})"
)
# ▲ 이름 님 별세
_RE_DECEASED_NIM_STAR = re.compile(
    r"[▲△]\s*(?P<name>[가-힣]{2,5})\s*님\s*별세"
)
# ■ 이름 씨(소속) 별세 — 괄호에 향년 없이 소속만
_RE_DECEASED_SQUARE = re.compile(
    r"[■▶◇]\s*(?P<name>[가-힣]{2,5})\s*씨\s*\([^)]+\)\s*별세"
)
# 이름 님, N월 N일 별세(향년 N세)
_RE_DECEASED_NIM_COMMA = re.compile(
    r"(?P<name>[가-힣]{2,5})\s*님,\s*(?:\d{1,2}월\s*)?\d{1,2}\s*일\s*별세\s*\(\s*향년\s*(?P<age>\d+세?)\s*\)"
)
# 이름 님이 N일 별세했다. 향년 N세
_RE_DECEASED_NIM_HADA = re.compile(
    r"(?P<name>[가-힣]{2,5})\s*님(?:이|께서)\s*\d{1,2}\s*일\s*별세했다\.\s*향년\s*(?P<age>\d+세?)"
)
# 이름 역할(사진)가 N일 별세했다. 향년 N세
_RE_DECEASED_ROLE = re.compile(
    r"(?P<name>[가-힣]{2,5})\s*(?:무용가|교수)(?:\([^)]*\))?가\s*\d{1,2}\s*일\s*별세했다\.\s*향년\s*(?P<age>\d+세?)"
)
# 고인 : 故 이름님 / 고인 : 이름 님 (▲△ 없이)
_RE_DECEASED_GOHIN_LABEL = re.compile(
    r"고인\s*[=:]\s*(?:故\s*)?(?P<name>[가-힣]{2,5})님?"
)
# 이름씨 N일 별세
_RE_DECEASED_SSI_DAY = re.compile(
    r"(?P<name>[가-힣]{2,5})\s*씨\s+\d{1,2}\s*일\s*별세"
)
# 부친/모친 이름 씨가 N일 별세했다
_RE_DECEASED_REL_SSIGA = re.compile(
    r"(?:부친|모친|조부|조모|외조부|외조모)\s+(?P<name>[가-힣]{2,5})\s*씨가\s+\d{1,2}\s*일\s*별세했다"
)
# 이름 씨(소속) 별세=N일
_RE_DECEASED_SSI_ORG_STAR = re.compile(
    r"(?P<name>[가-힣]{2,5})\s*씨\s*\([^)]+\)\s*별세\s*="
)
# ●이름(향년 N세·...)님 별세
_RE_DECEASED_BULLET_NIM = re.compile(
    r"[●◆]\s*(?P<name>[가-힣]{2,5})\s*\(\s*향년\s*\d+세?[^)]*\)\s*님\s*별세"
)
# 故 이름 님 / 외조모 故 이름 님
_RE_DECEASED_GO_NIM = re.compile(
    r"(?:외조모|부친|모친|조부|조모|외조부)?\s*故\s*(?P<name>[가-힣]{2,5})\s*님"
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
# 병원만 (장례식장 없음): "=6일 고려대 안암병원", "5일 충남대병원"
_RE_HOSPITAL_ONLY = re.compile(
    r"(?:=\s*)?\d{1,2}\s*일\s*([가-힣A-Za-z\s]+(?:병원|의료원))"
)
# 빈소는/빈소: 병원명
_RE_BINSO_HOSPITAL = re.compile(
    r"빈소\s*(?:는|:)\s*([가-힣A-Za-z\s]+(?:병원|의료원)(?:\s+[가-힣]+원)?)"
)
# 병원+백합원/국화원: "계명대학교 동산병원 백합원 2호"
_RE_HALL_BACKET = re.compile(
    r"([가-힣A-Za-z\s]+(?:병원|의료원))\s+([가-힣]+원)\s*(\d+호)?"
)

# 발인: "발인 3월 9일", "△발인=3월2일", "발인: 3월 1일", "발인은 7일 오전 5시"
# (월) 등 중간 괄호 허용, 2026년 등 연도 허용
_RE_FUNERAL_DATE = re.compile(
    r"발인\s*(?:은|[=:])?\s*"
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
# 이름 前/전 소속 직급 관계상 — 민지홍 前 네슬레코리아 본부장 모친상, 유남석 前 헌법재판소장 장모상
_RE_PERSON_WITH_ORG_NO_PAREN = re.compile(
    r"(?P<name>[가-힣]{2,5})\s+(?P<affil>(?:전|前)\s+[가-힣A-Za-z0-9\s]+?)\s+(?P<rel>[가-힣]+상)"
)
_RE_PERSON_SIMPLE = re.compile(
    r"(?P<name>[가-힣]{2,5})씨\s*(?P<rel>[가-힣]+상)"
)
# 고인 씨 별세. key_person(소속) 씨 관계상 — 본문에 명시된 핵심인물 (제목과 다를 수 있음)
# 별세 뒤 마침표/줄바꿈/공백 유연화 (실제 기사에서 "별세\n설명환(소속)씨 모친상" 형식 존재)
_RE_BODY_KEY_AFTER_DECEASED = re.compile(
    r"[가-힣]{2,5}\s*씨\s*별세[.\s]+"
    r"(?P<name>[가-힣]{2,5})\s*\((?P<affil>[^)]+)\)\s*씨?\s*(?P<rel>[가-힣]+상)"
)
# 고인씨 별세, 이름1(소속1)·이름2(소속2)·...·이름N씨 관계상 — 첫 이름(소속)이 핵심인물, 관계상은 끝에 공유
_RE_BODY_KEY_DOT_SEP = re.compile(
    r"[가-힣]{2,5}\s*씨\s*별세[.\s,·]*?"
    r"(?P<name>[가-힣]{2,5})\s*\((?P<affil>[^)]+)\)"
    r"[^=]*?(?P<rel>[가-힣]+상)"
)


def _parse_first_related_person(related_persons: str) -> dict | None:
    """related_persons 문자열에서 첫 인물의 name, org, pos, rel을 추출한다.
    형식: '이름(소속 직급) 관계상' 또는 '이름 관계상', 복수는 ' / '로 구분."""
    if not related_persons or not related_persons.strip():
        return None
    first = related_persons.split(" / ")[0].strip()
    # 이름(소속) 관계상
    m = re.match(r"^([가-힣]{2,5})\s*\(([^)]+)\)\s+([가-힣]+상)\s*$", first)
    if m:
        name = m.group(1).strip()
        affil = m.group(2).strip()
        rel = m.group(3)
        org, pos = _split_org_position(affil)
        return {"name": name, "org": org or None, "pos": pos or None, "rel": rel}
    # 이름 관계상 (소속 없음)
    m = re.match(r"^([가-힣]{2,5})\s+([가-힣]+상)\s*$", first)
    if m:
        return {"name": m.group(1).strip(), "org": None, "pos": None, "rel": m.group(2)}
    return None


def _extract_related_persons(text: str) -> list[str]:
    """본문에서 관계자 목록을 추출한다."""
    persons = []
    for m in _RE_PERSON_WITH_ORG.finditer(text):
        name = _strip_suffix(m.group("name"))
        org = m.group("org").strip()
        rel = m.group("rel")
        persons.append(f"{name}({org}) {rel}")

    # "별세, 이름1(소속1)·이름2(소속2)·...·이름N씨 관계상" 형식
    if not persons and "별세" in text:
        rel_m = re.search(r"별세[^=]*?(?P<rel>[가-힣]+상)", text)
        if rel_m:
            block = text[text.find("별세") : rel_m.end()]
            rel = rel_m.group("rel")
            for m in re.finditer(r"(?P<name>[가-힣]{2,5})\s*\((?P<affil>[^)]+)\)", block):
                name = _strip_suffix(m.group("name"))
                org = m.group("affil").strip()
                persons.append(f"{name}({org}) {rel}")

    for m in _RE_PERSON_SIMPLE.finditer(text):
        name = _strip_suffix(m.group("name"))
        rel = m.group("rel")
        entry = f"{name} {rel}"
        if entry in " ".join(persons):
            continue
        # "주자 모친상" 등 잘못된 추출 방지: 같은 rel로 이름(소속)이 이미 있으면 스킵 (기사 오기 "설주자"→"주자")
        if any(p.endswith(f" {rel}") and "(" in p for p in persons):
            continue
        persons.append(entry)

    return persons


def _clean_funeral_hall(hall: str) -> str:
    """장례식장 이름 앞뒤 쓰레기 문자 제거. '장레식장' 오타 정정.
    병원/의료원인데 '장례식장' 없으면 접미사 추가 (연세대 세브란스병원 → 연세대 세브란스병원 장례식장)."""
    hall = re.sub(r"^[\s=,]*(?:일|분|시|오전|오후|빈소|는)+\s*", "", hall)
    hall = re.sub(r"^[\s=,]+", "", hall)
    hall = hall.replace("장레식장", "장례식장").replace("장례예식장", "장례식장")
    hall = hall.strip()
    if hall and "장례식장" not in hall and re.search(r"(?:병원|의료원)\s*$", hall):
        hall = hall.rstrip() + " 장례식장"
    return hall


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
        dm_nairo = _RE_DECEASED_NAIRO.search(body)
        if dm_nairo:
            result["deceased_name"] = _strip_suffix(dm_nairo.group("name"))
            age = dm_nairo.group("age")
            result["deceased_age"] = age if "세" in age else age + "세"
        else:
            dm_hyang = _RE_DECEASED_HYANGNYON_RO.search(body)
            if dm_hyang:
                result["deceased_name"] = _strip_suffix(dm_hyang.group("name"))
                age = dm_hyang.group("age")
                result["deceased_age"] = age if "세" in age else age + "세"
            else:
                dm_simple = _RE_DECEASED_SIMPLE.search(body)
                if dm_simple:
                    result["deceased_name"] = _strip_suffix(dm_simple.group("name"))
                else:
                    dm_rel = _RE_DECEASED_REL.search(body)
                    if dm_rel:
                        result["deceased_name"] = _strip_suffix(dm_rel.group("name"))
                        age = dm_rel.group("age")
                        result["deceased_age"] = age if "세" in age else age + "세"
                    else:
                        dm_day = _RE_DECEASED_DAY.search(body)
                        if dm_day:
                            result["deceased_name"] = _strip_suffix(dm_day.group("name"))
                            result["deceased_age"] = dm_day.group("age") + "세"
                        else:
                            dm_label = _RE_DECEASED_LABEL.search(body)
                            if dm_label:
                                result["deceased_name"] = _strip_suffix(dm_label.group("name"))
                            else:
                                dm_nim_star = _RE_DECEASED_NIM_STAR.search(body)
                                if dm_nim_star:
                                    result["deceased_name"] = _strip_suffix(dm_nim_star.group("name"))
                                else:
                                    dm_sq = _RE_DECEASED_SQUARE.search(body)
                                    if dm_sq:
                                        result["deceased_name"] = _strip_suffix(dm_sq.group("name"))
                                    else:
                                        dm_nim = _RE_DECEASED_NIM_COMMA.search(body)
                                        if dm_nim:
                                            result["deceased_name"] = _strip_suffix(dm_nim.group("name"))
                                            result["deceased_age"] = dm_nim.group("age")
                                        else:
                                            dm_hada = _RE_DECEASED_NIM_HADA.search(body)
                                            if dm_hada:
                                                result["deceased_name"] = _strip_suffix(dm_hada.group("name"))
                                                result["deceased_age"] = dm_hada.group("age")
                                            else:
                                                dm_role = _RE_DECEASED_ROLE.search(body)
                                                if dm_role:
                                                    result["deceased_name"] = _strip_suffix(dm_role.group("name"))
                                                    result["deceased_age"] = dm_role.group("age")
                                                else:
                                                    dm_rel_no_ssi = _RE_DECEASED_REL_NO_SSI.search(body)
                                                    if dm_rel_no_ssi:
                                                        result["deceased_name"] = _strip_suffix(dm_rel_no_ssi.group("name"))
                                                        age = dm_rel_no_ssi.group("age")
                                                        result["deceased_age"] = age if "세" in age else age + "세"
                                                    else:
                                                        dm_rel_ssi_only = _RE_DECEASED_REL_SSI_ONLY.search(body)
                                                        if dm_rel_ssi_only:
                                                            result["deceased_name"] = _strip_suffix(dm_rel_ssi_only.group("name"))
                                                        else:
                                                            dm_gohin = _RE_DECEASED_GOHIN_LABEL.search(body)
                                                            if dm_gohin:
                                                                result["deceased_name"] = _strip_suffix(dm_gohin.group("name"))
                                                            else:
                                                                dm_ssi_day = _RE_DECEASED_SSI_DAY.search(body)
                                                                if dm_ssi_day:
                                                                    result["deceased_name"] = _strip_suffix(dm_ssi_day.group("name"))
                                                                else:
                                                                    dm_ssiga = _RE_DECEASED_REL_SSIGA.search(body)
                                                                    if dm_ssiga:
                                                                        result["deceased_name"] = _strip_suffix(dm_ssiga.group("name"))
                                                                    else:
                                                                        dm_org_star = _RE_DECEASED_SSI_ORG_STAR.search(body)
                                                                        if dm_org_star:
                                                                            result["deceased_name"] = _strip_suffix(dm_org_star.group("name"))
                                                                        else:
                                                                            dm_bullet = _RE_DECEASED_BULLET_NIM.search(body)
                                                                            if dm_bullet:
                                                                                result["deceased_name"] = _strip_suffix(dm_bullet.group("name"))
                                                                            else:
                                                                                dm_go_nim = _RE_DECEASED_GO_NIM.search(body)
                                                                                if dm_go_nim:
                                                                                    result["deceased_name"] = _strip_suffix(dm_go_nim.group("name"))

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
        if not result.get("funeral_hall"):
            bm = _RE_BINSO_HOSPITAL.search(body)
            if bm:
                hall = _clean_funeral_hall(bm.group(1))
                if hall:
                    result["funeral_hall"] = hall
        if not result.get("funeral_hall"):
            hm3 = _RE_HOSPITAL_ONLY.search(body)
            if hm3:
                hall = _clean_funeral_hall(hm3.group(1))
                if hall:
                    result["funeral_hall"] = hall
        if not result.get("funeral_hall"):
            bm2 = _RE_HALL_BACKET.search(body)
            if bm2:
                result["funeral_hall"] = f"{bm2.group(1).strip()} {bm2.group(2)}"
                if bm2.group(3):
                    result["room_number"] = bm2.group(3)

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

    # 고인 씨 별세. key_person(소속) 씨 관계상 — 본문에 명시된 핵심인물 (제목과 다를 수 있음)
    bm = _RE_BODY_KEY_AFTER_DECEASED.search(body)
    if not bm:
        # "별세, 이름1(소속1)·이름2(소속2)·...·이름N씨 관계상" 형식 (첫 이름(소속)이 핵심인물)
        bm = _RE_BODY_KEY_DOT_SEP.search(body)
    if bm:
        result["key_person"] = _strip_suffix(bm.group("name"))
        affil = bm.group("affil").strip()
        org, pos = _split_org_position(affil)
        result["organization"] = org or None
        result["position"] = pos or None
        result["relationship"] = bm.group("rel")

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
    # "고인 씨 별세. key_person(소속) 관계상" 형식이면 본문의 key_person 우선 (제목 오기재 시)
    if body_info.get("key_person"):
        result.key_person = body_info["key_person"]
        result.organization = body_info.get("organization") or result.organization
        result.position = body_info.get("position") or result.position
        result.relationship = body_info.get("relationship") or result.relationship
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

    # key_person=고인 본인인데 relationship이 '별세'면 '본인상'으로 보정
    if (
        result.relationship == "별세"
        and result.key_person
        and result.deceased_name
        and _normalize_dedup(result.key_person) == _normalize_dedup(result.deceased_name)
    ):
        result.relationship = "본인상"

    # key_person == deceased_name 이고 related_persons에 다른 인물이 있으면 → related_persons의 첫 인물을 key_person으로 승격
    # 예: [부고] 박옥선씨 → key_person=박옥선(고인), 본문에 "설명환(포스코DX 그룹장) 모친상" → key_person=설명환으로 보정
    if (
        result.key_person
        and result.deceased_name
        and _normalize_dedup(result.key_person) == _normalize_dedup(result.deceased_name)
        and result.related_persons
    ):
        first_related = _parse_first_related_person(result.related_persons)
        if first_related and _normalize_dedup(first_related["name"]) != _normalize_dedup(result.deceased_name):
            result.key_person = first_related["name"]
            if first_related.get("org"):
                result.organization = first_related["org"]
            if first_related.get("pos"):
                result.position = first_related["pos"]
            if first_related.get("rel"):
                result.relationship = first_related["rel"]

    # 관계 정규화: 형님상 → 형제상
    if result.relationship and "형님상" in result.relationship:
        result.relationship = result.relationship.replace("형님상", "형제상")

    # funeral_date에 연도 없으면 현재 연도 추가 (표시 일관성)
    if result.funeral_date and result.funeral_date.strip():
        fd = result.funeral_date.strip()
        if not re.search(r"\d{4}\s*년", fd):
            now = datetime.now()
            if re.match(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", fd):
                result.funeral_date = f"{now.year}년 {fd}"
            elif re.match(r"^\d{1,2}\s*일$", fd):
                result.funeral_date = f"{now.year}년 {now.month}월 {fd}"

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


def _extract_all_key_persons(text: str) -> list[tuple[str, str, str, str]]:
    """지정 텍스트에서 (이름, 소속, 직급, 관계상) 추출."""
    text = _clean_text(text)
    seen = set()
    result = []

    for m in _RE_PERSON_WITH_ORG.finditer(text):
        name = _strip_suffix(m.group("name"))
        affil = m.group("org").strip()
        rel = m.group("rel")
        key = (name, rel)
        if key in seen:
            continue
        seen.add(key)
        org, pos = _split_org_position(affil)
        result.append((name, org or "", pos or "", rel))

    for m in _RE_PERSON_WITH_ORG_NO_PAREN.finditer(text):
        name = _strip_suffix(m.group("name"))
        affil = m.group("affil").strip()
        rel = m.group("rel")
        key = (name, rel)
        if key in seen:
            continue
        seen.add(key)
        org, pos = _split_org_position(affil)
        result.append((name, org or "", pos or "", rel))

    # "별세, 이름1(소속1)·이름2(소속2)·...·이름N씨 관계상" 형식 (관계상이 끝에 공유)
    if not result and "별세" in text:
        rel_m = re.search(r"별세[^=]*?(?P<rel>[가-힣]+상)", text)
        if rel_m:
            block = text[text.find("별세") : rel_m.end()]
            rel = rel_m.group("rel")
            for m in re.finditer(r"(?P<name>[가-힣]{2,5})\s*\((?P<affil>[^)]+)\)", block):
                name = _strip_suffix(m.group("name"))
                affil = m.group("affil").strip()
                key = (name, rel)
                if key in seen:
                    continue
                seen.add(key)
                org, pos = _split_org_position(affil)
                result.append((name, org or "", pos or "", rel))

    return result


def _get_block_containing_deceased(body: str, deceased_name: str) -> str | None:
    """복수 부고(▲ 블록)에서 deceased_name이 포함된 블록만 반환.
    다른 고인 블록의 관계자가 섞이지 않도록."""
    if not body or not deceased_name:
        return body
    deceased_clean = deceased_name.replace(" ", "").strip()
    blocks = re.split(r"\n?[▲△◇◆▶]", body)
    for b in blocks:
        if not b.strip():
            continue
        if deceased_clean in b.replace(" ", ""):
            return b
    return body


def parse_obituary_multi(title: str, body: str) -> list[ParsedObituary]:
    """복수 부고 시 key_person별로 ParsedObituary 리스트 반환.

    '백옥문씨 별세, 민지홍 모친상, 유남석 장모상' → 2건 (민지홍, 유남석 각각).
    단일 부고면 1건만 반환.
    """
    base = parse_obituary(title, body)
    if base is None:
        return []

    # 복수 부고 시 해당 고인 블록에서만 관계자 추출 (다른 고인 블록 인물 제외)
    search_text = body or ""
    if base.deceased_name:
        block = _get_block_containing_deceased(search_text, base.deceased_name)
        if block:
            search_text = block
    persons = _extract_all_key_persons(search_text)
    if not persons:
        return [base]

    # key_person이 고인 본인(본문에서만)이고 다른 관계자가 있으면 제외
    deceased_norm = _normalize_dedup(base.deceased_name)
    others = [(n, o, p, r) for n, o, p, r in persons if _normalize_dedup(n) != deceased_norm]

    if not others:
        return [base]

    result = []
    for name, org, pos, rel in others:
        p = ParsedObituary(
            key_person=name,
            organization=org or None,
            position=pos or None,
            relationship=rel,
            deceased_name=base.deceased_name,
            deceased_age=base.deceased_age,
            funeral_hall=base.funeral_hall,
            room_number=base.room_number,
            funeral_date=base.funeral_date,
            funeral_time=base.funeral_time,
            contact=base.contact,
            related_persons=base.related_persons,
        )
        result.append(p)
    return result
