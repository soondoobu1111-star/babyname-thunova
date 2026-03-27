"""
써노바 작명연구소 — 아기 이름 오행 분석 리포트
babyname.kfortunewave.com
"""
import os
import sys
from datetime import date, datetime
from pathlib import Path

import yaml
from yaml.loader import SafeLoader
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Streamlit Cloud: st.secrets → os.environ 주입 (로컬은 .env 우선)
try:
    import streamlit as _st
    for _k, _v in _st.secrets.items():
        if isinstance(_v, str) and _k not in os.environ:
            os.environ[_k] = _v
except Exception:
    pass

import streamlit as st
import streamlit_authenticator as stauth

sys.path.insert(0, str(Path(__file__).parent))
from database import create_order, delete_order, get_orders, update_order
from naming.generator import generate_names
from pdf.generator import generate_pdf
from saju.calculator import calculate_saju

# ── 인증 초기화 ────────────────────────────────────────
_CONFIG_PATH = Path(__file__).parent / "auth_config.yaml"

def _load_authenticator():
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            config = yaml.load(f, Loader=SafeLoader)
    else:
        # Streamlit Cloud: auth_config stored as st.secrets["auth_config"] (YAML string)
        config = yaml.safe_load(st.secrets["auth_config"])
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )
    return authenticator, config

