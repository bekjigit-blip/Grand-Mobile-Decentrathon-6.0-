import re
import unicodedata
from typing import Dict, Any, List
from app.cp1251_fixer import fix_cp1251_kazakh
from app.lexicon import expand_multilingual_tokens

# Regex patterns
URL_PATTERN = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
NICKNAME_PATTERN = re.compile(r'\b[A-Z][a-zA-Z0-9]+_[A-Z][a-zA-Z0-9]+\b')
RULE_REF_PATTERN = re.compile(r'\b(?:п\.|пункт|пп\.|ереже|пункті|бап|ref|GZ|ЖБ)?\s*([0-9]+\.[0-9]+|GZ\s*[0-9\.]+|ЖБ\s*[0-9\.]+)\b', re.IGNORECASE)
ACCOUNT_ID_PATTERN = re.compile(r'(?:id|номер|аккаунт|аккаунта|шот|#)\s*[:#]?\s*(\d{3,8})\b', re.IGNORECASE)
DIGITS_PATTERN = re.compile(r'\b\d{3,}\b')

def process_ticket_text(raw_text: str, images_count: int = 0, explicit_rule_refs: List[str] = None) -> Dict[str, Any]:
    """
    Processes incoming ticket text according to strict Decentrathon 6.0 specs:
    - Retains original text completely unmodified.
    - Normalizes Unicode (NFKC) and collapses excessive whitespace.
    - Resolves Kazakh cp1251 letter corruptions in search representation.
    - Extracts structured entities: nicknames, rule_refs_raw, ids, has_attachments.
    - Normalizes tokens: replaces <url>, <email>, <digits> for clean TF-IDF feature space.
    - Enhances normalized text with cross-lingual semantic lexicon tokens.
    """
    if raw_text is None:
        raw_text = ""

    # 1. Preserve original text intact
    original_text = raw_text

    # 2. Unicode normalization (NFKC)
    normalized = unicodedata.normalize('NFKC', raw_text)

    # 3. Contextual CP1251 Kazakh fix
    fixed_cp1251 = fix_cp1251_kazakh(normalized)

    # 4. Extract entities BEFORE token replacement
    extracted_nicknames = list(set(NICKNAME_PATTERN.findall(fixed_cp1251)))
    
    extracted_rule_refs = []
    for match in RULE_REF_PATTERN.finditer(fixed_cp1251):
        ref_candidate = match.group(1).strip()
        if ref_candidate and ref_candidate not in extracted_rule_refs:
            extracted_rule_refs.append(ref_candidate)

    if explicit_rule_refs:
        for r in explicit_rule_refs:
            if r and r not in extracted_rule_refs:
                extracted_rule_refs.append(r)

    extracted_ids = list(set(ACCOUNT_ID_PATTERN.findall(fixed_cp1251)))
    has_attachments = (images_count > 0) or bool(URL_PATTERN.search(fixed_cp1251)) or ("скрин" in fixed_cp1251.lower() or "чек" in fixed_cp1251.lower() or "фрапс" in fixed_cp1251.lower())

    # 5. Mask URLs, emails, standalone digits in normalized search text
    masked_text = URL_PATTERN.sub(' <url> ', fixed_cp1251)
    masked_text = EMAIL_PATTERN.sub(' <email> ', masked_text)
    masked_text = DIGITS_PATTERN.sub(' <digits> ', masked_text)

    # Clean whitespace and case-fold for search
    cleaned_search_text = re.sub(r'\s+', ' ', masked_text).strip().lower()

    # 6. Cross-lingual semantic lexicon augmentation
    augmented_search_text = expand_multilingual_tokens(cleaned_search_text)

    return {
        "original_text": original_text,
        "normalized_text": cleaned_search_text,
        "augmented_text": augmented_search_text,
        "extracted": {
            "nicknames": extracted_nicknames,
            "rule_refs_raw": extracted_rule_refs,
            "ids": extracted_ids,
            "has_attachments": bool(has_attachments)
        }
    }
