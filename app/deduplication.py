import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Tuple
from app.config import DB_PATH, DUPLICATE_TIME_WINDOW_SECONDS

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets_history (
            ticket_id TEXT PRIMARY KEY,
            reporter_hash TEXT,
            text_hash TEXT,
            text_snippet TEXT,
            created_at TEXT,
            created_ts REAL,
            category TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reporter_time ON tickets_history(reporter_hash, created_ts)")
    conn.commit()
    conn.close()

def parse_iso_timestamp(ts_str: Optional[str]) -> Optional[float]:
    if not ts_str:
        return None
    try:
        # Handles 2026-10-30T10:15:00Z or with offset
        cleaned = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        return dt.timestamp()
    except Exception:
        return None

def compute_text_similarity(s1: str, s2: str) -> float:
    """Computes character trigram Jaccard similarity for dedup check."""
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
    Checks for duplicate ticket according to strict Decentrathon 6.0 constraints:
    - Must have reporter_hash and created_at metadata.
    - If metadata is absent, NEVER guess or assume cross-player duplicate.
    - Does NOT merge short messages from different players.
    - Low similarity alone is never flagged as spam.
    - Returns (is_spam_or_duplicate, reason).
    """
    init_db()

    # Rule: If reporter_hash or created_at is missing, do not fabricate duplicate detection
    if not reporter_hash or not reporter_hash.strip() or not created_at_str:
        # Save record without false duplicate assumption
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO tickets_history
                (ticket_id, reporter_hash, text_hash, text_snippet, created_at, created_ts, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket_id,
                reporter_hash or "",
                hashlib.md5((raw_text or "").encode('utf-8')).hexdigest(),
                (raw_text or "")[:100],
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

    text_hash = hashlib.md5((raw_text or "").encode('utf-8')).hexdigest()
    min_window_ts = current_ts - DUPLICATE_TIME_WINDOW_SECONDS

    is_duplicate = False
    reason = None

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT ticket_id, text_snippet, text_hash, created_ts
            FROM tickets_history
            WHERE reporter_hash = ? AND created_ts >= ? AND ticket_id != ?
            ORDER BY created_ts DESC
        """, (reporter_hash, min_window_ts, ticket_id))

        past_records = cur.fetchall()
        for past_id, past_snippet, past_thash, past_ts in past_records:
            # If exact text hash match or high content similarity within 1 hour
            if past_thash == text_hash:
                is_duplicate = True
                time_diff_min = max(1, int((current_ts - past_ts) / 60))
                reason = f"Қайталанған өтініш: осы ойыншы ({reporter_hash}) соңғы {time_diff_min} минутта ұқсас өтініш жолдаған (#{past_id})"
                break
            else:
                sim = compute_text_similarity(raw_text, past_snippet)
                if sim >= 0.85:
                    is_duplicate = True
                    time_diff_min = max(1, int((current_ts - past_ts) / 60))
                    reason = f"Қайталанған өтініш: мәселе ұқсастығы жоғары ({int(sim*100)}%), соңғы {time_diff_min} минутта жіберілген (#{past_id})"
                    break

        # Record this ticket
        cur.execute("""
            INSERT OR REPLACE INTO tickets_history
            (ticket_id, reporter_hash, text_hash, text_snippet, created_at, created_ts, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            reporter_hash,
            text_hash,
            raw_text[:100],
            created_at_str,
            current_ts,
            category
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        return False, None

    return is_duplicate, reason
