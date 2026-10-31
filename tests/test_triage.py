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
    assert res["category"] == "report.payment"
    assert res["priority"] == "p1"
    assert res["needs_human"] is True

def test_mandatory_human_routing_for_hacked_account(triage_service):
    """Hacked account must be p0 and needs_human = True."""
    ticket = {
        "text": "Менің аккаунтымды біреу бұзып кіріп, паролін ауыстырып тастапты! Срочно көмектесіңізші!",
        "images_count": 0
    }
    res = triage_service.triage_ticket(ticket)
    assert res["category"] == "report.account"
    assert res["priority"] == "p0"
    assert res["needs_human"] is True

def test_mandatory_human_routing_for_appeal(triage_service):
    """Punishment appeals must mandate needs_human = True, complaint.admin, and priority p2."""
    ticket = {
        "text": "Администратор ошибочно посадил меня в деморган на 120 минут за ДБ, прошу снять наказание.",
        "images_count": 1
    }
    res = triage_service.triage_ticket(ticket)
    assert res["category"] == "complaint.admin"
    assert res["priority"] == "p2"
    assert res["needs_human"] is True

def test_ban_appeal_routing(triage_service):
    """Explicit ban appeal must route to complaint.admin and needs_human = True."""
    ticket = {
        "text": "Администратор дал мне бан за DM. Я не согласен с наказанием, прошу пересмотреть.",
        "images_count": 1
    }
    res = triage_service.triage_ticket(ticket)
    assert res["category"] == "complaint.admin"
    assert res["priority"] == "p2"
    assert res["needs_human"] is True

def test_mute_appeal_routing(triage_service):
    """Explicit mute appeal must route to complaint.admin and needs_human = True."""
    ticket = {
        "text": "Мне выдали мут за оскорбление родных, я с этим наказанием не согласен.",
        "images_count": 1
    }
    res = triage_service.triage_ticket(ticket)
    assert res["category"] == "complaint.admin"
    assert res["priority"] == "p2"
    assert res["needs_human"] is True

def test_kazakh_appeal_paraphrase(triage_service):
    """Kazakh paraphrase of punishment appeal must route to complaint.admin and needs_human = True."""
    ticket = {
        "text": "Әкімші берген жазамен келіспеймін, қайта қарауды сұраймын",
        "images_count": 0
    }
    res = triage_service.triage_ticket(ticket)
    assert res["category"] == "complaint.admin"
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

def test_messages_input_adapter_and_admin_filtering(triage_service):
    """Input with kind and messages array must filter out admin messages and read player text."""
    input_payload = {
        "kind": "complaint",
        "messages": [
            {"role": "player", "text": "Игрок Sergey_Kozlov оскорбил мою маму в чате!", "attachments": 1},
            {"role": "admin", "text": "Жабота рассмотрена, игрок заблокирован на 7 дней.", "attachments": 0}
        ]
    }
    res = triage_service.triage_ticket(input_payload)
    assert res["category"] == "complaint.insult"
    assert res["priority"] in ["p2", "p3"]
    assert res["extracted"]["nickname"] == "Sergey_Kozlov"
    assert res["extracted"]["has_evidence"] is True
    # Admin text must not be echoed in draft reply
    assert "заблокирован на 7 дней" not in res["draft_reply"]["text"]

def test_attachment_preservation_messages_plus_top_level(triage_service):
    """Top-level images_count: 3 with messages should preserve evidence."""
    input_payload = {
        "kind": "complaint",
        "images_count": 3,
        "messages": [
            {"role": "player", "text": "Игрок Alex_King ДМит без причины"}
        ]
    }
    res = triage_service.triage_ticket(input_payload)
    assert res["extracted"]["has_evidence"] is True

def test_evidence_negation_detection(triage_service):
    """If player explicitly writes 'скринов нет' / 'дәлел жоқ' and attachments == 0, has_evidence must be False."""
    ticket = {
        "text": "Игрок Ivan_Ivanov убил меня, но скринов нет и фрапса нет",
        "images_count": 0
    }
    res = triage_service.triage_ticket(ticket)
    assert res["extracted"]["has_evidence"] is False

def test_cheats_escalation_to_p1(triage_service):
    """Cheat reports with speedhack/flyhack must map to complaint.cheat and escalate to p1."""
    ticket = {
        "text": "Игрок Speed_Demon использует спидхак и летает над военной частью",
        "images_count": 1
    }
    res = triage_service.triage_ticket(ticket)
    assert res["category"] == "complaint.cheat"
    assert res["priority"] == "p1"
    assert res["needs_human"] is True

def test_semantic_threshold_rejects_forced_irrelevant_citation(triage_service):
    """If player specifies an arbitrary rule ref (e.g. 8.1) but text is total gibberish, cited list must be empty."""
    ticket = {
        "text": "zzzzzz qqqqqq asdfghjk",
        "rule_refs_raw": ["8.1"]
    }
    res = triage_service.triage_ticket(ticket)
    assert "8.1" not in res["draft_reply"]["cited"]

def test_question_returns_empty_citations(triage_service):
    """Informational questions must not cite combat or penal rules."""
    ticket = {
        "text": "Как устроиться на работу дальнобойщика?",
        "images_count": 0
    }
    res = triage_service.triage_ticket(ticket)
    assert res["category"] in ["report.question", "report.help"]
    assert res["draft_reply"]["cited"] == []

def test_sqlite_admin_action_persistence():
    """Verify that admin ticket actions persist and reload via deduplication SQLite functions."""
    from app.deduplication import save_admin_action, get_admin_actions
    ticket_id = "TICKET_TEST_SQLITE_PERSIST_1"
    save_admin_action(
        ticket_id=ticket_id,
        action="APPROVED",
        category="complaint.dm",
        priority="p2",
        assigned_to="Admin_Kairat",
        note="Игрок посажен в деморган"
    )

    actions = get_admin_actions(ticket_id)
    assert len(actions) > 0
    latest = actions[0]
    assert latest["action"] == "APPROVED"
    assert latest["category"] == "complaint.dm"
    assert latest["assigned_to"] == "Admin_Kairat"
    assert latest["note"] == "Игрок посажен в деморган"
