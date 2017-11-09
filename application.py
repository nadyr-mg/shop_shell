import telebot
from flask import Flask, request, render_template

from random import randint, seed
from time import sleep
from urllib.parse import parse_qs
from json import loads
import schedule

import utils
from Data_base.user_db_class import Users_db
import config
import payeer_functions
import coinbase_functions

DEBUG = False

bot = telebot.TeleBot(config.TOKEN)
application = Flask(__name__)
bot.remove_webhook()
sleep(1)
if DEBUG == 0:
    bot.set_webhook(url="https://{}/{}".format(config.WEBHOOK_DOMAIN, config.TOKEN))
else:
    bot.set_webhook(url="https://{}:{}/{}".format(config.AWS_IP, config.WEBHOOK_PORT, config.TOKEN),
                    certificate=open('./SSL_certs/webhook_cert.pem', 'rb'))


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


@application.route('/check.php', methods=['POST'])
def handle_status():
    post_data = parse_qs(request.stream.read().decode("utf-8"))
    result = utils.check_payment(request.remote_addr, post_data)
    if result == -1:
        responce = "Wrong data"
    else:
        users_db = Users_db(config.DB_NAME)
        if result == 0:
            responce = post_data['m_orderid'][0] + '|error'
        else:
            responce = post_data['m_orderid'][0] + '|success'
            user_id, amount = users_db.select_repl_user_amount(post_data['m_orderid'][0])
            utils.invested(users_db, user_id, amount)

            is_eng = users_db.select_stats_field(user_id, 'is_eng')
            text = "Successfully invested {} USD" if is_eng else "Успешно внесена сумма {} USD"
            bot.send_message(user_id, text.format(amount))
        users_db.delete_repl_by_order(post_data['m_orderid'][0])
        users_db.close()
    return responce


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


# <editor-fold desc="Coinbase handler">
@application.route('/check_btc.php', methods=['GET', 'POST'])
def handle_status_btc():
    bot.send_message(config.HOST_ID, "Entered")

    bot.send_message(config.HOST_ID, str(request.environ))
    if 'CB-SIGNATURE' in request.environ:
        sign = request.environ['CB-SIGNATURE']
        bot.send_message(config.HOST_ID, sign)
    try:
        data = loads(request.stream.read().decode("utf-8"))
    except Exception:
        return "no", 500
    bot.send_message(config.HOST_ID, str(data))

    try:
        bot.send_message(config.HOST_ID, coinbase_functions.check(data, sign))
    except Exception:
        pass

    bot.send_message(config.HOST_ID, "End")
    return 500, ""
# </editor-fold>
# </editor-fold>


# <editor-fold desc="Event overcharge">
def overcharge():
    users_db = Users_db(config.DB_NAME)
    users = users_db.select_stats_users()

    text_variants = ("Вам начислена сумма дохода", "You are credited with the amount of income")
    for user in users:
        user_id = user[0]
        income, income_btc = users_db.select_stats_income(user_id)
        if income > 0.0 or income_btc > 0:
            is_eng = users_db.select_stats_field(user_id, 'is_eng')
            users_db.update_stats_add_income(user_id)
            bot.send_message(user_id, text_variants[is_eng])
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
            users_db.insert_stats((chat.id, 0.0, 0, 0.0, 0, 0.0, 0, 1))
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

        if users_db.select_addr_address(chat.id) is None:
            users_db.insert_addr(chat.id)

        users_db.close()
    else:
        bot.send_message(chat.id, "This bot can work only in private chats")
        bot.leave_chat(chat.id)


@bot.message_handler(commands=['menu'])
def menu_command(message):
    chat = message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    bot.send_message(chat.id, "...", reply_markup=utils.get_keyboard("main_keyboard", is_eng))


@bot.message_handler(commands=['schedule'])
def schedule_command(message):
    if message.chat.id != config.HOST_ID:
        return

    command = message.text.split()

    if len(command) == 2:
        command = command[1].lower()

    if command == 'start':
        if utils.schedule_thread is None:
            schedule.every().day.at("01:00").do(overcharge)
            utils.init_schedule(schedule.run_continuously())
        text = "Scheduler is running"
    elif command == 'stop':
        utils.stop_schedule_thread()
        schedule.clear()
        text = "Scheduler is stopped"
    else:
        text = "Wrong command"
    bot.send_message(config.HOST_ID, text)
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
    if user_stats[7]:
        text = "Your balance: *{:.2f} USD*\nYour balance: *{:.5f} BTC*\n\nSum of your investments: *{:.2f} USD*\nSum " \
               "of your investments: *{:.5f} BTC*\n\nIncome from the project: *{:.2f} USD*\nIncome from the project: " \
               "*{:.5f} BTC* "
    else:
        text = "Ваш баланс: *{:.2f} USD*\nВаш баланс: *{:.5f} BTC*\n\nСумма ваших инвестиций: *{:.2f} USD*\nСумма " \
               "ваших инвестиций: *{:.5f} BTC*\n\nДоход от проекта: *{:.2f} USD*\nДоход от проекта: *{:.5f} BTC* "
    bot.send_message(chat.id, text.format(user_stats[1], utils.to_bitcoin(user_stats[2]), user_stats[3],
                    utils.to_bitcoin(user_stats[4]), user_stats[5], utils.to_bitcoin(user_stats[6])),
                    reply_markup=utils.get_keyboard("balance_keyboard", user_stats[7]), parse_mode="Markdown")


