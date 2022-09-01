from config import TOKEN
import telebot
import datetime as dt
from models import Clients, Appointments
from db import db

from telebot.types import (
InlineKeyboardMarkup,
InlineKeyboardButton,
ReplyKeyboardMarkup
)
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def welcome(message):
    cursor = db.cursor()
    id_of_user = str(message.from_user.id)
    query = Clients.select().where(Clients.userid_tg == id_of_user)
    if query.exists():
        cursor.execute("SELECT full_name FROM clients WHERE userid_tg = '%s'" % id_of_user)
        fullname = cursor.fetchone()
        welcome_old = f"""
Добро пожаловать, <b>{fullname[0]}</b>!
С помощью нашего бота Вы можете записаться на приём к стоматологу.
Пожалуйста, выберите действие, нажав на кнопку ниже:"""
        bot.send_message(message.chat.id, welcome_old, reply_markup=markup_adder(), parse_mode="HTML")
    else:
        welcome_new = f"""
Добро пожаловать!
С помощью нашего бота Вы можете записаться на приём к стоматологу.
Пожалуйста, для начала работы, укажите Ваше полное имя:"""
        bot.send_message(message.chat.id, welcome_new, parse_mode="HTML")
        bot.register_next_step_handler(message, callback=get_full_name)


def markup_adder():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    new_appointment = InlineKeyboardButton("Записаться на прием", callback_data="new_appointment")
    show_data = InlineKeyboardButton("Мои данные", callback_data="show_data")
    change_name = InlineKeyboardButton("Изменить полное имя", callback_data="change_full_name")
    change_phone = InlineKeyboardButton("Изменить номер телефона", callback_data="change_phone")
    markup.add(new_appointment, show_data, change_name, change_phone)
    return markup


def get_full_name(message):
    global full_name
    full_name = message.text
    name_thanks = f"""
Спасибо, <b>{full_name}</b>, Ваше имя записано.
Для того, чтобы приступить к записи на приём, укажите также Ваш номер телефона:"""
    bot.send_message(message.chat.id, name_thanks, parse_mode="HTML")
    bot.register_next_step_handler(message, callback=get_phone)


def get_phone(message):
    id_of_user = str(message.from_user.id)
    phone = message.text
    phone_thanks = f"""
Спасибо, Ваш номер телефона записан."""
    bot.send_message(message.chat.id, phone_thanks, parse_mode="HTML")
    Clients.create(userid_tg=id_of_user, full_name=full_name, phone=phone)
    welcome(message)


@bot.callback_query_handler(func=lambda call: call.data == "show_data")
def show_data(call):
    id_of_user = str(call.from_user.id)
    name_of_user = Clients.get(Clients.userid_tg == id_of_user).full_name
    phone_of_user = Clients.get(Clients.userid_tg == id_of_user).phone
    appointments = ""
    appointments_user = Appointments.select().where(Appointments.userid_id == id_of_user)
    for appointment in appointments_user:
        date_and_time = f"\n{appointment.date} - {appointment.time}"
        appointments = appointments + date_and_time
    text = f"""
Ваше полное имя: <b>{name_of_user}</b>.
Ваш номер телефона: <b>{phone_of_user}</b>.
Вы записаны на следующее время: <b>{appointments}</b>.
"""
    bot.send_message(call.message.chat.id, text, reply_markup=markup_adder(), parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "change_full_name")
def change_full_name(call):
    message = call.message
    text = f"""
Пожалуйста, введите Ваше новое полное имя:"""
    bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(message, callback=get_new_full_name)


def get_new_full_name(message):
    id_of_user = str(message.from_user.id)
    new_full_name = message.text
    Clients.update(full_name=new_full_name).where(Clients.userid_tg == id_of_user).execute()
    text = f"""
Спасибо, <b>{new_full_name}</b>, Ваше полное имя обновлено."""
    bot.send_message(message.chat.id, text, reply_markup=markup_adder(), parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "change_phone")
def change_phone(call):
    message = call.message
    text = f"""
Пожалуйста, введите Ваш новый номер телефона:"""
    bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(message, callback=get_new_phone)


def get_new_phone(message):
    id_of_user = str(message.from_user.id)
    new_phone = message.text
    Clients.update(phone=new_phone).where(Clients.userid_tg == id_of_user).execute()
    name_of_user = Clients.get(Clients.userid_tg == id_of_user).full_name
    text = f"""
Спасибо, <b>{name_of_user}</b>, Ваш номер телефона обновлён."""
    bot.send_message(message.chat.id, text, reply_markup=markup_adder(), parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "new_appointment")
