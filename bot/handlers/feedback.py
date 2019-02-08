from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

from bot.utils import msg_admin

READ_FEEDBACK = 10


def default_msg(bot, update):
    update.effective_message.reply_text('Message must be text. Try again with /feedback')
    return ConversationHandler.END


def feedback(bot, update, args):
    if not args:
        update.effective_message.reply_text(
            'Please tell me your bug 🐞 feature request 🌟 or suggestion 💭.\n'
            'Be sure to include all relevant details', quote=False
        )
        return READ_FEEDBACK
    suggestion = ' '.join(args)
    _send_feedback(bot, update, suggestion)
    return ConversationHandler.END


def read_feedback(bot, update):
    suggestion = update.effective_message.text
    _send_feedback(bot, update, suggestion)
    return ConversationHandler.END


def _send_feedback(bot, update, suggestion):
    user = update.effective_message.from_user
    msg_admin(bot, f'💬 Feedback!\n\n{suggestion}\n\nby {user.to_dict()}')
    update.effective_message.reply_text('✅ Feedback sent 🗳', quote=False)


add_feedback = ConversationHandler(
    entry_points=[CommandHandler('feedback', feedback, pass_args=True)],
    states={
        READ_FEEDBACK: [MessageHandler(Filters.text, read_feedback)],
    },
    fallbacks=[MessageHandler(Filters.all, default_msg)],
    allow_reentry=True
)
