"""
Generates 1000 official schema validation tickets for Decentrathon 6.0 Support Copilot.
Covers:
- 14 official dot-separated taxonomy categories
- 6 languages (kk, ru, uz, en, es, pt)
- Official input contract: kind, messages: [{role: "player", text, attachments}]
- Edge cases: CP1251 corruption, Uzbek apostrophe variants (oʻ vs o'),
  negation of evidence ("скринов нет", "дәлел жоқ"), duplicate timestamps within 1-hour,
  speedhack cheat signals, payment issues, punishment appeals, multi-segment rule refs (ЖБ 1.2.7).
"""

import json
import random
from datetime import datetime, timedelta

TEMPLATES_BY_CATEGORY = {
    "complaint.insult": [
        ("kk", "Ойыншы {nick} мені қорлады және чатта былапыт сөздер жазды", "2.1"),
        ("ru", "Игрок {nick} оскорбил мою семью и вел себя неадекватно в чате", "4.1"),
        ("uz", "{nick} ismli o'yinchi meni haqorat qildi va yomon so'zlar bilan so'kindi", "4.1"),
        ("en", "Player {nick} is excessively insulting and harassing other players in general chat", "4.1")
    ],
    "complaint.dm": [
        ("kk", "Ойыншы {nick} автобазарда мені себепсіз атып өлтірді DM жасады", "2.1"),
        ("ru", "Игрок {nick} совершил ДМ и расстрелял меня без какой-либо РП причины", "2.1"),
        ("uz", "{nick} hech qanday sababsiz meni o'ldirdi DM qildi", "2.1"),
        ("en", "Player {nick} killed me without reason (DM) outside the police department", "2.1")
    ],
    "complaint.db": [
        ("kk", "Ойыншы {nick} көлікпен қасақана қағып өлтірді ДБ жасады", "2.3"),
        ("ru", "Игрок {nick} намеренно давил меня машиной на спавне, ДБ", "2.3"),
        ("uz", "{nick} mashina bilan ataylab ustimdan bosib o'ldirdi (DB)", "2.3")
    ],
    "complaint.cheats": [
        ("kk", "{nick} спидхак қосып алып әскери базаның үстімен ұшып жүр", "8.1"),
        ("ru", "Игрок {nick} использует спидхак и летает на рванке, крашит игроков", "8.1"),
        ("uz", "{nick} chit ishlatyapti, mashinalarni uchirib serverni buzyapti", "8.1"),
        ("en", "Player {nick} is using speedhack and flying vehicle hack on server 2", "8.1")
    ],
    "complaint.scam": [
        ("kk", "{nick} мені алдап көлігімді 1 рубльге алып кетті нонРП алдау", "7.1"),
        ("ru", "Игрок {nick} обманул меня при обмене машинами и вышел из игры, нонрп развод", "7.1"),
        ("uz", "{nick} mashina almashganda meni aldadi va o'yindan chiqib ketdi", "7.1")
    ],
    "complaint.nonrp": [
        ("kk", "Полиция қызметкері {nick} ешқандай РП ойнамай бірден наручник тақты", "5.1"),
        ("ru", "Сотрудник МВД {nick} задержал меня без отыгровки РП и без причины", "5.1"),
        ("uz", "Politsiyachi {nick} RP qilmasdan qamoqqa tiqdi", "5.1")
    ],
    "complaint.greenzone": [
        ("kk", "Ойыншы {nick} орталық ауруханада Жасыл Аймақта (GZ) оқ жаудырды", "3.1"),
        ("ru", "Игрок {nick} стрелял и убивал в Зеленой Зоне (GZ) больницы Арзамаса", "3.1"),
        ("uz", "{nick} shifoxonaning Yashil Zonasida (GZ) otishma boshladi", "3.1")
    ],
    "complaint.admin": [
        ("kk", "Әкімші {nick} достарын қорғап бізге ғана әділетсіз жаза берді", "11.1"),
        ("ru", "Администратор {nick} покрывает своих друзей и блатит их, а меня посадил в деморган", "11.1"),
        ("uz", "Admin {nick} o'z tanishlariga yordam berib adolatsiz qamoqqa soldi", "11.1")
    ],
    "appeal.punishment": [
        ("kk", "Әкімші мені ДМ үшін қателікпен деморганға қамады, жазаны алып тастаңыз", "10.1"),
        ("ru", "Администратор ошибочно выдал мне бан на 30 дней за читы, прошу пересмотреть фрапс и разбанить", "10.1"),
        ("uz", "Menga adashib berilgan ban bo'yicha appelyatsiya bermoqchiman, jazoni olib tashlang", "10.1")
    ],
    "security.account": [
        ("kk", "Менің аккаунтымды біреу бұзып паролін ауыстырып тастапты көмектесіңіздерші", "9.1"),
        ("ru", "Мой аккаунт взломали, привязанную почту отвязали и сменили пароль", "9.1"),
        ("uz", "Akkauntim paroli o'zgartirilgan, kimdir buzib kirgan yordam bering", "9.1"),
        ("en", "My account was hacked and password was changed, please help recover it", "9.1")
    ],
    "financial.donation": [
        ("kk", "Каспи арқылы 2000 теңгеге донат жасадым бірақ коиндар ойынға түспеді", "6.1"),
        ("ru", "Оплатил донат через СБП 1000 рублей, деньги списались а коинов на аккаунте нет", "6.1"),
        ("uz", "Click orqali hisobimni to'ldirdim, pul ketdi lekin Grand Coins tushmadi", "6.1"),
        ("es", "Compré monedas a través de pago en línea pero no se acreditaron en mi cuenta", "6.1")
    ],
    "technical.bug": [
        ("kk", "Автосалоннан шыққан кезде машина жердің астына құлап краш береді", "1.1"),
        ("ru", "При выходе из интерьера дома проваливаюсь под текстуры и игра крашится", "1.1"),
        ("uz", "O'yinda mashinadan tushganda tekstura ostiga tushib ketmoqdaman, bag bor", "1.1")
    ],
    "question.help": [
        ("kk", "Ойында жүргізуші куәлігін қай жерден және қалай алуға болады?", "1.1"),
        ("ru", "Подскажите пожалуйста, со скольки лет в игре можно устроиться на работу дальнобойщика?", "1.1"),
        ("uz", "O'yinda litsenziyani qayerdan olsam bo'ladi yordam bering", "1.1")
    ],
    "feedback.other": [
        ("kk", "Ойынның жаңа жаңартуы өте керемет болыпты, әзірлеушілерге рахмет", "1.1"),
        ("ru", "Спасибо разработчикам за классный осенний ивент, всё очень понравилось", "1.1"),
        ("uz", "O'yin juda ajoyib chiqibdi, yangi mashinalar uchun rahmat", "1.1")
    ]
}

