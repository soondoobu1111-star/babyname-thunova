"""
PDF 생성 엔진 v2 — Playwright HTML→PDF
ReportLab 대체. preview_report.html 디자인 기반 동적 HTML 생성.
"""
from __future__ import annotations
import html as _html_mod
from datetime import date
from typing import Optional


# ══════════════════════════════════════════════════════
# 상수 · 매핑
# ══════════════════════════════════════════════════════
HANJA_STEMS = {
    "갑": "甲", "을": "乙", "병": "丙", "정": "丁", "무": "戊",
    "기": "己", "경": "庚", "신": "辛", "임": "壬", "계": "癸",
}
HANJA_BRANCHES = {
    "자": "子", "축": "丑", "인": "寅", "묘": "卯",
    "진": "辰", "사": "巳", "오": "午", "미": "未",
    "신": "申", "유": "酉", "술": "戌", "해": "亥",
}

ELEMENT_EMOJI = {"목": "🌱", "화": "🔥", "토": "🌍", "금": "⚙️", "수": "💧"}
ELEMENT_BAR  = {"목": "#4a8c3f", "화": "#c0392b", "토": "#c49a55", "금": "#607d8b", "수": "#2980b9"}
ELEMENT_BG   = {"목": "#dcfce7", "화": "#fee2e2", "토": "#fef3c7", "금": "#f1f5f9", "수": "#dbeafe"}
ELEMENT_FG   = {"목": "#166534", "화": "#991b1b", "토": "#92400e", "금": "#455a64", "수": "#1d4ed8"}

LACKING_THRESHOLD = 1.5

# 음령오행: 초성 인덱스(0~18) → 오행
_EUMRYEONG_MAP: dict[int, str] = {
    0: "목", 1: "목", 15: "목",
    2: "화", 3: "화", 4: "화", 5: "화", 16: "화",
    6: "수", 7: "수", 8: "수", 17: "수",
    9: "금", 10: "금", 12: "금", 13: "금", 14: "금",
    11: "토", 18: "토",
}

# 2026년 흔한 이름 (상위 30위)
_COMMON_MALE = {
    "도윤","서준","도현","이준","시우","하준","우주","이안","지호","태오",
    "이현","도하","수호","유준","선우","은우","윤우","주원","시윤","은호",
    "이도","우진","하진","도준","예준","로운","연우","유찬","이한","유안",
}
_COMMON_FEMALE = {
    "서윤","서아","하린","하윤","이서","아윤","지안","아린","지유","윤서",
    "이솔","도아","지아","시아","채이","지우","유주","수아","예린","윤슬",
    "유나","서하","채원","재이","채아","이나","채윤","유하","이현","예나",
}

_STRENGTH = {
    "목": "목(木) 기운이 강해 <strong>창의력·성장력</strong>이 뛰어나며 진취적 기상이 강합니다. 새로운 시작을 두려워하지 않는 기질을 타고났습니다.",
    "화": "화(火) 기운이 넘쳐 <strong>열정과 표현력</strong>이 뛰어나며 사교적 기질이 강합니다. 주변을 밝히는 카리스마를 타고났습니다.",
    "토": "토(土) 기운이 충실해 <strong>신중함과 안정감</strong>이 넘치며 주변의 신뢰를 받습니다. 끈기 있게 목표를 이루는 기질을 타고났습니다.",
    "금": "금(金) 기운이 강해 <strong>결단력·집중력</strong>이 뛰어나며 원칙을 중시합니다. 맡은 일을 끝까지 완수하는 기질을 타고났습니다.",
    "수": "수(水) 기운이 풍부해 <strong>지혜롭고 직관력</strong>이 뛰어나며 적응력이 강합니다. 깊은 사고력과 감수성을 타고났습니다.",
}
_WEAKNESS = {
    "목": "목(木) 기운이 부족해 <strong>창의력·성장 에너지</strong>가 약할 수 있습니다. 이름에 목 기운 한자를 담아 보완하세요.",
    "화": "화(火) 기운이 부족해 <strong>추진력·활기</strong>가 약해질 수 있습니다. 이름에 화 기운 한자를 담아 보완하세요.",
    "토": "토(土) 기운이 부족해 <strong>안정감·지속력</strong>이 약할 수 있습니다. 이름에 토 기운 한자를 담아 보완하세요.",
    "금": "금(金) 기운이 부족해 <strong>결단력·집중력</strong>이 약할 수 있습니다. 이름에 금 기운 한자를 담아 보완하세요.",
    "수": "수(水) 기운이 부족해 <strong>지혜·직관</strong>이 약해질 수 있습니다. 이름에 수 기운 한자를 담아 보완하세요.",
}
_HANJA_RECO = {
    "목": ("🌱 목(木)", "#166534", "가(嘉)·건(建)·근(根)·기(起)·림(林)·수(樹)·성(成)·원(元)"),
    "화": ("🔥 화(火)", "#991b1b", "광(光)·도(道)·명(明)·서(曙)·열(烈)·영(榮)·훈(勳)"),
    "토": ("🌍 토(土)", "#92400e", "기(基)·산(山)·안(安)·우(宇)·원(苑)·현(玹)·호(浩)·희(熙)"),
    "금": ("⚙️ 금(金)", "#455a64", "강(鋼)·근(瑾)·서(瑞)·선(璇)·옥(玉)·찬(鑽)·현(鉉)·연(鍊)"),
    "수": ("💧 수(水)", "#1d4ed8", "민(旻)·빈(濱)·윤(潤)·준(濬)·진(溱)·택(澤)·함(涵)·천(泉)"),
}


