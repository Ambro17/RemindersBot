from telegram import InlineKeyboardMarkup, InlineKeyboardButton as Button


def time_options_keyboard():
    MINUTE = 60
    HOUR = 60 * MINUTE
    buttons = [
        [
            Button('5 Mins', callback_data=5 * MINUTE),
            Button('10 Mins', callback_data=10 * MINUTE),
            Button('20 Mins', callback_data=20 * MINUTE),
            Button('30 Mins', callback_data=30 * MINUTE),
        ],
        [
            Button('1 Hour', callback_data=HOUR),
            Button('2 Hours', callback_data=2 * HOUR),
            Button('4 Hours', callback_data=4 * HOUR),
            Button('8 Hours', callback_data=8 * HOUR),
        ],
        [
            Button('12 Hours', callback_data=12 * HOUR),
            Button('16 Hours', callback_data=16 * HOUR),
            Button('24 Hours', callback_data=24 * HOUR),
            Button('48 Hours', callback_data=48 * HOUR),
        ],
        [
            Button('Custom 📝', callback_data=-1)
        ]
    ]

    return InlineKeyboardMarkup(buttons)


DONE = 'Done'
REMIND_AGAIN = 'Remind again'
def done_or_repeat_reminder():
    buttons = [
        [
            Button('✅ Done', callback_data=DONE),
            Button('🔄 Remind again', callback_data=REMIND_AGAIN),
        ]
    ]
    return InlineKeyboardMarkup(buttons)
