from telegram import *
from telegram.ext import *
from requests import *

updater = Updater(token="")
dispatcher = updater.dispatcher

class User:
    def __init__(self):
        self.tasks = []
        self.current_task = None

class Task():
    def __init__(self, title):
        self.title = title
        self.desc = ""

users = {}

def startCommandHandler(update: Update, context: CallbackContext):
    if update.effective_chat.id not in users:
        users[update.effective_chat.id] = User()
    
    buttons = [[KeyboardButton("Мои задачи"), KeyboardButton("Создать задачу")]]
    context.bot.send_message(chat_id=update.effective_chat.id, text="Приветствую!", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

def createTask(update: Update, context: CallbackContext):
    if update.effective_chat.id not in users:
        users[update.effective_chat.id] = User()

    context.bot.send_message(chat_id=update.effective_chat.id, text="Введите название задачи.", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отменить создание задачи")]], resize_keyboard=True))
    
    return 0

def setTitle(update: Update, context: CallbackContext):
    if update.message.text == "Отменить создание задачи":
        cancelTaskCreation(update, context)
        return ConversationHandler.END

    if update.message.text.startswith("/"):
            buttons = [[KeyboardButton("Мои задачи"), KeyboardButton("Создать задачу")]]
            context.bot.send_message(chat_id=update.effective_chat.id, text="Невозможно создать задачу с таким названием..", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
            users[update.effective_chat.id].current_task = None
            return ConversationHandler.END

    for task in users[update.effective_chat.id].tasks:
        if task.title == update.message.text:
            buttons = [[KeyboardButton("Мои задачи"), KeyboardButton("Создать задачу")]]
            context.bot.send_message(chat_id=update.effective_chat.id, text="Задача с таким названием уже существует.", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
            users[update.effective_chat.id].current_task = None
            return ConversationHandler.END

    users[update.effective_chat.id].current_task = Task(update.message.text)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Введите описание или /skip, чтобы создать задачу без описания.", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Отменить создание задачи")]], resize_keyboard=True))

    return 1

def setDesc(update: Update, context: CallbackContext):
    if update.message.text == "Отменить создание задачи":
        cancelTaskCreation(update, context)
        return ConversationHandler.END

    if update.message.text == "/skip":
        skipDesc(update, context)
        return ConversationHandler.END

    users[update.effective_chat.id].current_task.desc = update.message.text
    users[update.effective_chat.id].tasks.append(users[update.effective_chat.id].current_task)
    buttons = [[KeyboardButton("Мои задачи"), KeyboardButton("Создать задачу")]]
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Задача создана: {users[update.effective_chat.id].current_task.title}", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    users[update.effective_chat.id].current_task = None

    return ConversationHandler.END

def skipDesc(update: Update, context: CallbackContext):
    users[update.effective_chat.id].tasks.append(users[update.effective_chat.id].current_task)
    buttons = [[KeyboardButton("Мои задачи"), KeyboardButton("Создать задачу")]]
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Задача создана: {users[update.effective_chat.id].current_task.title}", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    users[update.effective_chat.id].current_task = None

    return ConversationHandler.END

def cancelTaskCreation(update: Update, context: CallbackContext):
    users[update.effective_chat.id].current_task = None
    buttons = [[KeyboardButton("Мои задачи"), KeyboardButton("Создать задачу")]]
    context.bot.send_message(chat_id=update.effective_chat.id, text="Создание задачи отменено.", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

taskCreationConvHandler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex("Создать задачу"), createTask)],

    states={
        0: [MessageHandler(Filters.text, setTitle)],
        1: [MessageHandler(Filters.text, setDesc), CommandHandler('skip', skipDesc)]
    },

    fallbacks=[]
)

def viewTasks(update: Update, context: CallbackContext):
    if update.effective_chat.id not in users:
        users[update.effective_chat.id] = User()

    if users[update.effective_chat.id].tasks == []:
        buttons = [[KeyboardButton("Мои задачи"), KeyboardButton("Создать задачу")]]
        context.bot.send_message(chat_id=update.effective_chat.id, text="У вас нет задач.",    reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
        return ConversationHandler.END

    buttons = []
    for task in users[update.effective_chat.id].tasks:
        buttons.append([task.title])
    context.bot.send_message(chat_id=update.effective_chat.id, text="Ваши задачи. /menu, чтобы вернуться на главную.", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    
    return 0

def viewTask(update: Update, context: CallbackContext):
    buttons = [[KeyboardButton("Мои задачи"), KeyboardButton("Создать задачу")]]
    
    if update.message.text == "/menu":
        mainMenu(update, context)
        return ConversationHandler.END

    for task in users[update.effective_chat.id].tasks:
        if task.title == update.message.text:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"<b>{'• ' + task.title}</b>\n{task.desc}", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True), parse_mode="HTML")
            return ConversationHandler.END
    
    context.bot.send_message(chat_id=update.effective_chat.id, text="Такой задачи не существует.", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return ConversationHandler.END


def mainMenu(update: Update, context: CallbackContext):
    buttons = [[KeyboardButton("Мои задачи"), KeyboardButton("Создать задачу")]]
    context.bot.send_message(chat_id=update.effective_chat.id, text="Главное меню.", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

    return ConversationHandler.END


viewTasksConvHandler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex("Мои задачи"), viewTasks)],

    states={
        0: [MessageHandler(Filters.text, viewTask)]
    },

    fallbacks=[CommandHandler("menu", mainMenu)]
)

dispatcher.add_handler(CommandHandler("start", startCommandHandler))
dispatcher.add_handler(taskCreationConvHandler)
dispatcher.add_handler(viewTasksConvHandler)

updater.start_polling()
