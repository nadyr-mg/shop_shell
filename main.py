import telebot
from config import TOKEN, DB_NAME
from generate_keyboards import get_keyboard
from Data_base.user_db_class import Users_db

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start_command(message):
    chat = message.chat
    if chat.type == "private":
        bot.send_message(chat.id, "Hello, {}! Please select your language:".format(chat.first_name),
                         reply_markup=get_keyboard("lang_keyboard"))

        users_db = Users_db(DB_NAME)
        if not users_db.is_exist_stats(chat.id):
            data = (chat.id, 0.0, 0.0, 0.0, 1)
            users_db.insert_stats(data)
            users_db.insert_ref(chat.id)
        print(users_db.select_stats(chat.id))
        print(users_db.select_ref_all(chat.id))
        users_db.close()
    else:
        bot.send_message(chat.id, "This bot can work only in private chats")


# @bot.callback_query_handler(func=lambda call: True)
# def callback_inline(call):
#     if call.data == "Refill":
#         bot.send_message(chat_id=call.message.chat.id, text="U chose refill")
#     else:
#         bot.send_message(chat_id=call.message.chat.id, text="U chose Withdraw")


if __name__ == '__main__':
    from server_startup import start_server
    start_server(bot)
