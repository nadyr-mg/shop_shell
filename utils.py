from telebot.types import ReplyKeyboardMarkup


def generate_markup(buttons):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    row = buttons[:2]
    markup.row(*row)
    for button in buttons[2:]:
        markup.add(str(button))
    return markup