import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple

from app.cp1251_fixer import fix_cp1251_kazakh
from app.lexicon import expand_multilingual_tokens

# Regex patterns
URL_PATTERN = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
NICKNAME_PATTERN = re.compile(r'\b[A-Z][a-z]+_[A-Z][a-z]+\b')
RULE_REF_PATTERN = re.compile(
    r'\b(?:п\.?|пункт|статья|ереже|ережесі|бап|тармақ|rule|sec|section)?\s*'
    r'((?:ЖБ\s*)?(?:\d+\.)+\d+)\b',
    re.IGNORECASE
)
SERVER_PATTERN = re.compile(r'\b(?:сервер|серверде|сервере|server)\s*[:#]?\s*(\d{1,2})\b', re.IGNORECASE)
ACCOUNT_ID_PATTERN = re.compile(r'(?:id|номер|аккаунт|аккаунта|шот|#)\s*[:#]?\s*(\d{3,8})\b', re.IGNORECASE)
DIGITS_PATTERN = re.compile(r'\b\d{3,}\b')

# Phrases explicitly indicating NO evidence/screenshots provided
NO_EVIDENCE_PHRASES = [
    "скринов нет", "скрина нет", "нет скринов", "нет скриншота", "нету скрина",
    "без фрапса", "фрапса нет", "доказательств нет", "нет доказательств",
    "скрин жоқ", "дәлел жоқ", "дәлелдеме жоқ", "фрапс жоқ", "скриншот жоқ",
    "dalilsiz", "isbotsiz", "skrin yo'q", "screenshot yo'q", "no proof", "no screenshots"
]

def normalize_uzbek_apostrophes(text: str) -> str:
    """
    Normalizes various Unicode apostrophe and modifier characters (ʻ, ’, ‘, `, etc.)
    into a single standard ascii apostrophe (') so oʻldirdi and o'ldirdi are identical.
    """
    if not text:
        return text
    return re.sub(r'[\u02bb\u02bc\u2019\u2018\u0060]', "'", text)

