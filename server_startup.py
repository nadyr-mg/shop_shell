def start_server(bot):
    import config
    from telebot import types
    from flask import Flask, request
    server = Flask(__name__)

    @server.route('/{}'.format(config.TOKEN), methods=['POST'])
    def parse_request():
        bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
        return '', 200

    bot.remove_webhook()
    from time import sleep
    sleep(1)
    bot.set_webhook(url="https://{}:{}/{}".format(config.WEBHOOK_HOST, config.WEBHOOK_PORT, config.TOKEN),
                    certificate=open(config.WEBHOOK_SSL_CERT, 'rb'))
    server.run(host=config.WEBHOOK_LISTEN, port=config.WEBHOOK_PORT,
               ssl_context=(config.WEBHOOK_SSL_CERT, config.WEBHOOK_SSL_PKEY), debug=True)
