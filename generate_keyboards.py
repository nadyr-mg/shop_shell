from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

keyboard_names = {
    "lang_keyboard": 0,
    "main_keyboard": 1,
    "balance_keyboard": 2,
    "ref_program_keyboard": 3,
    "settings_keyboard": 4
}
options_variants = [
        [("🇷🇺 Русский", "🇺🇸 English")],
        [("📈 Statistics", "👥 Referral program", "📲 About the service", "⚙️ Settings"),
         ("📈 Статистика", "👥 Реферальная программа", "📲 О сервисе", "⚙️ Настройки")],
        [("💵 Refill", "💸Withdraw"), ("💵 Пополнить", "💸 Вывести")],
        [("🔗 Invitation link",), ("🔗 Пригласительная ссылка",)],
        [("💬 Language", "💳 Payment requisites", "👤 Set an inviter"),
         ("💬 Язык", "💳 Платежные реквизиты", "👤 Установить приглашающего")]
    ]


def get_keyboard(name, is_eng):
    keyboard_num = keyboard_names[name]
    if keyboard_num < 2:
        call_method = reply_keyboard
    else:
        call_method = inline_keyboard
    return call_method(options_variants[keyboard_num], is_eng)


def reply_keyboard(options, is_eng):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    if is_eng is None or is_eng:
        option_variant = options[0]
    else:
        option_variant = options[1]
    length = len(options)
    for cur_measure in range(0, length, 2):
        row = [option_variant[cur_measure]]
        if cur_measure + 1 < length:
            row.append(option_variant[cur_measure + 1])
        keyboard.row(*row)
    return keyboard


def inline_keyboard(options, is_eng):
    keyboard = InlineKeyboardMarkup()

    if is_eng is None or is_eng:
        option_variant = options[0]
    else:
        option_variant = options[1]
    length = len(option_variant)
    for cur_measure in range(0, length, 2):
        row = [InlineKeyboardButton(text=option_variant[cur_measure], callback_data=options[0][cur_measure][2:])]
        if cur_measure + 1 < length:
            row.append(InlineKeyboardButton(text=option_variant[cur_measure + 1],
                                            callback_data=options[0][cur_measure + 1][2:]))
        keyboard.row(*row)
    return keyboard
