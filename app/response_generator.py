from typing import Dict, Any, List
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
      NEVER outputs internal keys ('sec_dm::2.1') or RP definitions ('DM (DeathMatch)').
    - If no relevant rule passed the semantic threshold, cited is [].
    - Body text names the section.
    """
    selected_lang = lang if lang in TEMPLATES else "ru"
    lang_templates = TEMPLATES[selected_lang]

    # Clean cited rule references (string[])
    clean_cited: List[str] = []
    section_name = ""

    for r in matched_rules:
        # Strictly ignore RP definitions in cited point numbers
        if r.get("is_rp_term", False):
            continue
        ref = str(r.get("ref", "")).strip()
        if ref and ref not in clean_cited:
            clean_cited.append(ref)
            if not section_name:
                section_name = r.get("section_name", "")

    rule_cite_str = ""
    if clean_cited:
        if selected_lang == "kk":
            rule_cite_str = f"тармақ {', '.join(clean_cited)}"
        elif selected_lang == "uz":
            rule_cite_str = f"band {', '.join(clean_cited)}"
        elif selected_lang == "ru":
            rule_cite_str = f"пункт {', '.join(clean_cited)}"
        else:
            rule_cite_str = f"rule {', '.join(clean_cited)}"

    sec_display = section_name if section_name else (
        "Сервер ережелері" if selected_lang == "kk" else (
            "Server qoidalari" if selected_lang == "uz" else "Правила сервера"
        )
    )

    # Action type template selection
    if is_duplicate:
        template_text = lang_templates.get("duplicate_response", lang_templates["standard_receipt"])
    elif needs_human and category in {"financial.donation", "security.account"}:
        template_text = lang_templates.get("escalation_human", lang_templates["standard_receipt"])
    elif is_ambiguous:
        template_text = lang_templates.get("clarification_needed", lang_templates["standard_receipt"])
    elif not has_evidence and category in {"complaint.dm", "complaint.db", "complaint.scam", "complaint.cheats", "complaint.insult"}:
        template_text = lang_templates.get("insufficient_proof", lang_templates["standard_receipt"])
    elif needs_human:
        template_text = lang_templates.get("escalation_human", lang_templates["standard_receipt"])
    else:
        template_text = lang_templates.get("standard_receipt")

    reply_body = template_text.format(
        section_name=sec_display,
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
    import re
    cleaned = re.sub(r'\s+', ' ', text)
    cleaned = cleaned.replace(" (, )", "").replace("(, )", "").replace(" ()", "")
    return cleaned.strip()
