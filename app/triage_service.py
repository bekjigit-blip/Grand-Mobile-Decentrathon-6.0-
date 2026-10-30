import time
from typing import Dict, Any, List, Optional

from app.text_processor import process_ticket_text
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
            # Try to load existing cached indices or build from data/
            if not self.taxonomy_classifier.load_index():
                self.taxonomy_classifier.build_index()
            if not self.rule_indexer.load_index():
                self.rule_indexer.build_index()
            self._initialized = True

    def triage_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a single ticket and returns the standard Decentrathon 6.0 triage output.
        """
        self.initialize()

        raw_text = ticket.get("text") or ticket.get("body") or ticket.get("message") or ""
        images_count = ticket.get("images_count", 0)
        if "attachments" in ticket and isinstance(ticket["attachments"], list):
            images_count = max(images_count, len(ticket["attachments"]))

        ticket_id = str(ticket.get("ticket_id") or ticket.get("id") or f"TICKET_{int(time.time()*1000)}")
        reporter_hash = ticket.get("reporter_hash")
        created_at = ticket.get("created_at")
        hint_lang = ticket.get("lang") or ticket.get("server_lang")
        explicit_rule_refs = ticket.get("rule_refs_raw") or []

        # 1. Text processing & entity extraction
        processed = process_ticket_text(raw_text, images_count, explicit_rule_refs)
        extracted = processed["extracted"]

        # 2. Language detection (independent of server_lang)
        detected_lang = detect_language(raw_text, hint_lang)

        # 3. Category classification via TF-IDF prototypes & lexicon signals
        cat_result = self.taxonomy_classifier.classify(processed["augmented_text"], extracted)
        category = cat_result["category"]
        confidence = cat_result["confidence"]
        is_low_confidence = cat_result["is_low_confidence"]
        is_ambiguous = cat_result["is_ambiguous"]

        # 4. Priority & Human Escalation Determination
        priority, needs_human, priority_reasons = determine_priority_and_escalation(
            category=category,
            raw_text=raw_text,
            has_attachments=extracted["has_attachments"],
            is_low_confidence=is_low_confidence,
            is_ambiguous=is_ambiguous
        )

        # 5. Rule Search & Citation Verification
        matched_rules = self.rule_indexer.search_rules(
            query_text=processed["augmented_text"],
            top_k=3,
            rule_refs_raw=extracted["rule_refs_raw"]
        )

        # 6. Deduplication & Spam check (1-hour window with reporter_hash & created_at)
        is_spam_or_duplicate, dup_reason = check_and_record_duplicate(
            ticket_id=ticket_id,
            reporter_hash=reporter_hash,
            created_at_str=created_at,
            raw_text=raw_text,
            category=category
        )

        all_reasons = cat_result["reasons"] + priority_reasons
        if dup_reason:
            all_reasons.append(dup_reason)

        # 7. Draft reply formatting
        draft_reply = format_draft_reply(
            lang=detected_lang,
            category=category,
            is_duplicate=is_spam_or_duplicate,
            needs_human=needs_human,
            is_ambiguous=is_ambiguous,
            has_attachments=extracted["has_attachments"],
            matched_rules=matched_rules
        )

        return {
            "ticket_id": ticket_id,
            "lang": detected_lang,
            "category": category,
            "priority": priority,
            "is_spam_or_duplicate": bool(is_spam_or_duplicate),
            "extracted": extracted,
            "draft_reply": draft_reply,
            "needs_human": bool(needs_human),
            "confidence": float(confidence),
            "reasons": all_reasons,
            "matched_rules": matched_rules  # for UI display and detailed inspection
        }

# Global service instance
_triage_instance = None

def get_triage_service() -> TriageService:
    global _triage_instance
    if _triage_instance is None:
        _triage_instance = TriageService()
        _triage_instance.initialize()
    return _triage_instance
