from telegram import *
from telegram.ext import *
from requests import *

updater = Updater(token="986301212:AAFtT4czM2csK5XaE98pkn9k6R-t_OrTyJ4")
dispatcher = updater.dispatcher

class User:
    def __init__(self):
        self.tasks = []
        self.isCreatingTaskName = False
        self.isCreatingTaskDesc = False

users = {}

def startCommandHandler(update: Update, context: CallbackContext):
    if update.effective_chat.id not in users:
        users[update.effective_chat.id] = User()
    user = users[update.effective_chat.id]
    user.isCreatingTask = False
    
    buttons = [[KeyboardButton("Мои задачи"), KeyboardButton("Создать задачу")]]
    context.bot.send_message(chat_id=update.effective_chat.id, text="Приветствую!", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

def messageHandler(update: Update, context: CallbackContext):
    if update.effective_chat.id not in users:
        users[update.effective_chat.id] = User()
    user = users[update.effective_chat.id]

    if user.isCreatingTask:
        user.tasks.append(update.message.text)
        user.isCreatingTask = False
        context.bot.send_message(chat_id=update.effective_chat.id, text="Задача создана: " + update.message.text)
        return

    match update.message.text:
        case "Мои задачи":
            buttons = [[KeyboardButton(task)] for task in user.tasks] + [[KeyboardButton("На главную")]]
            context.bot.send_message(chat_id=update.effective_chat.id, text="Ваши задачи:\n" + "\n".join("• " + task for task in user.tasks), reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
        case "Создать задачу":
            context.bot.send_message(chat_id=update.effective_chat.id, text="Введите название задачи:")
            user.isCreatingTaskName = True
        case "На главную":
            buttons = [[KeyboardButton("Мои задачи"), KeyboardButton("Создать задачу")]]
            context.bot.send_message(chat_id=update.effective_chat.id, text="Меню", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

            

dispatcher.add_handler(CommandHandler("start", startCommandHandler))
dispatcher.add_handler(MessageHandler(Filters.text, messageHandler))

updater.start_polling()