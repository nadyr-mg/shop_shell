from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

import config

import binascii
from hashlib import sha256
from random import choice


ALPHABET = "_-0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

# <editor-fold desc="Keyboards info">
keyboard_names = {
    "lang_keyboard": 0,
    "main_keyboard": 1,
    "balance_keyboard": 2,
    "ref_program_keyboard": 3,
    "settings_keyboard": 4,
    "requisites_keyboard": 5,
    "currency_keyboard": 6
}
options_variants = [
    [("🇷🇺 Русский", "🇺🇸 English")],
    [("📈 Statistics", "👥 Referral program", "📲 About the service", "⚙ Settings"),
     ("📈 Статистика", "👥 Реферальная программа", "📲 О сервисе", "⚙ Настройки")],
    [("💵 Refill", "💸 Withdraw", "🔄 Reinvest"), ("💵 Пополнить", "💸 Вывести", "🔄 Реинвест")],
    [("🔗 Invitation link",), ("🔗 Пригласительная ссылка",)],
    [("💬 Language", "💳 Payment requisites", "👤 Set an inviter"),
     ("💬 Язык", "💳 Платежные реквизиты", "👤 Установить приглашающего")],
    ("AdvCash", "Payeer", "Bitcoin", "Qiwi", "Perfect Money"),
    [("USD", "BTC")]
]
# </editor-fold>


# <editor-fold desc="Generate keyboards">
def get_keyboard(name, is_eng=None):
    keyboard_num = keyboard_names[name]
    if keyboard_num < 2:
        call_method = reply_keyboard
    else:
        call_method = inline_keyboard
    return call_method(options_variants[keyboard_num], is_eng)


def reply_keyboard(options, is_eng):
    if is_eng is None or is_eng:
        option_variant = options[0]
    else:
        option_variant = options[1]

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    length = len(option_variant)
    for cur_measure in range(0, length, 2):
        row = [option_variant[cur_measure]]
        if cur_measure + 1 < length:
            row.append(option_variant[cur_measure + 1])
        keyboard.row(*row)
    return keyboard


def inline_keyboard(options, is_eng):
    if is_eng is None or is_eng:
        option_variant = options[0]
    else:
        option_variant = options[1]

    keyboard = InlineKeyboardMarkup()
    length = len(option_variant)
    for cur_measure in range(0, length, 2):
        row = [InlineKeyboardButton(text=option_variant[cur_measure], callback_data=options[0][cur_measure])]
        if cur_measure + 1 < length:
            row.append(InlineKeyboardButton(text=option_variant[cur_measure + 1],
                                            callback_data=options[0][cur_measure + 1]))
        keyboard.row(*row)
    return keyboard


def requisites_keyboard(name, requisites):
    options = options_variants[keyboard_names[name]]
    keyboard = InlineKeyboardMarkup()
    for cur_measure in range(len(options)):
        keyboard.add(InlineKeyboardButton(text=options[cur_measure] + ": {}".format(requisites[cur_measure]),
                                          callback_data=options[cur_measure]))
    return keyboard
# </editor-fold>


# <editor-fold desc="Check requisite validity">
def check_requisite(pay_method, requisite):
    flag = True
    if pay_method == "AdvCash" and (len(requisite) != 13 or not (requisite[0].isalpha() and requisite[1:].isnumeric())):
        flag = False
    elif pay_method == "Payeer" and (len(requisite) != 9 or not (requisite[0].isalpha() and requisite[1:].isnumeric())):
        flag = False
    elif pay_method == "Bitcoin" and len(requisite) < 20:
        flag = False
    elif pay_method == "Qiwi" and (len(requisite) < 6 or not (requisite[2:].isnumeric())):
        flag = False
    elif pay_method == "Perfect Money" and (len(requisite) != 9 or not (requisite[1:].isnumeric())):
        flag = False
    return flag
# </editor-fold>


# <editor-fold desc="Referral program functions">
def lift_on_lines(users_db,  user_id, func, **kwargs):
    cur_id = user_id
    remember_ids = [cur_id]
    for cur_line in range(1, 4):
        inviter = users_db.select_ref_inviter(cur_id)
        if inviter is None or inviter in remember_ids:
            break

        func(users_db, cur_line, inviter, kwargs)

        cur_id = inviter
        remember_ids.append(cur_id)


def update_people_on_line(users_db, user_id, cur_line, **kwargs):
    operation = kwargs.get('operation')
    users_db.update_ref_people_count(user_id, cur_line, operation)


def update_earn_on_line(users_db, user_id, cur_line, **kwargs):
    line_value = kwargs.get('line_value') * (0.08 / (2 ** (cur_line - 1)))
    users_db.update_ref_line(user_id, cur_line, line_value)
# </editor-fold>


# <editor-fold desc="Common functions">
def calc_percent(value):
    percentage = 0
    if 1 <= value <= 50:
        percentage = 0.0111
    elif 51 <= value <= 100:
        percentage = 0.0222
    elif 101 <= value <= 500:
        percentage = 0.0333
    elif 501 <= value <= 1000:
        percentage = 0.0444
    elif value > 1000:
        percentage = 0.0555
    return percentage


def gen_salt():
    chars = []
    for i in range(8):
        chars.append(choice(ALPHABET))

    return "".join(chars)
# </editor-fold>


# <editor-fold desc="Functions for payeer merchant">
def get_desc_sign(order_id, amount):
    desc = binascii.b2a_base64(config.PAYEER_PAY_DESC.format(order_id).encode('utf8'))[:-1]
    string_to_hash = ":".join(map(str, [config.PAYEER_MERCHANT_ID, order_id, amount, config.PAYEER_CURRENCY, desc,
                                       config.PAYEER_SECRET_KEY]))
    return desc, sha256(string_to_hash.encode()).hexdigest().upper()
# </editor-fold>


if __name__ == '__main__':
    print(calc_percent(1.0))
