from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

from bot.utils import msg_admin

READ_FEEDBACK = 10


def default_msg(update, context):
    update.effective_message.reply_text('Message must be text. Try again with /feedback')
    return ConversationHandler.END


def feedback(update, context):
    if not context.args:
        update.effective_message.reply_text(
            'Please tell me your bug 🐞 feature request 🌟 or suggestion 💭.\n'
            'Be sure to include all relevant details', quote=False
        )
        return READ_FEEDBACK
    suggestion = ' '.join(context.args)
    _send_feedback(update, context, suggestion)
    return ConversationHandler.END


def read_feedback(update, context):
    suggestion = update.effective_message.text
    _send_feedback(update, context, suggestion)
    return ConversationHandler.END


def _send_feedback(update, context, suggestion):
    user = update.effective_message.from_user
    msg_admin(context.bot, f'💬 Feedback!\n\n{suggestion}\n\nby {user.to_dict()}')
    update.effective_message.reply_text('✅ Feedback sent 🗳', quote=False)


add_feedback = ConversationHandler(
    entry_points=[CommandHandler('feedback', feedback)],
    states={
        READ_FEEDBACK: [MessageHandler(Filters.text, read_feedback)],
    },
    fallbacks=[MessageHandler(Filters.all, default_msg)],
    allow_reentry=True
)
