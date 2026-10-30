# Multilingual, safe, verified response templates
# Compliant with Decentrathon 6.0: no false promises, no unverified assumptions, proper section citations.

TEMPLATES = {
    "kk": {
        "greeting": "Сәлеметсіз бе!",
        "standard_receipt": (
            "Сәлеметсіз бе! Сіздің өтінішіңіз тіркелді және модерация қарауына жіберілді. "
            "Сервер тәртібіне сәйкес ({section_name}, {rule_cite}) барлық жағдайлар мұқият тексеріледі. "
            "Егер ереже бұзушылық расталса, регламент бойынша шара қолданылады."
        ),
        "clarification_needed": (
            "Сәлеметсіз бе! Өтінішіңізді толық және әділ қарастыру үшін қосымша ақпарат қажет. "
            "Оқиға болған уақытты, нақты серверді және /time белгісі бар толық бейнежазбаны ұсынуыңызды сұраймыз."
        ),
        "escalation_human": (
            "Сәлеметсіз бе! Сіздің мәселеңіз кешенді тексеруді талап ететіндіктен, "
            "өтініш аға әкімшілік пен жауапты мамандарға тексеруге жолданды. "
            "Логтар мен деректер тексерілгеннен кейін нәтижесі осында хабарланады."
        ),
        "insufficient_proof": (
            "Сәлеметсіз бе! Ұсынылған деректер шешім қабылдауға жеткіліксіз. "
            "Ережеге сәйкес ({section_name}), дәлелдеме ретінде /time белгісі бар үзіліссіз видео жазба (фрапс) қажет."
        ),
        "duplicate_response": (
            "Сәлеметсіз бе! Осы мәселе бойынша өтінішіңіз бұған дейін тіркелген. "
            "Қайта хабарлама жолдамай, алдыңғы өтініштің қаралуын күтуіңізді сұраймыз."
        )
    },
    "ru": {
        "greeting": "Здравствуйте!",
        "standard_receipt": (
            "Здравствуйте! Ваше обращение принято к рассмотрению. "
            "В соответствии с регламентом сервера ({section_name}, {rule_cite}), ситуация будет детально проверена. "
            "При подтверждении нарушения будут приняты меры согласно правилам."
        ),
        "clarification_needed": (
            "Здравствуйте! Для объективного рассмотрения вашего обращения требуется уточнить детали. "
            "Пожалуйста, укажите точный никнейм игрока, время происшествия и предоставьте видеозапись с командой /time."
        ),
        "escalation_human": (
            "Здравствуйте! Ваше обращение передано на рассмотрение старшей администрации и профильным специалистам. "
            "Проверка логов и игровых данных требует времени, ожидайте ответа в данном обращении."
        ),
        "insufficient_proof": (
            "Здравствуйте! Предоставленных материалов недостаточно для вынесения вердикта. "
            "Согласно регламенту ({section_name}), доказательства должны содержать фиксацию времени через /time без монтажа."
        ),
        "duplicate_response": (
            "Здравствуйте! По данному вопросу вами уже было создано обращение. "
            "Пожалуйста, ожидайте ответа по ранее поданной заявке, повторное создание обращений замедляет их обработку."
        )
    },
    "uz": {
        "greeting": "Assalomu alaykum!",
        "standard_receipt": (
            "Assalomu alaykum! Sizning murojaatingiz qabul qilindi va ko'rib chiqishga yuborildi. "
            "Server qoidalariga muvofiq ({section_name}, {rule_cite}), vaziyat batafsil o'rganib chiqiladi. "
            "Qoidabuzarlik tasdiqlansa, belgilangan tartibda chora ko'riladi."
        ),
        "clarification_needed": (
            "Assalomu alaykum! Murojaatingizni to'liq ko'rib chiqish uchun qo'shimcha ma'lumot kerak. "
            "Iltimos, hodisa yuz bergan vaqtni va /time buyrug'i bilan yozilgan to'liq video dalilni taqdim eting."
        ),
        "escalation_human": (
            "Assalomu alaykum! Sizning masalangiz qo'shimcha tekshiruv talab qilgani sababli, "
            "murojaat katta ma'muriyat va mas'ul xodimlarga yo'naltirildi. Tez orada javob beriladi."
        ),
        "insufficient_proof": (
            "Assalomu alaykum! Taqdim etilgan dalillar yetarli emas. "
            "Qoidalarga binoan ({section_name}), /time yozuvi bilan to'liq video dalil taqdim etishingiz kerak."
        ),
        "duplicate_response": (
            "Assalomu alaykum! Ushbu masala yuzasidan murojaatingiz avvalroq qabul qilingan. "
            "Iltimos, oldingi arizangiz javobini kuting."
        )
    },
    "en": {
        "greeting": "Hello!",
        "standard_receipt": (
            "Hello! Your report has been received and queued for review. "
            "In accordance with server guidelines ({section_name}, {rule_cite}), the incident will be thoroughly examined. "
            "If a violation is confirmed, appropriate actions will be taken."
        ),
        "clarification_needed": (
            "Hello! To process your request accurately, additional details are needed. "
            "Please provide the exact player nickname, server number, and full video proof with the /time timestamp."
        ),
        "escalation_human": (
            "Hello! Your request has been escalated to senior staff and payment/security specialists. "
            "Please allow some time for log verification."
        ),
        "insufficient_proof": (
            "Hello! The provided materials are insufficient to reach a verdict. "
            "According to server rules ({section_name}), video evidence with the /time command is required."
        ),
        "duplicate_response": (
            "Hello! A report regarding this issue has already been registered from your account. "
            "Please await response on your previous ticket."
        )
    },
    "es": {
        "greeting": "¡Hola!",
        "standard_receipt": (
            "¡Hola! Su reporte ha sido registrado y está en proceso de revisión. "
            "De acuerdo con las reglas del servidor ({section_name}, {rule_cite}), la situación será investigada detenidamente."
        ),
        "clarification_needed": (
            "¡Hola! Para revisar su caso adecuadamente, necesitamos información adicional. "
            "Por favor adjunte el apodo exacto del jugador y un video con el comando /time."
        ),
        "escalation_human": (
            "¡Hola! Su solicitud ha sido remitida a la administración superior para una verificación exhaustiva."
        ),
        "insufficient_proof": (
            "¡Hola! Las pruebas proporcionadas no son suficientes. Se requiere grabación de video con /time."
        ),
        "duplicate_response": (
            "¡Hola! Ya hemos recibido un reporte similar de su parte. Por favor espere la respuesta al ticket previo."
        )
    },
    "pt": {
        "greeting": "Olá!",
        "standard_receipt": (
            "Olá! Seu relatório foi recebido e está sendo analisado pela equipe. "
            "De acordo com as regras do servidor ({section_name}, {rule_cite}), o caso será verificado cuidadosamente."
        ),
        "clarification_needed": (
            "Olá! Para prosseguir com a análise, forneça mais informações e gravação de vídeo com o comando /time."
        ),
        "escalation_human": (
            "Olá! Sua solicitação foi encaminhada para a administração sênior e equipe financeira."
        ),
        "insufficient_proof": (
            "Olá! As evidências enviadas são insuficientes. É necessária gravação de vídeo contendo /time."
        ),
        "duplicate_response": (
            "Olá! Já existe um chamado registrado sobre este assunto. Por favor aguarde o atendimento."
        )
    }
}
