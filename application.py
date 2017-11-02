import telebot
from flask import Flask, request, render_template

from random import randint, seed
from time import sleep

import utils
from Data_base.user_db_class import Users_db
import config

bot = telebot.TeleBot(config.TOKEN, threaded=False)
application = Flask(__name__)
bot.remove_webhook()
sleep(1)
bot.set_webhook(url="https://{}/{}".format(config.WEBHOOK_DOMAIN, config.TOKEN))

payed = False


# <editor-fold desc="Server's handlers">
@application.route('/{}'.format(config.TOKEN), methods=['POST'])
def handle_request():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return '', 200


# <editor-fold desc="Main handlers">
@application.route('/')
def handle_index():
    return render_template('index.html')


@application.route('/about.html')
def handle_about():
    return render_template('about.html')
# </editor-fold>


# <editor-fold desc="Payeer handlers">
@application.route('/gratz.php')
def handle_success():
    return '<b style="color:#03C159;"> Оплата прошла успешно </b>'


@application.route('/fiasko.php')
def handle_fail():
    return '<b style="color:#C12503;"> В процессе оплаты произошла ошибка. Попробуйте еще раз </b>'


@application.route('/check.php', methods=['GET', 'POST'])
def handle_status():
    global payed
    if request.method == 'GET':
        text = '<b style="color:#D7F900;"> Платеж еще обрабатывается </b>' if not payed else '<b style=' \
                                                                        '"color:#03C159;"> Оплата прошла успешно </b>'
        return text
    else:
        try:
            payed = True
            bot.send_message(config.HOST_ID, request.stream.read().decode("utf-8"))
        except Exception:
            return "Error"
    return ""


@application.route('/payment/<order_id>')
def handle_payment(order_id):
    users_db = Users_db(config.DB_NAME)
    amount = users_db.select_repl_amount(order_id)
    users_db.close()

    if amount is None:
        result = '<b style="color:#EE6060;"> Неправильный номер заказа </b>'
    else:
        amount = amount[0]
        desc, sign = utils.get_desc_sign(order_id, amount)
        result = render_template('make_payment.html', m_shop=config.PAYEER_MERCHANT_ID, m_orderid=order_id,
                                 m_amount=amount, m_curr=config.PAYEER_CURRENCY, m_desc=desc, m_sign=sign)

    return result


@application.route('/payeer_421419776.txt')
def handle_payeer_confirm():
    return config.PAYEER_CONFIRM
# </editor-fold>
# </editor-fold>


# <editor-fold desc="Standard commands">
@bot.message_handler(commands=['start'])
def start_command(message):
    chat = message.chat
    if chat.type == "private":
        bot.send_message(chat.id, "Hello, {}! Please select your language:".format(chat.first_name),
                         reply_markup=utils.get_keyboard("lang_keyboard"))
        users_db = Users_db(config.DB_NAME)
        # Handle inserting user's statistics and ref_program info
        if not users_db.is_exist_stats(chat.id):
            users_db.insert_stats((chat.id, 0.0, 0.0, 0.0, 1))
            users_db.insert_ref(chat.id)

        # Handle updating inviter from ref_program
        salt = message.text.split()[-1]
        if salt.isnumeric():
            found_user_id = users_db.select_salts_user_id(salt)
            if found_user_id is not None:
                users_db.update_ref_inviter(chat.id, found_user_id[0])
                utils.lift_on_lines(users_db, chat.id, utils.update_people_on_line, operation='+')

        # Handle inserting user's requisites
        if not users_db.is_exist_requisites(chat.id):
            users_db.insert_requisites(chat.id)
        users_db.close()
    else:
        bot.send_message(chat.id, "This bot can work only in private chats")
        bot.leave_chat(chat.id)


@bot.message_handler(commands=['menu'])
def start_command(message):
    chat = message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    bot.send_message(chat.id, "...", reply_markup=utils.get_keyboard("main_keyboard", is_eng))


# </editor-fold>


# <editor-fold desc="Reply markup handlers">
@bot.message_handler(func=lambda message: message.text == "🇺🇸 English" or message.text == "🇷🇺 Русский")
def handle_language(message):
    chat = message.chat
    is_eng = message.text == '🇺🇸 English'
    if is_eng:
        text = "You chose english language"
    else:
        text = "Вы выбрали русский язык"
    bot.send_message(chat.id, text, reply_markup=utils.get_keyboard("main_keyboard", is_eng))

    users_db = Users_db(config.DB_NAME)
    users_db.update_stats_field(chat.id, 'is_eng', int(is_eng))
    users_db.close()


@bot.message_handler(func=lambda message: message.text == "📈 Statistics" or message.text == "📈 Статистика")
def handle_statistics(message):
    chat = message.chat
    users_db = Users_db(config.DB_NAME)
    user_stats = users_db.select_stats(chat.id)
    users_db.close()
    if user_stats[4]:
        text = "Your balance: *{:.2f} USD*\n\nSum of your investments: *{:.2f} USD*\n\nProfit from the project: " \
               "*{:.2f} USD*"
    else:
        text = "Ваш баланс: *{:.2f} USD*\n\nСумма ваших инвестиций: *{:.2f} USD*\n\nПрибыль от проэкта: *{:.2f} USD*"
    bot.send_message(chat.id, text.format(user_stats[1], user_stats[2], user_stats[3]),
                     reply_markup=utils.get_keyboard("balance_keyboard", user_stats[4]), parse_mode="Markdown")


