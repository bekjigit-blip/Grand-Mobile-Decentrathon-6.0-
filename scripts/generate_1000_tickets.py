"""
Generates 1000 official validation tickets for Decentrathon 6.0 Support Copilot.
Strictly conforms to:
- 14 official dot-separated categories:
    complaint.insult
    complaint.cheat
    complaint.dm
    complaint.scam
    complaint.rmt_ads
    complaint.admin
    complaint.other
    complaint.invalid
    report.question
    report.help
    report.complaint
    report.account
    report.payment
    report.offtopic
- 2 transport kinds: 'complaint' and 'report'
- Multilingual test cases (kk, ru, uz, en, es, pt)
- Real punishment appeals (ban/mute/demorgan) routing to complaint.admin
- Account security & hack tickets routing to report.account
- Payment & donation tickets routing to report.payment
- Edge cases: CP1251 Kazakh corruption, Uzbek apostrophe variants, evidence negation,
  repeated authors with different accused players, attachment preservation.
"""

import json
import random
from datetime import datetime, timedelta

TEMPLATES_BY_CATEGORY = {
    "complaint.insult": [
        ("kk", "Ойыншы {nick} мені және ата-анамды былапыт сөздермен қорлады чатта", "4.1"),
        ("ru", "Игрок {nick} жестко оскорбил моих родных в общем чате", "4.1"),
        ("uz", "{nick} ismli o'yinchi meni haqorat qildi va yomon so'zlar bilan so'kindi", "4.1"),
        ("en", "Player {nick} is insulting players in chat with toxic language", "4.1"),
        ("es", "El jugador {nick} me insultó gravemente en el chat público", "4.1")
    ],
    "complaint.cheat": [
        ("kk", "Ойыншы {nick} спидхак және флайхак қолданып әскери база үстінде ұшып жүр", "8.1"),
        ("ru", "Игрок {nick} использует спидхак и летает на рванке, разносит спавн", "8.1"),
        ("uz", "{nick} chit ishlatyapti, mashinalarni uchirib serverni buzyapti", "8.1"),
        ("en", "Player {nick} is using speedhack and flying hack on server", "8.1")
    ],
    "complaint.dm": [
        ("kk", "Ойыншы {nick} автобазарда мені себепсіз атып өлтірді, DM жасады", "2.1"),
        ("ru", "Игрок {nick} совершил ДМ и расстрелял меня без какой-либо причины", "2.1"),
        ("uz", "{nick} hech qanday sababsiz meni o'ldirdi DM qildi", "2.1"),
        ("en", "Player {nick} killed me without reason (DM) outside the hospital", "2.1")
    ],
    "complaint.scam": [
        ("kk", "Ойыншы {nick} мені нонРП алдап көлігімді 1 рубльге алып қашып кетті", "7.1"),
        ("ru", "Игрок {nick} обманул меня при обмене машинами и офнулся, нонрп развод", "7.1"),
        ("uz", "{nick} mashina almashganda meni aldadi va o'yindan chiqib ketdi", "7.1"),
        ("en", "Player {nick} scammed me during car trade and immediately disconnected", "7.1")
    ],
    "complaint.rmt_ads": [
        ("kk", "Ойыншы {nick} вирт сатамын деп телеграм арнасын жарнамалап жатыр", "4.2"),
        ("ru", "Игрок {nick} рекламирует продажу виртов за реал и сторонний телеграм канал", "4.2"),
        ("uz", "{nick} virt sotaman deb telegram kanalini reklama qilyapti", "4.2"),
        ("en", "Player {nick} is spamming third party links selling in-game currency for real money", "4.2")
    ],
    "complaint.admin": [
        ("ru", "Администратор дал мне бан за DM. Я не согласен с наказанием, прошу пересмотреть.", "11.1"),
        ("ru", "Мне выдали мут за оскорбление родных, я с этим наказанием не согласен.", "11.1"),
        ("kk", "Әкімші берген жазамен келіспеймін, қате деморганға тықты қайта қарауды сұраймын", "11.1"),
        ("ru", "Администратор {nick} блатит своих друзей и посадил меня без доказательств", "11.1"),
        ("uz", "Admin {nick} menga noto'g'ri jazo berdi, apellyatsiya bermoqchiman", "11.1")
    ],
    "complaint.other": [
        ("kk", "Ойыншы {nick} басқаларға кедергі келтіріп автотұрақты бітеп тастады", "1.1"),
        ("ru", "Игрок {nick} создает помеху на спавне и блокирует выезд машиной", "1.1"),
        ("uz", "{nick} yo'lni to'sib boshqa o'yinchilarga xalaqit beryapti", "1.1")
    ],
    "complaint.invalid": [
        ("ru", "Игрок плохой накажите его", "1.1"),
        ("kk", "Мына ойыншыны банға тығыңдар", "1.1"),
        ("en", "Ban this guy please", "1.1")
    ],
    "report.question": [
        ("kk", "Ойында жүргізуші куәлігін қай жерден және қалай алуға болады?", "1.1"),
        ("ru", "Как устроиться на работу дальнобойщика и со скольки лет?", "1.1"),
        ("uz", "O'yinda haydovchilik guvohnomasini qayerdan olsam bo'ladi?", "1.1"),
        ("en", "How can I join the police department on the server?", "1.1")
    ],
    "report.help": [
        ("kk", "Көлігім шұңқырға түсіп қалды шығарып беріңізші көмек керек", "1.1"),
        ("ru", "Помогите пожалуйста, застрял в текстурах около автосалона", "1.1"),
        ("uz", "Yordam bering, mashinam suvga tushib ketdi", "1.1")
    ],
    "report.complaint": [
        ("ru", "Репорт: игрок {nick} нарушает правила прямо сейчас на спавне, последите", "2.1"),
        ("kk", "Репорт: {nick} ойыншысын қазір тексеріңізші ереже бұзып жатыр", "2.1"),
        ("uz", "Report: {nick} qoidani buzyapti iltimos tekshiring", "2.1")
    ],
    "report.account": [
        ("kk", "Менің аккаунтымды біреу бұзып кіріп, паролін ауыстырып тастапты, көмектесіңізші", "9.1"),
        ("ru", "Мой аккаунт взломали, привязанную почту сменили и украли имущество", "9.1"),
        ("uz", "Akkauntim paroli buzilgan, kiring va tiklashga yordam bering", "9.1"),
        ("en", "My account was hacked and password was changed, please help recover it", "9.1")
    ],
    "report.payment": [
        ("kk", "Каспи арқылы 5000 теңгеге донат жасадым, ақша кетті бірақ коиндар түспеді чек бар", "6.1"),
        ("ru", "Оплатил донат через СБП 1500 рублей, деньги списались а Grand Coins не пришли", "6.1"),
        ("uz", "Click orqali to'lov qildim, pul yechildi lekin hisobga tushmadi", "6.1"),
        ("pt", "Paguei moedas pelo Pix mas não caíram na conta, tenho comprovante", "6.1")
    ],
    "report.offtopic": [
        ("ru", "Всем привет как погода в Москве?", "1.1"),
        ("kk", "Сәлем достар бүгін кім ойнайды", "1.1"),
        ("uz", "Salom hammaga qandaysizlar", "1.1")
    ]
}

