import telebot

from config import TOKEN

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    from generate_keyboards import get_keyboard
    bot.send_message(message.chat.id, "Привет!", reply_markup=get_keyboard("settings_keyboard", 1))


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "Refill":
        bot.send_message(chat_id=call.message.chat.id, text="U chose refill")
    else:
        bot.send_message(chat_id=call.message.chat.id, text="U chose Withdraw")


if __name__ == '__main__':
    from server_startup import start_server
    start_server(bot)
