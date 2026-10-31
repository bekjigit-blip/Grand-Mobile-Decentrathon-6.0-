import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from app.config import DB_PATH, DUPLICATE_TIME_WINDOW_SECONDS

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Table for dedup tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets_history (
            ticket_id TEXT PRIMARY KEY,
            reporter_hash TEXT,
            text_hash TEXT,
            full_text TEXT,
            created_at TEXT,
            created_ts REAL,
            category TEXT
        )
    """)
    # Check if full_text column exists in existing table
    cursor.execute("PRAGMA table_info(tickets_history)")
    columns = [col[1] for col in cursor.fetchall()]
    if "full_text" not in columns:
        cursor.execute("ALTER TABLE tickets_history ADD COLUMN full_text TEXT")
        if "text_snippet" in columns:
            cursor.execute("UPDATE tickets_history SET full_text = text_snippet WHERE full_text IS NULL")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reporter_time ON tickets_history(reporter_hash, created_ts)")

    # Table for admin queue actions persistence (Point 11)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_actions (
            ticket_id TEXT PRIMARY KEY,
            status TEXT,
            draft_text TEXT,
            action TEXT,
            category TEXT,
            priority TEXT,
            assigned_to TEXT,
            note TEXT,
            updated_at TEXT
        )
    """)
    cursor.execute("PRAGMA table_info(admin_actions)")
    action_cols = [col[1] for col in cursor.fetchall()]
    for col_name in ["action", "category", "priority", "assigned_to", "note"]:
        if col_name not in action_cols:
            cursor.execute(f"ALTER TABLE admin_actions ADD COLUMN {col_name} TEXT")

    conn.commit()
    conn.close()

def parse_iso_timestamp(ts_str: Optional[str]) -> Optional[float]:
    if not ts_str:
        return None
    try:
        cleaned = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        return dt.timestamp()
    except Exception:
        return None

def compute_full_text_similarity(s1: str, s2: str) -> float:
    """Computes character trigram Jaccard similarity across the entire text."""
    if not s1 or not s2:
        return 0.0
    s1_clean = "".join(s1.lower().split())
    s2_clean = "".join(s2.lower().split())
    if s1_clean == s2_clean:
        return 1.0
    if len(s1_clean) < 3 or len(s2_clean) < 3:
        return 1.0 if s1_clean == s2_clean else 0.0

    tri1 = {s1_clean[i:i+3] for i in range(len(s1_clean) - 2)}
    tri2 = {s2_clean[i:i+3] for i in range(len(s2_clean) - 2)}

    intersection = len(tri1.intersection(tri2))
    union = len(tri1.union(tri2))
    return intersection / union if union > 0 else 0.0

def check_and_record_duplicate(
    ticket_id: str,
    reporter_hash: Optional[str],
    created_at_str: Optional[str],
    raw_text: str,
    category: str
) -> Tuple[bool, Optional[str]]:
    """
    Checks for duplicate ticket within the 1-hour window:
    current_ts - 3600 <= stored_ts <= current_ts
    - Does NOT consider future records as duplicates of earlier records.
    - Compares the entire normalized text.
    - If reporter_hash or created_at_str is missing, does NOT guess cross-player duplicate.
    """
    init_db()

    # Rule: If reporter or created_at is missing, do NOT assume duplicate
    if not reporter_hash or not reporter_hash.strip() or not created_at_str:
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO tickets_history
                (ticket_id, reporter_hash, text_hash, full_text, created_at, created_ts, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket_id,
                reporter_hash or "",
                hashlib.sha256((raw_text or "").encode('utf-8')).hexdigest(),
                raw_text or "",
                created_at_str or "",
                0.0,
                category
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass
        return False, None

    current_ts = parse_iso_timestamp(created_at_str)
    if current_ts is None:
        return False, None

    text_hash = hashlib.sha256((raw_text or "").encode('utf-8')).hexdigest()
    min_window_ts = current_ts - DUPLICATE_TIME_WINDOW_SECONDS

    is_duplicate = False
    reason = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Query past records strictly within current_ts - 3600 <= created_ts <= current_ts
        cur.execute("""
            SELECT ticket_id, full_text, text_hash, created_ts
            FROM tickets_history
            WHERE reporter_hash = ? AND created_ts >= ? AND created_ts <= ? AND ticket_id != ?
            ORDER BY created_ts DESC
        """, (reporter_hash, min_window_ts, current_ts, ticket_id))

        past_records = cur.fetchall()
        for past_id, past_full_text, past_thash, past_ts in past_records:
            if past_thash == text_hash:
                is_duplicate = True
                time_diff_min = max(1, int((current_ts - past_ts) / 60))
                reason = f"Қайталанған өтініш: осы ойыншы ({reporter_hash}) соңғы {time_diff_min} минутта ұқсас өтініш жолдаған (#{past_id})"
                break
            else:
                sim = compute_full_text_similarity(raw_text, past_full_text)
                if sim >= 0.85:
                    is_duplicate = True
                    time_diff_min = max(1, int((current_ts - past_ts) / 60))
                    reason = f"Қайталанған өтініш: мәселе ұқсастығы жоғары ({int(sim*100)}%), соңғы {time_diff_min} минутта жіберілген (#{past_id})"
                    break

        # Save record for future checks
        cur.execute("""
            INSERT OR REPLACE INTO tickets_history
            (ticket_id, reporter_hash, text_hash, full_text, created_at, created_ts, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            reporter_hash,
            text_hash,
            raw_text,
            created_at_str,
            current_ts,
            category
        ))
        conn.commit()
        conn.close()
    except Exception:
        return False, None

    return is_duplicate, reason

def save_admin_action(
    ticket_id: str,
    status: str = "pending",
    draft_text: str = "",
    action: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    note: Optional[str] = None
):
    """Persists admin moderation actions into SQLite."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    effective_action = action or status
    cur.execute("""
        INSERT OR REPLACE INTO admin_actions
        (ticket_id, status, draft_text, action, category, priority, assigned_to, note, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_id,
        status,
        draft_text or "",
        effective_action,
        category or "",
        priority or "",
        assigned_to or "",
        note or "",
        datetime.utcnow().isoformat() + "Z"
    ))
    conn.commit()
    conn.close()

def get_admin_actions(ticket_id: Optional[str] = None) -> Any:
    """
    Retrieves persisted admin moderation actions from SQLite.
    If ticket_id is provided, returns list of matching actions (for inspection/tests).
    Otherwise returns Dict[ticket_id -> {status, draft_text, updated_at}] for server/UI merge.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if ticket_id:
        cur.execute("SELECT * FROM admin_actions WHERE ticket_id = ?", (ticket_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    cur.execute("SELECT ticket_id, status, draft_text, updated_at FROM admin_actions")
    rows = cur.fetchall()
    conn.close()
    return {
        r["ticket_id"]: {"status": r["status"], "draft_text": r["draft_text"], "updated_at": r["updated_at"]}
        for r in rows
    }
