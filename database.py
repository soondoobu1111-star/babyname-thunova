"""
SQLite 주문 관리 DB
- 주문 저장 / 조회 / 상태 업데이트
"""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "orders" / "orders.db"


def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id          TEXT PRIMARY KEY,
                created_at  TEXT NOT NULL,
                surname     TEXT NOT NULL,
                gender      TEXT NOT NULL,
                birth_date  TEXT NOT NULL,
                birth_hour  INTEGER,
                customer_name TEXT,
                customer_email TEXT,
                saju_data   TEXT,
                names_data  TEXT,
                pdf_path    TEXT,
                status      TEXT DEFAULT 'pending',
                email_sent  INTEGER DEFAULT 0,
                memo        TEXT
            )
        """)
        conn.commit()


def create_order(
    surname: str,
    gender: str,
    birth_date: str,
    birth_hour,  # int or None
    customer_name: str = "",
    customer_email: str = "",
) -> str:
    """주문 생성 → order_id 반환"""
    order_id = str(uuid.uuid4())[:8].upper()
    now = datetime.now().isoformat()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO orders
               (id, created_at, surname, gender, birth_date, birth_hour,
                customer_name, customer_email)
               VALUES (?,?,?,?,?,?,?,?)""",
            (order_id, now, surname, gender, birth_date, birth_hour,
             customer_name, customer_email),
        )
        conn.commit()
    return order_id


def update_order(order_id: str, **kwargs):
    """주문 필드 업데이트"""
    if not kwargs:
        return
    # saju_data, names_data는 JSON 직렬화
    for k in ("saju_data", "names_data"):
        if k in kwargs and not isinstance(kwargs[k], str):
            kwargs[k] = json.dumps(kwargs[k], ensure_ascii=False)

    sets   = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [order_id]
    with _conn() as conn:
        conn.execute(f"UPDATE orders SET {sets} WHERE id = ?", values)
        conn.commit()


def get_orders(limit: int = 50) -> list[dict]:
    """최근 주문 목록"""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def delete_order(order_id: str):
    """주문 삭제"""
    with _conn() as conn:
        conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()


def get_order(order_id: str):
    """단일 주문 조회"""
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
    if row:
        d = dict(row)
        for k in ("saju_data", "names_data"):
            if d.get(k):
                try:
                    d[k] = json.loads(d[k])
                except Exception:
                    pass
        return d
    return None


# 앱 시작 시 자동 초기화
init_db()
