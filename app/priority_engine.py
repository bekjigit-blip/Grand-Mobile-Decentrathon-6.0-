import re
from typing import Tuple, List, Dict, Any
from app.config import MANDATORY_HUMAN_CATEGORIES

# Intent & textual markers
HACK_MARKERS = re.compile(
    r'\b(взлом|взломали|украли\s+аккаунт|сменили\s+почту|сменили\s+пароль|аккаунт\s+ұрланды|құпиясөз\s+ұрланды|паролін\s+ауыстыр|akkaunt\s+buzildi|parol\s+o\'zgar|hacked|stolen\s+account)\b',
    re.IGNORECASE
)
PAYMENT_MARKERS = re.compile(
    r'\b(донат|grand\s+coins|коины|коиндар|списали\s+деньги|деньги\s+ушли|чек|квитанция|төлем|каспи|kaspi|click|сбп|pul\s+yechildi|donat|payment|coins)\b',
    re.IGNORECASE
)
ADMIN_MARKERS = re.compile(
    r'\b(жалоба\s+на\s+админа|блат\s+админа|блатит|покрывает|әкімшіге\s+шағым|adminga\s+shikoyat|блат)\b',
    re.IGNORECASE
)
CHEAT_MARKERS = re.compile(
    r'\b(рванка|carshot|дамгер|damager|крашер|разносит\s+сервер|speedhack|летает|flying|аим|софт|читтер|читер|спидхак)\b',
    re.IGNORECASE
)
RMT_MARKERS = re.compile(
    r'\b(вирты|продажа\s+виртов|покупка\s+виртов|рмт|за\s+реал|за\s+рубли|за\s+тенге|вирт\s+сату|rmt)\b',
    re.IGNORECASE
)

# Comprehensive punishment appeal intent markers (covers Russian, Kazakh, Uzbek, English)
PUNISHMENT_APPEAL_MARKERS = re.compile(
    r'('
    r'не\s+согласен\s+с\s+наказанием|не\s+согласна\s+с\s+наказанием|с\s+этим\s+наказанием\s+не\s+согласен|'
    r'не\s+согласен\s+с\s+баном|не\s+согласен\s+с\s+мутом|не\s+согласен\s+с\s+деморганом|'
    r'прошу\s+пересмотреть|пересмотрите|пересмотр\s+наказания|'
    r'ошибочный\s+бан|ошибочный\s+мут|ошибочно\s+выдал|ошибочно\s+посадил|ошибочно\s+забанил|'
    r'бан\s+ни\s+за\s+что|мут\s+ни\s+за\s+что|деморган\s+ни\s+за\s+что|посадил\s+ни\s+за\s+что|'
    r'обжалование|обжаловать|апелляция|апелляци|разбан|разбаньте|размутьте|снизить\s+срок|снятие\s+наказания|'
    r'жазамен\s+келіспеймін|жазаға\s+келіспеймін|қате\s+бан|қате\s+мут|қате\s+жаза|қайта\s+қараңыз|қайта\s+қарауды\s+сұраймын|себепсіз\s+жаза|жазаны\s+алып\s+таста|'
    r'jazodan\s+noroziman|rozi\s+emasman|qayta\s+ko\'rib\s+chiqing|adashib\s+berilgan|jazoni\s+bekor|'
    r'disagree\s+with\s+punishment|wrongful\s+ban|wrongful\s+mute|please\s+reconsider|unban|unmute|appeal'
    r')',
    re.IGNORECASE
)

# Official priority mapping for all 14 official category codes
OFFICIAL_PRIORITY_MAP = {
    # report.*
    "report.account": "p0",
    "report.payment": "p1",
    "report.complaint": "p2",
    "report.question": "p3",
    "report.help": "p3",
    "report.offtopic": "p3",
    # complaint.*
    "complaint.cheat": "p1",
    "complaint.scam": "p1",
    "complaint.rmt_ads": "p1",
    "complaint.insult": "p2",
    "complaint.dm": "p2",
    "complaint.admin": "p2",
    "complaint.other": "p3",
    "complaint.invalid": "p3"
}

def determine_priority_and_escalation(
    category: str,
    raw_text: str,
    has_evidence: bool,
    is_low_confidence: bool,
    is_ambiguous: bool
) -> Tuple[str, bool, List[str]]:
    """
    Separately and deterministically computes Priority (p0-p3) and Human Escalation flag (needs_human).
    Strictly aligns with official taxonomy priorities and mandatory human routing conditions:
    - Ban/mute appeals mandate needs_human = True (Requirement 4).
    - Payments (report.payment) mandate needs_human = True, priority = p1.
    - Hacked accounts (report.account) mandate needs_human = True, priority = p0.
    - Cheats (complaint.cheat) mandate needs_human = True, priority = p1.
    - Admin complaints (complaint.admin) mandate needs_human = True, priority = p2.
    """
    reasons = []
    text_lower = raw_text.lower()

    # --- Priority Determination ---
    # 1. Base priority from official category
    priority = OFFICIAL_PRIORITY_MAP.get(category, "p2")

    # 2. Textual priority escalation
    if HACK_MARKERS.search(text_lower):
        priority = "p0"
        reasons.append("Басымдық p0: Мәтінде аккаунт ұрлануы немесе бұзылуы белгілері бар")
    elif CHEAT_MARKERS.search(text_lower) and priority in {"p2", "p3"}:
        priority = "p1"
        reasons.append("Басымдық p1: Серверге қауіп төндіретін чит/софт анықталды")
    elif RMT_MARKERS.search(text_lower) and priority in {"p2", "p3"}:
        priority = "p1"
        reasons.append("Басымдық p1: Вирт сату немесе RMT анықталды")
    elif PAYMENT_MARKERS.search(text_lower) and priority in {"p2", "p3"}:
        priority = "p1"
        reasons.append("Басымдық p1: Төлем немесе донат белгілері анықталды")
    else:
        reasons.append(f"Басымдық {priority}: Ресми таксономияға сәйкес ({category})")

    # --- Human Escalation Determination (Independent of category alone) ---
    needs_human = False

    # Check Category Conditions
    if category in MANDATORY_HUMAN_CATEGORIES:
        needs_human = True
        reasons.append(f"Адамға міндетті бағыттау: '{category}' санаты")

    # Check Textual Intent & Indicators
    if PUNISHMENT_APPEAL_MARKERS.search(text_lower):
        needs_human = True
        reasons.append("Адамға бағыттау: Жазаға келіспеу / жазаны қайта қарау / апелляция")

    if HACK_MARKERS.search(text_lower):
        needs_human = True
        reasons.append("Адамға бағыттау: Аккаунт қауіпсіздігіне байланысты оқиға")

    if PAYMENT_MARKERS.search(text_lower):
        needs_human = True
        reasons.append("Адамға бағыттау: Қаржылық төлемді тексеру қажет")

    if ADMIN_MARKERS.search(text_lower):
        needs_human = True
        reasons.append("Адамға бағыттау: Әкімшілік үстінен түскен шағым")

    if CHEAT_MARKERS.search(text_lower):
        needs_human = True
        reasons.append("Адамға бағыттау: Чит немесе үшінші жақты бағдарламаны тексеру")

    # Low confidence or ambiguity
    if is_low_confidence:
        needs_human = True
        reasons.append("Адамға бағыттау: Ұқсастық ұпайы төмен болғандықтан модератор тексеруі қажет")

    if is_ambiguous:
        needs_human = True
        reasons.append("Адамға бағыттау: Екі санат арасындағы нәтиже жақын болғандықтан нақтылау қажет")

    return priority, needs_human, reasons
