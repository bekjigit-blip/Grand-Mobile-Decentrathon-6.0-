from typing import Dict, Any, Tuple, List
import re
from app.config import MANDATORY_HUMAN_CATEGORIES

# Textual markers for priority escalation & human routing
P0_MARKERS = re.compile(r'\b(взлом|взломали|украли\s+аккаунт|сменили\s+почту|аккаунт\s+ұрланды|құпиясөз\s+ұрланды|akkaunt\s+buzildi|hacked|stolen\s+account)\b', re.IGNORECASE)
P1_PAYMENT_MARKERS = re.compile(r'\b(донат|grand\s+coins|списали\s+деньги|чек|төлем|коиндар|pul\s+yechildi|payment|coins)\b', re.IGNORECASE)
P1_SEVERE_CHEAT_MARKERS = re.compile(r'\b(рванка|carshot|дамгер|damager|крашер|разносит\s+сервер)\b', re.IGNORECASE)
P2_APPEAL_MARKERS = re.compile(r'\b(обжалование|разбан|снизить\s+срок|ошибочный\s+бан|деморган\s+ни\s+за\s+что|жазаны\s+алып\s+тастаңыз|jazoni\s+bekor)\b', re.IGNORECASE)
P2_ADMIN_MARKERS = re.compile(r'\b(жалоба\s+на\s+админа|блат\s+админа|әкімшіге\s+шағым|adminga\s+shikoyat)\b', re.IGNORECASE)

def determine_priority_and_escalation(
    category: str,
    raw_text: str,
    has_attachments: bool,
    is_low_confidence: bool,
    is_ambiguous: bool
) -> Tuple[str, bool, List[str]]:
    """
    Evaluates priority (p0-p3) and human escalation flag in strict documented order:
    1. p0 (Critical): Account security breaches, password theft, severe server crashes.
    2. p1 (High): Financial payments / donation issues, severe active server-laggers/cheats, major scam.
    3. p2 (Medium): Standard player complaints (DM, DB, NonRP, GZ, chat), punishment appeals, admin complaints, bugs.
    4. p3 (Low): General help questions, GPS/jobs guides, suggestions/feedback.

    Note: Attachments (images_count) DO NOT automatically escalate p2 complaints to p1!
    Mandatory human routing is triggered by category or textual markers for:
    - Payments/donations
    - Account access/theft
    - Punishment appeals
    - Admin complaints
    - Ambiguous / low-confidence classifications
    """
    reasons = []
    text_lower = raw_text.lower()

    # --- Step 1: Check p0 (Critical) ---
    if category == "account_access" or P0_MARKERS.search(text_lower):
        priority = "p0"
        needs_human = True
        reasons.append("Басымдық p0: Аккаунт қауіпсіздігіне немесе ұрлануына қатысты мәселе (Адамға міндетті жіберу)")
        return priority, needs_human, reasons

    # --- Step 2: Check p1 (High) ---
    if category == "donation_payment" or P1_PAYMENT_MARKERS.search(text_lower) and "рубл" in text_lower or "теңге" in text_lower or "сом" in text_lower:
        priority = "p1"
        needs_human = True
        reasons.append("Басымдық p1: Қаржылық төлем / Grand Coins донат мәселесі (Адамға міндетті жіберу)")
        return priority, needs_human, reasons

    if category == "player_report_cheats" and P1_SEVERE_CHEAT_MARKERS.search(text_lower):
        priority = "p1"
        needs_human = False  # Standard severe cheat report can be triaged with high priority
        reasons.append("Басымдық p1: Сервер тұрақтылығына қауіп төндіретін зиянды чит/рванка анықталды")
        return priority, needs_human, reasons

    if category == "player_report_scam":
        priority = "p1"
        needs_human = True
        reasons.append("Басымдық p1: Мүлікті / көлікті NonRP алдап тартып алу (Адамға міндетті жіберу)")
        return priority, needs_human, reasons

    # --- Step 3: Check p2 (Medium) ---
    if category in {
        "player_report_dm", "player_report_db", "player_report_greenzone",
        "player_report_nonrp", "player_report_insult", "appeal_punishment",
        "admin_complaint", "gameplay_bug"
    }:
        priority = "p2"
        # Determine human escalation
        if category in MANDATORY_HUMAN_CATEGORIES or P2_APPEAL_MARKERS.search(text_lower) or P2_ADMIN_MARKERS.search(text_lower):
            needs_human = True
            reasons.append(f"Басымдық p2: '{category}' санаты адам бақылауын қажет етеді (әкімшілік / жаза шағымы)")
        else:
            needs_human = False
            reasons.append(f"Басымдық p2: Ойыншылар арасындағы стандартты ереже бұзушылық немесе баг")

        # Clarification / low confidence trigger
        if is_low_confidence or is_ambiguous:
            needs_human = True
            reasons.append("Классификация ұқсастығы төмен немесе екіұшты болғандықтан адам тексеруі белгіленді")

        return priority, needs_human, reasons

    # --- Step 4: Check p3 (Low) ---
    priority = "p3"
    needs_human = False
    reasons.append(f"Басымдық p3: Ақпараттық сұрақ немесе жалпы ұсыныс/пікір ({category})")

    if is_low_confidence or is_ambiguous:
        needs_human = True
        reasons.append("Төмен ұқсастық ұпайы себепті адам бақылауына жолданды")

    return priority, needs_human, reasons
