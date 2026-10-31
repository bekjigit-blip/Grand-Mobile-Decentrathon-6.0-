import pytest
import time
from app.deduplication import check_and_record_duplicate

def test_duplicate_detected_for_same_reporter_within_hour():
    rep = f"player_hash_alpha_{time.time()}"
    now_iso = "2026-10-30T14:00:00Z"
    later_iso = "2026-10-30T14:15:00Z"

    # First ticket
    is_dup1, _ = check_and_record_duplicate(
        ticket_id=f"T_A1_{time.time()}",
        reporter_hash=rep,
        created_at_str=now_iso,
        raw_text="Игрок читерит и летает на рванке",
        category="complaint.cheat"
    )
    assert is_dup1 is False

    # Second identical ticket 15 minutes later by SAME reporter
    is_dup2, reason = check_and_record_duplicate(
        ticket_id="T_A2",
        reporter_hash=rep,
        created_at_str=later_iso,
        raw_text="Игрок читерит и летает на рванке",
        category="complaint.cheat"
    )
    assert is_dup2 is True
    assert "Қайталанған" in reason or "минутта" in reason

def test_no_false_duplicate_when_metadata_missing():
    """If reporter_hash or created_at is missing, must NEVER guess duplicate across players!"""
    is_dup1, _ = check_and_record_duplicate(
        ticket_id="T_NO_META1",
        reporter_hash=None,
        created_at_str=None,
        raw_text="Помогите пожалуйста",
        category="report.help"
    )
    assert is_dup1 is False

    is_dup2, _ = check_and_record_duplicate(
        ticket_id="T_NO_META2",
        reporter_hash=None,
        created_at_str=None,
        raw_text="Помогите пожалуйста",
        category="report.help"
    )
    assert is_dup2 is False

def test_different_players_with_same_short_text_not_merged():
    """Different players submitting the same short greeting must NOT be marked duplicate."""
    now_iso = "2026-10-30T15:00:00Z"

    is_dup_p1, _ = check_and_record_duplicate(
        ticket_id="T_P1",
        reporter_hash="rep_player_1",
        created_at_str=now_iso,
        raw_text="Сәлем көмек керек",
        category="report.help"
    )
    assert is_dup_p1 is False

    is_dup_p2, _ = check_and_record_duplicate(
        ticket_id="T_P2",
        reporter_hash="rep_player_2",
        created_at_str=now_iso,
        raw_text="Сәлем көмек керек",
        category="report.help"
    )
    assert is_dup_p2 is False

def test_same_reporter_different_accused_not_duplicate():
    """Single reporter filing identical complaint text against TWO DIFFERENT accused players must not be duplicate."""
    rep = f"reporter_batch_{time.time()}"
    now_iso = "2026-10-30T16:00:00Z"
    next_iso = "2026-10-30T16:05:00Z"

    is_dup_target1, _ = check_and_record_duplicate(
        ticket_id="T_TARGET_1",
        reporter_hash=rep,
        created_at_str=now_iso,
        raw_text="Игрок оскорбил родных в вип-чате",
        category="complaint.insult",
        reported_nick="Ivan_Ivanov"
    )
    assert is_dup_target1 is False

    is_dup_target2, _ = check_and_record_duplicate(
        ticket_id="T_TARGET_2",
        reporter_hash=rep,
        created_at_str=next_iso,
        raw_text="Игрок оскорбил родных в вип-чате",
        category="complaint.insult",
        reported_nick="Petr_Petrov"
    )
    assert is_dup_target2 is False