# ══════════════════════════════════════════════════════
# 유틸리티
# ══════════════════════════════════════════════════════
def _esc(s) -> str:
    return _html_mod.escape(str(s))

def _eumryeong(char: str) -> str:
    code = ord(char)
    if 0xAC00 <= code <= 0xD7A3:
        return _EUMRYEONG_MAP.get((code - 0xAC00) // (21 * 28), "토")
    return "토"

def _surname_eumryeong(surname: str) -> str:
    for ch in surname:
        if 0xAC00 <= ord(ch) <= 0xD7A3:
            return _eumryeong(ch)
    return "토"

def _lacking(five_detail: dict) -> list[str]:
    return [e for e, v in five_detail.items() if v <= LACKING_THRESHOLD]

def _bar_pct(val: float) -> int:
    return min(100, max(2, int(val / 4.0 * 100)))

def _elem_badge(elem: str, label: str | None = None) -> str:
    text = label or f"{ELEMENT_EMOJI.get(elem,'')} {elem}"
    bg = ELEMENT_BG.get(elem, "#f0f0f0"); fg = ELEMENT_FG.get(elem, "#666")
    return (f'<span style="background:{bg};color:{fg};font-size:10px;font-weight:700;'
            f'padding:2px 8px;border-radius:20px;white-space:nowrap;">{text}</span>')

def _rarity_cell(korean_name: str, gender: str) -> str:
    common = _COMMON_MALE if gender == "male" else _COMMON_FEMALE
    if korean_name in common:
        return '<span style="color:#c0392b;font-size:11px;font-weight:600;">흔함 ▲</span>'
    return '<span style="color:#4a8c3f;font-size:11px;font-weight:600;">희소 ✦</span>'

def _gender_kor(gender: str) -> str:
    return "남아" if gender == "male" else "여아"

def _birth_str(birth_date: date, birth_hour: Optional[int], birth_minute: Optional[int]) -> str:
    s = birth_date.strftime("%Y년 %m월 %d일")
    if birth_hour is not None:
        meridiem = "오전" if birth_hour < 12 else "오후"
        h12 = birth_hour % 12 or 12
        s += f" {meridiem} {h12}시"
        if birth_minute:
            s += f" {birth_minute:02d}분"
    else:
        s += " (시간 미상)"
    return s


# ══════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════
def _css() -> str:
    return """
<style>
@page { size: A4; margin: 0mm; }
:root {
  --brown-dark:#2b1a0e; --brown-mid:#4a2c10;
  --gold:#d4a76a; --gold-deep:#c49a55; --gold-bg:#fdf0df;
  --cream:#fdf8f2; --cream-warm:#fff7ee;
  --border:#eedfc8; --text-dark:#2b1a0e;
  --text-mid:#6b5c4e; --text-light:#8a7060; --text-tiny:#999;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family:'Noto Sans CJK KR','Noto Sans KR','Apple SD Gothic Neo',sans-serif;
  background:#e8e0d4; color:var(--text-dark);
  -webkit-print-color-adjust:exact; print-color-adjust:exact;
  font-size:13px; line-height:1.6;
}
.page {
  width:210mm; min-height:297mm; margin:0 auto;
  background:var(--cream);
  break-after:page; page-break-after:always;
}
.page:last-of-type { break-after:auto; page-break-after:auto; }
.page-inner { padding:14mm 16mm; }
.part-badge {
  display:inline-block; background:var(--gold-bg); color:var(--gold-deep);
  font-size:10px; font-weight:700; padding:3px 12px; border-radius:20px;
  letter-spacing:1px; margin-bottom:10px; border:1px solid var(--border);
}
.part-title { font-size:16px; font-weight:800; color:var(--text-dark); margin-bottom:14px; }
.part-block {
  background:#fff; border:1px solid var(--border); border-radius:14px;
  padding:18px 16px; margin-bottom:14px;
}
.hero {
  background:linear-gradient(160deg,var(--brown-dark) 0%,var(--brown-mid) 50%,var(--brown-dark) 100%);
  padding:50px 28px; text-align:center;
}
.hero-label { color:var(--gold); font-size:11px; letter-spacing:4px; font-weight:700; margin-bottom:12px; }
.hero-name {
  font-family:'Noto Serif CJK KR','Noto Sans CJK KR',serif; color:#fff;
  font-size:38px; font-weight:900; letter-spacing:6px; margin-bottom:4px;
}
.hero-subtitle { color:var(--gold); font-size:14px; font-weight:500; margin-bottom:22px; letter-spacing:2px; }
.hero-info-box {
  background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.18);
  border-radius:10px; padding:14px 20px; display:inline-block;
  text-align:left; min-width:230px;
}
.hero-info-row { font-size:12px; color:rgba(255,255,255,0.82); line-height:2.2; }
.hero-info-row strong { color:var(--gold); margin-right:8px; }
.hero-disclaimer {
  margin-top:18px; background:rgba(255,255,255,0.06);
  border:1px solid rgba(255,255,255,0.15); border-radius:8px;
  padding:12px 16px; font-size:11px; color:rgba(255,255,255,0.6);
  line-height:1.7; text-align:left; max-width:420px; margin-left:auto; margin-right:auto;
}
.cover-content { padding:26px 22px 22px; }
.obar-row { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.obar-label { width:38px; font-size:11px; color:var(--text-light); text-align:right; }
.obar-track { flex:1; background:#f0e8dc; border-radius:4px; height:14px; overflow:hidden; }
.obar-fill { height:100%; border-radius:4px; }
.obar-val { font-size:12px; font-weight:700; width:38px; }
.sw-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:14px 0; }
.sw-card { border-radius:10px; padding:14px 12px; }
.sw-title { font-size:11px; font-weight:700; margin-bottom:8px; }
.name-card {
  border:1px solid var(--border); border-radius:12px;
  padding:14px 14px; margin-bottom:10px; background:#fff;
}
.name-card.top { border:2px solid var(--gold); background:#fffdf8; }
.name-hj { font-size:26px; font-weight:900; color:var(--text-dark); line-height:1; }
.name-korean { font-size:20px; font-weight:900; color:var(--text-dark); margin-bottom:4px; }
.name-korean span { color:var(--gold-deep); }
.name-badge-num {
  display:inline-block; background:var(--gold-bg); color:var(--gold-deep);
  font-size:10px; font-weight:700; padding:2px 10px; border-radius:20px;
  border:1px solid var(--border);
}
.name-badge-top {
  display:inline-block; background:var(--gold); color:#fff;
  font-size:10px; font-weight:700; padding:2px 10px; border-radius:20px;
}
.name-summary {
  background:var(--gold-bg); border-radius:6px; padding:7px 10px;
  font-size:11px; color:#7a5c2e; font-weight:600;
}
.eumryeong-table { width:100%; border-collapse:collapse; font-size:11px; }
.eumryeong-table th {
  padding:7px 5px; background:var(--brown-dark); color:var(--gold);
  font-weight:700; border:1px solid #4a2c10; text-align:center;
}
.eumryeong-table td { padding:6px 5px; border:1px solid var(--border); text-align:center; }
.eumryeong-table tr:nth-child(odd) td { background:#fffdf8; }
.closing-section {
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  min-height:297mm; background:linear-gradient(160deg,var(--brown-dark) 0%,var(--brown-mid) 60%,var(--brown-dark) 100%);
  text-align:center; padding:60px 40px;
}
.closing-divider { width:80px; height:2px; background:var(--gold); border-radius:2px; margin:20px auto; }
.closing-title { font-family:'Noto Serif CJK KR','Noto Sans CJK KR',serif; color:#fff; font-size:22px; font-weight:700; line-height:1.5; margin-bottom:10px; }
.closing-sub { color:rgba(255,255,255,0.7); font-size:13px; line-height:1.8; max-width:320px; margin-bottom:8px; }
.closing-star { color:var(--gold); font-size:14px; font-weight:700; margin:16px 0 10px; }
.closing-brand { color:rgba(255,255,255,0.55); font-size:11px; line-height:1.9; }
@media print {
  body { background:transparent; }
  .page { margin:0; box-shadow:none; page-break-after:always; }
  .page:last-of-type { page-break-after:auto; }
}
</style>"""


# ══════════════════════════════════════════════════════
# PAGE 1 — 표지
# ══════════════════════════════════════════════════════
def _page_cover(surname, gender, birth_date, birth_hour, birth_minute, birth_second, saju_data, order_id):
    pillars  = saju_data.get("pillars", {})
    dominant = saju_data.get("dominant_element", "")
    today    = date.today().strftime("%Y년 %m월 %d일")

    def hj_pair(key):
        p  = pillars.get(key, {})
        hs = HANJA_STEMS.get(p.get("stem","?"), "?")
        hb = HANJA_BRANCHES.get(p.get("branch","?"), "?")
        return f"{hs}{hb}" if p else "—"

    pillars_str = " ".join(hj_pair(k) for k in ["year","month","day","hour"])
    birth_str   = _birth_str(birth_date, birth_hour, birth_minute)

    return f"""
<div class="page">
  <div class="hero">
    <div style="font-size:42px;margin-bottom:14px;">🌙</div>
    <div class="hero-label">써노바 작명연구소 · AI 사주 오행 분석</div>
    <div class="hero-name">{_esc(surname)}○○</div>
    <div class="hero-subtitle">아기 이름 오행 분석 리포트</div>
    <div class="hero-info-box">
      <div class="hero-info-row"><strong>성씨</strong>{_esc(surname)} ({_gender_kor(gender)})</div>
      <div class="hero-info-row"><strong>생년월일</strong>{_esc(birth_str)}</div>
      <div class="hero-info-row"><strong>사주팔자</strong>{_esc(pillars_str)}</div>
      <div class="hero-info-row"><strong>주 오행</strong>{_esc(dominant)}</div>
    </div>
    <div class="hero-disclaimer">
      ⚠️ 본 리포트는 전통 사주 명리학을 AI로 분석한 <strong style="color:rgba(255,255,255,0.85);">참고용 자료</strong>입니다.
      이름 선택의 최종 결정은 보호자의 판단에 따르며, 특정 결과를 보장하지 않습니다.
    </div>
  </div>
  <div class="cover-content">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">
      <div style="background:var(--gold-bg);border:1px solid var(--border);border-radius:10px;padding:14px 16px;">
        <div style="font-size:10px;font-weight:700;color:var(--gold-deep);margin-bottom:8px;letter-spacing:1px;">REPORT CONTENTS</div>
        <div style="font-size:12px;color:var(--text-mid);line-height:2.1;">
          📊 PART 1 · 사주팔자 &amp; 오행 분석<br>
          ✍️ PART 2 · 추천 이름 10선<br>
          🔊 PART 3 · 음령오행 &amp; 종합 추천
        </div>
      </div>
      <div style="background:var(--cream-warm);border:1px solid var(--border);border-radius:10px;padding:14px 16px;">
        <div style="font-size:10px;font-weight:700;color:var(--gold-deep);margin-bottom:8px;letter-spacing:1px;">ORDER INFO</div>
        <div style="font-size:12px;color:var(--text-mid);line-height:2.1;">
          주문번호: {_esc(order_id)}<br>
          발급일: {_esc(today)}<br>
          분석: AI 명리학 엔진
        </div>
      </div>
    </div>
    <div style="padding:12px 16px;background:var(--cream);border:1px solid var(--border);border-radius:8px;font-size:12px;color:var(--text-mid);line-height:1.9;text-align:center;">
      ★ 표시된 이름이 오행 균형상 가장 권장하는 이름입니다.<br>
      최종 결정은 가족과 함께 가장 마음에 드는 이름으로 선택해 주세요.
    </div>
  </div>
</div>"""


# ══════════════════════════════════════════════════════
# PAGE 2 — PART 1 · 사주팔자 오행 분석
# ══════════════════════════════════════════════════════
def _page_part1(saju_data: dict) -> str:
    pillars  = saju_data.get("pillars", {})
    five     = saju_data.get("five_elements_detail", {})
    dominant = saju_data.get("dominant_element", "")
    lacking  = _lacking(five)

    def stem_td(key):
        p = pillars.get(key, {})
        s = p.get("stem","?") if p else "?"
        h = HANJA_STEMS.get(s, "?") if p else "—"
        return (f'<td style="padding:8px 4px;border:1px solid var(--border);text-align:center;">'
                f'<div style="font-size:22px;font-weight:900;color:var(--text-dark);">{h}</div>'
                f'<div style="font-size:10px;color:var(--text-light);">{s if p else "미상"}</div></td>')

    def branch_td(key):
        p = pillars.get(key, {})
        b = p.get("branch","?") if p else "?"
        h = HANJA_BRANCHES.get(b,"?") if p else "—"
        col = "var(--gold-deep)" if p else "var(--text-tiny)"
        return (f'<td style="padding:8px 4px;border:1px solid var(--border);text-align:center;">'
                f'<div style="font-size:22px;font-weight:900;color:{col};">{h}</div>'
                f'<div style="font-size:10px;color:var(--text-light);">{b if p else "미상"}</div></td>')

    def th(label):
        return (f'<th style="background:var(--brown-dark);color:var(--gold);font-size:11px;'
                f'font-weight:700;border:1px solid #4a2c10;text-align:center;padding:7px 4px;">{label}</th>')

    saju_table = f"""
<table style="width:100%;border-collapse:collapse;margin-bottom:16px;">
  <tr>{th("구분")}{th("년주(年柱)")}{th("월주(月柱)")}{th("일주(日柱)")}{th("시주(時柱)")}</tr>
  <tr style="background:var(--cream);">
    <td style="padding:7px 4px;font-size:11px;font-weight:700;color:var(--text-light);border:1px solid var(--border);text-align:center;">천간</td>
    {stem_td("year")}{stem_td("month")}{stem_td("day")}{stem_td("hour")}
  </tr>
  <tr>
    <td style="padding:7px 4px;font-size:11px;font-weight:700;color:var(--text-light);background:var(--cream);border:1px solid var(--border);text-align:center;">지지</td>
    {branch_td("year")}{branch_td("month")}{branch_td("day")}{branch_td("hour")}
  </tr>
</table>"""

    obar_rows = ""
    for elem in ["목","화","토","금","수"]:
        val = five.get(elem, 0.0)
        pct = _bar_pct(val)
        col = ELEMENT_BAR.get(elem,"#999")
        fg  = ELEMENT_FG.get(elem,"#666") if val > LACKING_THRESHOLD else "#999"
        warn = " ⚠️" if elem in lacking else ""
        obar_rows += (
            f'<div class="obar-row">'
            f'<div class="obar-label">{ELEMENT_EMOJI.get(elem,"")} {elem}</div>'
            f'<div class="obar-track"><div class="obar-fill" style="width:{pct}%;background:{col};"></div></div>'
            f'<div class="obar-val" style="color:{fg};">{val:.1f}{warn}</div></div>'
        )

    strength = _STRENGTH.get(dominant, "균형 잡힌 오행 구성입니다.")
    weakness_lines = "<br>".join(_WEAKNESS[e] for e in lacking if e in _WEAKNESS)
    if not weakness_lines:
        weakness_lines = "오행이 비교적 균형 잡혀 있습니다."

    hanja_dirs = ""
    for e in lacking:
        if e in _HANJA_RECO:
            label, color, hanja = _HANJA_RECO[e]
            hanja_dirs += (
                f'<div style="background:var(--gold-bg);border-radius:8px;padding:10px 12px;'
                f'font-size:12px;color:var(--text-mid);line-height:1.9;margin-bottom:6px;">'
                f'<strong style="color:{color};">{label} 보완</strong><br>{hanja}</div>'
            )
    if not hanja_dirs:
        hanja_dirs = '<div style="background:var(--gold-bg);border-radius:8px;padding:10px 12px;font-size:12px;color:var(--text-mid);">오행이 균형 잡혀 있어 어떤 한자도 잘 어울립니다.</div>'

    lacking_str = "·".join(lacking) if lacking else "없음 (균형)"

    return f"""
<div class="page">
  <div class="page-inner">
    <div class="part-badge">PART 1 · 오행 분석</div>
    <div class="part-title">아기 사주팔자 · 오행 구성 분석</div>
    <div class="part-block">
      {saju_table}
      <div style="font-size:12px;font-weight:700;color:var(--text-dark);margin-bottom:10px;">
        오행 분포 <span style="font-size:11px;font-weight:400;color:var(--text-light);margin-left:8px;">부족한 오행: <strong style="color:#c0392b;">{_esc(lacking_str)}</strong></span>
      </div>
      {obar_rows}
    </div>
    <div class="sw-grid">
      <div class="sw-card" style="background:#f0f7ee;border:1px solid #b8d9b2;">
        <div class="sw-title" style="color:#4a8c3f;">✅ 타고난 강점</div>
        <div style="font-size:12px;color:#3a5c38;line-height:1.8;">{strength}</div>
      </div>
      <div class="sw-card" style="background:#fff7ee;border:1px solid #f0c87a;">
        <div class="sw-title" style="color:#c0392b;">⚠️ 보완 필요</div>
        <div style="font-size:12px;color:#7a3a2a;line-height:1.8;">{weakness_lines}</div>
      </div>
    </div>
    <div style="font-size:12px;font-weight:700;color:var(--text-dark);margin-bottom:8px;">📌 이름 짓기 방향</div>
    {hanja_dirs}
    <div style="margin-top:10px;padding:10px 14px;background:var(--cream);border:1px solid var(--border);border-radius:8px;font-size:11px;color:var(--text-mid);line-height:1.9;">
      이름 후보 10개는 모두 위 방향을 기반으로 선정되었습니다. ★ 추천 이름이 오행 균형상 가장 권장하는 이름입니다.
    </div>
  </div>
</div>"""


# ══════════════════════════════════════════════════════
# PART 2 — 이름 카드
# ══════════════════════════════════════════════════════
def _name_card(name: dict, surname: str) -> str:
    is_top  = name.get("is_top3", False)
    rank    = name.get("rank", "?")
    korean  = name.get("korean_name", "")
    hj_each = name.get("hanja_each", [])
    st_each = name.get("strokes_each", [])
    el_each = name.get("elements_each", [])
    hm_each = name.get("hanja_meaning_each", [])
    meaning = name.get("full_meaning", "")
    reason  = name.get("saju_reason", "")
    total_s = name.get("total_strokes_with_surname", "—")

    badge_html = ('<span class="name-badge-top">★ 추천</span>' if is_top
                  else f'<span class="name-badge-num">No.{rank}</span>')
    card_cls = "name-card top" if is_top else "name-card"
    hanja_display = "".join(hj_each) if hj_each else name.get("hanja_name","")

    detail_lines = []
    for i, items in enumerate(zip(hj_each, st_each, el_each, hm_each)):
        hj, st, el, hm = items
        char = korean[i] if i < len(korean) else ""
        badge = _elem_badge(el, f"{ELEMENT_EMOJI.get(el,'')}{el}")
        detail_lines.append(f"<strong>{hj}({_esc(char)})</strong> {_esc(hm)} · {st}획 &nbsp;{badge}")
    detail_html = "<br>".join(detail_lines)

    return f"""
<div class="{card_cls}">
  <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:10px;">
    <div style="text-align:center;min-width:50px;">
      <div class="name-hj">{_esc(hanja_display)}</div>
      <div style="font-size:10px;color:var(--text-light);">한자</div>
    </div>
    <div style="flex:1;">
      <div class="name-korean">{_esc(surname)}<span>{_esc(korean)}</span>
        <span style="font-size:10px;color:var(--text-tiny);font-weight:400;margin-left:6px;">총획 {total_s}획</span>
      </div>
      <div>{badge_html}</div>
    </div>
  </div>
  <div style="font-size:11px;color:var(--text-mid);line-height:1.9;margin-bottom:8px;">{detail_html}</div>
  <div style="font-size:12px;color:var(--text-mid);line-height:1.8;margin-bottom:6px;">{_esc(meaning)}</div>
  <div style="font-size:11px;color:var(--text-light);line-height:1.7;margin-bottom:8px;">💡 {_esc(reason)}</div>
</div>"""


def _name_cards_pages(names: list, surname: str) -> str:
    pages = ""
    for chunk in [names[0:4], names[4:8], names[8:]]:
        if not chunk:
            continue
        start_r = chunk[0].get("rank","?"); end_r = chunk[-1].get("rank","?")
        pages += f"""
<div class="page">
  <div class="page-inner">
    <div class="part-badge">PART 2 · 이름 추천</div>
    <div class="part-title">추천 이름 10선 — No.{start_r}~{end_r}</div>
    {"".join(_name_card(n, surname) for n in chunk)}
  </div>
</div>"""
    return pages


# ══════════════════════════════════════════════════════
# PART 3 — 음령오행 & 종합 분석
# ══════════════════════════════════════════════════════
def _page_part3(saju_data: dict, names: list, surname: str, gender: str) -> str:
    five    = saju_data.get("five_elements_detail", {})
    lacking = _lacking(five)
    sur_el  = _surname_eumryeong(surname)

    rows_html = ""
    scored_list = []
    for name in names:
        k       = name.get("korean_name","")
        is_top  = name.get("is_top3", False)
        chars   = list(k)[:2]
        elems   = [_eumryeong(c) for c in chars]
        comps   = [e for e in elems if e in lacking]
        score   = len(comps)

        def ecell(elem, label):
            bg = ELEMENT_BG.get(elem,"#f0f0f0"); fg = ELEMENT_FG.get(elem,"#666")
            return (f'<td><span style="background:{bg};color:{fg};font-size:10px;font-weight:700;'
                    f'padding:2px 6px;border-radius:10px;">{_esc(label)}→{elem}</span></td>')

        sur_cell   = ecell(sur_el, surname[:1])
        char_cells = "".join(ecell(_eumryeong(c), c) for c in chars)
        sup_str    = "·".join(set(comps)) + " 보완" if comps else "—"
        sup_col    = ("color:#4a8c3f;font-weight:700;" if score >= 2
                      else "color:#c0392b;font-weight:700;" if score == 0
                      else "")
        name_style = "font-weight:800;" + ("color:var(--gold-deep);" if is_top else "")
        rarity     = _rarity_cell(k, gender)

        rows_html += f"""
<tr>
  <td style="{name_style}">{"★ " if is_top else ""}{_esc(k)}</td>
  {sur_cell}{char_cells}
  <td style="{sup_col}">{_esc(sup_str)}</td>
  <td>{rarity}</td>
</tr>"""
        scored_list.append({"name": k, "score": score, "is_top": is_top, "elems": elems})

    top3 = sorted(scored_list, key=lambda x: (x["score"], int(x["is_top"])), reverse=True)[:3]
    medal = ["🥇","🥈","🥉"]; rank_labels = ["1위","2위","3위"]
    podium_html = ""
    for i, cand in enumerate(top3):
        is_first = i == 0
        bdr  = "border:2px solid var(--gold);" if is_first else "border:1px solid var(--border);"
        bg   = "background:#fffdf8;" if is_first else ""
        badg = " ".join(_elem_badge(e) for e in cand["elems"])
        podium_html += f"""
<div style="{bdr}{bg}border-radius:12px;padding:13px 10px;text-align:center;">
  <div style="font-size:10px;font-weight:700;color:{'var(--gold)' if is_first else 'var(--gold-deep)'};margin-bottom:5px;">{medal[i]} {rank_labels[i]}</div>
  <div style="font-size:20px;font-weight:900;color:var(--text-dark);margin-bottom:4px;">{_esc(cand['name'])}</div>
  <div style="font-size:10px;margin-bottom:4px;">{badg}</div>
  <div style="font-size:10px;color:var(--text-light);line-height:1.7;">음령 보완 {cand['score']}개<br>{'AI ★ 추천' if cand['is_top'] else ''}</div>
</div>"""

    return f"""
<div class="page">
  <div class="page-inner">
    <div class="part-badge">PART 3 · 음령오행 &amp; 종합 분석</div>
    <div class="part-title">이름의 소리에 담긴 오행 — 음령오행(音靈五行) 분석</div>
    <div style="background:linear-gradient(135deg,var(--brown-dark),var(--brown-mid));border-radius:12px;padding:14px 16px;margin-bottom:14px;">
      <div style="font-size:11px;font-weight:700;color:var(--gold);margin-bottom:8px;">음령오행이란?</div>
      <div style="font-size:12px;color:rgba(255,255,255,0.85);line-height:1.8;">
        이름을 소리 내어 부를 때 발생하는 기운. 초성(첫 자음)에 따라 오행이 결정됩니다.
      </div>
      <div style="display:flex;gap:7px;flex-wrap:wrap;margin-top:10px;">
        <span style="background:rgba(46,125,50,0.3);color:#8fda8f;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;">ㄱ·ㅋ→목</span>
        <span style="background:rgba(198,40,40,0.3);color:#ffaaaa;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;">ㄴ·ㄷ·ㄹ·ㅌ→화</span>
        <span style="background:rgba(212,134,10,0.3);color:#ffd080;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;">ㅇ·ㅎ→토</span>
        <span style="background:rgba(69,90,100,0.4);color:#ccc;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;">ㅅ·ㅈ·ㅊ→금</span>
        <span style="background:rgba(21,101,192,0.3);color:#8ac8ff;font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;">ㅁ·ㅂ·ㅍ→수</span>
      </div>
    </div>
    <div class="part-block" style="padding:14px;margin-bottom:12px;">
      <div style="font-size:12px;font-weight:700;color:var(--text-dark);margin-bottom:10px;">이름별 음령오행 흐름</div>
      <table class="eumryeong-table">
        <tr><th>이름</th><th>성({_esc(surname[:1])})</th><th>첫글자</th><th>둘째글자</th><th>사주 보완</th><th>희소성</th></tr>
        {rows_html}
      </table>
    </div>
    <div class="part-block" style="padding:14px;">
      <div style="font-size:12px;font-weight:700;color:var(--text-dark);margin-bottom:12px;">🏆 음령오행 기준 종합 추천</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:12px;">{podium_html}</div>
      <div style="padding:10px 12px;background:var(--gold-bg);border-radius:8px;font-size:11px;color:#7a5c2e;line-height:1.9;">
        💡 음령오행 보완 점수가 높을수록 이름을 부를 때마다 부족한 기운이 채워집니다.
        희소성 높은 이름(희소 ✦)은 개성과 독창성을 더해줍니다.
      </div>
    </div>
  </div>
</div>"""


# ══════════════════════════════════════════════════════
# PAGE — 마무리
# ══════════════════════════════════════════════════════
def _page_closing(names: list, order_id: str) -> str:
    top3     = [n for n in names if n.get("is_top3")][:3]
    top3_str = " · ".join(n.get("korean_name","") for n in top3)
    today    = date.today().strftime("%Y년 %m월 %d일")
    return f"""
<div class="page">
  <div class="closing-section">
    <div style="font-size:44px;margin-bottom:16px;">🌙</div>
    <div class="closing-divider"></div>
    <div class="closing-title">소중한 아이에게<br>최고의 이름을 선물하세요</div>
    <div class="closing-sub">이름에는 부모의 사랑과 소망이 담겨 있습니다.</div>
    {f'<div class="closing-star">★ 추천 이름: {_esc(top3_str)}</div>' if top3_str else ''}
    <div class="closing-sub" style="max-width:300px;">
      오행의 균형 속에서 아이가 건강하고 행복하게 자라나길 바랍니다.<br><br>
      선택이 어려우실 때는 ★ 추천 이름을 참고하시고,<br>
      가족과 함께 가장 마음에 드는 이름으로 결정하세요.
    </div>
    <div class="closing-divider"></div>
    <div class="closing-brand">
      <strong>써노바 작명연구소</strong><br>
      AI 사주 오행 분석 기반 작명 서비스<br>
      발급일: {_esc(today)} &nbsp;|&nbsp; 주문번호: {_esc(order_id)}
    </div>
  </div>
</div>"""


# ══════════════════════════════════════════════════════
# HTML 조립
# ══════════════════════════════════════════════════════
def _build_html(surname, gender, birth_date, birth_hour, birth_minute, birth_second,
                saju_data, names, order_id) -> str:
    body = (
        _page_cover(surname, gender, birth_date, birth_hour, birth_minute, birth_second, saju_data, order_id)
        + _page_part1(saju_data)
        + _name_cards_pages(names, surname)
        + _page_part3(saju_data, names, surname, gender)
        + _page_closing(names, order_id)
    )
    return (f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">'
            f'<title>써노바 작명연구소</title>{_css()}</head><body>{body}</body></html>')


# ══════════════════════════════════════════════════════
# 공개 API
# ══════════════════════════════════════════════════════
def generate_pdf(
    surname: str,
    gender: str,
    birth_date: date,
    birth_hour: Optional[int] = None,
    birth_minute: Optional[int] = None,
    birth_second: Optional[int] = None,
    saju_data: dict | None = None,
    names: list | None = None,
    order_id: str = "N/A",
) -> bytes:
    """HTML → WeasyPrint → PDF bytes"""
    html = _build_html(
        surname=surname, gender=gender, birth_date=birth_date,
        birth_hour=birth_hour, birth_minute=birth_minute, birth_second=birth_second,
        saju_data=saju_data or {}, names=names or [], order_id=order_id,
    )
    import weasyprint
    return weasyprint.HTML(string=html).write_pdf()
