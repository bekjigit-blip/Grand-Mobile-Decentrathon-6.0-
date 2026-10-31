import re
from typing import Optional

KAZAKH_SPECIFIC_LETTERS = set('әіңғүұқөһӘІҢҒҮҰҚӨҺ')

KAZAKH_KEYWORDS = {
    'сәлеметсіз', 'сәлем', 'көмек', 'болды', 'және', 'деген', 'өлтірді', 'ақша',
    'рахмет', 'болады', 'қандай', 'жоқ', 'жазалаңыздаршы', 'жазалаңыз', 'көлікпен',
    'машинамен', 'алдап', 'құпиясөз', 'жұмыс', 'шағым', 'ереже', 'айтып', 'кетті',
    'қылып', 'тұрғанда', 'келіп', 'атып', 'басып', 'қорлады', 'былапыт'
}

UZBEK_KEYWORDS = {
    'salom', 'yordam', 'o\'yin', 'akkaunt', 'pul', 'bo\'ldi', 'lekin', 'qildi',
    'bor', 'yo\'q', 'iltimos', 'nima', 'bering', 'o\'ldirdi', 'sababsiz', 'otdi',
    'tushmadi', 'yechildi', 'so\'mga', 'donat', 'chora', 'ko\'ring', 'shikoyat',
    'qamoqqa', 'mashina', 'moshina', 'aldadi', 'so\'kdi', 'so\'kindi', 'haqorat'
}

SPANISH_KEYWORDS = {
    'hola', 'gracias', 'por', 'favor', 'jugador', 'mató', 'mato', 'cuenta',
    'servidor', 'sancionen', 'dinero', 'ayuda', 'estaba', 'juego', 'revisen',
    'reporte', 'baneo'
}

PORTUGUESE_KEYWORDS = {
    'olá', 'ola', 'obrigado', 'por', 'favor', 'jogador', 'matou', 'conta',
    'servidor', 'moedas', 'caiu', 'ajuda', 'jogo', 'comprovante', 'dinheiro',
    'denúncia', 'denuncia'
}

ENGLISH_KEYWORDS = {
    'hello', 'hi', 'help', 'please', 'player', 'kill', 'killed', 'car', 'server',
    'cheat', 'cheater', 'ban', 'report', 'stolen', 'hacked', 'money', 'reason',
    'speedhack', 'admin', 'driving', 'spawn'
}

def detect_language(text: str, hint_lang: Optional[str] = None) -> str:
    """
    Detect text language among: ru, kk, uz, en, es, pt.
    Should be called on CP1251-restored and apostrophe-normalized text.
    """
    if not text or not text.strip():
        return hint_lang if hint_lang in {'ru', 'kk', 'uz', 'en', 'es', 'pt'} else 'ru'

    cleaned = text.lower()
    # Normalize apostrophes for uniform word token matching
    cleaned = re.sub(r'[\u02bb\u02bc\u2019\u2018\u0060]', "'", cleaned)

    tokens = set(re.findall(r'[a-zA-Zа-яА-ЯёЁәіңғүұқөһӘІҢҒҮҰҚӨҺo\'g\']+', cleaned))

    # 1. Kazakh detection (distinctive Cyrillic letters or Kazakh vocabulary)
    kazakh_letters_count = sum(1 for ch in cleaned if ch in KAZAKH_SPECIFIC_LETTERS)
    kazakh_word_matches = len(tokens.intersection(KAZAKH_KEYWORDS))
    if kazakh_letters_count >= 1 or kazakh_word_matches >= 1:
        return 'kk'

    # 2. Uzbek detection (Latin with apostrophes or typical Uzbek vocabulary)
    uzbek_word_matches = len(tokens.intersection(UZBEK_KEYWORDS))
    if uzbek_word_matches >= 1 or ("o'" in cleaned or "g'" in cleaned and any(w in cleaned for w in ['bilan', 'uchun', 'qilish', 'bolgan', 'kerak'])):
        return 'uz'

    # 3. Spanish detection
    spanish_word_matches = len(tokens.intersection(SPANISH_KEYWORDS))
    if spanish_word_matches >= 2:
        return 'es'

    # 4. Portuguese detection
    portuguese_word_matches = len(tokens.intersection(PORTUGUESE_KEYWORDS))
    if portuguese_word_matches >= 2:
        return 'pt'

    # 5. English detection
    latin_chars = sum(1 for ch in cleaned if 'a' <= ch <= 'z')
    cyrillic_chars = sum(1 for ch in cleaned if 'а' <= ch <= 'я' or ch in 'ё')

    if latin_chars > cyrillic_chars * 2:
        if len(tokens.intersection(ENGLISH_KEYWORDS)) >= 1:
            return 'en'
        if spanish_word_matches >= 1:
            return 'es'
        if portuguese_word_matches >= 1:
            return 'pt'
        return 'en'

    # 6. Cyrillic text without Kazakh markers is Russian
    if cyrillic_chars > 0:
        return 'ru'

    if hint_lang in {'ru', 'kk', 'uz', 'en', 'es', 'pt'}:
        return hint_lang
    return 'ru'