@bot.message_handler(
    func=lambda message: message.text == "👥 Referral program" or message.text == "👥 Реферальная программа")
def handle_ref_program(message):
    chat = message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    ref_program_info = users_db.select_ref_all(chat.id)
    users_db.close()
    if is_eng:
        text = "Earned total: *{:.2f} USD*\nEarned total: *{:.5f} BTC*\n\nInvited in 1st line: *{}*\nInvited in 2nd " \
               "line: *{}*\nInvited in 3rd line: *{}*\n\nEarned from 1st line: *{:.2f} USD*\nEarned from 1st line: *{" \
               ":.5f} BTC*\n\nEarned from 2nd line: *{:.2f} USD*\nEarned from 2nd line: *{:.5f} BTC*\n\nEarned from " \
               "3rd line: *{:.2f} USD*\nEarned from 3rd line: *{:.5f} BTC*\n\nYour id in Telegram: *{}* "
    else:
        text = "Прибыль вообщем: *{:.2f} USD*\nПрибыль вообщем: *{:.5f} BTC*\n\nПриглашенных в 1-ой линии: *{" \
               "}*\nПриглашенных во 2-ой линии: *{}*\nПриглашенных в 3-ей линии: *{}*\n\nПрибыль с 1-ой линии: *{" \
               ":.2f} USD*\nПрибыль с 1-ой линии: *{:.5f} BTC*\n\nПрибыль со 2-ой линии: *{:.2f} " \
               "USD*\nПрибыль со 2-ой линии: *{:.5f} BTC*\n\nПрибыль с 3-ей линии: *{:.2f} USD*\nПрибыль с " \
               "3-ей линии: *{:.5f} BTC*\n\nВаш id в Telegram: *{}*"
    ref_program_info = tuple(map(lambda line: 0 if line is None else line, ref_program_info))
    bot.send_message(chat.id, text.format(ref_program_info[2] + ref_program_info[4] + ref_program_info[6],
        utils.to_bitcoin(ref_program_info[3] + ref_program_info[5] + ref_program_info[7]), ref_program_info[8],
        ref_program_info[9], ref_program_info[10], ref_program_info[2], utils.to_bitcoin(ref_program_info[3]),
        ref_program_info[4], utils.to_bitcoin(ref_program_info[5]), ref_program_info[6],
        utils.to_bitcoin(ref_program_info[7]), chat.id),
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


@bot.callback_query_handler(func=lambda call: call.data == "💳 Requisites examples")
def handle_requisites(call):
    chat = call.message.chat
    text = "*AdvCash:* advcash@gmail.com\n*Payeer:* P1000000\n*Bitcoin:* 13C3fxYMZzbt9HsTvCni779gqXyPadGtTQ\n*Qiwi:* " \
           "+7953155XXXX\n*Yandex Money:* 410011499718000 "
    bot.send_message(chat.id, text, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "🔄 Reinvest")
def handle_change_reinvest(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    balance = users_db.select_stats_field(chat.id, 'balance')
    balance_btc = users_db.select_stats_field(chat.id, 'balance_btc')

    if balance < config.MIN_REFILL_USD and balance_btc < config.MIN_REFILL_BTC:
        if is_eng:
            text = "You don't have enough money on balance to reinvest.\nMinimum is *{} USD* or *{} BTC*"
        else:
            text = "У вас не достаточно средств, чтобы реинвестировать.\nМинимальная сумма: *{} USD* или *{} BTC*"
        text = text.format(config.MIN_REFILL_USD, utils.to_bitcoin(config.MIN_REFILL_BTC))
    else:
        if balance >= config.MIN_REFILL_USD:
            users_db.update_stats_nullify_balance(chat.id)
            utils.invested(users_db, chat.id, balance)
        if balance_btc >= config.MIN_REFILL_BTC:
            users_db.update_stats_nullify_balance_btc(chat.id)
            utils.invested(users_db, chat.id, balance_btc, 1)
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
    func=lambda call: call.data in ("AdvCash", "Payeer", "Bitcoin", "Qiwi", "Yandex Money"))
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

    bot.send_message(chat.id, text.format(requisite), reply_markup=utils.get_keyboard("main_keyboard", is_eng),
                     parse_mode="Markdown")
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

    bot.send_message(chat.id, text, reply_markup=utils.get_keyboard("currency_keyboard"))


# <editor-fold desc="USD">
@bot.callback_query_handler(func=lambda call: call.data == "USD")
def handle_refill_usd(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "🔢 Type in desired amount:\n*Minimal amount is {} USD*"
    else:
        text = "🔢 Введите желаемую сумму:\n*Минимальная сумма: {} USD*"

    force_reply = telebot.types.ForceReply(selective=False)
    bot.send_message(chat.id, text.format(config.MIN_REFILL_USD), reply_markup=force_reply, parse_mode="Markdown")


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
    if amount >= config.MIN_REFILL_USD:
        text = "Follow the link to make payment:" if is_eng else "Перейдите по ссылке для оплаты:"
        btn_text = "Link for payment:" if is_eng else "Ссылка на оплату:"

        order_id = utils.gen_salt()
        users_db.insert_repl_order(order_id, amount, chat.id)
        users_db.close()

        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton(text=btn_text, url="https://{}/payment/{}".format(
            config.WEBHOOK_DOMAIN, order_id)))
    else:
        users_db.close()
        if amount == -1:
            text = "🔢 Invalid amount provided" if is_eng else "🔢 Введена неправильная сумма"
        else:
            text = "🔢 Amount should be greater than *{} USD*" if is_eng else "🔢 Сумма должна быть больше *{} USD*"
            text = text.format(config.MIN_REFILL_USD)
        keyboard = telebot.types.ForceReply(selective=False)

    bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")
# </editor-fold>


# <editor-fold desc="BTC">
@bot.callback_query_handler(func=lambda call: call.data == "BTC")
def handle_refill_btc(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    address = users_db.select_addr_address(chat.id)
    if address is None:
        address = coinbase_functions.generate_address()
    else:
        address = address[0]

    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "*Minimal amount is {} BTC*\nYou can send desired amount of BTC and the bot will automatically charge " \
               "them to your deposit.\nSend only one transaction to this address:\n`{}`"
    else:
        text = "*Минимальная сумма: {} BTC*\nВы можете отправить желаемую сумму BTC и бот автоматически занесет её " \
               "в ваш депозит.\nОтправляйте только одну транзакцию на этот адрес:\n`{}`"

    bot.send_message(chat.id, text.format(utils.to_bitcoin(config.MIN_REFILL_BTC), address), parse_mode="Markdown")
# </editor-fold>
# </editor-fold>


# <editor-fold desc="Withdraw interaction">
@bot.callback_query_handler(func=lambda call: call.data == "💸 Withdraw")
def handle_withdraw(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    balance = users_db.select_stats_field(chat.id, 'balance')
    balance_btc = users_db.select_stats_field(chat.id, 'balance_btc')
    users_db.close()

    keyboard = None
    if balance < config.MIN_WITHDRAW_USD and balance_btc < config.MIN_WITHDRAW_BTC:
        if is_eng:
            text = "You don't have enough money to withdraw\nMinimum is *{} USD* or *{} BTC*"
        else:
            text = "У вас нехватает средств для вывода\nМинимальная сумма: *{} USD* or *{} BTC*"
        text = text.format(config.MIN_WITHDRAW_USD, utils.to_bitcoin(config.MIN_WITHDRAW_BTC))
    else:
        if is_eng:
            text = "Choose currency:"
        else:
            text = "Выберете валюту:"
        keyboard = utils.get_keyboard("withdraw_currency")

    bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data in ("💸 USD", "💸 BTC"))
def handle_withdraw_currency(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')

    keyboard = None
    if call.data == "💸 BTC":
        balance_btc = users_db.select_stats_field(chat.id, 'balance_btc')
        users_db.close()
        if balance_btc < config.MIN_WITHDRAW_BTC:
            if is_eng:
                text = "You don't have enough money to withdraw\nMinimum is *{} BTC*"
            else:
                text = "У вас нехватает средств для вывода\nМинимальная сумма: *{} BTC*"
        else:
            if is_eng:
                text = "🅱 Type in desired amount:\nMinimum is *{} BTC*"
            else:
                text = "🅱 Укажите желаемую сумму\nМинимальная сумма: *{} BTC*"
            keyboard = telebot.types.ForceReply(selective=False)
        text = text.format(utils.to_bitcoin(config.MIN_WITHDRAW_BTC))
    else:
        balance = users_db.select_stats_field(chat.id, 'balance')
        users_db.close()
        if balance < config.MIN_WITHDRAW_USD:
            if is_eng:
                text = "You don't have enough money to withdraw\nMinimum is *{} USD*"
            else:
                text = "У вас нехватает средств для вывода\nМинимальная сумма: *{} USD*"
            text = text.format(config.MIN_WITHDRAW_USD)
        else:
            text = "Choose payment system:" if is_eng else "Выберете платежную систему:"
            keyboard = utils.get_keyboard("pay_sys_keyboard")

    bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")


# <editor-fold desc="USD">
@bot.callback_query_handler(
    func=lambda call: call.data[0] == '💸' and call.data in ("💸 AdvCash", "💸 Payeer", "💸 Qiwi", "💸 Yandex Money"))
def handle_pay_sys(call):
    chat = call.message.chat
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    pay_sys = 'yandex' if call.data[2] == 'Y' else call.data[2:].lower()
    requisite = users_db.select_requisite(chat.id, pay_sys)
    users_db.close()

    keyboard = None
    if requisite is not None:
        if is_eng:
            text = "💲 {} chosen. Type in desired amount:\nMinimum is *{} USD*"
        else:
            text = "💲 {} выбран. Укажите желаемую сумму\nМинимальная сумма: *{} USD*"
        text = text.format(call.data[2:], config.MIN_WITHDRAW_USD)
        keyboard = telebot.types.ForceReply(selective=False)
    else:
        if is_eng:
            text = "Requisite is not provided. You can change it in settings"
        else:
            text = "Реквизит не указан. Вы можете изменить это в настройках"

    bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")


@bot.message_handler(func=
                     lambda message: message.reply_to_message is not None and message.reply_to_message.text[0] == "💲")
def handle_withdraw_pay_sys_entered(message):
    chat = message.chat
    try:
        amount = round(float(message.text.strip()), 2)
    except ValueError:
        amount = -1
    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')

    keyboard = None
    if amount >= config.MIN_WITHDRAW_USD:
        pay_sys = message.reply_to_message.text[2: message.reply_to_message.text.find(' ', 2)]
        requisite = users_db.select_requisite(chat.id, pay_sys.lower())
        users_db.close()

        if requisite is None:
            if is_eng:
                text = "Requisite is not provided. You can change it in settings"
            else:
                text = "Реквизит не указан. Вы можете изменить это в настройках"
        else:
            errors = payeer_functions.payout_possibility(pay_sys, requisite, amount, is_eng)
            if errors == "":
                errors = payeer_functions.payout(pay_sys, requisite, amount, is_eng)
            text = errors
    else:
        users_db.close()

        text = message.reply_to_message.text[:message.reply_to_message.text.find('.') + 2]
        if amount == -1:
            text += "Invalid amount provided" if is_eng else "Введена неправильная сумма"
        else:
            text += "Amount should be greater than *{} USD*" if is_eng else "Сумма должна быть больше *{} USD*"
            text = text.format(config.MIN_WITHDRAW_USD)
        keyboard = telebot.types.ForceReply(selective=False)

    bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")
# </editor-fold>


# <editor-fold desc="BTC">
@bot.message_handler(func=
                     lambda message: message.reply_to_message is not None and message.reply_to_message.text[0] == "🅱")
def handle_withdraw_btc_entered(message):
    chat = message.chat
    try:
        amount = utils.to_satoshi(float(message.text.strip()))
    except ValueError:
        amount = -1

    users_db = Users_db(config.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    requisite = users_db.select_requisite(chat.id, 'bitcoin')
    users_db.close()

    keyboard = None
    if requisite is None:
        if is_eng:
            text = "Requisite is not provided. You can change it in settings"
        else:
            text = "Реквизит не указан. Вы можете изменить это в настройках"
    else:
        if amount >= config.MIN_WITHDRAW_BTC:
            text = coinbase_functions.send_money(requisite, amount, is_eng)
        else:
            if amount == -1:
                text = "Invalid amount provided" if is_eng else "Введена неправильная сумма"
            else:
                text = "Amount should be greater than *{} BTC*" if is_eng else "Сумма должна быть больше *{} BTC*"
                text = text.format(utils.to_bitcoin(config.MIN_WITHDRAW_BTC))
            keyboard = telebot.types.ForceReply(selective=False)

    bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")
# </editor-fold>
# </editor-fold>


if __name__ == '__main__':
    if not DEBUG:
        application.run(host=config.WEBHOOK_LISTEN, port=config.WEBHOOK_PORT)
    else:
        application.run(host=config.WEBHOOK_LISTEN, port=config.WEBHOOK_PORT,
                        ssl_context=('./SSL_certs/webhook_cert.pem', './SSL_certs/webhook_pkey.pem'), debug=True)
