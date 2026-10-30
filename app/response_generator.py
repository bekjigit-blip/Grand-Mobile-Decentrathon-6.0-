from typing import Dict, Any, List
from app.templates import TEMPLATES

def format_draft_reply(
    lang: str,
    category: str,
    is_duplicate: bool,
    needs_human: bool,
    is_ambiguous: bool,
    has_attachments: bool,
    matched_rules: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Constructs the final draft_reply conforming strictly to Decentrathon 6.0:
    - draft_reply.cited: string[] containing only clean genuine rule point numbers (e.g. ['2.1']).
      NEVER outputs internal technical IDs like 'sec_dm::2.1'!
    - draft_reply.text: mentions the genuine section name in the player's language.
    - No false promises (no guaranteed unbans, refunds, or unilateral punishments).
    - No pretending to have seen the screenshot.
    """
    selected_lang = lang if lang in TEMPLATES else "ru"
    lang_templates = TEMPLATES[selected_lang]

    # Clean cited rule references (string[])
    clean_cited: List[str] = []
    section_name = "Жалпы ережелер / Общие правила"

    for r in matched_rules:
        # Don't cite pure RP definitions as point numbers if real points exist
        ref = r.get("ref", "")
        if ref and not r.get("is_rp_term", False):
            if ref not in clean_cited:
                clean_cited.append(ref)
            if not section_name or section_name == "Жалпы ережелер / Общие правила":
                section_name = r.get("section_name", section_name)

    # If no numbered point matched but an RP term did, use the RP term
    if not clean_cited and matched_rules:
        first_r = matched_rules[0]
        ref = first_r.get("ref", "")
        if ref and ref not in clean_cited:
            clean_cited.append(ref)
        section_name = first_r.get("section_name", section_name)

    rule_cite_str = f"тармақ {', '.join(clean_cited)}" if selected_lang == "kk" else (
        f"band {', '.join(clean_cited)}" if selected_lang == "uz" else (
            f"пункт {', '.join(clean_cited)}" if selected_lang == "ru" else f"rule {', '.join(clean_cited)}"
        )
    ) if clean_cited else ""

    # Select template action type
    if is_duplicate:
        template_text = lang_templates.get("duplicate_response", lang_templates["standard_receipt"])
    elif needs_human and category in {"donation_payment", "account_access"}:
        template_text = lang_templates.get("escalation_human", lang_templates["standard_receipt"])
    elif is_ambiguous:
        template_text = lang_templates.get("clarification_needed", lang_templates["standard_receipt"])
    elif not has_attachments and category in {"player_report_dm", "player_report_db", "player_report_scam", "player_report_cheats"}:
        # In RP servers, reports without video/photo proof cannot be resolved without proof
        template_text = lang_templates.get("insufficient_proof", lang_templates["standard_receipt"])
    elif needs_human:
        template_text = lang_templates.get("escalation_human", lang_templates["standard_receipt"])
    else:
        template_text = lang_templates.get("standard_receipt")

    # Interpolate section and rule citation
    reply_body = template_text.format(
        section_name=section_name,
        rule_cite=rule_cite_str
    ).strip()

    # Clean double spaces or dangling punctuation
    reply_body = " ".join(reply_body.split()).replace(", )", ")").replace("(, ", "(")

    return {
        "text": reply_body,
        "cited": clean_cited
    }