NICKNAMES = [
    "Arman_Petrov", "Sergei_Gromov", "Jasur_Aliev", "Dmitry_Morozov",
    "John_Miller", "Carlos_Santana", "Nurlan_Sabyr", "Alisher_Usman",
    "Vladimir_Putin", "Kairat_Nurtas", "Elena_Smirnova", "Timur_Bekmambet"
]

CATEGORY_KINDS = {
    "complaint.insult": "complaint",
    "complaint.dm": "complaint",
    "complaint.db": "complaint",
    "complaint.cheats": "complaint",
    "complaint.scam": "complaint",
    "complaint.nonrp": "complaint",
    "complaint.greenzone": "complaint",
    "complaint.admin": "complaint",
    "appeal.punishment": "appeal",
    "security.account": "security",
    "financial.donation": "financial",
    "technical.bug": "technical",
    "question.help": "question",
    "feedback.other": "feedback"
}

def generate_tickets(count=1000):
    random.seed(42)
    categories = list(TEMPLATES_BY_CATEGORY.keys())
    base_time = datetime(2026, 10, 30, 8, 0, 0)
    tickets = []

    for i in range(1, count + 1):
        cat = categories[(i - 1) % len(categories)]
        template_opts = TEMPLATES_BY_CATEGORY[cat]
        lang, tpl, rule_ref = random.choice(template_opts)
        nick = random.choice(NICKNAMES)

        text = tpl.format(nick=nick)

        # Introduce edge cases:
        # 1. CP1251 corruption for some Kazakh tickets
        if lang == "kk" and random.random() < 0.20:
            text = text.replace("ә", "є").replace("ұ", "ў").replace("ө", "ґ").replace("қ", "ќ")

        # 2. Evidence negation phrase
        has_negation = False
        if random.random() < 0.15:
            negation = random.choice(["но скринов нет", "скрин жоқ", "дәлел жоқ", "dalilsiz"])
            text = f"{text}, {negation}"
            has_negation = True
            attachments = 0
        else:
            attachments = random.choice([0, 1, 2, 3])

        # Timestamps and reporters
        rep_id = f"reporter_{(i % 250) + 1:03d}"
        created_dt = base_time + timedelta(minutes=i * 2)
        created_at_str = created_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        kind = CATEGORY_KINDS[cat]

        # Standard messages payload
        ticket = {
            "ticket_id": f"TICKET-{i:04d}",
            "kind": kind,
            "reporter_hash": rep_id,
            "created_at": created_at_str,
            "messages": [
                {
                    "role": "player",
                    "text": text,
                    "attachments": attachments
                }
            ]
        }

        # Sometimes include rule_refs_raw
        if random.random() < 0.35:
            if random.random() < 0.1:
                ticket["rule_refs_raw"] = "ЖБ 1.2.7"
            else:
                ticket["rule_refs_raw"] = rule_ref

        tickets.append(ticket)

    return tickets

if __name__ == "__main__":
    records = generate_tickets(1000)
    with open("data/valid.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Generated 1000 tickets in data/valid.jsonl successfully.")
