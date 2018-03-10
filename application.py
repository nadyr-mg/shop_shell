import telebot
from flask import Flask, request, render_template

from random import randint, seed
from time import sleep, time
from urllib.parse import parse_qs
from json import loads
import schedule

import utils
from Data_base.user_db_class import Users_db
import project_variables
import payeer_functions
import coinbase_functions

DEBUG = False
ONE_DAY = 82800
MAX_REQUESTS_PER_TIME = 6
NULLIFY_AFTER = 10
REWARD_AMOUNT = 5

bot = telebot.TeleBot(project_variables.TOKEN)
application = Flask(__name__)
bot.remove_webhook()
sleep(1)
if not DEBUG:
    bot.set_webhook(url="https://{}/{}".format(project_variables.WEBHOOK_DOMAIN, project_variables.TOKEN))
else:
    bot.set_webhook(url="https://{}:{}/{}".format(project_variables.SERVER_IP, project_variables.WEBHOOK_PORT, project_variables.TOKEN),
                    certificate=open('./SSL_certs/webhook_cert.pem', 'rb'))


# <editor-fold desc="Server's handlers">
# <editor-fold desc="Main handlers">
@application.route('/{}'.format(project_variables.TOKEN), methods=['POST'])
def handle_request():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return '', 200


@application.route('/')
def handle_index():
    return render_template('index.html')
# </editor-fold>


# <editor-fold desc="Payeer handlers">
@application.route('/congrats.php')
def handle_success():
    return '<b style="color:#03C159;"> Оплата прошла успешно </b>'


@application.route('/failure.php')
def handle_fail():
    return '<b style="color:#C12503;"> В процессе оплаты произошла ошибка. Попробуйте еще раз </b>'


@application.route('/check.php', methods=['POST'])
def handle_status():
    post_data = parse_qs(request.stream.read().decode("utf-8"))
    result = utils.check_payment(request.remote_addr, post_data)
    if result == -1:
        responce = "Wrong data"
    else:
        users_db = Users_db(project_variables.DB_NAME)
        if result == 0:
            responce = post_data['m_orderid'][0] + '|error'
        else:
            responce = post_data['m_orderid'][0] + '|success'
            try:
                user_id, amount = users_db.select_repl_user_amount(post_data['m_orderid'][0])
            except TypeError:
                return responce
            utils.invested(users_db, user_id, amount)

            is_eng = users_db.select_stats_field(user_id, 'is_eng')
            text = "Successfully invested {} USD" if is_eng else "Успешно внесена сумма {} USD"
            try:
                bot.send_message(user_id, text.format(amount))
            except telebot.apihelper.ApiException:
                pass
        users_db.delete_repl_by_order(post_data['m_orderid'][0])
        users_db.close()
    return responce


@application.route('/payment/<order_id>')
def handle_payment(order_id):
    users_db = Users_db(project_variables.DB_NAME)
    amount = users_db.select_repl_amount(order_id)
    users_db.close()

    if amount is None:
        result = '<b style="color:#EE6060;"> Неправильный номер заказа </b>'
    else:
        amount = amount[0]
        desc, sign = utils.get_desc_sign(order_id, amount)
        result = render_template('make_payment.html', m_shop=project_variables.PAYEER_MERCHANT_ID, m_orderid=order_id,
                                 m_amount=amount, m_curr=project_variables.PAYEER_CURRENCY, m_desc=desc, m_sign=sign)

    return result


@application.route('/payeer_428636358.txt')
def handle_payeer_confirm():
    return project_variables.PAYEER_CONFIRM
# </editor-fold>


