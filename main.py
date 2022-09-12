from telegram import *
from telegram.ext import *
from requests import *
import asyncio
import time
import datetime
from ics_parser import *
import os

TOKEN = open("token.txt").read()
MAIN_MENU_BUTTONS = [[KeyboardButton("📝Мои задачи"), KeyboardButton("📅Календарь")]]

updater = Updater(TOKEN)
dispatcher = updater.dispatcher

class User:
    def __init__(self):
        self.tasks = []
        self.current_task = None
        self.events = []
        self.current_event = None

class Task:
    def __init__(self, title):
        self.title = title
        self.desc = ""
        self.reminders = []

class Reminder:
    def __init__(self, user_id, time, text):
        self.user_id = user_id
        self.time = time
        self.text = text

users = {}
reminders = []

async def remind():
    bot = Bot(TOKEN)
    global reminders
    while True:
        reminders_new = []
        for reminder in reminders:
            if time.time() >= reminder.time:
                bot.sendMessage(chat_id=reminder.user_id, text=f"⏰Напоминание: <b>{reminder.text}</b>.", parse_mode="HTML")
            else:
                reminders_new.append(reminder)
        reminders = reminders_new[:]

def startCommandHandler(update: Update, context: CallbackContext):
    if update.effective_chat.id not in users:
        users[update.effective_chat.id] = User()
    
    context.bot.send_message(chat_id=update.effective_chat.id, text="Приветствую!", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

def createTask(update: Update, context: CallbackContext):
    if update.effective_chat.id not in users:
        users[update.effective_chat.id] = User()

    context.bot.send_message(chat_id=update.effective_chat.id, text="Введите название задачи.", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🚫Отменить создание задачи")]], resize_keyboard=True))
    
    return 3

def setTitle(update: Update, context: CallbackContext):
    if update.message.text.startswith("/"):
            buttons = MAIN_MENU_BUTTONS
            context.bot.send_message(chat_id=update.effective_chat.id, text="⛔️Невозможно создать задачу с таким названием..", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
            users[update.effective_chat.id].current_task = None
            return ConversationHandler.END

    for task in users[update.effective_chat.id].tasks:
        if task.title == update.message.text:
            buttons = MAIN_MENU_BUTTONS
            context.bot.send_message(chat_id=update.effective_chat.id, text="⛔️Задача с таким названием уже существует.", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
            users[update.effective_chat.id].current_task = None
            return ConversationHandler.END

    users[update.effective_chat.id].current_task = Task(update.message.text)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Введите описание или /skip, чтобы создать задачу без описания.", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🚫Отменить создание задачи")]], resize_keyboard=True))

    return 4

def setDesc(update: Update, context: CallbackContext):
    users[update.effective_chat.id].current_task.desc = update.message.text
    users[update.effective_chat.id].tasks.append(users[update.effective_chat.id].current_task)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Задача создана: <b>{users[update.effective_chat.id].current_task.title}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")
    users[update.effective_chat.id].current_task = None

    return ConversationHandler.END

def skipDesc(update: Update, context: CallbackContext):
    users[update.effective_chat.id].tasks.append(users[update.effective_chat.id].current_task)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Задача создана: <b>{users[update.effective_chat.id].current_task.title}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")
    users[update.effective_chat.id].current_task = None

    return ConversationHandler.END

def cancelTaskCreation(update: Update, context: CallbackContext):
    users[update.effective_chat.id].current_task = None
    context.bot.send_message(chat_id=update.effective_chat.id, text="✅Создание задачи отменено.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def viewTasks(update: Update, context: CallbackContext):
    if update.effective_chat.id not in users:
        users[update.effective_chat.id] = User()

    buttons = [[KeyboardButton("✏️Создать задачу")]]
    for task in users[update.effective_chat.id].tasks:
        buttons.append([task.title])
    context.bot.send_message(chat_id=update.effective_chat.id, text="📖Ваши задачи. /menu, чтобы вернуться на главную.", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    
    return 0

def viewTask(update: Update, context: CallbackContext):
    for task in users[update.effective_chat.id].tasks:
        if task.title == update.message.text:
            users[update.effective_chat.id].current_task = task
            buttons = [[KeyboardButton("🏠На главную")], [KeyboardButton("⏰Добавить напоминание")], [KeyboardButton("❌Удалить задачу")]]
            text = f"<b>{'• ' + task.title}</b>"
            if task.desc != "":
                text += f"\n{task.desc}"
            if task.reminders != []:
                text += "\n\n-----"
                for reminder in task.reminders:
                    text += f"\n⏰Напоминание: {reminder}"
            context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True), parse_mode="HTML")
            return 1
    
    context.bot.send_message(chat_id=update.effective_chat.id, text="⛔️Такой задачи не существует.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
    return ConversationHandler.END


def mainMenu(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="🏠Главное меню.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def createTaskReminder(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="🕰Введите время (год.месяц.день.час.минута).", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🚫Отменить добавление напоминания")]], resize_keyboard=True))

    return 2

def deleteTask(update: Update, context: CallbackContext):
    users[update.effective_chat.id].tasks.pop(users[update.effective_chat.id].tasks.index(users[update.effective_chat.id].current_task))
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Задача удалена: <b>{users[update.effective_chat.id].current_task.title}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")
    users[update.effective_chat.id].current_task = None
    
    return ConversationHandler.END

