import config
from peewee import *

db = SqliteDatabase(config.database['path'])

class Ticket(Model):
    number = TextField()
    contacted = TextField()
    class Meta:
        database = db # This model uses the "people.db" database.

def getData(ticket_num):
    db.connect()
    try:
        query = Ticket.get(Ticket.number == ticket_num)
    except DoesNotExist:
        query = ""
    db.close()
    return query

def saveData(ticket_num, boolvalue):
    db.connect()
    try:
        item = Ticket.get(Ticket.number == ticket_num)
        item.contacted = boolvalue
        item.save()
    except DoesNotExist:
        item = Ticket(number=ticket_num, contacted=boolvalue)
        item.save()
    db.close()
    return item