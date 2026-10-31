import pytest
from app.rule_indexer import RuleIndexer
from app.triage_service import get_triage_service

def test_repeated_rule_numbers_isolation():
    """Ensure rule index preserves distinct identity for repeated point refs across sections."""
    indexer = RuleIndexer()
    indexer.build_index()

    # Verify that key_to_index uses section_id::ref
    keys = list(indexer.key_to_index.keys())
    assert any("1::1.1" in k for k in keys)
    assert any("2::2.1" in k for k in keys)
    assert any("3::3.1" in k for k in keys)

    # Check that search returns section_id and section_name
    results = indexer.search_rules("убийство без причины DM", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert "section_id" in top
    assert "section_name" in top
    assert "ref" in top
    assert "score" in top
    # Internal key must NOT be equal to ref
    assert top["ref"] != top["internal_key"]

def test_invalid_rule_citation_not_hallucinated():
    """Non-existent rule reference (e.g. 99.99) should not create a fake rule."""
    indexer = RuleIndexer()
    indexer.load_index()

    results = indexer.search_rules("помогите", rule_refs_raw=["99.99"])
    for r in results:
        assert r["ref"] != "99.99"

def test_cited_in_draft_reply_is_clean_string_list():
    """draft_reply.cited must be list of strings without technical prefixes."""
    service = get_triage_service()
    ticket = {
        "text": "Игрок Vanya_Shooter убил меня в Зеленой Зоне больницы",
        "rule_refs_raw": ["3.1"]
    }
    res = service.triage_ticket(ticket)
    cited = res["draft_reply"]["cited"]
    assert isinstance(cited, list)
    for c in cited:
        assert isinstance(c, str)
        assert "::" not in c  # No internal technical separator!
        assert "sec_" not in c  # No internal section ID in cited list!
    assert "Зелен" in res["draft_reply"]["text"] or "GZ" in res["draft_reply"]["text"] or "Правила" in res["draft_reply"]["text"]