def setTaskReminder(update: Update, context: CallbackContext):
    try:
        time = datetime.datetime(*[int(i) for i in update.message.text.split(".")])

        reminders.append(Reminder(update.effective_chat.id, time.timestamp(), users[update.effective_chat.id].current_task.title))

        users[update.effective_chat.id].tasks[users[update.effective_chat.id].tasks.index(users[update.effective_chat.id].current_task)].reminders.append(time)

        context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Напоминание добавлено: {time}.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
        users[update.effective_chat.id].current_task = None
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⛔️Ошибка при добавлении напоминания. Вероятно, время введено в неверном формате.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
        users[update.effective_chat.id].current_task = None

    return ConversationHandler.END

def cancelReminderCreation(update: Update, context: CallbackContext):
    users[update.effective_chat.id].current_task = None
    context.bot.send_message(chat_id=update.effective_chat.id, text="✅Добавление напоминания отменено.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

viewTasksConvHandler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex("📝Мои задачи"), viewTasks)],

    states={
        0: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("✏️Создать задачу"), createTask), MessageHandler(Filters.text, viewTask)],
        1: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("🏠На главную"), mainMenu), MessageHandler(Filters.regex("⏰Добавить напоминание"), createTaskReminder), MessageHandler(Filters.regex("❌Удалить задачу"), deleteTask)],
        2: [MessageHandler(Filters.regex("🚫Отменить добавление напоминания"), cancelReminderCreation), MessageHandler(Filters.text, setTaskReminder)],
        3: [MessageHandler(Filters.regex("🚫Отменить создание задачи"), cancelTaskCreation), MessageHandler(Filters.text, setTitle)],
        4: [CommandHandler("skip", skipDesc), MessageHandler(Filters.regex("🚫Отменить создание задачи"), cancelTaskCreation), MessageHandler(Filters.text, setDesc)]
    },

    fallbacks=[]
)

def createReminder(update: Update, context: CallbackContext):
    time, text = update.message.text[8:].split()
    reminders.append(Reminder(update.effective_chat.id, datetime.datetime(*[int(i) for i in time.split(".")]).timestamp(), text))

def importCalendar(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="📁Отправьте .ics файл календаря.", reply_markup=ReplyKeyboardMarkup([["🚫Отменить импорт календаря"]], resize_keyboard=True))

    return 2

def icsHandler(update: Update, context: CallbackContext):
    if update.effective_chat.id not in users:
        users[update.effective_chat.id] = User()

    try:
        filename = str(update.effective_chat.id)+"_"+str(time.time())+".ics"
        context.bot.get_file(update.message.document).download(custom_path=filename)
        
        events = getEvents(filename)
        for event in events:
            start = event.start.strftime("%d.%m.%Y %H:%M")
            if event.start.strftime("%d.%m.%Y") == event.end.strftime("%d.%m.%Y"):
                end = event.end.strftime("%H:%M")
            else:
                end = event.end.strftime("%d.%m.%Y %H:%M")
            taskname = f"{start} - {end} | {event.name}"
            for user_event in users[update.effective_chat.id].events:
                if user_event.title == taskname: break
            else:
                users[update.effective_chat.id].events.append(Task(taskname))
                if event.start.timestamp() > time.time():
                    reminders.append(Reminder(update.effective_chat.id, event.start.timestamp() - 3600, taskname))

        os.remove(filename)
        context.bot.send_message(chat_id=update.effective_chat.id, text="✅Календарь импортирован успешно.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="⛔️Ошибка при чтении файла календаря.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END

def viewCalendar(update: Update, context: CallbackContext):
    if update.effective_chat.id not in users:
        users[update.effective_chat.id] = User()

    buttons = [["📲Импортировать календарь"]]
    for event in users[update.effective_chat.id].events:
        buttons.append([event.title])
    context.bot.send_message(chat_id=update.effective_chat.id, text="📅Календарь. /menu, чтобы вернуться на главную.", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    
    return 0

def viewEvent(update: Update, context: CallbackContext):
    for event in users[update.effective_chat.id].events:
        if event.title == update.message.text:
            users[update.effective_chat.id].current_event = event
            buttons = [[KeyboardButton("🏠На главную")], [KeyboardButton("❌Удалить событие")]]
            text = f"<b>{'• ' + event.title}</b>"
            context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True), parse_mode="HTML")
            return 1
    
    context.bot.send_message(chat_id=update.effective_chat.id, text="⛔️Такой задачи не существует.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))
    return ConversationHandler.END

def deleteEvent(update: Update, context: CallbackContext):
    users[update.effective_chat.id].events.pop(users[update.effective_chat.id].events.index(users[update.effective_chat.id].current_event))
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅Событие удалено: <b>{users[update.effective_chat.id].current_event.title}</b>.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True), parse_mode="HTML")
    users[update.effective_chat.id].current_event = None
    
    return ConversationHandler.END

def cancelIcsImport(update: Update, context: CallbackContext):
    users[update.effective_chat.id].current_event = None
    context.bot.send_message(chat_id=update.effective_chat.id, text="✅Импорт календаря отменён.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True))

    return ConversationHandler.END


viewCalendarConvHandler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex("📅Календарь"), viewCalendar)],

    states={
        0: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("📲Импортировать календарь"), importCalendar), MessageHandler(Filters.text, viewEvent)],
        1: [CommandHandler("menu", mainMenu), MessageHandler(Filters.regex("🏠На главную"), mainMenu), MessageHandler(Filters.regex("❌Удалить событие"), deleteEvent)],
        2: [MessageHandler(Filters.regex("🚫Отменить импорт календаря"), cancelIcsImport), MessageHandler(Filters.document, icsHandler)]
    },

    fallbacks=[]
)

dispatcher.add_handler(CommandHandler("start", startCommandHandler))
dispatcher.add_handler(CommandHandler("remind", createReminder))
dispatcher.add_handler(viewTasksConvHandler)
dispatcher.add_handler(viewCalendarConvHandler)

updater.start_polling()
asyncio.run(remind())