from telegram.ext import CommandHandler

events_set = CommandHandler('event', lambda b, u: u.message.reply_text('Proximamente..'))