@bot.message_handler(
    func=lambda message: message.text == "👥 Referral program" or message.text == "👥 Реферальная программа")
def handle_ref_program(message):
    chat = message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    ref_program_info = users_db.select_ref_all(chat.id)
    users_db.close()
    if is_eng:
        text = "Earned total: *{:.2f} USD*\n\nInvited in 1st line: *{}*\nInvited in 2nd line: *{}*\nInvited in 3rd" \
               " line: *{}*\n\nEarned from 1st line: *{:.2f} USD*\nEarned from 2nd line: *{:.2f} USD*" \
               "\nEarned from 3rd line: *{:.2f} USD*\n\nYour id in Telegram: *{}*"
    else:
        text = "Заработано вообщем: *{:.2f} USD*\n\nПриглашенных в 1-ой линии: *{}*\nПриглашенных во 2-ой линии: *{}*" \
               "\nПриглашенных в 3ей линии: *{}*\n\nЗаработано с 1-ой линии: *{:.2f} USD*\nЗаработано со 2-ой линии: " \
               "*{:.2f} USD*\nЗаработано с 3-ей линии: *{:.2f} USD*\n\nВаш id в Telegram: *{}*"
    ref_program_info = tuple(map(lambda line: 0.0 if line is None else line, ref_program_info))
    bot.send_message(chat.id, text.format(ref_program_info[2] + ref_program_info[3] + ref_program_info[4],
                                          ref_program_info[5], ref_program_info[6], ref_program_info[7],
                                          ref_program_info[2], ref_program_info[3], ref_program_info[4], chat.id),
                     reply_markup=utils.get_keyboard("ref_program_keyboard", is_eng), parse_mode="Markdown")


@bot.message_handler(func=lambda message: message.text == "📲 About the service" or message.text == "📲 О сервисе")
def handle_statistics(message):
    chat = message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "Sample text"
    else:
        text = "Сампл текст"
    bot.send_message(chat.id, text)


@bot.message_handler(func=lambda message: message.text == "⚙ Settings" or message.text == "⚙ Настройки")
def handle_statistics(message):
    chat = message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "What you want to change?"
    else:
        text = "Что вы хотите изменить?"
    bot.send_message(chat.id, text, reply_markup=utils.get_keyboard("settings_keyboard", is_eng))


# </editor-fold>


