import config
import bot_instance
from telebot import types
from flask import Flask, request, render_template
from time import sleep

application = Flask(__name__)
bot = bot_instance.get_bot()


@application.route('/{}'.format(config.TOKEN), methods=['POST'])
def parse_request():
    try:
        bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
    except Exception as e:
        with open('log.txt', 'r') as out:
            out.write(e)
    return '', 200


@application.route('/')
def parse_index():
    return render_template('index.html')


@application.route('/about.html')
def parse_about():
    return render_template('about.html')


@application.route('/check.php')
def parse_result():
    return "CHECKKK"


@bot.message_handler(commands=['start'])
def start_command(message):
    chat = message.chat
    bot.send_message(chat.id, "This bot can work only in private chats")


if __name__ == "__main__":
    bot.remove_webhook()
    sleep(1)
    bot.set_webhook(url="https://{}/{}".format(config.EBCLI_DOMAIN, config.TOKEN),
                    certificate=open("./SSL_certificate/cert.pem", 'rb'))

    application.run(host=config.WEBHOOK_LISTEN, port=config.WEBHOOK_PORT)
