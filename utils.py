from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

import config

import binascii
from hashlib import sha256
from random import choice

schedule_thread = None
ALPHABET = "_-0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
post_data_fields = ("m_operation_id", "m_operation_ps", "m_operation_date", "m_operation_pay_date", "m_shop",
                    "m_orderid", "m_amount", "m_curr", "m_desc", "m_status", "m_sign")

# <editor-fold desc="Keyboards info">
keyboard_names = {
    "lang_keyboard": 0,
    "main_keyboard": 1,
    "balance_keyboard": 2,
    "ref_program_keyboard": 3,
    "settings_keyboard": 4,
    "requisites_keyboard": 5,
    "currency_keyboard": 6,
    'withdraw_currency': 7,
    "pay_sys_keyboard": 8
}
options_variants = [
    [("🇷🇺 Русский", "🇺🇸 English")],
    [("📈 Statistics", "👥 Referral program", "📲 About the service", "⚙ Settings"),
     ("📈 Статистика", "👥 Реферальная программа", "📲 О сервисе", "⚙ Настройки")],
    [("💵 Refill", "💸 Withdraw", "🔄 Reinvest"), ("💵 Пополнить", "💸 Вывести", "🔄 Реинвест")],
    [("🔗 Invitation link",), ("🔗 Пригласительная ссылка",)],
    [("💬 Language", "💳 Payment requisites", "👤 Set an inviter", "💳 Requisites examples"),
     ("💬 Язык", "💳 Платежные реквизиты", "👤 Установить приглашающего", "💳 Примеры реквизитов")],
    ("AdvCash", "Payeer", "Bitcoin", "Qiwi", "Yandex Money"),
    [("USD", "BTC")],
    [("💸 USD", "💸 BTC")],
    [("💸 AdvCash", "💸 Payeer", "💸 Qiwi", "💸 Yandex Money")]
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
    if pay_method == "AdvCash":
        from re import match
        if match(r"[\w.-]+@[\w.-]+", requisite) is None:
            flag = False
    elif pay_method == "Payeer" and (len(requisite) != 9 or not (requisite[0].isalpha() and requisite[1:].isnumeric())):
        flag = False
    elif pay_method == "Bitcoin" and len(requisite) < 20:
        flag = False
    elif pay_method == "Qiwi" and (len(requisite) < 6 or not (requisite[2:].isnumeric())):
        flag = False
    elif pay_method == "Yandex Money" and (len(requisite) != 15 or not (requisite.isnumeric())):
        flag = False
    return flag
# </editor-fold>


# <editor-fold desc="Referral program functions">
def lift_on_lines(users_db, user_id, func, **kwargs):
    cur_id = user_id
    remember_ids = [cur_id]
    is_people = func == update_people_on_line
    for cur_line in range(1, 4):
        inviter = users_db.select_ref_inviter(cur_id)
        if inviter is None or inviter in remember_ids:
            break

        if is_people:
            func(users_db, inviter, cur_line, **kwargs)
        else:
            value = func(users_db, inviter, cur_line, **kwargs)
            users_db.update_stats_add_to_balance(inviter, value, func == update_earn_on_line_btc)

        cur_id = inviter
        remember_ids.append(cur_id)


def update_people_on_line(users_db, user_id, cur_line, **kwargs):
    operation = kwargs.get('operation')
    users_db.update_ref_people_count(user_id, cur_line, operation)


def update_earn_on_line(users_db, user_id, cur_line, **kwargs):
    line_value = kwargs.get('line_value') * (0.08 / (2 ** (cur_line - 1)))
    users_db.update_ref_line(user_id, cur_line, line_value)
    return line_value


def update_earn_on_line_btc(users_db, user_id, cur_line, **kwargs):
    line_value_btc = kwargs.get('line_value_btc') * (0.08 / (2 ** (cur_line - 1)))
    users_db.update_ref_line_btc(user_id, cur_line, line_value_btc)
    return line_value_btc
# </editor-fold>


# <editor-fold desc="Invest handler">
def invested(users_db, user_id, amount, is_btc=0):
    if is_btc:
        percent_btc = calc_percent_btc(amount)
        users_db.update_stats_invested_btc(user_id, amount, amount * percent_btc)
        lift_on_lines(users_db, user_id, update_earn_on_line_btc, line_value_btc=amount)
    else:
        percent = calc_percent(amount)
        users_db.update_stats_invested(user_id, amount, amount * percent)
        lift_on_lines(users_db, user_id, update_earn_on_line, line_value=amount)
# </editor-fold>


# <editor-fold desc="Common functions">
def calc_percent(value):
    percent = 0
    if config.MIN_REFILL_USD <= value <= 50:
        percent = 0.0111
    elif 51 <= value <= 100:
        percent = 0.0222
    elif 101 <= value <= 500:
        percent = 0.0333
    elif 501 <= value <= 1000:
        percent = 0.0444
    elif value > 1000:
        percent = 0.0555
    return percent


def calc_percent_btc(value):
    percent = 0
    if config.MIN_REFILL_BTC <= value <= 50:
        percent = 0.0111
    elif 51 <= value <= 100:
        percent = 0.0222
    elif 101 <= value <= 500:
        percent = 0.0333
    elif 501 <= value <= 1000:
        percent = 0.0444
    elif value > 1000:
        percent = 0.0555
    return percent


def gen_salt():
    chars = []
    for i in range(10):
        chars.append(choice(ALPHABET))

    return "".join(chars)


def to_bitcoin(value):
    return value / 100000000 if value != 0 else 0


def to_satoshi(value):
    return int(value * 100000000)


def init_schedule(schedule):
    global schedule_thread
    schedule_thread = schedule


def stop_schedule_thread():
    global schedule_thread
    if schedule_thread is not None:
        schedule_thread.set()
        schedule_thread = None
# </editor-fold>


# <editor-fold desc="Functions for payeer merchant">
def adjust_float(a):
    a = str(a)
    dot_idx = a.find('.')
    if dot_idx == -1:
        a += ".00"
    elif len(a) - dot_idx - 1 < 2:
        a += "0"
    return a


def get_desc_sign(order_id, amount):
    amount = adjust_float(amount)
    desc = binascii.b2a_base64(config.PAYEER_PAY_DESC.encode('utf8'))[:-1].decode()
    string_to_hash = ":".join(map(str, [config.PAYEER_MERCHANT_ID, order_id, amount, config.PAYEER_CURRENCY, desc,
                                       config.PAYEER_SECRET_KEY]))
    return desc, sha256(string_to_hash.encode()).hexdigest().upper()


def check_payment(ip_address, post_data):
    if ip_address in config.PAYEER_TRUSTED_IPS and all(key in post_data for key in post_data_fields):
        parameters = [post_data[post_data_fields[cur_key]][0] for cur_key in range(len(post_data_fields) - 1)]
        if 'm_params' in post_data:
            parameters.append(post_data['m_params'][0])
        parameters.append(config.PAYEER_SECRET_KEY)

        result_hash = sha256(":".join(parameters).encode()).hexdigest().upper()
        if post_data['m_sign'][0] == result_hash:
            if post_data['m_status'][0] == 'success':
                return 1
            else:
                return 0
    return -1
# </editor-fold>


if __name__ == '__main__':
    print(calc_percent(1.0))