# <editor-fold desc="Handlers with callbacks. First level">
@bot.callback_query_handler(func=lambda call: call.data == "🔗 Invitation link")
def handle_invitation_link(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "Here is your invitation link:\n{}"
    else:
        text = "Ваша пригласительная ссылка:\n{}"

    users_db = Users_db(config.DB_NAME)
    salt = users_db.select_salt(chat.id)
    if salt is None:
        if not users_db.insert_salt(randint(1, 1000000000), chat.id):
            seed()
            users_db.insert_salt(randint(1, 1000000000), chat.id)
    else:
        salt = salt[0]
    users_db.close()
    invitation_link = "https://t.me/{}?start={}".format(config.BOT_USERNAME, salt)
    bot.send_message(chat.id, text.format(invitation_link))


@bot.callback_query_handler(func=lambda call: call.data == "💬 Language")
def handle_change_language(call):
    chat = call.message.chat
    bot.send_message(chat.id, "Choose language:", reply_markup=utils.get_keyboard("lang_keyboard"))


@bot.callback_query_handler(func=lambda call: call.data == "💳 Payment requisites")
def handle_change_requisites(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    requisites = users_db.select_requisites(chat.id)
    users_db.close()

    if is_eng:
        requisites = tuple(map(lambda requisite: "Missing" if requisite is None else requisite, requisites))
        text = "*Your requisites:*"
    else:
        requisites = tuple(map(lambda requisite: "Отсутствует" if requisite is None else requisite, requisites))
        text = "*Ваши реквизиты:*"

    bot.send_message(chat.id, text, reply_markup=utils.requisites_keyboard("requisites_keyboard", requisites[1:]),
                     parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "🔄 Reinvest")
def handle_change_reinvest(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    balance = users_db.select_stats_field(chat.id, 'balance')

    percentage = utils.calc_percent(balance)
    if not percentage:
        if is_eng:
            text = "You don't have enough money on balance to reinvest.\nMinimum is *1 USD*"
        else:
            text = "У вас не достаточно средств, чтобы реинвестировать.\nМинимальная сумма: *1 USD*"
    else:
        users_db.update_stats_reinvest(chat.id, balance * percentage)
        if is_eng:
            text = "Successfully reinvested"
        else:
            text = "Реинвестирование прошло успешно"
    users_db.close()

    bot.send_message(chat.id, text, reply_markup=utils.get_keyboard("main_keyboard", is_eng), parse_mode="Markdown")


# </editor-fold>


# <editor-fold desc="Setting an inviter interaction">
@bot.callback_query_handler(func=lambda call: call.data == "👤 Set an inviter")
def handle_change_inviter(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')

    inviter = users_db.select_ref_inviter(chat.id)
    if inviter is not None:
        if is_eng:
            text = "You already have inviter: *{}*"
        else:
            text = "У вас уже есть пригласитель: *{}*"
        bot.send_message(chat.id, text.format(inviter), parse_mode="Markdown")
        return
    users_db.close()

    if is_eng:
        text = "👤 Select your inviter. Type in his id:"
    else:
        text = "👤 Выберете пригласителя. Введите его id:"
    force_reply = telebot.types.ForceReply(selective=False)
    bot.send_message(chat.id, text, reply_markup=force_reply)


@bot.message_handler(func=
                     lambda message: message.reply_to_message is not None and message.reply_to_message.text[
                                                                                  0] == "👤")
def handle_reply_inviter(message):
    chat = message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    if len(message.text) < 20 and message.text.isnumeric():
        inviter_id = int(message.text)
        users_db.update_ref_inviter(chat.id, inviter_id)

        utils.lift_on_lines(users_db, chat.id, utils.update_people_on_line, operation='+')

        if is_eng:
            text = "Inviter is set up!"
        else:
            text = "Пригласитель установлен!"
    else:
        if is_eng:
            text = "You provided wrong id"
        else:
            text = "Введен неправильный id"
    users_db.close()

    bot.send_message(chat.id, text)


# </editor-fold>


# <editor-fold desc="Saving requisite info interaction">
@bot.callback_query_handler(
    func=lambda call: call.data in ("AdvCash", "Payeer", "Bitcoin", "Qiwi", "Perfect Money"))
def handle_requisites(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "💳 {} chosen. Type in your requisite:"
    else:
        text = "💳 {} выбран. Укажите ваш реквизит:"

    force_reply = telebot.types.ForceReply(selective=False)
    bot.send_message(chat.id, text.format(call.data), reply_markup=force_reply)


@bot.message_handler(func=
                     lambda message: message.reply_to_message is not None and message.reply_to_message.text[0] == "💳")
def handle_reply_requisite(message):
    chat = message.chat
    pay_method = message.reply_to_message.text.split()[1]
    requisite = ''.join(message.text.split())

    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    if not utils.check_requisite(pay_method, requisite):
        if is_eng:
            text = "You provided invalid requisite"
        else:
            text = "Введен неправильный реквизит"
    else:
        users_db.update_requisite(chat.id, pay_method, requisite)
        if is_eng:
            text = "Requisite is saved: *{}*"
        else:
            text = "Реквизит сохранен: *{}*"
    users_db.close()

    bot.send_message(chat.id, text, reply_markup=utils.get_keyboard("main_keyboard", is_eng), parse_mode="Markdown")
# </editor-fold>


# <editor-fold desc="Refill interaction">
@bot.callback_query_handler(func=lambda call: call.data == "💵 Refill")
def handle_refill(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "Choose currency:"
    else:
        text = "Выберете валюту:"

    bot.send_message(chat.id, text.format(call.data), reply_markup=utils.get_keyboard("currency_keyboard"))


@bot.callback_query_handler(func=lambda call: call.data == "USD")
def handle_refill_usd(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "🔢 Type in desired amount:"
    else:
        text = "🔢 Введите желаемую сумму:"

    force_reply = telebot.types.ForceReply(selective=False)
    bot.send_message(chat.id, text.format(call.data), reply_markup=force_reply)


@bot.message_handler(func=
                     lambda message: message.reply_to_message is not None and message.reply_to_message.text[0] == "🔢")
def handle_refill_usd_entered(message):
    chat = message.chat
    try:
        amount = round(float(message.text.strip()), 2)
    except ValueError:
        amount = -1

    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    if amount > 1:
        text = "Follow the link to make payment:" if is_eng else "Перейдите по ссылке для оплаты:"
        btn_text = "Link for payment:" if is_eng else "Ссылка на оплату:"

        order_id = utils.gen_salt()
        users_db.insert_repl_order(order_id, amount, chat.id)

        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton(text=btn_text, url="https://{}/payment/{}".format(
                                                                        config.WEBHOOK_DOMAIN, order_id)))
    else:
        if amount == -1:
            text = "🔢 Invalid amount provided" if is_eng else "🔢 Введена неправильная сумма"
        else:
            text = "🔢 Amount should be greater than *1$*" if is_eng else "🔢 Сумма должна быть больше *1$*"
        keyboard = telebot.types.ForceReply(selective=False)
    users_db.close()

    bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")
# </editor-fold>


if __name__ == '__main__':
    application.run(host=config.WEBHOOK_LISTEN, port=config.WEBHOOK_PORT, debug=True)