def new_appointment(call):
    id_of_user = str(call.from_user.id)
    name_of_user = Clients.get(Clients.userid_tg == id_of_user).full_name
    weekdays = {0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг", 4: "Пятница"}
    make_calendar()
    weekdays_list = get_weekdays()
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    times = generate_times()
    times = set(times)
    cursor = db.cursor()

    for item in weekdays_list:
        for key, value in item.items():
            cursor.execute("SELECT time FROM appointments WHERE date = '%s'" % key)
            records = cursor.fetchall()
            records_list = [i[0] for i in records]
            busy_times_set = set()
            for record in records_list:
                record = (dt.datetime.min + record).time().strftime("%H:%M:%S")
                busy_times_set.add(record)
            if busy_times_set == times:
                pass
            else:
                markup.add(InlineKeyboardButton(weekdays.get(value) + ' - ' + key, callback_data=f"{key}"))
    text = f"""
<b>{name_of_user}</b>, пожалуйста, выберите день, на который Вы хотите записаться:"""
    bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data in my_calendar)
def scheduler(call):
    global appointment_date
    appointment_date = call.data
    message = call.message
    id_of_user = str(call.from_user.id)
    name_of_user = Clients.get(Clients.userid_tg == id_of_user).full_name
    cursor = db.cursor()
    cursor.execute("SELECT time FROM appointments WHERE date = '%s'" % appointment_date)
    records = cursor.fetchall()
    time = [i[0] for i in records]
    busy_times = []
    for item in time:
        item = (dt.datetime.min + item).time().strftime("%H:%M:%S")
        busy_times.append(item)
    times = generate_times()
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row_width = 1
    for item in times:
        if item not in busy_times:
            markup.add(item)
    text = f"""
    <b>{name_of_user}</b>, пожалуйста, выберите час, на который Вы хотите записаться:"""
    bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    bot.register_next_step_handler(message, callback=set_time)


def set_time(message):
    id_of_user = str(message.from_user.id)
    appointment_time = message.text
    Appointments.create(userid_id=id_of_user, date=appointment_date, time=appointment_time)
    name_of_user = Clients.get(Clients.userid_tg == id_of_user).full_name
    text = f"""
Спасибо, <b>{name_of_user}</b>, Вы записаны на <b>{appointment_date}</b> в <b>{appointment_time}</b>.
"""
    bot.send_message(message.chat.id, text, reply_markup=markup_adder(), parse_mode="HTML")


def generate_times():
    timestamp_format = '%H:%M:%S'
    start_time = '09:00:00'
    ts_obj = dt.datetime.strptime(start_time, timestamp_format)
    end_time = '17:00:00'
    latest_ts_obj = dt.datetime.strptime(end_time, timestamp_format)
    times = []
    while ts_obj <= latest_ts_obj:
        times.append(ts_obj)
        ts_obj += dt.timedelta(hours=1)
    times = [d.strftime('%H:%M:%S') for d in times]
    return times


def make_calendar():
    def daterange(date1, date2):
        for n in range(int((date2 - date1).days)):
            yield date1 + dt.timedelta(n)
    date1 = dt.date(2022, 1, 1)
    date2 = dt.date(2022, 12, 31)
    holidays = ['2022-01-01', '2022-01-07', '2022-02-23', '2022-03-08', '2022-03-21', '2022-04-07', '2022-05-02',
                '2022-05-03', '2022-05-04', '2022-05-05', '2022-05-06', '2022-05-09', '2022-07-11', '2022-08-31',
                '2022-11-07', '2022-11-08']
    global my_calendar
    my_calendar = {}
    for single_date in daterange(date1, date2):
        if single_date.weekday() == 5 or single_date.weekday() == 6:
            pass
        elif single_date.strftime("%Y-%m-%d") in holidays:
            pass
        else:
            my_calendar.update({single_date.strftime("%Y-%m-%d"): single_date.weekday()})
    return my_calendar


def get_weekdays():
    tomorrow = (dt.date.today() + dt.timedelta(days=1)).strftime("%Y-%m-%d")
    present_date = dt.datetime.strptime(tomorrow, "%Y-%m-%d")
    end_date = (dt.date.today() + dt.timedelta(days=14)).strftime("%Y-%m-%d")
    end_date = dt.datetime.strptime(end_date, "%Y-%m-%d")
    return [{key: value} for key, value in make_calendar().items() if
            present_date <= dt.datetime.strptime(key, "%Y-%m-%d") <= end_date]


bot.infinity_polling()