NICKNAMES = [
    "Arman_Petrov", "Sergei_Gromov", "Jasur_Aliev", "Dmitry_Morozov",
    "John_Miller", "Carlos_Santana", "Nurlan_Sabyr", "Alisher_Usman",
    "Kairat_Nurtas", "Elena_Smirnova", "Timur_Bekmambet", "Danil_Voronov"
]

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

        # 1. CP1251 corruption for some Kazakh tickets
        if lang == "kk" and random.random() < 0.20:
            text = text.replace("ә", "є").replace("ұ", "ў").replace("ө", "ґ").replace("қ", "ќ")

        # 2. Uzbek apostrophe variants
        if lang == "uz" and random.random() < 0.30:
            text = text.replace("o'", "oʻ").replace("g'", "gʻ")

        # 3. Evidence negation vs evidence presence
        attachments = 0
        if "complaint" in cat:
            if random.random() < 0.20:
                negation = random.choice(["но скринов нет", "скрин жоқ", "дәлел жоқ", "dalilsiz"])
                text = f"{text}, {negation}"
                attachments = 0
            else:
                attachments = random.choice([1, 2, 3])
        elif cat in ["report.payment"]:
            attachments = random.choice([1, 2])
        else:
            attachments = 0 if random.random() < 0.85 else 1

        # Timestamps and reporters
        rep_id = f"reporter_{(i % 250) + 1:03d}"
        created_dt = base_time + timedelta(minutes=i * 2)
        created_at_str = created_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Kind must be strictly 'complaint' or 'report'
        kind = "complaint" if cat.startswith("complaint.") else "report"

        ticket = {
            "ticket_id": f"TICKET-{i:04d}",
            "kind": kind,
            "reporter_hash": rep_id,
            "created_at": created_at_str,
            "images_count": attachments,
            "messages": [
                {
                    "role": "player",
                    "text": text,
                    "attachments": attachments
                }
            ]
        }

        # Rule refs occasionally present
        if random.random() < 0.30:
            if random.random() < 0.15:
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
    print(f"Generated 1000 tickets in data/valid.jsonl successfully with official 14 categories and 2 kinds.")
