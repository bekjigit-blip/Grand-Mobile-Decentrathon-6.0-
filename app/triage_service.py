import time
from typing import Dict, Any, List, Optional

from app.text_processor import adapt_input_ticket, process_ticket_text
from app.language_detector import detect_language
from app.taxonomy_classifier import TaxonomyClassifier
from app.rule_indexer import RuleIndexer
from app.priority_engine import determine_priority_and_escalation
from app.deduplication import check_and_record_duplicate
from app.response_generator import format_draft_reply

class TriageService:
    def __init__(self):
        self.taxonomy_classifier = TaxonomyClassifier()
        self.rule_indexer = RuleIndexer()
        self._initialized = False

    def initialize(self):
        if not self._initialized:
            if not self.taxonomy_classifier.load_index():
                self.taxonomy_classifier.build_index()
            if not self.rule_indexer.load_index():
                self.rule_indexer.build_index()
            self._initialized = True

    def triage_ticket(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified triage pipeline strictly conforming to official Decentrathon 6.0 contract:
        - Accepts messages format: {kind, messages: [{role, text, attachments}]}
        - Or legacy format: {text, images_count, rule_refs_raw}
        - Returns:
          {
            "lang": "kk",
            "category": "complaint.insult",
            "priority": "p2",
            "is_spam_or_duplicate": false,
            "extracted": {
              "nickname": "Arman_Petrov",
              "rule_refs": [],
              "has_evidence": true,
              "server": null
            },
            "draft_reply": {
              "lang": "kk",
              "text": "...",
              "cited": []
            },
            "needs_human": true,
            "confidence": 0.0,
            "reasons": []
          }
        """
        self.initialize()

        # 1. Adapt input (filters out admin messages, unifies attachments)
        adapted = adapt_input_ticket(raw_input)
        raw_text = adapted["raw_text"]
        ticket_id = adapted["ticket_id"] or f"TICKET_{int(time.time()*1000)}"
        reporter_hash = adapted["reporter_hash"]
        created_at = adapted["created_at"]
        kind = adapted["kind"]

        # 2. Text processing and structured entity extraction
        processed = process_ticket_text(
            raw_text=raw_text,
            attachments_count=adapted["attachments_count"],
            explicit_rule_refs=adapted["rule_refs_raw"]
        )
        extracted = processed["extracted"]

        # 3. Multilingual language detection (runs on CP1251-restored text)
        detected_lang = detect_language(processed["fixed_text"], adapted.get("server_hint"))

        # 4. Taxonomy classification with kind constraint
        cat_result = self.taxonomy_classifier.classify(
            text=processed["augmented_text"],
            extracted=extracted,
            kind_constraint=kind
        )
        category = cat_result["category"]
        confidence = cat_result["confidence"]
        is_low_confidence = cat_result["is_low_confidence"]
        is_ambiguous = cat_result["is_ambiguous"]

        # 5. Deterministic priority and human escalation
        priority, needs_human, priority_reasons = determine_priority_and_escalation(
            category=category,
            raw_text=raw_text,
            has_evidence=extracted["has_evidence"],
            is_low_confidence=is_low_confidence,
            is_ambiguous=is_ambiguous
        )

        # 6. Rule search with category relevance constraint and semantic relevance gate
        matched_rules = self.rule_indexer.search_rules(
            query_text=processed["augmented_text"],
            category=category,
            top_k=3,
            rule_refs_raw=extracted["rule_refs"]
        )

        # 7. Deduplication within 1-hour window with accused player differentiation (Requirement 6)
        is_spam_or_duplicate, dup_reason = check_and_record_duplicate(
            ticket_id=ticket_id,
            reporter_hash=reporter_hash,
            created_at_str=created_at,
            raw_text=raw_text,
            category=category,
            reported_hash=adapted.get("reported_hash"),
            reported_nick=adapted.get("reported_nick")
        )

        all_reasons = cat_result["reasons"] + priority_reasons
        if dup_reason:
            all_reasons.append(dup_reason)

        # 8. Draft reply generation
        draft_reply = format_draft_reply(
            lang=detected_lang,
            category=category,
            is_duplicate=is_spam_or_duplicate,
            needs_human=needs_human,
            is_ambiguous=is_ambiguous,
            has_evidence=extracted["has_evidence"],
            matched_rules=matched_rules
        )

        # Result matching the exact Decentrathon 6.0 contract
        result = {
            "lang": detected_lang,
            "category": category,
            "priority": priority,
            "is_spam_or_duplicate": bool(is_spam_or_duplicate),
            "extracted": {
                "nickname": extracted["nickname"],
                "rule_refs": extracted["rule_refs"],
                "has_evidence": bool(extracted["has_evidence"]),
                "server": extracted["server"]
            },
            "draft_reply": {
                "lang": draft_reply["lang"],
                "text": draft_reply["text"],
                "cited": draft_reply["cited"]
            },
            "needs_human": bool(needs_human),
            "confidence": float(confidence),
            "reasons": all_reasons,
            # Auxiliary fields for UI
            "ticket_id": ticket_id,
            "matched_rules": matched_rules
        }

        return result

_triage_instance = None

def get_triage_service() -> TriageService:
    global _triage_instance
    if _triage_instance is None:
        _triage_instance = TriageService()
        _triage_instance.initialize()
    return _triage_instance
