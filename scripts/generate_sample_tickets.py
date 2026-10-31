import json

tickets = [
    # 1. Kazakh Insult report (messages schema with attachments=2) -> complaint.insult
    {
        "ticket_id": "TICKET-1001",
        "kind": "complaint",
        "reporter_hash": "rep_kz_001",
        "created_at": "2026-10-30T10:15:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Arman_Petrov мені қорлады және чатта анамды былапыт сөздермен балағаттады",
                "attachments": 2
            }
        ]
    },
    # 2. Kazakh CP1251 corrupted text -> complaint.db
    {
        "ticket_id": "TICKET-1002",
        "kind": "complaint",
        "reporter_hash": "rep_kz_002",
        "created_at": "2026-10-30T10:18:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Сєлеметсіз бе! Бўл ойыншы автобазарда мені кґлікпен ќасаќана басып ґлтірді, ДБ жасады! Скрин бар.",
                "attachments": 1
            }
        ],
        "rule_refs_raw": "2.3"
    },
    # 3. Uzbek donation payment issue (needs_human, p1) -> financial.donation
    {
        "ticket_id": "TICKET-1003",
        "kind": "financial",
        "reporter_hash": "rep_uz_001",
        "created_at": "2026-10-30T10:20:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Salom adminlar. Men Click orqali 50000 so'mga donat qildim, kartamdan pul yechildi lekin Grand Coins tushmadi. Chek ilova qildim, yordam bering.",
                "attachments": 1
            }
        ]
    },
    # 4. Russian account hack (needs_human, p0) -> security.account
    {
        "ticket_id": "TICKET-1004",
        "kind": "security",
        "reporter_hash": "rep_ru_001",
        "created_at": "2026-10-30T10:25:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Срочно помогите, меня взломали! Захожу на сервер, пишет неверный пароль, почта отвязана и 2FA сброшен. Ник Sergei_Gromov, номер аккаунта 184920.",
                "attachments": 0
            }
        ]
    },
    # 5. Russian Green Zone violation with GZ prefix -> complaint.greenzone
    {
        "ticket_id": "TICKET-1005",
        "kind": "complaint",
        "reporter_hash": "rep_ru_002",
        "created_at": "2026-10-30T10:30:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Игрок Vanya_Shooter устроил массовую стрельбу прямо в здании ЦБ в Зеленой Зоне (GZ 3.1). Накажите за DM в ЗЗ!",
                "attachments": 2
            }
        ],
        "rule_refs_raw": "GZ 3.1"
    },
    # 6. Kazakh NonRP scam / car trade -> complaint.scam
    {
        "ticket_id": "TICKET-1006",
        "kind": "complaint",
        "reporter_hash": "rep_kz_003",
        "created_at": "2026-10-30T10:35:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Мені автобазарда алдап кетті. M5 F90 көлігін 15 миллионға аламын деп, арзан скутер лақтырып қашып кетті. Нонрп развод, көмектесіңіздер!",
                "attachments": 1
            }
        ],
        "rule_refs_raw": "7.3"
    },
    # 7. Speedhack cheat report (p1) -> complaint.cheats
    {
        "ticket_id": "TICKET-1007",
        "kind": "complaint",
        "reporter_hash": "rep_en_001",
        "created_at": "2026-10-30T10:40:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Игрок летает speedhack и разносит всех рванкой на спавне! Ник Dark_Rider, сервер 2.",
                "attachments": 0
            }
        ]
    },
    # 8. Punishment appeal (needs_human, p2) -> appeal.punishment
    {
        "ticket_id": "TICKET-1008",
        "kind": "appeal",
        "reporter_hash": "rep_ru_003",
        "created_at": "2026-10-30T10:45:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Администратор Pavel_Korshunov посадил меня в деморган на 120 минут по причине ДБ, но я просто случайно врезался из-за пинга. Прошу пересмотреть наказание.",
                "attachments": 1
            }
        ],
        "rule_refs_raw": "10.3"
    },
    # 9. Uzbek insult with Unicode apostrophe oʻldirdi -> complaint.dm
    {
        "ticket_id": "TICKET-1009",
        "kind": "complaint",
        "reporter_hash": "rep_uz_002",
        "created_at": "2026-10-30T10:50:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Salom adminlar. Men tinch turgandim, kelib sababsiz oʻldirib ketdi, DM qildi. Chora koʻring.",
                "attachments": 1
            }
        ],
        "rule_refs_raw": "2.1"
    },
    # 10. Kazakh in-game help (p3) -> question.help
    {
        "ticket_id": "TICKET-1010",
        "kind": "question",
        "reporter_hash": "rep_kz_004",
        "created_at": "2026-10-30T10:55:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Сәлеметсіздер ме! Жаңадан бастадым, жүргізуші куәлігін (права) қай жерден алуға болады? Автомектептің GPS нөмірі қандай?",
                "attachments": 0
            }
        ]
    },
    # 11. Duplicate ticket within 15 minutes by SAME reporter
    {
        "ticket_id": "TICKET-1011",
        "kind": "complaint",
        "reporter_hash": "rep_kz_001",
        "created_at": "2026-10-30T10:22:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Arman_Petrov мені қорлады және чатта анамды былапыт сөздермен балағаттады",
                "attachments": 2
            }
        ]
    },
    # 12. Text saying explicitly NO screenshots -> has_evidence should be False
    {
        "ticket_id": "TICKET-1012",
        "kind": "complaint",
        "reporter_hash": "rep_ru_004",
        "created_at": "2026-10-30T11:00:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Меня заДМили на спавне, но скринов нет, фрапса нет.",
                "attachments": 0
            }
        ]
    },
    # 13. Short message without reporter hash
    {
        "ticket_id": "TICKET-1013",
        "kind": "question",
        "created_at": "2026-10-30T11:05:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Сәлем админ көмек керек",
                "attachments": 0
            }
        ]
    },
    # 14. Technical gameplay bug / crash -> technical.bug
    {
        "ticket_id": "TICKET-1014",
        "kind": "technical",
        "reporter_hash": "rep_ru_005",
        "created_at": "2026-10-30T11:10:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Когда выхожу из квартиры в Батырево, сразу проваливаюсь под текстуры в виртуальный мир и игра крашится.",
                "attachments": 0
            }
        ]
    },
    # 15. Admin complaint -> complaint.admin
    {
        "ticket_id": "TICKET-1015",
        "kind": "complaint",
        "reporter_hash": "rep_ru_006",
        "created_at": "2026-10-30T11:15:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Администратор Sergey_Admin блатит своих друзей из фамы, закрывает глаза на их ДМ и сажает только нас!",
                "attachments": 1
            }
        ]
    },
    # 16. Multi-level rule ЖБ 1.2.7 citation test
    {
        "ticket_id": "TICKET-1016",
        "kind": "appeal",
        "reporter_hash": "rep_ru_007",
        "created_at": "2026-10-30T11:20:00Z",
        "messages": [
            {
                "role": "player",
                "text": "Подаю жалобу согласно пункту ЖБ 1.2.7 на пересмотр видеозаписи ситуации за 30 секунд до стрельбы.",
                "attachments": 1
            }
        ],
        "rule_refs_raw": "ЖБ 1.2.7"
    }
]

# Write to valid.jsonl and sample_tickets.jsonl
with open("data/valid.jsonl", "w", encoding="utf-8") as f:
    for t in tickets:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")

with open("data/sample_tickets.jsonl", "w", encoding="utf-8") as f:
    for t in tickets:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")

print(f"Generated data/valid.jsonl and data/sample_tickets.jsonl with {len(tickets)} official contract tickets.")
