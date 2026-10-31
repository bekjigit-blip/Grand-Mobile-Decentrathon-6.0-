import re
from typing import Tuple, List, Dict, Any
from app.config import MANDATORY_HUMAN_CATEGORIES

# Textual markers
HACK_MARKERS = re.compile(
    r'\b(взлом|взломали|украли\s+аккаунт|сменили\s+почту|аккаунт\s+ұрланды|құпиясөз\s+ұрланды|akkaunt\s+buzildi|hacked|stolen\s+account)\b',
    re.IGNORECASE
)
PAYMENT_MARKERS = re.compile(
    r'\b(донат|grand\s+coins|списали\s+деньги|чек|төлем|коиндар|pul\s+yechildi|payment|coins)\b',
    re.IGNORECASE
)
APPEAL_MARKERS = re.compile(
    r'\b(обжалование|разбан|снизить\s+срок|ошибочный\s+бан|деморган\s+ни\s+за\s+что|жазаны\s+алып\s+тастаңыз|jazoni\s+bekor|unban)\b',
    re.IGNORECASE
)
ADMIN_MARKERS = re.compile(
    r'\b(жалоба\s+на\s+админа|блат\s+админа|әкімшіге\s+шағым|adminga\s+shikoyat|блат)\b',
    re.IGNORECASE
)
CHEAT_MARKERS = re.compile(
    r'\b(рванка|carshot|дамгер|damager|крашер|разносит\s+сервер|speedhack|летает|flying|аим|софт)\b',
    re.IGNORECASE
)

# Official priority mapping for all 14 official category codes
OFFICIAL_PRIORITY_MAP = {
    "security.account": "p0",
    "financial.donation": "p1",
    "complaint.cheats": "p1",
    "complaint.scam": "p1",
    "complaint.insult": "p2",
    "complaint.dm": "p2",
    "complaint.db": "p2",
    "complaint.nonrp": "p2",
    "complaint.greenzone": "p2",
    "complaint.admin": "p2",
    "appeal.punishment": "p2",
    "technical.bug": "p2",
    "question.help": "p3",
    "feedback.other": "p3"
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
    Strictly aligns with official taxonomy priorities and mandatory human routing conditions.
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
    elif PAYMENT_MARKERS.search(text_lower) and priority in {"p2", "p3"}:
        priority = "p1"
        reasons.append("Басымдық p1: Төлем немесе донат белгілері анықталды")
    else:
        reasons.append(f"Басымдық {priority}: Ресми таксономияға сәйкес ({category})")

    # --- Human Escalation Determination (Independent of early returns) ---
    needs_human = False

    # Check Category Conditions
    if category in MANDATORY_HUMAN_CATEGORIES:
        needs_human = True
        reasons.append(f"Адамға міндетті бағыттау: '{category}' санаты")

    # Check Textual Indicators
    if HACK_MARKERS.search(text_lower):
        needs_human = True
        reasons.append("Адамға бағыттау: Аккаунт қауіпсіздігіне байланысты оқиға")
    if PAYMENT_MARKERS.search(text_lower):
        needs_human = True
        reasons.append("Адамға бағыттау: Қаржылық төлемді тексеру қажет")
    if APPEAL_MARKERS.search(text_lower):
        needs_human = True
        reasons.append("Адамға бағыттау: Жазаны қайта қарау / апелляция")
    if CHEAT_MARKERS.search(text_lower):
        needs_human = True
        reasons.append("Адамға бағыттау: Чит немесе үшінші жақты бағдарламаны тексеру")
    if ADMIN_MARKERS.search(text_lower):
        needs_human = True
        reasons.append("Адамға бағыттау: Әкімшілік үстінен түскен шағым")

    # Low confidence or ambiguity
    if is_low_confidence:
        needs_human = True
        reasons.append("Адамға бағыттау: Ұқсастық ұпайы төмен болғандықтан модератор тексеруі қажет")
    if is_ambiguous:
        needs_human = True
        reasons.append("Адамға бағыттау: Екі санат арасындағы нәтиже жақын болғандықтан нақтылау қажет")

    return priority, needs_human, reasons
