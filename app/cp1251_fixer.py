import re

# Mapping of cp1251 Kazakh corrupted characters to modern Kazakh Cyrillic
# ќ -> қ (U+049B)
# ґ -> ғ (U+0493)
# ѕ -> ң (U+04A3)
# є -> ә (U+04D9)
# ј -> ө (U+04E9)
# ў -> ұ (U+04B1)
# ї -> ү (U+04AF)

CP1251_MAP = {
    'ќ': 'қ', 'Ќ': 'Қ',
    'ґ': 'ғ', 'Ґ': 'Ғ',
    'ѕ': 'ң', 'Ѕ': 'Ң',
    'є': 'ә', 'Є': 'Ә',
    'ј': 'ө', 'Ј': 'Ө',
    'ў': 'ұ', 'Ў': 'Ұ',
    'ї': 'ү', 'Ї': 'Ү'
}

UKRAINIAN_MARKERS = {
    'дякую', 'привіт', 'якщо', 'було', 'року', 'після', 'що', 'його', 'його',
    'також', 'цього', 'бути', 'мене', 'був', 'була', 'тобі', 'собі'
}

KAZAKH_ROOT_PATTERNS = [
    r'с[єе]лем', r'к[ґг]л[іi]к', r'[ґг]лт[іi]р', r'[ќк]ас[ќк]', r'жазал[ае][ѕн]ыз',
    r'б[ўу]л', r'ж[ўу]мыс', r'[ќк][ўу]пи[яе]', r'б[ўу]з', r'к[ґг]мек',
    r'ж[ўу]рг[іi]зуш[іi]', r'қ[ўу]жат', r'аккаун[ўу]т', r'к[єе]рек'
]

def is_ukrainian_context(text: str) -> bool:
    """Detect if the text is predominantly Ukrainian to avoid mangling genuine letters є, ї."""
    tokens = set(re.findall(r'[a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ\']+', text.lower()))
    return len(tokens.intersection(UKRAINIAN_MARKERS)) >= 2

def fix_cp1251_kazakh(text: str) -> str:
    """
    Context-aware fixer for CP1251 encoded Kazakh characters.
    Replaces corrupted codepoints into proper Kazakh Cyrillic without damaging genuine Ukrainian words.
    Always produces a normalized copy; original text remains preserved in ticket structures.
    """
    if not text:
        return text

    # Fast-path check: do any corrupted characters even exist in text?
    has_target_chars = any(ch in text for ch in CP1251_MAP)
    if not has_target_chars:
        return text

    is_ukr = is_ukrainian_context(text)

    result_chars = []
    for ch in text:
        if ch in CP1251_MAP:
            # If Ukrainian context is detected, preserve Ukrainian specific letters (є, ї, ґ)
            if is_ukr and ch in {'є', 'Є', 'ї', 'Ї', 'ґ', 'Ґ'}:
                result_chars.append(ch)
            else:
                result_chars.append(CP1251_MAP[ch])
        else:
            result_chars.append(ch)

    fixed_text = "".join(result_chars)

    # Contextual Kazakh word pattern fixes (e.g. кғлік -> көлік, ғлтір -> өлтір when ґ was typed instead of ј)
    if not is_ukr:
        fixed_text = re.sub(r'\bкғл([іi])к', r'көл\1к', fixed_text, flags=re.IGNORECASE)
        fixed_text = re.sub(r'\bғлт([іi])р', r'өлт\1р', fixed_text, flags=re.IGNORECASE)

    return fixed_text