def adapt_input_ticket(ticket_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified input adapter for HTTP and JSONL tickets:
    - Reads player text from 'messages' array, filtering only roles in {'player', 'reported_player', 'user'}.
    - Strictly excludes admin/system roles to prevent outcome/verdict data leakage.
    - Preserves attachments from messages AND top-level images_count / attachments without double-counting (Requirement 3).
    - Preserves reported_hash and reported_nick for accurate accused deduplication (Requirement 6).
    - Normalizes kind strictly to 'complaint', 'report', or None (no artificial transport kinds).
    """
    raw_kind = ticket_input.get("kind")
    if raw_kind:
        raw_kind_lower = str(raw_kind).strip().lower()
        if raw_kind_lower.startswith("complaint"):
            kind = "complaint"
        elif raw_kind_lower.startswith("report"):
            kind = "report"
        else:
            kind = raw_kind_lower
    else:
        kind = None

    ticket_id = str(ticket_input.get("ticket_id") or ticket_input.get("id") or "")
    reporter_hash = ticket_input.get("reporter_hash")
    created_at = ticket_input.get("created_at")

    # Preserve accused player metadata for deduplication (Requirement 6)
    reported_hash = ticket_input.get("reported_hash") or ticket_input.get("reported_player_hash")
    reported_nick = ticket_input.get("reported_nick") or ticket_input.get("reported_player") or ticket_input.get("reported_nickname")

    player_texts = []
    msg_attachments = 0

    if "messages" in ticket_input and isinstance(ticket_input["messages"], list):
        for msg in ticket_input["messages"]:
            if not isinstance(msg, dict):
                continue
            role = str(msg.get("role", "")).lower()
            # Only consider player and reported_player; never admin/system
            if role in {"player", "reported_player", "user", ""}:
                text_content = msg.get("text", "")
                if text_content:
                    player_texts.append(str(text_content))
                att = msg.get("attachments", 0)
                if isinstance(att, int):
                    msg_attachments += att
                elif isinstance(att, list):
                    msg_attachments += len(att)
    else:
        # Fallback to direct text fields
        text = ticket_input.get("text") or ticket_input.get("body") or ticket_input.get("message") or ""
        if text:
            player_texts.append(str(text))

    # Read top-level attachments / images_count even when messages exist (Requirement 3)
    top_images_count = ticket_input.get("images_count", 0)
    top_att = ticket_input.get("attachments", 0)
    top_attachments = 0
    if isinstance(top_att, int):
        top_attachments = max(top_images_count, top_att)
    elif isinstance(top_att, list):
        top_attachments = max(top_images_count, len(top_att))
    else:
        top_attachments = top_images_count

    # Combine message attachments and top-level attachments without double-counting
    total_attachments = max(msg_attachments, top_attachments)

    full_raw_text = " ".join(player_texts).strip()

    # Rule refs raw can be string or list
    raw_refs = ticket_input.get("rule_refs_raw") or ticket_input.get("rule_refs") or []
    if isinstance(raw_refs, str):
        rule_refs_list = [raw_refs.strip()] if raw_refs.strip() else []
    elif isinstance(raw_refs, list):
        rule_refs_list = [str(r).strip() for r in raw_refs if str(r).strip()]
    else:
        rule_refs_list = []

    # If reported_nick was not given explicitly, try finding nickname in text
    if not reported_nick:
        nicks = NICKNAME_PATTERN.findall(full_raw_text)
        if nicks:
            reported_nick = nicks[0]

    return {
        "kind": kind,
        "ticket_id": ticket_id,
        "reporter_hash": reporter_hash,
        "reported_hash": reported_hash,
        "reported_nick": reported_nick,
        "created_at": created_at,
        "raw_text": full_raw_text,
        "attachments_count": total_attachments,
        "rule_refs_raw": rule_refs_list,
        "server_hint": ticket_input.get("server") or ticket_input.get("server_lang")
    }

def process_ticket_text(
    raw_text: str,
    attachments_count: int = 0,
    explicit_rule_refs: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Standard text processor:
    - Normalizes Unicode and Uzbek apostrophes.
    - Fixes CP1251 Kazakh corrupted characters in search text.
    - Extracts primary nickname, rule refs (preserving multi-part like 1.2.7), server ID, and evidence.
    - Distinguishes actual evidence vs negation phrases like 'скринов нет'.
    """
    if raw_text is None:
        raw_text = ""

    # 1. Preserve original text unmodified
    original_text = raw_text

    # 2. Normalize Unicode (NFKC) and Uzbek apostrophes
    normalized = unicodedata.normalize('NFKC', raw_text)
    normalized = normalize_uzbek_apostrophes(normalized)

    # 3. Contextual CP1251 Kazakh restoration
    fixed_cp1251 = fix_cp1251_kazakh(normalized)

    # 4. Extract primary nickname
    nicks = NICKNAME_PATTERN.findall(fixed_cp1251)
    primary_nickname = nicks[0] if nicks else None

    # 5. Extract rule refs
    extracted_rule_refs = []
    for match in RULE_REF_PATTERN.finditer(fixed_cp1251):
        ref_cand = match.group(1).strip()
        if ref_cand and ref_cand not in extracted_rule_refs:
            extracted_rule_refs.append(ref_cand)

    if explicit_rule_refs:
        for r in explicit_rule_refs:
            if r and r not in extracted_rule_refs:
                extracted_rule_refs.append(r)

    # 6. Extract server number if mentioned
    server_match = SERVER_PATTERN.search(fixed_cp1251)
    extracted_server = server_match.group(1) if server_match else None

    # 7. Check for evidence fact vs negation
    text_lower = fixed_cp1251.lower()
    has_negation = any(neg in text_lower for neg in NO_EVIDENCE_PHRASES)

    if attachments_count > 0:
        has_evidence = True
    elif has_negation:
        has_evidence = False
    elif URL_PATTERN.search(fixed_cp1251):
        has_evidence = True
    elif any(pos in text_lower for pos in ["скрин есть", "скрины есть", "чек прикрепил", "прикрепил чек", "видео есть", "видеозапись приложена", "чек бар", "скрин бар", "видео бар"]):
        has_evidence = True
    else:
        has_evidence = False

    # 8. Token masking for clean search representation
    masked_text = URL_PATTERN.sub(' <url> ', fixed_cp1251)
    masked_text = EMAIL_PATTERN.sub(' <email> ', masked_text)
    masked_text = DIGITS_PATTERN.sub(' <digits> ', masked_text)

    cleaned_search_text = re.sub(r'\s+', ' ', masked_text).strip().lower()
    augmented_search_text = expand_multilingual_tokens(cleaned_search_text)

    return {
        "original_text": original_text,
        "fixed_text": fixed_cp1251,
        "normalized_text": cleaned_search_text,
        "augmented_text": augmented_search_text,
        "extracted": {
            "nickname": primary_nickname,
            "rule_refs": extracted_rule_refs,
            "has_evidence": bool(has_evidence),
            "server": extracted_server
        }
    }
