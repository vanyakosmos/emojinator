from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_buttons_markup(rates: dict):
    keys = []
    sorted_bs = sorted(rates.keys(), key=lambda x: rates[x]['pos'])
    for name in sorted_bs:
        text = name
        score = rates[name]['score']
        if score:
            text += f' {score}'
        keys.append(InlineKeyboardButton(text, callback_data=name))
    max_cols = 3
    keyboard = []
    while keys:
        keyboard += [keys[:max_cols]]
        keys = keys[max_cols:]
    return InlineKeyboardMarkup(keyboard)
