"""
아기 이름 생성 엔진
Gemini AI 기반 — 사주오행 분석 + 한자 작명
이름 후보 10개 생성 (한글+한자+획수+오행+의미)
"""
import json
import os

from google import genai

LACKING_THRESHOLD = 1.5  # 이 수치 이하면 부족한 오행으로 판단


def _get_lacking_elements(five_elements: dict) -> list:
    """부족한 오행 탐지 (0 또는 1.5 이하)"""
    return [elem for elem, val in five_elements.items() if val <= LACKING_THRESHOLD]


def _build_prompt(surname: str, gender: str, saju_data: dict) -> str:
    pillars = saju_data["pillars"]
    five = saju_data["five_elements"]
    five_detail = saju_data["five_elements_detail"]
    dominant = saju_data["dominant_element"]
    lacking = _get_lacking_elements(five)

    year_p = pillars.get("year", {})
    month_p = pillars.get("month", {})
    day_p = pillars.get("day", {})
    hour_p = pillars.get("hour", {})

    gender_kor = "남아" if gender == "male" else "여아"
    lacking_str = "·".join(lacking) if lacking else "균형잡힘 (특별히 부족하지 않음)"

    return f"""당신은 전통 한국 작명의 최고 전문가입니다. 사주팔자와 오행 이론에 기반하여 아기 이름을 짓습니다.

【아기 정보】
- 성(姓): {surname}
- 성별: {gender_kor}
- 년주(年柱): {year_p.get('stem','?')}{year_p.get('branch','?')}
- 월주(月柱): {month_p.get('stem','?')}{month_p.get('branch','?')}
- 일주(日柱): {day_p.get('stem','?')}{day_p.get('branch','?')}
- 시주(時柱): {hour_p.get('stem','?')}{hour_p.get('branch','?')}
- 오행 분포 (지장간 포함): 목{five_detail.get('목',0):.1f} 화{five_detail.get('화',0):.1f} 토{five_detail.get('토',0):.1f} 금{five_detail.get('금',0):.1f} 수{five_detail.get('수',0):.1f}
- 주 오행: {dominant}
- 부족한 오행: {lacking_str}

【작명 원칙】
1. 부족한 오행을 이름으로 보완 (한자의 오행 의미와 소리 모두 고려)
2. 성({surname})과 발음·획수·오행이 잘 어울리는 이름
3. {gender_kor}에 적합한 아름다운 의미
4. 현대에도 사용하기 좋은 세련되고 독창적인 이름 (흔한 이름 최대한 지양)
5. 획수: 성+이름 전체의 획수 배합이 길한 수리(數理)
6. 반드시 실제 존재하는 한자만 사용
7. 【희소성 필수】 아래 흔한 이름은 반드시 피하고, 독창적이고 세련된 이름을 우선 선택하세요.
   - 남아 흔한 이름 (상위 30위): 도윤, 서준, 도현, 이준, 시우, 하준, 우주, 이안, 지호, 태오, 이현, 도하, 수호, 유준, 선우, 은우, 윤우, 주원, 시윤, 은호, 이도, 우진, 하진, 도준, 예준, 로운, 연우, 유찬, 이한, 유안
   - 여아 흔한 이름 (상위 30위): 서윤, 서아, 하린, 하윤, 이서, 아윤, 지안, 아린, 지유, 윤서, 이솔, 도아, 지아, 시아, 채이, 지우, 유주, 수아, 예린, 윤슬, 유나, 서하, 채원, 재이, 채아, 이나, 채윤, 유하, 이현, 예나
   - 오행 균형이 같다면 희소성 높은 이름을 선택하세요.

【출력 형식】
이름 후보 10개를 아래 JSON 배열로만 출력하세요. 설명 텍스트 없이 JSON만.
문자열 값 안에 큰따옴표(")를 절대 사용하지 마세요.

[
  {{
    "rank": 1,
    "korean_name": "한글이름(성 제외, 2자)",
    "hanja_name": "한자이름",
    "hanja_each": ["첫글자한자", "둘째글자한자"],
    "strokes_each": [첫글자획수, 둘째글자획수],
    "total_strokes_with_surname": 성획수포함총획수,
    "elements_each": ["첫글자오행", "둘째글자오행"],
    "hanja_meaning_each": ["첫글자한자뜻", "둘째글자한자뜻"],
    "full_meaning": "이름 전체 의미 (150자 내외, 아름답고 따뜻하게)",
    "saju_reason": "이 사주에 이 이름이 좋은 이유 (100자 내외)",
    "is_top3": true
  }},
  ...
]

주의: is_top3는 가장 추천하는 3개만 true, 나머지는 false.
반드시 10개 정확히 생성하세요.
"""


def generate_names(surname: str, gender: str, saju_data: dict) -> list:
    """사주 기반 이름 후보 10개 생성"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    client = genai.Client(api_key=api_key)
    prompt = _build_prompt(surname, gender, saju_data)

    last_err = None
    for model in ["gemini-2.0-flash", "gemini-2.5-flash"]:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "temperature": 0.7,
                    "max_output_tokens": 16384,
                    "response_mime_type": "application/json",
                },
            )
            text = response.text.strip()
            names = _extract_json(text)
            names.sort(key=lambda x: x.get("rank", 99))
            return names[:10]
        except Exception as e:
            last_err = e
            continue

    raise last_err


def _extract_json(text: str) -> list:
    """Gemini 응답에서 JSON 배열 추출 — json-repair 우선, fallback 내장"""
    import re

    # 1) 직접 파싱 시도
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2) ```json 코드블록 추출 시도
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            text = m.group(1)

    # 3) [ ... ] 범위 추출
    start = text.find("[")
    end   = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
    else:
        candidate = text

    # 4) json-repair 라이브러리 시도 (설치된 경우)
    try:
        from json_repair import repair_json
        repaired = repair_json(candidate)
        result = json.loads(repaired)
        if isinstance(result, list):
            return result
    except ImportError:
        pass
    except Exception:
        pass

    # 5) 수동 복구: 제어문자 제거 후 재시도
    cleaned = _sanitize_json(candidate)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 6) 마지막 완전한 객체까지만 잘라내기
    truncated = _truncate_to_last_complete(cleaned)
    return json.loads(truncated)


def _sanitize_json(text: str) -> str:
    """JSON 문자열 내 제어문자 및 이스케이프 문제 정리"""
    import re
    # 문자열 값 안의 실제 개행/탭을 escape 처리
    # JSON 구조 바깥의 제어문자 제거
    result = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            result.append(ch)
            escape_next = False
            continue
        if ch == "\\" and in_string:
            result.append(ch)
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            result.append(ch)
            continue
        if in_string and ch in ("\n", "\r", "\t"):
            # 문자열 내 실제 개행/탭 → escape
            result.append("\\n" if ch == "\n" else ("\\r" if ch == "\r" else "\\t"))
            continue
        result.append(ch)
    return "".join(result)


def _truncate_to_last_complete(text: str) -> str:
    """마지막 완전한 } 위치에서 배열 닫기"""
    last_complete = text.rfind("},")
    if last_complete == -1:
        last_complete = text.rfind("}")
    if last_complete != -1:
        return text[:last_complete + 1] + "]"
    return text
