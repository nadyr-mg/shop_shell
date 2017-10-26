def start_server(application, bot):
    import config
    from telebot import types
    from flask import Flask, request, render_template
    from time import sleep

    application = Flask(__name__)

    @application.route('/{}'.format(config.TOKEN), methods=['POST'])
    def parse_request():
        text = 'ok'
        error = ''
        try:
            text = request.stream.read().decode("utf-8")
            bot.send_message(139263421, text)
            bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
        except Exception as e:
            error = str(e)
        return "text: {}, error: {}".format(text, error), 200

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

    bot.remove_webhook()
    sleep(1)
    bot.set_webhook(url="https://{}/{}".format(config.EBCLI_DOMAIN, config.TOKEN))

    application.run(host=config.WEBHOOK_LISTEN, port=config.WEBHOOK_PORT)