# <editor-fold desc="Coinbase handler">
@application.route('/check_btc.php', methods=['GET', 'POST'])
def handle_status_btc():
    body = request.get_data()
    if not coinbase_functions.check(body, request.environ):
        return "", 500

    body = loads(body)
    amount = utils.to_satoshi(float(body["additional_data"]["amount"]["amount"]))
    if amount < project_variables.MIN_REFILL_BTC:
        return "", 200

    address = body["data"]["address"]
    users_db = Users_db(project_variables.DB_NAME)
    user_id = users_db.select_addr_user(address)
    if user_id is None:
        return "", 500
    else:
        user_id = user_id[0]

    utils.invested(users_db, user_id, amount, is_btc=1)
    users_db.delete_addr_by_user(user_id)

    is_eng = users_db.select_stats_field(user_id, 'is_eng')
    text = "Successfully invested {:.8f} BTC" if is_eng else "Успешно внесено *{:.8f} BTC*"
    text.format(amount)
    users_db.close()

    try:
        bot.send_message(user_id, text.format(amount), parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass
    return "", 200
# </editor-fold>
# </editor-fold>


# <editor-fold desc="Schedule events">
def overcharge_and_clean_repl():
    users_db = Users_db(project_variables.DB_NAME)

    repls = users_db.select_repl_orders()
    for repl in repls:
        order, date = repl
        if int(time()) - date > ONE_DAY:
            users_db.delete_repl_by_order(order)

    users = users_db.select_stats_users()

    text_variants = ("Вам начислена сумма дохода:\n", "You are credited with the amount of income:\n")
    for user in users:
        user_id = user[0]
        income, income_btc = user[1], user[2]
        if income > 0.0 or income_btc > 0:
            is_eng = user[3]
            users_db.update_stats_add_income(user_id)

            text = text_variants[is_eng]
            if income > 0.0:
                text += "*{} USD* ".format(income)
            if income_btc > 0:
                text += "*{:.8f} BTC*".format(utils.to_bitcoin(income_btc))

            try:
                bot.send_message(user_id, text, parse_mode="Markdown")
            except telebot.apihelper.ApiException:
                pass
    users_db.close()


def nullify_spam_cnt():
    users_db = Users_db(project_variables.DB_NAME)
    users_db.nullify_spam()
    users_db.close()
# </editor-fold>


# <editor-fold desc="Standard commands">
@bot.message_handler(commands=['start'])
def start_command(message):
    chat = message.chat
    if chat.type == "private":
        try:
            bot.send_message(chat.id, "Hello, {}! Please select your language:".format(chat.first_name),
                             reply_markup=utils.get_keyboard("lang_keyboard"))
        except telebot.apihelper.ApiException:
            pass
        users_db = Users_db(project_variables.DB_NAME)
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

        # Handle inserting user's addresses
        if users_db.select_addr_address(chat.id) is None:
            users_db.insert_addr(chat.id)

        # Handle inserting user's spam cnt
        if users_db.select_spam_cnt(chat.id) is None:
            users_db.insert_spam_record(chat.id)

        # Handle reward
        make_reward(chat.id, REWARD_AMOUNT, users_db)

        users_db.close()
    else:
        try:
            bot.send_message(chat.id, "This bot can work only in private chats")
        except telebot.apihelper.ApiException:
            pass
        bot.leave_chat(chat.id)


@bot.message_handler(commands=['menu'])
def menu_command(message):
    chat = message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    try:
        bot.send_message(chat.id, "...", reply_markup=utils.get_keyboard("main_keyboard", is_eng))
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(commands=['schedule'])
def schedule_command(message):
    if message.chat.id != project_variables.HOST_ID:
        return

    command = message.text.split()

    if len(command) == 2:
        command = command[1].lower()

    if command == 'start':
        if utils.schedule_thread is None:
            schedule.every().day.at("01:00").do(overcharge_and_clean_repl)
            schedule.every(NULLIFY_AFTER).minutes.do(nullify_spam_cnt)
            utils.init_schedule(schedule.run_continuously())

        text = "Scheduler is running"
    elif command == 'stop':
        utils.stop_schedule_thread()
        schedule.clear()
        text = "Scheduler is stopped"
    else:
        text = "Wrong command"
    try:
        bot.send_message(project_variables.HOST_ID, text)
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(commands=['balance'])
def balance_command(message):
    if message.chat.id != project_variables.HOST_ID:
        return

    try:
        bot.send_message(project_variables.HOST_ID, "{:.8f}".format(utils.to_bitcoin(coinbase_functions.get_balance())))
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(commands=['reward'])
def reward_command(message):
    if message.chat.id != project_variables.HOST_ID:
        return

    args = message.text.split()
    if len(args) != 2:
        try:
            bot.send_message(message.chat.id, "Wrong command")
        except telebot.apihelper.ApiException:
            pass
    else:
        users_db = Users_db(project_variables.DB_NAME)
        amount = float(args[1])
        users = users_db.select_stats_users_id()
        for user in users:
            user_id = user[0]
            make_reward(user_id, amount, users_db)
        try:
            bot.send_message(message.chat.id, "Rewarded users")
        except telebot.apihelper.ApiException:
            pass
        users_db.close()


@bot.message_handler(commands=['rewardone'])
def reward_one(message):
    if message.chat.id not in project_variables.TRUSTED_IDs:
        return

    args = message.text.split()
    if len(args) != 3:
        try:
            bot.send_message(message.chat.id, "Wrong command")
        except telebot.apihelper.ApiException:
            pass
    else:
        users_db = Users_db(project_variables.DB_NAME)
        user_id = args[1]
        amount = float(args[2])
        make_reward(user_id, amount, users_db, with_check=0)
        try:
            bot.send_message(message.chat.id, "Rewarded user")
        except telebot.apihelper.ApiException:
            pass
        users_db.close()


def make_reward(user_id, amount, users_db, with_check=1):
    if with_check and users_db.select_reward(user_id) is not None:
        return

    is_eng = users_db.select_stats_field(user_id, 'is_eng')
    utils.invested(users_db, user_id, amount, make_lift=0)
    if with_check:
        users_db.insert_reward(user_id)

    text = "You were rewarded with amount *{} USD*" if is_eng else "Вы были вознаграждены суммой в *{} USD*"
    text = text.format(amount)

    try:
        bot.send_message(user_id, text, parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(commands=['notify'])
def notify_all(message):
    if message.chat.id != project_variables.HOST_ID:
        return

    notify_message = message.text[message.text.find(" ") + 1:]

    users_db = Users_db(project_variables.DB_NAME)
    users = users_db.select_stats_users_id()
    for user in users:
        user_id = user[0]
        try:
            bot.send_message(user_id, notify_message)
        except telebot.apihelper.ApiException:
            pass
    try:
        bot.send_message(project_variables.HOST_ID, "Notified users")
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(commands=['charge'])
def overcharge_manual(message):
    if message.chat.id != project_variables.HOST_ID:
        return

    if message.text.split()[-1] == "ok":
        overcharge_and_clean_repl()
        try:
            bot.send_message(project_variables.HOST_ID, "Overcharged")
        except telebot.apihelper.ApiException:
            pass


@bot.message_handler(commands=['calcincome'])
def calcincome(message):
    if message.chat.id != project_variables.HOST_ID:
        return

    if message.text.split()[-1] == "ok":
        users_db = Users_db(project_variables.DB_NAME)
        users = users_db.select_stats_users_id()
        for user in users:
            user_id = user[0]
            utils.calc_income(users_db, user_id)
        users_db.close()
    try:
        bot.send_message(project_variables.HOST_ID, "ReCalced")
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(commands=['get_table'])
def get_table(message):
    if message.chat.id not in project_variables.TRUSTED_IDs:
        return

    args = message.text.split()
    if len(args) != 2:
        try:
            bot.send_message(message.chat.id, "Wrong command")
        except telebot.apihelper.ApiException:
            pass
    else:
        table = args[1]
        users_db = Users_db(project_variables.DB_NAME)
        tables_commands = {
            'Addresses': users_db.select_addr_all,
            'Ref_program': users_db.select_ref_all_all,
            'Replenishments': users_db.select_repl_all,
            'Requisites': users_db.select_requisites_all,
            'Rewards': users_db.select_reward_all,
            'Salts': users_db.select_salts_all,
            'Statistics': users_db.select_stats_all
        }

        if table not in tables_commands:
            try:
                bot.send_message(message.chat.id, "Wrong table")
            except telebot.apihelper.ApiException:
                pass
            return

        data = tables_commands[table]()
        users_db.close()

        text = ""
        for ind, element in enumerate(data):
            text += "#" + str(ind + 1) + ". "
            text += " ".join(map(str, element))
            text += '\n'

            if len(text) > 4000:
                try:
                    bot.send_message(message.chat.id, text)
                except telebot.apihelper.ApiException:
                    pass
                text = ""

        try:
            bot.send_message(message.chat.id, text)
        except telebot.apihelper.ApiException:
            pass
# </editor-fold>


# <editor-fold desc="Reply markup handlers">
@bot.message_handler(func=lambda message: message.text == "🇺🇸 English" or message.text == "🇷🇺 Русский")
def handle_language(message):
    chat = message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = message.text == '🇺🇸 English'

    if users_db.select_spam_cnt(chat.id)[0] > MAX_REQUESTS_PER_TIME:
        if is_eng:
            text = "You are sending messages too quickly. You can change language after {} minutes"
        else:
            text = "Вы посылаете сообщения слишком быстро. Вы сможете изменить язык после {} минут"
        text = text.format(NULLIFY_AFTER)
    else:
        users_db.update_spam_cnt(chat.id)
        if is_eng:
            text = "You chose english language"
        else:
            text = "Вы выбрали русский язык"
        users_db.update_stats_field(chat.id, 'is_eng', int(is_eng))
    users_db.close()

    try:
        bot.send_message(chat.id, text, reply_markup=utils.get_keyboard("main_keyboard", is_eng))
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(func=lambda message: message.text == "📈 Statistics" or message.text == "📈 Статистика")
def handle_statistics(message):
    chat = message.chat
    users_db = Users_db(project_variables.DB_NAME)
    user_stats = users_db.select_stats(chat.id)
    users_db.close()

    is_eng = user_stats[7]
    if is_eng:
        text = "Your balance: *{:.2f} USD*\nYour balance: *{:.8f} BTC*\n\nSum of your investments: *{:.2f} USD*\nSum " \
               "of your investments: *{:.8f} BTC*\n\nIncome from the project: *{:.2f} USD*\nIncome from the project: " \
               "*{:.8f} BTC* "
    else:
        text = "Ваш баланс: *{:.2f} USD*\nВаш баланс: *{:.8f} BTC*\n\nСумма ваших инвестиций: *{:.2f} USD*\nСумма " \
               "ваших инвестиций: *{:.8f} BTC*\n\nДоход от проекта: *{:.2f} USD*\nДоход от проекта: *{:.8f} BTC* "
    try:
        bot.send_message(chat.id, text.format(user_stats[1], utils.to_bitcoin(user_stats[2]), user_stats[3],
                                              utils.to_bitcoin(user_stats[4]), user_stats[5],
                                              utils.to_bitcoin(user_stats[6])),
                         reply_markup=utils.get_keyboard("balance_keyboard", user_stats[7]), parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(
    func=lambda message: message.text == "👥 Referral program" or message.text == "👥 Реферальная программа")
def handle_ref_program(message):
    chat = message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    ref_program_info = users_db.select_ref_all(chat.id)
    users_db.close()
    if is_eng:
        text = "Earned total: *{:.2f} USD*\nEarned total: *{:.8f} BTC*\n\nInvited in 1st line: *{}*\nInvited in 2nd " \
               "line: *{}*\nInvited in 3rd line: *{}*\n\nEarned from 1st line: *{:.2f} USD*\nEarned from 1st line: *{" \
               ":.8f} BTC*\n\nEarned from 2nd line: *{:.2f} USD*\nEarned from 2nd line: *{:.8f} BTC*\n\nEarned from " \
               "3rd line: *{:.2f} USD*\nEarned from 3rd line: *{:.8f} BTC*\n\nYour id in Telegram: *{}* "
    else:
        text = "Прибыль вообщем: *{:.2f} USD*\nПрибыль вообщем: *{:.8f} BTC*\n\nПриглашенных в 1-ой линии: *{" \
               "}*\nПриглашенных во 2-ой линии: *{}*\nПриглашенных в 3-ей линии: *{}*\n\nПрибыль с 1-ой линии: *{" \
               ":.2f} USD*\nПрибыль с 1-ой линии: *{:.8f} BTC*\n\nПрибыль со 2-ой линии: *{:.2f} " \
               "USD*\nПрибыль со 2-ой линии: *{:.8f} BTC*\n\nПрибыль с 3-ей линии: *{:.2f} USD*\nПрибыль с " \
               "3-ей линии: *{:.8f} BTC*\n\nВаш id в Telegram: *{}*"
    ref_program_info = tuple(map(lambda line: 0 if line is None else line, ref_program_info))
    try:
        bot.send_message(chat.id, text.format(ref_program_info[2] + ref_program_info[4] + ref_program_info[6],
                                              utils.to_bitcoin(
                                                  ref_program_info[3] + ref_program_info[5] + ref_program_info[7]),
                                              ref_program_info[8],
                                              ref_program_info[9], ref_program_info[10], ref_program_info[2],
                                              utils.to_bitcoin(ref_program_info[3]),
                                              ref_program_info[4], utils.to_bitcoin(ref_program_info[5]),
                                              ref_program_info[6],
                                              utils.to_bitcoin(ref_program_info[7]), chat.id),
                         reply_markup=utils.get_keyboard("ref_program_keyboard", is_eng), parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(func=lambda message: message.text == "📲 About the service" or message.text == "📲 О сервисе")
def handle_about(message):
    chat = message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()

    text = project_variables.ABOUT_TEXT[is_eng]
    try:
        bot.send_message(chat.id, text)
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(func=lambda message: message.text == "⚙ Settings" or message.text == "⚙ Настройки")
def handle_settings(message):
    chat = message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "What you want to change?"
    else:
        text = "Что вы хотите изменить?"
    try:
        bot.send_message(chat.id, text, reply_markup=utils.get_keyboard("settings_keyboard", is_eng))
    except telebot.apihelper.ApiException:
        pass
# </editor-fold>


# <editor-fold desc="Handlers with callbacks. First level">
@bot.callback_query_handler(func=lambda call: call.data == "🔗 Invitation link")
def handle_invitation_link(call):
    chat = call.message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "Here is your invitation link:\n{}"
    else:
        text = "Ваша пригласительная ссылка:\n{}"

    users_db = Users_db(project_variables.DB_NAME)
    salt = users_db.select_salt(chat.id)
    if salt is None:
        if not users_db.insert_salt(randint(1, 1000000000), chat.id):
            seed()
            users_db.insert_salt(randint(1, 1000000000), chat.id)
    else:
        salt = salt[0]
    users_db.close()
    invitation_link = "https://t.me/{}?start={}".format(project_variables.BOT_USERNAME, salt)
    try:
        bot.send_message(chat.id, text.format(invitation_link))
    except telebot.apihelper.ApiException:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "💬 Language")
def handle_change_language(call):
    chat = call.message.chat
    try:
        bot.send_message(chat.id, "Choose language:", reply_markup=utils.get_keyboard("lang_keyboard"))
    except telebot.apihelper.ApiException:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "💳 Payment requisites")
def handle_change_requisites(call):
    chat = call.message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    requisites = users_db.select_requisites(chat.id)
    users_db.close()

    if is_eng:
        requisites = tuple(map(lambda requisite: "Missing" if requisite is None else requisite, requisites))
        text = "*Your requisites:*"
    else:
        requisites = tuple(map(lambda requisite: "Отсутствует" if requisite is None else requisite, requisites))
        text = "*Ваши реквизиты:*"

    try:
        bot.send_message(chat.id, text, reply_markup=utils.requisites_keyboard("requisites_keyboard", requisites[1:]),
                         parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "💳 Requisites examples")
def handle_requisites(call):
    chat = call.message.chat
    text = "*AdvCash:* advcash@gmail.com\n*Payeer:* P1000000\n*Bitcoin:* 13C3fxYMZzbt9HsTvCni779gqXyPadGtTQ\n*Qiwi:* " \
           "+7953155XXXX\n*Yandex Money:* 410011499718000 "
    try:
        bot.send_message(chat.id, text, parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "🔄 Reinvest")
def handle_change_reinvest(call):
    chat = call.message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    balance = users_db.select_stats_field(chat.id, 'balance')
    balance_btc = users_db.select_stats_field(chat.id, 'balance_btc')

    if balance > 0:
        users_db.update_stats_nullify_balance(chat.id)
        utils.invested(users_db, chat.id, balance, make_lift=0)
    if balance_btc > 0:
        users_db.update_stats_nullify_balance_btc(chat.id)
        utils.invested(users_db, chat.id, balance_btc, is_btc=1, make_lift=0)
    if is_eng:
        text = "Successfully reinvested"
    else:
        text = "Реинвестирование прошло успешно"
    users_db.close()

    try:
        bot.send_message(chat.id, text, reply_markup=utils.get_keyboard("main_keyboard", is_eng), parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass
# </editor-fold>


# <editor-fold desc="Setting an inviter interaction">
@bot.callback_query_handler(func=lambda call: call.data == "👤 Set an inviter")
def handle_change_inviter(call):
    chat = call.message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')

    inviter = users_db.select_ref_inviter(chat.id)
    if inviter is not None:
        if is_eng:
            text = "You already have inviter: *{}*"
        else:
            text = "У вас уже есть пригласитель: *{}*"
        try:
            bot.send_message(chat.id, text.format(inviter), parse_mode="Markdown")
        except telebot.apihelper.ApiException:
            pass
        return
    users_db.close()

    if is_eng:
        text = "👤 Select your inviter. Type in his id:"
    else:
        text = "👤 Выберете пригласителя. Введите его id:"
    force_reply = telebot.types.ForceReply(selective=False)
    try:
        bot.send_message(chat.id, text, reply_markup=force_reply)
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(func=
                     lambda message: message.reply_to_message is not None and message.reply_to_message.text[
                                                                                  0] == "👤")
def handle_reply_inviter(message):
    chat = message.chat
    users_db = Users_db(project_variables.DB_NAME)
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

    try:
        bot.send_message(chat.id, text)
    except telebot.apihelper.ApiException:
        pass
# </editor-fold>


# <editor-fold desc="Saving requisite info interaction">
@bot.callback_query_handler(
    func=lambda call: call.data in ("AdvCash", "Payeer", "Bitcoin", "Qiwi", "Yandex Money"))
def handle_requisites(call):
    chat = call.message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "💳 {} chosen. Type in your requisite:"
    else:
        text = "💳 {} выбран. Укажите ваш реквизит:"

    force_reply = telebot.types.ForceReply(selective=False)
    try:
        bot.send_message(chat.id, text.format(call.data), reply_markup=force_reply)
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(func=
                     lambda message: message.reply_to_message is not None and message.reply_to_message.text[0] == "💳")
def handle_reply_requisite(message):
    chat = message.chat
    pay_method = message.reply_to_message.text.split()[1]
    requisite = ''.join(message.text.split())

    users_db = Users_db(project_variables.DB_NAME)
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

    try:
        bot.send_message(chat.id, text.format(requisite), reply_markup=utils.get_keyboard("main_keyboard", is_eng),
                         parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass
# </editor-fold>


# <editor-fold desc="Refill interaction">
@bot.callback_query_handler(func=lambda call: call.data == "💵 Refill")
def handle_refill(call):
    chat = call.message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "Choose currency:"
    else:
        text = "Выберете валюту:"

    try:
        bot.send_message(chat.id, text, reply_markup=utils.get_keyboard("currency_keyboard"))
    except telebot.apihelper.ApiException:
        pass


# <editor-fold desc="USD">
@bot.callback_query_handler(func=lambda call: call.data == "USD")
def handle_refill_usd(call):
    chat = call.message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "🔢 Type in desired amount:\n*Minimal amount is {} USD*"
    else:
        text = "🔢 Введите желаемую сумму:\n*Минимальная сумма: {} USD*"

    force_reply = telebot.types.ForceReply(selective=False)
    try:
        bot.send_message(chat.id, text.format(project_variables.MIN_REFILL_USD), reply_markup=force_reply, parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(func=
                     lambda message: message.reply_to_message is not None and message.reply_to_message.text[0] == "🔢")
def handle_refill_usd_entered(message):
    chat = message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    keyboard = None

    if users_db.select_spam_cnt(chat.id, False)[0] > MAX_REQUESTS_PER_TIME:
        if is_eng:
            text = "You are sending messages too quickly. You can create order after {} minutes"
        else:
            text = "Вы посылаете сообщения слишком быстро. Вы сможете создать заказ после {} минут"
        text = text.format(NULLIFY_AFTER)
    else:
        users_db.update_spam_cnt(chat.id, False)

        try:
            amount = round(float(message.text.strip()), 2)
        except ValueError:
            amount = -1

        if amount >= project_variables.MIN_REFILL_USD:
            text = "Follow the link to make payment:" if is_eng else "Перейдите по ссылке для оплаты:"
            btn_text = "Link for payment:" if is_eng else "Ссылка на оплату:"

            order_id = utils.gen_salt()
            users_db.insert_repl_order(order_id, amount, chat.id)
            users_db.close()

            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(telebot.types.InlineKeyboardButton(text=btn_text, url="https://{}/payment/{}".format(
                project_variables.WEBHOOK_DOMAIN, order_id)))
        else:
            users_db.close()
            if amount == -1:
                text = "🔢 Invalid amount provided" if is_eng else "🔢 Введена неправильная сумма"
            else:
                text = "🔢 Amount should be greater than *{} USD*" if is_eng else "🔢 Сумма должна быть больше *{} USD*"
                text = text.format(project_variables.MIN_REFILL_USD)
            keyboard = telebot.types.ForceReply(selective=False)

    try:
        bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass
# </editor-fold>


# <editor-fold desc="BTC">
@bot.callback_query_handler(func=lambda call: call.data == "BTC")
def handle_refill_btc(call):
    chat = call.message.chat
    users_db = Users_db(project_variables.DB_NAME)
    address = users_db.select_addr_address(chat.id)[0]
    if address is None:
        address = coinbase_functions.generate_address()
        users_db.update_addr_by_user(chat.id, address)

    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    users_db.close()
    if is_eng:
        text = "*Minimal amount is {:.8f} BTC*\nYou can send desired amount of BTC and the bot will automatically" \
               " charge them to your deposit.\nSend only one transaction to this address:\n`{}`\nNote that BTC " \
               "transfers are not instant"
    else:
        text = "*Минимальная сумма: {:.8f} BTC*\nВы можете отправить желаемую сумму BTC и бот автоматически занесет её " \
               "в ваш депозит.\nОтправляйте только одну транзакцию на этот адрес:\n`{}`\nОбратите внимание, что" \
               " переводы BTC осуществляются не моментально."

    try:
        bot.send_message(chat.id, text.format(utils.to_bitcoin(project_variables.MIN_REFILL_BTC), address), parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass
# </editor-fold>
# </editor-fold>


# <editor-fold desc="Withdraw interaction">
@bot.callback_query_handler(func=lambda call: call.data == "💸 Withdraw")
def handle_withdraw(call):
    chat = call.message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    balance = users_db.select_stats_field(chat.id, 'balance')
    balance_btc = users_db.select_stats_field(chat.id, 'balance_btc')
    users_db.close()

    keyboard = None
    if balance < project_variables.MIN_WITHDRAW_USD and balance_btc < project_variables.MIN_WITHDRAW_BTC:
        if is_eng:
            text = "You don't have enough money to withdraw\nMinimum is *{} USD* or *{:.8f} BTC*"
        else:
            text = "У вас нехватает средств для вывода\nМинимальная сумма: *{} USD* or *{:.8f} BTC*"
        text = text.format(project_variables.MIN_WITHDRAW_USD, utils.to_bitcoin(project_variables.MIN_WITHDRAW_BTC))
    else:
        if is_eng:
            text = "Choose currency:"
        else:
            text = "Выберете валюту:"
        keyboard = utils.get_keyboard("withdraw_currency")

    try:
        bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass


@bot.callback_query_handler(func=lambda call: call.data in ("💸 USD", "💸 BTC"))
def handle_withdraw_currency(call):
    chat = call.message.chat
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')

    keyboard = None
    if call.data == "💸 BTC":
        balance_btc = users_db.select_stats_field(chat.id, 'balance_btc')
        users_db.close()
        if balance_btc < project_variables.MIN_WITHDRAW_BTC:
            if is_eng:
                text = "You don't have enough money to withdraw\nMinimum is *{:.8f} BTC*"
            else:
                text = "У вас нехватает средств для вывода\nМинимальная сумма: *{:.8f} BTC*"
            text = text.format(utils.to_bitcoin(project_variables.MIN_WITHDRAW_BTC))
        else:
            if is_eng:
                text = "🅱 Type in desired amount:\nMinimum is *{:.8f} BTC*\nCurrent bitcoin fee is *{:.8f} BTC*"
            else:
                text = "🅱 Укажите желаемую сумму\nМинимальная сумма: *{:.8f} BTC*\nТекущая коммисия, при отправке " \
                       "bitcoin: *{:.8f} BTC*"
            cur_fee = coinbase_functions.get_cur_fee()
            text = text.format(utils.to_bitcoin(project_variables.MIN_WITHDRAW_BTC), utils.to_bitcoin(cur_fee))

            keyboard = telebot.types.ForceReply(selective=False)
    else:
        balance = users_db.select_stats_field(chat.id, 'balance')
        users_db.close()
        if balance < project_variables.MIN_WITHDRAW_USD:
            if is_eng:
                text = "You don't have enough money to withdraw\nMinimum is *{} USD*"
            else:
                text = "У вас нехватает средств для вывода\nМинимальная сумма: *{} USD*"
            text = text.format(project_variables.MIN_WITHDRAW_USD)
        else:
            text = "Choose payment system:" if is_eng else "Выберете платежную систему:"
            keyboard = utils.get_keyboard("pay_sys_keyboard")

    try:
        bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass


# <editor-fold desc="USD">
@bot.callback_query_handler(
    func=lambda call: call.data[0] == '💸' and call.data in ("💸 AdvCash", "💸 Payeer", "💸 Qiwi", "💸 Yandex Money"))
def handle_pay_sys(call):
    chat = call.message.chat
    users_db = Users_db(project_variables.DB_NAME)
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
        text = text.format(call.data[2:], project_variables.MIN_WITHDRAW_USD)
        keyboard = telebot.types.ForceReply(selective=False)
    else:
        if is_eng:
            text = "Requisite is not provided. You can change it in settings"
        else:
            text = "Реквизит не указан. Вы можете изменить это в настройках"

    try:
        bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass


@bot.message_handler(func=
                     lambda message: message.reply_to_message is not None and message.reply_to_message.text[0] == "💲")
def handle_withdraw_pay_sys_entered(message):
    chat = message.chat
    try:
        amount = round(float(message.text.strip()), 2)
    except ValueError:
        amount = -1
    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    balance = users_db.select_stats_field(chat.id, 'balance')

    keyboard = None
    if amount > balance:
        users_db.close()

        text = message.reply_to_message.text[:message.reply_to_message.text.find('.') + 2]
        text += "You don't have enough money to withdraw" if is_eng else "Нехватает средств для вывода"
        keyboard = telebot.types.ForceReply(selective=False)
    elif amount >= project_variables.MIN_WITHDRAW_USD:
        pay_sys = message.reply_to_message.text[2: message.reply_to_message.text.find(' ', 2)]
        requisite = users_db.select_requisite(chat.id, pay_sys.lower())

        if requisite is None:
            if is_eng:
                text = "Requisite is not provided. You can change it in settings"
            else:
                text = "Реквизит не указан. Вы можете изменить это в настройках"
        else:
            errors = payeer_functions.payout_possibility(pay_sys, requisite, amount, is_eng)
            if errors == "":
                errors = payeer_functions.payout(pay_sys, requisite, amount, is_eng)
            if errors == "Withdraw completed successfully!" or errors == "Вывод завершен успешно!":
                users_db.update_stats_dec_balance(chat.id, amount)
            text = errors
        users_db.close()
    else:
        users_db.close()

        text = message.reply_to_message.text[:message.reply_to_message.text.find('.') + 2]
        if amount == -1:
            text += "Invalid amount provided" if is_eng else "Введена неправильная сумма"
        else:
            text += "Amount should be greater than *{} USD*" if is_eng else "Сумма должна быть больше *{} USD*"
            text = text.format(project_variables.MIN_WITHDRAW_USD)
        keyboard = telebot.types.ForceReply(selective=False)

    try:
        bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass
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

    users_db = Users_db(project_variables.DB_NAME)
    is_eng = users_db.select_stats_field(chat.id, 'is_eng')
    requisite = users_db.select_requisite(chat.id, 'bitcoin')
    balance_btc = users_db.select_stats_field(chat.id, 'balance_btc')
    users_db.close()

    keyboard = None
    if requisite is None:
        if is_eng:
            text = "Requisite is not provided. You can change it in settings"
        else:
            text = "Реквизит не указан. Вы можете изменить это в настройках"
    else:
        if amount > balance_btc:
            text = "🅱 You don't have enough money to withdraw" if is_eng else "🅱 Нехватает средств для вывода"
            keyboard = telebot.types.ForceReply(selective=False)
        elif amount >= project_variables.MIN_WITHDRAW_BTC:
            text = coinbase_functions.send_money(requisite, amount, is_eng)
            if (len(text) == 23 or len(text) == 23) and text[-1] == '!':
                users_db.update_stats_dec_balance(chat.id, amount, is_btc=1)
        else:
            if amount == -1:
                text = "🅱 Invalid amount provided" if is_eng else "🅱 Введена неправильная сумма"
            else:
                text = "🅱 Amount should be greater than *{:.8f} BTC*" if is_eng else "🅱 Сумма должна быть больше *{" \
                                                                                      ":.8f} BTC* "
                text = text.format(utils.to_bitcoin(project_variables.MIN_WITHDRAW_BTC))
            keyboard = telebot.types.ForceReply(selective=False)

    try:
        bot.send_message(chat.id, text, reply_markup=keyboard, parse_mode="Markdown")
    except telebot.apihelper.ApiException:
        pass
# </editor-fold>
# </editor-fold>


if __name__ == '__main__':
    if not DEBUG:
        application.run(host=project_variables.WEBHOOK_LISTEN, port=project_variables.WEBHOOK_PORT)
    else:
        application.run(host=project_variables.WEBHOOK_LISTEN, port=project_variables.WEBHOOK_PORT,
                        ssl_context=('./SSL_certs/webhook_cert.pem', './SSL_certs/webhook_pkey.pem'), debug=True)
