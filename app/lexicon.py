import re

LEXICON_VERSION = "1.0.0"

# Mapping patterns from Kazakh, Uzbek, and English to Russian RP rule keywords
# This provides the semantic bridge allowing offline TF-IDF to link multilingual tickets to Russian rules
CROSS_LINGUAL_BRIDGES = [
    # DM (Deathmatch)
    (r'\b(ө[лl]т[іi]рд[іi]|атып\s+тастады|оқ\s+атты|себепсіз\s+ату)\b', ' DM убийство нанесение урона без причины '),
    (r'\b(o[\'`]?ldirdi|sababsiz\s+otdi|otib\s+tashladi)\b', ' DM убийство нанесение урона без причины '),
    (r'\b(killed\s+me|no\s+reason\s+kill|deathmatch)\b', ' DM убийство нанесение урона без причины '),

    # DB (DriveBy / Ramming)
    (r'\b(к[өо]л[іi]кпен\s+баст[ыі]|машинамен\s+соқт[ыі]|қағып\s+кетт[іi]|көлікпен\s+қақты)\b', ' DB DriveBy наезд автомобилем таран '),
    (r'\b(moshina\s+bilan\s+bosdi|mashina\s+bosdi|turtib\s+ketdi)\b', ' DB DriveBy наезд автомобилем таран '),
    (r'\b(car\s+ramming|ran\s+over\s+me|driveby)\b', ' DB DriveBy наезд автомобилем таран '),

    # Green Zone (GZ)
    (r'\b(жасыл\s+аймақ|ауруханада\s+атыс|спавнда\s+атыс)\b', ' Зеленая Зона GZ Green Zone больница спавн '),
    (r'\b(yashil\s+hudud|kasalxona\s+oldida\s+otishma)\b', ' Зеленая Зона GZ Green Zone больница спавн '),
    (r'\b(green\s+zone|safe\s+zone)\b', ' Зеленая Зона GZ Green Zone больница спавн '),

    # Cheats & Software
    (r'\b(ұшып\s+жүр|жылдам\s+жүгіру|бағдарлама|софт|аимбот)\b', ' читы софт AIM Speedhack рванка вредоносное по '),
    (r'\b(uchib\s+yuribdi|tezlik\s+cheati|soft|aimbot)\b', ' читы софт AIM Speedhack рванка вредоносное по '),
    (r'\b(speedhack|flying\s+car|teleporting|aimbot)\b', ' читы софт AIM Speedhack рванка вредоносное по '),

    # Scam & Fraud
    (r'\b(алдап\s+кетт[іi]|к[өо]л[іi]кт[іi]\s+тартып\s+алды|ақшамды\s+бермед[іi]|айырбастауда\s+алдады)\b', ' NonRP обман развод скам трейд мошенничество '),
    (r'\b(aldab\s+ketdi|mashinamni\s+olib\s+qo[\'`]?ydi|pullarimni\s+bermadi)\b', ' NonRP обман развод скам трейд мошенничество '),
    (r'\b(scammed\s+me|trade\s+scam|fraud|stole\s+my\s+car)\b', ' NonRP обман развод скам трейд мошенничество '),

    # Account Hack & Security
    (r'\b(аккаунт\s+ұрланд[ыі]|бұзып\s+к[іi]рд[іi]|құпияс[өо]з\s+ауыстырылд[ыі]|к[іi]ре\s+алмаймын|почта\s+ауысты)\b', ' взлом аккаунта кража пароля утеря доступа 2fa сброс почты '),
    (r'\b(akkaunt\s+buzildi|parol\s+o[\'`]?zgartirildi|kira\s+olmayapman|og[\'`]?irlandi)\b', ' взлом аккаунта кража пароля утеря доступа 2fa сброс почты '),
    (r'\b(account\s+hacked|password\s+changed|stolen\s+account|lost\s+access)\b', ' взлом аккаунта кража пароля утеря доступа 2fa сброс почты '),

    # Donation & Payments
    (r'\b(донат\s+келмед[іi]|ақша\s+кетт[іi]|коиндар\s+т[үу]спед[іi]|каспи|чек\s+бар|т[өо]лем)\b', ' донат платеж Grand Coins коины списание денег чек пополнение '),
    (r'\b(donat\s+tushmadi|pul\s+yechildi|tangalar\s+tushmadi|click|payme|chek\s+bor)\b', ' донат платеж Grand Coins коины списание денег чек пополнение '),
    (r'\b(coins\s+not\s+received|money\s+deducted|payment\s+receipt|donation\s+issue)\b', ' донат платеж Grand Coins коины списание денег чек пополнение '),

    # Chat Insults & Family mentions
    (r'\b(балағаттад[ыі]|анама\s+т[іi]л\s+тиг[іi]зд[іi]|боқтад[ыі]|былапыт\s+с[өо]з|оск\s+род)\b', ' оскорбление игроков упоминание родителей родных нецензурная брань оск родни '),
    (r'\b(so[\'`]?kindi|haqorat\s+qildi|onamdan\s+so[\'`]?kdi|oilamni\s+haqorat)\b', ' оскорбление игроков упоминание родителей родных нецензурная брань оск родни '),
    (r'\b(insulted\s+my\s+family|offensive\s+language|curse\s+words)\b', ' оскорбление игроков упоминание родителей родных нецензурная брань оск родни '),

    # Punishment Appeal & Admin Complaints
    (r'\b(жазаны\s+алып\s+таста[ңн]ыз|себепс[іi]з\s+бан|деморганға\s+қате\s+т[үу]ст[іi]м|әкімшіге\s+шағым|блат\s+жасайды)\b', ' обжалование наказания ошибочный бан деморган жалоба на администратора пересмотр вердикта '),
    (r'\b(jazoni\s+bekor\s+qiling|noto[\'`]?g[\'`]?ri\s+ban|adashib\s+qamashdi|adminga\s+shikoyat)\b', ' обжалование наказания ошибочный бан деморган жалоба на администратора пересмотр вердикта '),
    (r'\b(unban\s+appeal|wrongfully\s+banned|admin\s+complaint|false\s+jail)\b', ' обжалование наказания ошибочный бан деморган жалоба на администратора пересмотр вердикта '),

    # Gameplay Bugs & Crashes
    (r'\b(құлап\s+кетт[іi]м|ойын\s+[өо]ш[іi]п\s+қалады|шығып\s+кетед[іi]|текстураға\s+қысылд[ыі]м)\b', ' баг текстуры краш вылет застрял ошибка клиента '),
    (r'\b(qotib\s+qoldi|o[\'`]?chib\s+ketdi|xatolik\s+berdi|qisilib\s+qoldim)\b', ' баг текстуры краш вылет застрял ошибка клиента '),
    (r'\b(game\s+crash|stuck\s+under\s+texture|fell\s+under\s+map|bug)\b', ' баг текстуры краш вылет застрял ошибка клиента '),

    # In-game Help & Novice
    (r'\b(ж[үу]рг[іi]зуш[іi]\s+ку[әа]л[іi]г[іi]|автомектеп|қай\s+жерден|қалай\s+жұмысқа|права\s+қалай)\b', ' помощь новичкам как устроиться на работу где автошкола получение прав gps команды '),
    (r'\b(haydovchilik\s+guvohnomasi|qayerdan\s+olsam|qanday\s+qilib\s+ishga|buyruqlar)\b', ' помощь новичкам как устроиться на работу где автошкола получение прав gps команды '),
    (r'\b(how\s+to\s+get\s+license|where\s+is\s+driving\s+school|commands\s+list)\b', ' помощь новичкам как устроиться на работу где автошкола получение прав gps команды ')
]

def expand_multilingual_tokens(text: str) -> str:
    """
    Appends normalized semantic bridge tokens to the search text representation.
    Enables cross-lingual TF-IDF indexing and retrieval between Kazakh/Uzbek/English and Russian rules.
    """
    if not text:
        return text

    expanded_additions = []
    text_lower = text.lower()

    for pattern, russian_synonyms in CROSS_LINGUAL_BRIDGES:
        if re.search(pattern, text_lower, flags=re.IGNORECASE):
            expanded_additions.append(russian_synonyms)

    if expanded_additions:
        return text + " " + " ".join(expanded_additions)
    return text
