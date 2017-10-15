import telebot
from config import TOKEN, DB_NAME, BOT_USERNAME
from generate_keyboards import get_keyboard, requisites_keyboard
from Data_base.user_db_class import Users_db
from random import randint, seed

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start_command(message):
    chat = message.chat
    if chat.type == "private":
        bot.send_message(chat.id, "Hello, {}! Please select your language:".format(chat.first_name),
                         reply_markup=get_keyboard("lang_keyboard"))
        users_db = Users_db(DB_NAME)
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

        # Handle inserting user's requisites
        if not users_db.is_exist_requisites(chat.id):
            users_db.insert_requisites(chat.id)
        users_db.close()
    else:
        bot.send_message(chat.id, "This bot can work only in private chats")
        bot.leave_chat(chat.id)


@bot.message_handler(func=lambda message: message.text == "🇺🇸 English" or message.text == "🇷🇺 Русский")
def handle_language(message):
    chat = message.chat
    is_eng = message.text == '🇺🇸 English'
    if is_eng:
        text = "You chose english language"
    else:
        text = "Вы выбрали русский язык"
    bot.send_message(chat.id, text, reply_markup=get_keyboard("main_keyboard", is_eng))

    users_db = Users_db(DB_NAME)
    users_db.update_stats_lang(chat.id, int(is_eng))
    users_db.close()


@bot.message_handler(func=lambda message: message.text == "📈 Statistics" or message.text == "📈 Статистика")
def handle_statistics(message):
    chat = message.chat
    users_db = Users_db(DB_NAME)
    user_stats = users_db.select_stats(chat.id)
    users_db.close()
    if user_stats[4]:
        text = "Your balance: *{:.2f} USD*\nSum of your investments: *{:.2f} USD*\nProfit from the project: " \
               "*{:.2f} USD*"
    else:
        text = "Ваш баланс: *{:.2f} USD*\nСумма ваших инвестиций: *{:.2f} USD*\nПрибыль от проэкта: *{:.2f} USD*"
    bot.send_message(chat.id, text.format(user_stats[1], user_stats[2], user_stats[3]),
                     reply_markup=get_keyboard("balance_keyboard", user_stats[4]), parse_mode="Markdown")


@bot.message_handler(
    func=lambda message: message.text == "👥 Referral program" or message.text == "👥 Реферальная программа")
def handle_ref_program(message):
    chat = message.chat
    users_db = Users_db(DB_NAME)
    is_eng = users_db.select_is_eng(chat.id)
    ref_program_info = users_db.select_ref_all(chat.id)
    users_db.close()
    if is_eng:
        text = "Earned total: *{:.2f} USD*\n\nEarned from 1st line: *{:.2f} USD*\nEarned from 2nd line: *{:.2f} USD*" \
               "\nEarned from 3rd line: *{:.2f} USD*\n\nYour id in Telegram: *{}*"
    else:
        text = "Заработано вообщем: *{:.2f} USD*\n\nЗаработано с 1-ой линии: *{:.2f} USD*\nЗаработано с 2-ой линии: " \
               "*{:.2f} USD*\nЗаработано с 3-ей линии: *{:.2f} USD*\n\nВаш id в Telegram: *{}*"
    ref_program_info = tuple(map(lambda line: 0.0 if line is None else line, ref_program_info))
    bot.send_message(chat.id, text.format(ref_program_info[2] + ref_program_info[3] + ref_program_info[4],
                                          ref_program_info[2], ref_program_info[3], ref_program_info[4], chat.id),
                     reply_markup=get_keyboard("ref_program_keyboard", is_eng), parse_mode="Markdown")


@bot.message_handler(func=lambda message: message.text == "📲 About the service" or message.text == "📲 О сервисе")
def handle_statistics(message):
    chat = message.chat
    users_db = Users_db(DB_NAME)
    is_eng = users_db.select_is_eng(chat.id)
    users_db.close()
    if is_eng:
        text = "Sample text"
    else:
        text = "Сампл текст"
    bot.send_message(chat.id, text)


@bot.message_handler(func=lambda message: message.text == "⚙️ Settings" or message.text == "⚙️ Настройки")
def handle_statistics(message):
    chat = message.chat
    users_db = Users_db(DB_NAME)
    is_eng = users_db.select_is_eng(chat.id)
    users_db.close()
    if is_eng:
        text = "What you want to change?"
    else:
        text = "Что вы хотите изменить?"
    bot.send_message(chat.id, text, reply_markup=get_keyboard("settings_keyboard", is_eng))


# Callbacks
@bot.callback_query_handler(func=lambda call: call.data == "🔗 Invitation link")
def handle_invitation_link(call):
    chat = call.message.chat
    users_db = Users_db(DB_NAME)
    is_eng = users_db.select_is_eng(chat.id)
    users_db.close()
    if is_eng:
        text = "Here is your invitation link:\n{}"
    else:
        text = "Ваша пригласительная ссылка:\n{}"

    users_db = Users_db(DB_NAME)
    salt = users_db.select_salt(chat.id)
    if salt is None:
        if not users_db.insert_salt(randint(1, 1000000000), chat.id):
            seed()
            users_db.insert_salt(randint(1, 1000000000), chat.id)
    else:
        salt = salt[0]
    users_db.close()
    invitation_link = "https://t.me/{}?start={}".format(BOT_USERNAME, salt)
    bot.send_message(chat.id, text.format(invitation_link))


@bot.callback_query_handler(func=lambda call: call.data == "💬 Language")
def handle_change_language(call):
    chat = call.message.chat
    bot.send_message(chat.id, "Choose language:", reply_markup=get_keyboard("lang_keyboard"))


@bot.callback_query_handler(func=lambda call: call.data == "💳 Payment requisites")
def handle_change_requisites(call):
    chat = call.message.chat
    users_db = Users_db(DB_NAME)
    is_eng = users_db.select_is_eng(chat.id)
    requisites = users_db.select_requisites(chat.id)
    users_db.close()

    if is_eng:
        requisites = tuple(map(lambda requisite: "Missing" if requisite is None else requisite, requisites))
        text = "*Your requisites:*"
    else:
        requisites = tuple(map(lambda requisite: "Отсутствует" if requisite is None else requisite, requisites))
        text = "*Ваши реквизиты:*"

    bot.send_message(chat.id, text, reply_markup=requisites_keyboard("requisites_keyboard", requisites[1:]),
                     parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "👤 Set an inviter")
def handle_change_inviter(call):
    chat = call.message.chat
    users_db = Users_db(DB_NAME)
    is_eng = users_db.select_is_eng(chat.id)

    inviter = users_db.select_ref_inviter(chat.id)
    if inviter is not None:
        if is_eng:
            text = "You already have inviter: *{}*"
        else:
            text = "У вас уже есть пригласитель: *{}*"
        bot.send_message(chat.id, text.format(inviter), parse_mode="Markdown")
        return

    users_db.close()

    # TODO make force reply for setting inviter


if __name__ == '__main__':
    from server_startup import start_server
    start_server(bot)
