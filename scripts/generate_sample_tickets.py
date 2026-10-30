import json
import random

tickets = [
    # 1. Kazakh DM complaint with nickname & rule ref
    {
        "ticket_id": "TICKET-1001",
        "reporter_hash": "rep_kz_001",
        "created_at": "2026-10-30T10:15:00Z",
        "server_lang": "ru",
        "lang": "kk",
        "text": "Сәлеметсіз бе! Мен спавнда тыныш тұрғанда Arman_Kaspi деген ойыншы келіп еш себепсіз диглмен атып өлтірді (DM). 2.1 ережесін бұзды. Жазалаңыздаршы!",
        "images_count": 2,
        "rule_refs_raw": ["2.1"]
    },
    # 2. Russian cp1251 corrupted Kazakh text (ќ→қ, ґ→ғ, ѕ→ң, є→ә, ј→ө, ў→ұ, ї→ү)
    {
        "ticket_id": "TICKET-1002",
        "reporter_hash": "rep_kz_002",
        "created_at": "2026-10-30T10:18:00Z",
        "server_lang": "kz",
        "lang": "kk",
        "text": "Сєлеметсіз бе! Бўл ойыншы автобазарда мені кґлікпен ќасаќана басып ґлтірді, ДБ жасады! Скрин бар.",
        "images_count": 1,
        "rule_refs_raw": ["2.3"]
    },
    # 3. Uzbek donation payment issue (needs_human, p1)
    {
        "ticket_id": "TICKET-1003",
        "reporter_hash": "rep_uz_001",
        "created_at": "2026-10-30T10:20:00Z",
        "server_lang": "ru",
        "lang": "uz",
        "text": "Salom adminlar. Men Click orqali 50000 so'mga donat qildim, kartamdan pul yechildi lekin Grand Coins hisobimga tushmadi. Chek ilova qildim, yordam bering.",
        "images_count": 1,
        "rule_refs_raw": []
    },
    # 4. Russian account hack (needs_human, p0)
    {
        "ticket_id": "TICKET-1004",
        "reporter_hash": "rep_ru_001",
        "created_at": "2026-10-30T10:25:00Z",
        "server_lang": "ru",
        "lang": "ru",
        "text": "Срочно помогите, меня взломали! Захожу на сервер, пишет неверный пароль, почта отвязана и 2FA сброшен. Ник Sergei_Gromov, номер аккаунта 184920.",
        "images_count": 0,
        "rule_refs_raw": []
    },
    # 5. Russian Green Zone violation (GZ context test)
    {
        "ticket_id": "TICKET-1005",
        "reporter_hash": "rep_ru_002",
        "created_at": "2026-10-30T10:30:00Z",
        "server_lang": "ru",
        "lang": "ru",
        "text": "Игрок Vanya_Shooter устроил массовую стрельбу прямо в здании ЦБ в Зеленой Зоне (GZ 3.1). Накажите за DM в ЗЗ!",
        "images_count": 2,
        "rule_refs_raw": ["GZ 3.1"]
    },
    # 6. Kazakh NonRP scam / car trade
    {
        "ticket_id": "TICKET-1006",
        "reporter_hash": "rep_kz_003",
        "created_at": "2026-10-30T10:35:00Z",
        "server_lang": "kz",
        "lang": "kk",
        "text": "Мені автобазарда алдап кетті. M5 F90 көлігін 15 миллионға аламын деп, арзан скутер лақтырып қашып кетті. Нонрп развод, көмектесіңіздер!",
        "images_count": 1,
        "rule_refs_raw": ["7.3"]
    },
    # 7. English cheat / speedhack complaint
    {
        "ticket_id": "TICKET-1007",
        "reporter_hash": "rep_en_001",
        "created_at": "2026-10-30T10:40:00Z",
        "server_lang": "en",
        "lang": "en",
        "text": "Player Dark_Rider is using speedhack and flying car on server 2. He is crashing into everyone and teleporting around.",
        "images_count": 0,
        "rule_refs_raw": ["6.1"]
    },
    # 8. Russian punishment appeal (needs_human, p2)
    {
        "ticket_id": "TICKET-1008",
        "reporter_hash": "rep_ru_003",
        "created_at": "2026-10-30T10:45:00Z",
        "server_lang": "ru",
        "lang": "ru",
        "text": "Администратор Pavel_Korshunov посадил меня в деморган на 120 минут по причине ДБ, но я просто случайно врезался из-за пинга. Прошу пересмотреть наказание.",
        "images_count": 1,
        "rule_refs_raw": ["10.3"]
    },
    # 9. Uzbek insult / toxic chat
    {
        "ticket_id": "TICKET-1009",
        "reporter_hash": "rep_uz_002",
        "created_at": "2026-10-30T10:50:00Z",
        "server_lang": "uz",
        "lang": "uz",
        "text": "VIP chatda bir o'yinchi meni va ota-onamni so'kib, qattiq haqorat qildi. Screenshot olib qo'ydim, mut bering.",
        "images_count": 1,
        "rule_refs_raw": ["4.2"]
    },
    # 10. Kazakh novice in-game help question (p3)
    {
        "ticket_id": "TICKET-1010",
        "reporter_hash": "rep_kz_004",
        "created_at": "2026-10-30T10:55:00Z",
        "server_lang": "kz",
        "lang": "kk",
        "text": "Сәлеметсіздер ме! Жаңадан бастадым, жүргізуші куәлігін (права) қай жерден және қалай алуға болады? Автомектептің GPS нөмірі қандай?",
        "images_count": 0,
        "rule_refs_raw": []
    },
    # 11. Duplicate ticket within 10 minutes from same reporter
    {
        "ticket_id": "TICKET-1011",
        "reporter_hash": "rep_kz_001",
        "created_at": "2026-10-30T10:22:00Z",
        "server_lang": "ru",
        "lang": "kk",
        "text": "Сәлеметсіз бе! Мен спавнда тыныш тұрғанда Arman_Kaspi деген ойыншы келіп еш себепсіз диглмен атып өлтірді (DM). 2.1 ережесін бұзды. Жазалаңыздаршы!",
        "images_count": 2,
        "rule_refs_raw": ["2.1"]
    },
    # 12. Short message without reporter hash (edge case)
    {
        "ticket_id": "TICKET-1012",
        "created_at": "2026-10-30T11:00:00Z",
        "text": "Сәлем админ көмек керек",
        "images_count": 0
    },
    # 13. Another player with similar short message (must NOT be marked as duplicate because reporter_hash differs or is missing)
    {
        "ticket_id": "TICKET-1013",
        "reporter_hash": "rep_other_999",
        "created_at": "2026-10-30T11:05:00Z",
        "text": "Сәлем админ көмек керек",
        "images_count": 0
    },
    # 14. Technical gameplay bug / crash
    {
        "ticket_id": "TICKET-1014",
        "reporter_hash": "rep_ru_004",
        "created_at": "2026-10-30T11:10:00Z",
        "server_lang": "ru",
        "lang": "ru",
        "text": "Когда выхожу из квартиры в Батырево, сразу проваливаюсь под текстуры в виртуальный мир и игра крашится с ошибкой 0x0045.",
        "images_count": 0,
        "rule_refs_raw": []
    },
    # 15. Spanish player ticket
    {
        "ticket_id": "TICKET-1015",
        "reporter_hash": "rep_es_001",
        "created_at": "2026-10-30T11:15:00Z",
        "server_lang": "es",
        "lang": "es",
        "text": "Hola administradores, un jugador me mató sin ninguna razón en el hospital (DM en Green Zone). Por favor sancionen al usuario.",
        "images_count": 1,
        "rule_refs_raw": []
    },
    # 16. Portuguese player ticket
    {
        "ticket_id": "TICKET-1016",
        "reporter_hash": "rep_pt_001",
        "created_at": "2026-10-30T11:20:00Z",
        "server_lang": "pt",
        "lang": "pt",
        "text": "Olá equipe, comprei moedas pelo Pix e o dinheiro saiu da minha conta, mas os Grand Coins não caíram na conta do jogo. Segue comprovante.",
        "images_count": 1,
        "rule_refs_raw": []
    }
]

# Write valid.jsonl with realistic tickets
with open("data/valid.jsonl", "w", encoding="utf-8") as f:
    for t in tickets:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")

with open("data/sample_tickets.jsonl", "w", encoding="utf-8") as f:
    for t in tickets:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")

print(f"Generated data/valid.jsonl and data/sample_tickets.jsonl with {len(tickets)} sample tickets.")
