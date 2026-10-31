import re
from typing import Dict, Any, List
from collections import OrderedDict
from app.templates import TEMPLATES

def format_draft_reply(
    lang: str,
    category: str,
    is_duplicate: bool,
    needs_human: bool,
    is_ambiguous: bool,
    has_evidence: bool,
    matched_rules: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Constructs the final draft_reply conforming strictly to official Decentrathon 6.0 schema:
    - draft_reply: { "lang": "kk", "text": "...", "cited": ["2.1"] }
    - draft_reply.cited: string[] containing only actual rule point numbers.
      NEVER outputs internal keys ('2::2.1') or RP definitions ('DM (DeathMatch)').
    - Correctly groups citations under their respective section names without conflating sections (Requirement 5).
    - If no relevant rule passed the semantic threshold, cited is [].
    """
    selected_lang = lang if lang in TEMPLATES else "ru"
    lang_templates = TEMPLATES[selected_lang]

    # Clean cited rule references (string[]) and group by section
    clean_cited: List[str] = []
    section_to_points: Dict[str, List[str]] = OrderedDict()

    for r in matched_rules:
        # Strictly ignore RP definitions in cited point numbers
        if r.get("is_rp_term", False):
            continue
        ref = str(r.get("ref", "")).strip()
        sec_name = str(r.get("section_name", "")).strip()
        if not sec_name:
            sec_name = "Сервер ережелері" if selected_lang == "kk" else "Правила сервера"

        if ref and ref not in clean_cited:
            clean_cited.append(ref)
            if sec_name not in section_to_points:
                section_to_points[sec_name] = []
            if ref not in section_to_points[sec_name]:
                section_to_points[sec_name].append(ref)

    # Format multi-section citation string accurately (Requirement 5)
    section_clauses = []
    for sec, pts in section_to_points.items():
        if selected_lang == "kk":
            pts_str = f"тармақ {', '.join(pts)}" if pts else ""
        elif selected_lang == "uz":
            pts_str = f"band {', '.join(pts)}" if pts else ""
        elif selected_lang == "ru":
            pts_str = f"пункт {', '.join(pts)}" if pts else ""
        else:
            pts_str = f"rule {', '.join(pts)}" if pts else ""

        if pts_str:
            section_clauses.append(f"{sec}, {pts_str}")
        else:
            section_clauses.append(sec)

    if section_clauses:
        section_display = "; ".join(section_clauses)
        rule_cite_str = ""
    else:
        section_display = "Сервер ережелері" if selected_lang == "kk" else (
            "Server qoidalari" if selected_lang == "uz" else "Правила сервера"
        )
        rule_cite_str = ""

    # Action type template selection with official 14 categories
    if is_duplicate:
        template_text = lang_templates.get("duplicate_response", lang_templates["standard_receipt"])
    elif needs_human and category in {"report.payment", "report.account"}:
        template_text = lang_templates.get("escalation_human", lang_templates["standard_receipt"])
    elif is_ambiguous:
        template_text = lang_templates.get("clarification_needed", lang_templates["standard_receipt"])
    elif not has_evidence and category in {"complaint.dm", "complaint.scam", "complaint.cheat", "complaint.insult", "complaint.other"}:
        template_text = lang_templates.get("insufficient_proof", lang_templates["standard_receipt"])
    elif needs_human:
        template_text = lang_templates.get("escalation_human", lang_templates["standard_receipt"])
    else:
        template_text = lang_templates.get("standard_receipt")

    reply_body = template_text.format(
        section_name=section_display,
        rule_cite=rule_cite_str
    ).strip()

    # Clean up double punctuation if rule_cite was empty
    reply_body = re_clean_spaces(reply_body)

    return {
        "lang": selected_lang,
        "text": reply_body,
        "cited": clean_cited
    }

def re_clean_spaces(text: str) -> str:
    cleaned = re.sub(r'\s+', ' ', text)
    cleaned = cleaned.replace(" (, )", "").replace("(, )", "").replace(" ()", "")
    cleaned = cleaned.replace(" (, ", " (").replace(", )", ")")
    return cleaned.strip()
