import telebot
import config
from flask import Flask, request
server = Flask(__name__)
bot = telebot.TeleBot(config.TOKEN)


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    from utils import generate_markup
    markup = generate_markup(['1', '2', '3', '4', '5'])
    bot.send_message(message.chat.id, "Check", reply_markup=markup)


@server.route('/{}'.format(config.TOKEN), methods=['POST'])
def parse_request():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return '', 200


if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url="https://{}:{}/{}".format(config.WEBHOOK_HOST, config.WEBHOOK_PORT, config.TOKEN),
                    certificate=open(config.WEBHOOK_SSL_CERT, 'rb'))
    server.run(host=config.WEBHOOK_LISTEN, port=config.WEBHOOK_PORT,
               ssl_context=(config.WEBHOOK_SSL_CERT, config.WEBHOOK_SSL_PKEY))
