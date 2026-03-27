"""
사주팔자 계산 엔진
sxtwl (四柱万年历) 기반 — 절기(節氣) 정확 적용
- 년주: 입춘(立春) 기준 변경 (기존 1월 1일 오류 수정)
- 월주: 12절기 기준 변경 (기존 매월 1일 오류 수정)
- 일주/시주: sxtwl 정확 계산
"""
from datetime import date
from typing import Optional

import sxtwl

HEAVENLY_STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
EARTHLY_BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

HEAVENLY_STEM_ELEMENT = {
    "갑": "목", "을": "목", "병": "화", "정": "화",
    "무": "토", "기": "토", "경": "금", "신": "금",
    "임": "수", "계": "수"
}

EARTHLY_BRANCH_ELEMENT = {
    "자": "수", "축": "토", "인": "목", "묘": "목",
    "진": "토", "사": "화", "오": "화", "미": "토",
    "신": "금", "유": "금", "술": "토", "해": "수"
}

# 지장간 표 (地藏干) — 각 지지(地支)에 숨겨진 천간(天干)과 비율 (합산 = 1.0)
JIJANGGAN: dict[str, list[tuple[str, float]]] = {
    "자": [("임", 1/3),  ("계", 2/3)],
    "축": [("계", 3/10), ("신", 1/10), ("기", 6/10)],
    "인": [("무", 7/30), ("병", 7/30), ("갑", 16/30)],
    "묘": [("갑", 1/3),  ("을", 2/3)],
    "진": [("을", 9/30), ("계", 3/30), ("무", 18/30)],
    "사": [("무", 7/30), ("경", 7/30), ("병", 16/30)],
    "오": [("병", 10/30), ("기", 9/30), ("정", 11/30)],
    "미": [("정", 9/30), ("을", 3/30), ("기", 18/30)],
    "신": [("무", 7/30), ("임", 7/30), ("경", 16/30)],
    "유": [("경", 1/3),  ("신", 2/3)],
    "술": [("신", 9/30), ("정", 3/30), ("무", 18/30)],
    "해": [("갑", 5/30), ("임", 25/30)],
}


def _compute_elements_detail(stems: list[str], branches: list[str]) -> dict[str, float]:
    """지장간 포함 오행 상세 계산 (float).
    - 천간(天干): 각 1.0
    - 지지(地支): 지장간 비율로 분산 (합 = 1.0/지지)
    """
    elements: dict[str, float] = {"목": 0.0, "화": 0.0, "토": 0.0, "금": 0.0, "수": 0.0}
    for stem in stems:
        elem = HEAVENLY_STEM_ELEMENT.get(stem)
        if elem:
            elements[elem] += 1.0
    for branch in branches:
        for hidden_stem, weight in JIJANGGAN.get(branch, []):
            elem = HEAVENLY_STEM_ELEMENT.get(hidden_stem)
            if elem:
                elements[elem] += weight
    return {k: round(v, 2) for k, v in elements.items()}


KPOP_ELEMENT_MAPPING = {
    "목": "BLACKPINK energy — creative, fresh, always growing 🌱",
    "화": "BTS fire energy — passionate, charismatic, unstoppable 🔥",
    "토": "TWICE energy — warm, stable, everyone's fave 🌍",
    "금": "aespa energy — sharp, futuristic, powerful ⚡",
    "수": "IU energy — deep, intuitive, emotionally rich 💧"
}


def _hour_to_branch_idx(hour: int) -> int:
    """0~23시 → 시지(時支) 인덱스 (자=0, 축=1, ..., 해=11)"""
    return (hour + 1) // 2 % 12


def calculate_saju(birth_date: date, birth_hour: Optional[int] = None) -> dict:
    day = sxtwl.fromSolar(birth_date.year, birth_date.month, birth_date.day)

    # 년주 — 입춘 기준 자동 처리
    yg = day.getYearGZ()
    year_stem   = HEAVENLY_STEMS[yg.tg]
    year_branch = EARTHLY_BRANCHES[yg.dz]

    # 월주 — 절기 기준 자동 처리
    mg = day.getMonthGZ()
    month_stem   = HEAVENLY_STEMS[mg.tg]
    month_branch = EARTHLY_BRANCHES[mg.dz]

    # 일주
    dg = day.getDayGZ()
    day_stem   = HEAVENLY_STEMS[dg.tg]
    day_branch = EARTHLY_BRANCHES[dg.dz]

    pillars = {
        "year":  {"stem": year_stem,  "branch": year_branch},
        "month": {"stem": month_stem, "branch": month_branch},
        "day":   {"stem": day_stem,   "branch": day_branch},
        "hour":  {}
    }

    if birth_hour is not None:
        branch_idx = _hour_to_branch_idx(birth_hour)
        hg = day.getHourGZ(branch_idx)
        pillars["hour"] = {
            "stem":   HEAVENLY_STEMS[hg.tg],
            "branch": EARTHLY_BRANCHES[hg.dz]
        }

    # 오행 분포 계산
    all_chars = [year_stem, year_branch, month_stem, month_branch, day_stem, day_branch]
    stems    = [year_stem, month_stem, day_stem]
    branches = [year_branch, month_branch, day_branch]
    if birth_hour is not None:
        all_chars.extend([pillars["hour"]["stem"], pillars["hour"]["branch"]])
        stems.append(pillars["hour"]["stem"])
        branches.append(pillars["hour"]["branch"])

    elements = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    for char in all_chars:
        elem = HEAVENLY_STEM_ELEMENT.get(char) or EARTHLY_BRANCH_ELEMENT.get(char)
        if elem:
            elements[elem] += 1

    dominant_element = max(elements, key=elements.get)  # type: ignore[arg-type]

    return {
        "pillars":              pillars,
        "five_elements":        elements,
        "five_elements_detail": _compute_elements_detail(stems, branches),
        "dominant_element":     dominant_element,
        "kpop_energy":          KPOP_ELEMENT_MAPPING[dominant_element],
        "day_stem":             day_stem
    }
