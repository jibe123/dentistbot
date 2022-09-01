import peewee

from db import db


class Clients(peewee.Model):
    userid_tg = peewee.CharField(unique=True)
    full_name = peewee.CharField()
    phone = peewee.CharField()

    class Meta:
        database = db
        table_settings = ['ENGINE=InnoDB', 'DEFAULT CHARSET=utf8']


class Appointments(peewee.Model):
    userid = peewee.ForeignKeyField(Clients, to_field='userid_tg', on_delete='CASCADE')
    date = peewee.DateField()
    time = peewee.TimeField()

    class Meta:
        database = db
        table_settings = ['ENGINE=InnoDB', 'DEFAULT CHARSET=utf8']


if not Clients.table_exists():
    Clients.create_table()

if not Appointments.table_exists():
    Appointments.create_table()