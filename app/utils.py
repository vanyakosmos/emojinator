from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, User, Chat


def get_buttons_markup(original_message: Message, rates: dict):
    keys = []
    sorted_bs = sorted(rates.keys(), key=lambda x: rates[x]['pos'])
    for name in sorted_bs:
        text = name
        score = rates[name]['score']
        if score:
            text += f' {score}'
        keys.append(InlineKeyboardButton(text, callback_data=name))

    keyboard = []
    if original_message:
        keyboard.append(sign_buttons(original_message))

    max_cols = 3
    while keys:
        keyboard += [keys[:max_cols]]
        keys = keys[max_cols:]

    return InlineKeyboardMarkup(keyboard)


def sign_buttons(message: Message):
    buttons = []

    from_user = message.from_user
    forward_from: User = message.forward_from
    forward_from_chat: Chat = message.forward_from_chat

    # by user
    if from_user.username:
        from_user_button = InlineKeyboardButton('by ' + from_user.name, url='https://t.me/' + from_user.username)
    else:
        from_user_button = InlineKeyboardButton('by ' + from_user.name)
    buttons.append(from_user_button)

    # from source
    if forward_from and from_user.name != forward_from.name:
        if forward_from.username:
            button = InlineKeyboardButton(text='from ' + forward_from.username,
                                          url='https://t.me/' + forward_from.username)
            buttons.append(button)
        else:
            from_user_button.text += ', from ' + forward_from.name

    if forward_from_chat and forward_from_chat.username:
        username = forward_from_chat.username
        msg_id = message.forward_from_message_id

        button = InlineKeyboardButton(text='from ' + username,
                                      url=f'https://t.me/{username}/{msg_id}')
        buttons.append(button)

    return buttons
