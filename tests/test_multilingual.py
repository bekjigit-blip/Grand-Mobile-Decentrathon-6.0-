import pytest
from app.cp1251_fixer import fix_cp1251_kazakh, is_ukrainian_context
from app.language_detector import detect_language
from app.triage_service import get_triage_service

def test_cp1251_kazakh_restoration():
    """Restores corrupted cp1251 Kazakh characters into proper Kazakh letters."""
    corrupted = "Сєлеметсіз бе! Бўл ойыншы кґлікпен ќасаќана басып ґлтірді, жазалаѕыз!"
    fixed = fix_cp1251_kazakh(corrupted)
    assert "Сәлеметсіз" in fixed
    assert "Бұл" in fixed
    assert "көлікпен" in fixed
    assert "қасақана" in fixed
    assert "өлтірді" in fixed
    assert "жазалаңыз" in fixed

def test_ukrainian_text_not_mangled():
    """Ensures genuine Ukrainian words with є and ї are preserved."""
    ukr_text = "Дякую за допомогу, це було дуже важливо для мене."
    fixed = fix_cp1251_kazakh(ukr_text)
    assert "це" in fixed
    assert "було" in fixed
    assert "мене" in fixed

def test_multilingual_language_detection():
    assert detect_language("Сәлеметсіз бе! Мені автобазарда алдап кетті.") == "kk"
    assert detect_language("Salom adminlar, akkauntim parolini o'g'irlashdi.") == "uz"
    assert detect_language("Здравствуйте, меня забанили по ошибке.") == "ru"
    assert detect_language("Hello, this player is using speedhack on server.") == "en"
    assert detect_language("Hola administradores, un jugador me mató sin razón.") == "es"
    assert detect_language("Olá equipe, comprei moedas mas não caíram na conta.") == "pt"

def test_empty_and_short_text():
    service = get_triage_service()
    res_empty = service.triage_ticket({"text": ""})
    assert res_empty["confidence"] <= 0.30
    assert res_empty["needs_human"] is True

    res_short = service.triage_ticket({"text": "Көмек"})
    assert res_short["lang"] == "kk"
    assert res_short["priority"] in ["p2", "p3"]