def _save_config(config):
    with open(_CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

# ── 페이지 설정 ────────────────────────────────────────
st.set_page_config(
    page_title="써노바 작명연구소",
    page_icon="🏮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .header-box {
    background: linear-gradient(135deg, #1B3A6B 0%, #2C5282 100%);
    border-radius: 14px;
    padding: 28px 32px 22px;
    text-align: center;
    margin-bottom: 28px;
  }
  .header-box h1 { color: #C8A84B; margin: 0 0 6px; font-size: 26px; letter-spacing: 2px; }
  .header-box p  { color: #A0AEC0; margin: 0; font-size: 13px; }
  .name-card {
    background: #FFFDF5;
    border: 1px solid #E8DFC8;
    border-left: 4px solid #C8A84B;
    border-radius: 8px;
    padding: 14px 18px 10px;
    margin-bottom: 10px;
  }
  .name-card.top3 { background: #FFF8EC; border-left-color: #D97706; }
  .name-big   { font-size: 26px; font-weight: bold; color: #1B3A6B; }
  .hanja-mid  { font-size: 20px; color: #4A4A4A; margin-left: 10px; }
  .elem-tag   { display:inline-block; padding:2px 8px; border-radius:10px;
                font-size:11px; margin:2px; background:#EEF2FF; color:#3730A3; }
  .order-row  { padding: 10px 14px; border-radius:8px; background:#F9F7F0;
                border:1px solid #E8DFC8; margin-bottom:8px; font-size:13px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# 사이드바 — 이전 주문 이력
# ══════════════════════════════════════════════════════
def _sidebar(authenticator=None):
    with st.sidebar:
        if authenticator:
            st.markdown(f"👤 **{st.session_state.get('name', 'Admin')}**")
            authenticator.logout("로그아웃", location="sidebar")
            st.divider()
        st.markdown("### 📋 주문 이력")
        orders = get_orders(30)
        if not orders:
            st.caption("아직 주문이 없습니다.")
            return

        for o in orders:
            status_icon = {"done": "✅", "pending": "⏳", "error": "❌"}.get(o["status"], "⏳")
            with st.expander(
                f"{status_icon} {o['id']} · {o['surname']} · {o['created_at'][:10]}",
                expanded=False,
            ):
                g = "남아" if o["gender"] == "male" else "여아"
                st.caption(f"{g} · {o['birth_date']}")

                pdf_path = o.get("pdf_path")
                if pdf_path and Path(pdf_path).exists():
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "📄 PDF 재다운로드",
                            f.read(),
                            file_name=f"{o['surname']}_이름리포트_{o['id']}.pdf",
                            mime="application/pdf",
                            key=f"dl_{o['id']}",
                        )
                elif o["status"] == "done":
                    st.caption("PDF 파일 없음")

                if st.button("🗑️ 삭제", key=f"del_{o['id']}", use_container_width=True):
                    delete_order(o["id"])
                    st.rerun()


# ══════════════════════════════════════════════════════
# 메인 화면
# ══════════════════════════════════════════════════════
def main():
    authenticator, config = _load_authenticator()

    # ── 로그인 화면 ────────────────────────────────────
    authenticator.login(location="main")

    auth_status = st.session_state.get("authentication_status")

    if auth_status is False:
        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
        return
    if auth_status is None:
        st.markdown("""
        <div style="text-align:center;padding:32px 0 8px;">
          <h2 style="color:#1B3A6B;letter-spacing:2px;">🏮 써노바 작명연구소</h2>
          <p style="color:#888;font-size:13px;">관리자만 접근 가능합니다.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── 로그인 성공 ────────────────────────────────────
    _sidebar(authenticator)

    st.markdown("""
    <div class="header-box">
      <h1>🏮 써노바 작명연구소</h1>
      <p>사주팔자 오행 분석 기반 · AI 아기 이름 리포트</p>
    </div>
    """, unsafe_allow_html=True)

    # ── 탭: 주문 + 비밀번호 변경 ─────────────────────────
    tab_order, tab_pw = st.tabs(["📝 새 주문", "🔑 비밀번호 변경"])

    with tab_pw:
        try:
            result = authenticator.reset_password(
                st.session_state.get("username", ""),
                location="main",
            )
            if result:
                _save_config(config)
                st.success("✅ 비밀번호가 변경되었습니다.")
        except Exception as e:
            st.error(str(e))

    with tab_order:
        import calendar
        import sxtwl
        from datetime import time as dtime

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 아기 정보")
            surname = st.text_input("성(姓) *", placeholder="김 / 이 / 박 / 최", max_chars=2)
            gender  = st.radio("성별 *", ["남아", "여아"], horizontal=True)

            st.markdown("생년월일 *")
            cy, cm, cd = st.columns(3)
            today     = date.today()
            sel_year  = cy.selectbox("년", range(today.year, 1949, -1), label_visibility="collapsed")
            sel_month = cm.selectbox("월", [f"{m}월" for m in range(1, 13)], label_visibility="collapsed")
            max_day   = calendar.monthrange(sel_year, int(sel_month[:-1]))[1]
            sel_day   = cd.selectbox("일", [f"{d}일" for d in range(1, max_day + 1)], label_visibility="collapsed")
            birth_date = date(sel_year, int(sel_month[:-1]), int(sel_day[:-1]))

            try:
                _lday = sxtwl.fromSolar(birth_date.year, birth_date.month, birth_date.day)
                _leap = "윤" if _lday.isLunarLeap() else ""
                st.caption(f"음력 {_lday.getLunarYear()}년 {_leap}{_lday.getLunarMonth()}월 {_lday.getLunarDay()}일")
            except Exception:
                pass

            time_unknown = st.checkbox("태어난 시간 모름")
            if not time_unknown:
                use_seconds = st.toggle("초 설정", value=False)
                if use_seconds:
                    th, tm, ts = st.columns(3)
                    sel_hour = th.selectbox("시", range(24), index=12)
                    sel_min  = tm.selectbox("분", range(60), index=0)
                    sel_sec  = ts.selectbox("초", range(60), index=0)
                else:
                    th, tm = st.columns(2)
                    sel_hour = th.selectbox("시", range(24), index=12)
                    sel_min  = tm.selectbox("분", range(60), index=0)
                    sel_sec  = 0
                birth_time_val = dtime(sel_hour, sel_min, sel_sec)
            else:
                birth_time_val = None

        with col2:
            st.markdown("#### 주문 메모 (내부용)")
            order_memo = st.text_area(
                "스마트스토어 주문번호 / 고객명 / 메모",
                placeholder="네이버 주문번호: 2024...\n고객: 홍길동 님\n기타 요청사항",
                height=148,
            )

        st.markdown("")
        submitted = st.button("✨ 이름 리포트 생성", type="primary", use_container_width=True)

        if not submitted:
            st.info("📌 성·성별·생년월일 입력 후 **이름 리포트 생성** 버튼을 누르면 PDF가 자동 생성됩니다.")
        else:
            if not surname:
                st.error("성(姓)을 입력해주세요.")
            else:
                gender_val   = "male" if gender == "남아" else "female"
                birth_hour   = birth_time_val.hour   if birth_time_val else None
                birth_minute = birth_time_val.minute if birth_time_val else None
                birth_second = birth_time_val.second if birth_time_val else None
                _run_pipeline(surname, gender_val, birth_date, birth_hour, birth_minute, birth_second, order_memo)


# ══════════════════════════════════════════════════════
# 파이프라인: 사주 → 이름 → PDF
# ══════════════════════════════════════════════════════
def _run_pipeline(surname, gender, birth_date, birth_hour, birth_minute, birth_second, memo):
    # 주문 DB 저장
    order_id = create_order(
        surname=surname,
        gender=gender,
        birth_date=str(birth_date),
        birth_hour=birth_hour,
    )
    if memo:
        update_order(order_id, memo=memo)

    prog   = st.progress(0)
    status = st.empty()

    try:
        # ── 1. 사주 계산 ────────────────────────────────
        status.info("⚙️ 사주팔자 계산 중…")
        saju_data = calculate_saju(birth_date, birth_hour)
        update_order(order_id, saju_data=saju_data)
        prog.progress(15)

        _show_saju(saju_data)

        # ── 2. Gemini 이름 생성 ──────────────────────────
        status.info("🤖 AI가 이름을 생성하고 있습니다… (30~60초)")
        names = generate_names(surname, gender, saju_data)
        update_order(order_id, names_data=names)
        prog.progress(65)

        _show_names(names, surname)

        # ── 3. PDF 생성 ─────────────────────────────────
        status.info("📄 PDF 리포트 생성 중…")
        pdf_bytes = generate_pdf(
            surname=surname,
            gender=gender,
            birth_date=birth_date,
            birth_hour=birth_hour,
            birth_minute=birth_minute,
            birth_second=birth_second,
            saju_data=saju_data,
            names=names,
            order_id=order_id,
        )

        # PDF 저장
        pdf_dir  = Path(__file__).parent / "orders"
        pdf_dir.mkdir(exist_ok=True)
        pdf_path = str(pdf_dir / f"{order_id}_{surname}_이름리포트.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        update_order(order_id, pdf_path=pdf_path, status="done")
        prog.progress(100)

        status.success(f"✅ 완료! 주문번호: {order_id}")

        st.download_button(
            label=f"📥 PDF 다운로드 — {surname}○○ 이름 오행 분석 리포트",
            data=pdf_bytes,
            file_name=f"{surname}_이름_오행분석_리포트_{order_id}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as e:
        update_order(order_id, status="error")
        status.error(f"❌ 오류 발생: {e}")
        st.exception(e)


# ══════════════════════════════════════════════════════
# 미리보기 컴포넌트
# ══════════════════════════════════════════════════════
def _show_saju(saju_data):
    pillars = saju_data.get("pillars", {})
    five    = saju_data.get("five_elements_detail", {})
    dom     = saju_data.get("dominant_element", "")

    with st.expander("📊 사주팔자 계산 결과", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        for col, k, lbl in [(c1,"year","년주"),(c2,"month","월주"),(c3,"day","일주"),(c4,"hour","시주")]:
            p = pillars.get(k, {})
            col.metric(lbl, f"{p.get('stem','-')}{p.get('branch','-')}")
        st.caption(f"주 오행: **{dom}** · " + " ".join(f"{e} {v:.1f}" for e, v in five.items()))


def _show_names(names, surname):
    ELEM_COLOR = {"목":"#166534","화":"#991B1B","토":"#92400E","금":"#374151","수":"#1E3A5F"}

    with st.expander(f"📜 생성된 이름 후보 {len(names)}개", expanded=True):
        for name in names:
            is_top3 = name.get("is_top3", False)
            korean  = name.get("korean_name", "")
            hanja   = name.get("hanja_name", "")
            elems   = name.get("elements_each", [])
            hj_each = name.get("hanja_each", [])
            st_each = name.get("strokes_each", [])
            meaning = name.get("full_meaning", "")
            reason  = name.get("saju_reason", "")
            rank    = name.get("rank", "")
            total_s = name.get("total_strokes_with_surname", "-")

            badge = "⭐ 추천" if is_top3 else f"No.{rank}"
            cls   = "name-card top3" if is_top3 else "name-card"

            tags = "".join(
                f'<span class="elem-tag" style="background:#F0FDF4;color:{ELEM_COLOR.get(e,"#374151")}">'
                f'{h}({s}획/{e})</span>'
                for h, s, e in zip(hj_each, st_each, elems)
            )

            st.markdown(f"""
            <div class="{cls}">
              <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:6px;">
                <span style="font-size:11px;color:#999;">{badge}</span>
                <span class="name-big">{surname}{korean}</span>
                <span class="hanja-mid">{hanja}</span>
                <span style="font-size:12px;color:#aaa;margin-left:auto;">총획 {total_s}획</span>
              </div>
              <div style="margin-bottom:6px;">{tags}</div>
              <p style="font-size:13px;color:#333;margin:4px 0 3px;">{meaning}</p>
              <p style="font-size:12px;color:#888;margin:0;">💡 {reason}</p>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
