import pytest
import os
import json
from app.triage_service import get_triage_service
from app.predict import sanitize_input_ticket, run_batch_prediction

@pytest.fixture(scope="session")
def triage_service():
    service = get_triage_service()
    service.initialize()
    return service

def test_mandatory_human_routing_for_payments(triage_service):
    """Payment / donation tickets must mandate needs_human = True and priority p1."""
    ticket = {
        "text": "Донатил через Каспи 5000 тенге, деньги ушли, а коинов нет! Чек прикрепил.",
        "images_count": 1
    }
    res = triage_service.triage_ticket(ticket)
    assert res["category"] == "donation_payment"
    assert res["priority"] == "p1"
    assert res["needs_human"] is True

def test_mandatory_human_routing_for_hacked_account(triage_service):
    """Hacked account must be p0 and needs_human = True."""
    ticket = {
        "text": "Менің аккаунтымды біреу бұзып кіріп, паролін ауыстырып тастапты! Срочно көмектесіңізші!",
        "images_count": 0
    }
    res = triage_service.triage_ticket(ticket)
    assert res["category"] == "account_access"
    assert res["priority"] == "p0"
    assert res["needs_human"] is True

def test_mandatory_human_routing_for_appeal(triage_service):
    """Punishment appeals must mandate needs_human = True and priority p2."""
    ticket = {
        "text": "Администратор ошибочно посадил меня в деморган на 120 минут за ДБ, прошу снять наказание.",
        "images_count": 1
    }
    res = triage_service.triage_ticket(ticket)
    assert res["category"] == "appeal_punishment"
    assert res["priority"] == "p2"
    assert res["needs_human"] is True

def test_data_leakage_sanitization():
    """Ensure admin verdicts, statuses, and punishment notes are strictly scrubbed."""
    dirty_ticket = {
        "text": "Игрок Ivan_Ivanov убил меня на спавне",
        "verdict": "ACCEPTED",
        "punishment": "JAIL 60 MIN",
        "status": "RESOLVED",
        "admin_reply": "Игрок уже наказан."
    }
    clean = sanitize_input_ticket(dirty_ticket)
    assert "verdict" not in clean
    assert "punishment" not in clean
    assert "status" not in clean
    assert "admin_reply" not in clean
    assert clean["text"] == dirty_ticket["text"]

def test_batch_prediction_row_count_and_order(tmp_path):
    """JSONL output count and order must match input exactly."""
    in_file = tmp_path / "test_in.jsonl"
    out_file = tmp_path / "test_out.jsonl"

    sample_lines = [
        {"ticket_id": f"T-{i}", "text": f"Тестовый тикет #{i} помощь по моду"}
        for i in range(10)
    ]
    with open(in_file, "w", encoding="utf-8") as f:
        for t in sample_lines:
            f.write(json.dumps(t) + "\n")

    stats = run_batch_prediction(str(in_file), str(out_file))
    assert stats["total"] == 10
    assert stats["success"] == 10

    with open(out_file, "r", encoding="utf-8") as f:
        out_lines = [json.loads(line) for line in f]

    assert len(out_lines) == 10
    for i in range(10):
        assert out_lines[i]["ticket_id"] == f"T-{i}"
