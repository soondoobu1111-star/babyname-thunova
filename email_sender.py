"""
이메일 발송 서비스
Gmail SMTP + PDF 첨부
"""
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_report_email(
    to_email: str,
    customer_name: str,
    surname: str,
    pdf_bytes: bytes,
    order_id: str = "",
) -> bool:
    """
    PDF 리포트 이메일 발송.
    Returns True on success, False on failure.
    """
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
    sender_name = os.getenv("SENDER_NAME", "써노바 작명연구소")

    if not gmail_user or not gmail_pass:
        raise ValueError("GMAIL_USER, GMAIL_APP_PASSWORD 환경변수가 필요합니다.")

    subject = f"[써노바 작명연구소] {surname}○○ 아기 이름 오행 분석 리포트가 완성됐습니다 ✨"

    body_html = f"""
<div style="font-family:'Apple SD Gothic Neo',sans-serif;max-width:560px;margin:0 auto;background:#FFFDF5;padding:0;border:1px solid #E8DFC8;border-radius:12px;overflow:hidden;">

  <!-- 헤더 -->
  <div style="background:#1B3A6B;padding:32px 24px;text-align:center;">
    <h1 style="color:#C8A84B;font-size:22px;margin:0 0 8px;">써노바 작명연구소</h1>
    <p style="color:white;font-size:14px;margin:0;">AI 사주 오행 분석 기반 작명 서비스</p>
  </div>

  <!-- 본문 -->
  <div style="padding:32px 28px;">
    <p style="font-size:16px;color:#1A1A1A;margin:0 0 16px;">
      안녕하세요, <strong>{customer_name}</strong>님 👋
    </p>
    <p style="font-size:15px;color:#333;line-height:1.7;margin:0 0 20px;">
      <strong style="color:#1B3A6B;">{surname}○○</strong> 아기의 이름 오행 분석 리포트가 완성되었습니다.<br>
      전통 사주팔자를 기반으로 오행 균형을 고려한 <strong>이름 후보 10개</strong>를 담았습니다.
    </p>

    <!-- 안내 박스 -->
    <div style="background:#F5E6B8;border-left:4px solid #C8A84B;padding:16px 20px;border-radius:6px;margin:0 0 24px;">
      <p style="margin:0;font-size:14px;color:#5A3E00;line-height:1.6;">
        📎 <strong>첨부된 PDF</strong>를 저장하여 가족과 함께 검토해보세요.<br>
        ⭐ <strong>추천 이름</strong>은 이 아이의 사주에 가장 잘 어울리는 이름입니다.
      </p>
    </div>

    <p style="font-size:13px;color:#666;line-height:1.7;margin:0 0 8px;">
      리포트에 관해 궁금하신 점은 스마트스토어 문의 또는 <br>
      이 이메일에 답장으로 남겨주세요.
    </p>

    {f'<p style="font-size:12px;color:#999;margin:16px 0 0;">주문번호: {order_id}</p>' if order_id else ''}
  </div>

  <!-- 푸터 -->
  <div style="background:#F0EEE8;padding:16px 24px;text-align:center;border-top:1px solid #E8DFC8;">
    <p style="font-size:11px;color:#999;margin:0;">
      써노바 작명연구소 · AI 사주 오행 분석 서비스<br>
      이 이메일은 주문 완료 후 자동 발송됩니다.
    </p>
  </div>
</div>
"""

    # 메시지 구성
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"]    = f"{sender_name} <{gmail_user}>"
    msg["To"]      = to_email

    # HTML 본문
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(body_html, "html", "utf-8"))
    msg.attach(alt)

    # PDF 첨부
    filename = f"{surname}_이름_오행분석_리포트.pdf"
    part = MIMEBase("application", "octet-stream")
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=("utf-8", "", filename))
    msg.attach(part)

    # 발송
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, to_email, msg.as_bytes())
        return True
    except Exception as e:
        print(f"이메일 발송 실패: {e}")
        raise
