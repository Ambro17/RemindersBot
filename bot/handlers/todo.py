from telegram.ext import CommandHandler

from bot.jobs.models import Session, Todo


def add_todo(update, context):
    todo_text = context.args
    if not todo_text:
        msg = 'Usage: `/todo something`'
    else:
        try:
            todo = ' '.join(todo_text)
            session = Session()
            session.add(Todo(text=todo))
            session.commit()
            msg = '✅ Saved'
        except Exception as e:
            msg = f'Error: {repr(e)}'

    update.message.reply_markdown(msg)


def show_todos(update, context):
    text = context.args
    session = Session()

    include_done_tasks = '--all' in ' '.join(text)
    todos = session.query(Todo).filter_by(done=include_done_tasks).all()
    if not todos:
        msg = 'No pending todos'
    else:
        msg = '\n'.join(f"{todo.id}: {todo.text}" for todo in todos)

    update.message.reply_text(msg)


def mark_as_done(update, context):
    todo = context.args
    if not todo:
        update.message.reply_text('Missing todo id')
        return
    try:
        todo_id = int(todo[0])
    except ValueError:
        update.message.reply_text('Todo id must be a digit')
        return

    s = Session()
    todo = s.query(Todo).filter_by(id=todo_id, done=False).first()
    if todo is None:
        msg = f'🚫 No pending todo with id`{todo_id}`'
    else:
        todo.done = True
        s.commit()
        msg = f"✅ Congratz. You've finished one todo"

    update.message.reply_markdown(msg)


add_todo_cmd = CommandHandler('todo', add_todo)
show_todos_cmd = CommandHandler('todos', show_todos)
mark_as_done_cmd = CommandHandler('mark_todo_as_done', mark_as_done)

