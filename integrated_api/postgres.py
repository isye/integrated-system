import os
from flask import  g
from sqlalchemy import create_engine, MetaData, Table, Column, String, SmallInteger, TEXT, DateTime
import uuid, datetime
from integrated_api import utils
from sqlalchemy.dialects.postgresql import insert

postgres_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/apiv3')
engine = create_engine(postgres_url, convert_unicode=True)
metadata = MetaData(bind=engine)

tblClient = Table('tbl_client', metadata,
        Column('client_id', String(36), default=str(uuid.uuid4()),primary_key=True),
        Column('client_name', TEXT, default=''),
        Column('calendar_id', String(36), default='0'),
        Column('updated', DateTime(timezone=False), default=datetime.datetime.now()),
        Column('updated_by_id', TEXT, default='System'),
        autoload=True)


tblProduct = Table('tbl_product', metadata,
        Column('product_id', String(36), default=str(uuid.uuid4()),primary_key=True),
        Column('client_id', String(36),  default=''),
        Column('product_name', TEXT, default=''),
        Column('product_description', TEXT, default=''),
        Column('duration_minutes', SmallInteger, default=0),
        Column('producer_offset_minutes', SmallInteger, default=60),
        Column('producer_count', SmallInteger, default=1),
        Column('updated', DateTime(timezone=False), default=datetime.datetime.now()),
        Column('updated_by_id', String(36), default='System'),
        autoload=True)


tblEventTag = Table('tbl_event_tag', metadata,
        Column('event_id', String(36), primary_key=True),
        Column('tag_name', TEXT, primary_key=True),
        Column('tag_value', TEXT, default=''),
        Column('updated', DateTime(timezone=False), default=datetime.datetime.now()),
        Column('updated_by_id', String(36), default='System'),
        autoload=True)

tblPerson = Table('tbl_person', metadata,
       Column('person_id', String(36), default=str(uuid.uuid4()), primary_key=True),
       Column('first_name', String(100), default=''),
       Column('last_name', String(100), default=''),
       Column('email', String(100), default=''),
       Column('cell', String(36), default=''),
       Column('primary_comm_method', String(36), default=''),
       Column('notes', TEXT, default=''),
       Column('updated', DateTime(timezone=False), default=datetime.datetime.now()),
       Column('updated_by_id', String(36), default='System'),
       autoload=True)

tblCalendar = Table('tbl_calendar', metadata,
       Column('calendar_id', String(36), default=str(uuid.uuid4()),primary_key=True),
       Column('calendar_name', TEXT, default=''),
       Column('platform_id', TEXT, default=''),
       Column('updated', DateTime(timezone=False), default=datetime.datetime.now()),
       Column('updated_by_id', String(36), default='System'),
                    extend_existing=True)

def upsertCalendar(data):
    try:
        con = get_pgcon()
        calendarId = data.get('calendar_id', None)
        if(calendarId):
            insert_stmt = insert(tblCalendar).values(data)
            update_stmt = insert_stmt.on_conflict_do_update(
                constraint='tbl_calendar_pk',
                set_=data)
            con.execute(update_stmt)
            data = con.execute(tblCalendar.select().where(tblCalendar.c.calendar_id == calendarId)).fetchone()
            if (data):
                return [dict(data.items())]
            else:
                return None
        else:
            return None
    except Exception as e:
        errormessage = utils.customError("upsertCalendar", e)
        print(errormessage)
        raise

def deleteCalendar(calendarId):
    try:
        con = get_pgcon()
        if(calendarId):
            data = con.execute(tblCalendar.delete().where(tblCalendar.c.calendar_id == calendarId))
            if (data):
                return "Success to delete data calendar with ID: " + calendarId
            else:
                return "Failed to delete data calendar, check ID: " + calendarId + " is exist"
        else:
            return None
    except Exception as e:
        errormessage = utils.customError("deleteCalendar", e)
        print(errormessage)
        raise

def getEventDetail(eventID):
    try:
        con = get_pgcon()
        strsql = "select a.email, b.person_role, c.event_name, c.event_start, c.duration_minutes, c.time_zone from tbl_person a, tbl_event_person b, tbl_event c " \
                 "where b.person_role='Producer' and a.person_id=b.person_id and c.event_id=b.event_id and b.event_id=%s;"
        data = con.execute(strsql, eventID).fetchall()
        if (data):
            if (isinstance(data, list)):
                return [dict(row.items()) for row in data]
            else:
                return [dict(data.items())]
        else:
            return None
    except Exception as e:
        errormessage = utils.customError("getEventDetail", e)
        print(errormessage)
        raise

def getCalendarID(eventID=None):
    try:
        con = get_pgcon()
        if(eventID):
            strsql = "select c.calendar_id from tbl_event a, tbl_project b, tbl_client c " \
                     "where b.project_id=a.project_id and c.client_id=b.client_id and a.event_id=%s;"
            data = con.execute(strsql, eventID).fetchone()
        else:
            strsql = "select calendar_id from tbl_calendar where calendar_name='Producer Calendar';"
            data = con.execute(strsql).fetchone()

        if (data):
            return dict(data.items())
        else:
            return None
    except Exception as e:
        errormessage = utils.customError("getCalendarID", e)
        print(errormessage)
        raise

def listCalendar(calendarID=None):
    try:
        con = get_pgcon()
        if (calendarID):
            data = con.execute(tblCalendar.select().where(tblCalendar.c.calendar_id == calendarID)).fetchone()
        else:
            data = con.execute(tblCalendar.select()).fetchall()
        if (data):
            if (isinstance(data, list)):
                return [dict(row.items()) for row in data]
            else:
                return [dict(data.items())]
        else:
            return None

    except Exception as e:
        errormessage = utils.customError("listCalendar", e)
        print(errormessage)
        raise

def upsertPerson(data):
    try:
        con = get_pgcon()
        personId = data.get('person_id', None)
        if (personId is None):
            personId = str(uuid.uuid4())
        data['person_id'] = personId

        insert_stmt = insert(tblPerson).values(data)
        update_stmt = insert_stmt.on_conflict_do_update(
                constraint='tbl_person_pk',
                set_=data)
        con.execute(update_stmt)
        data = con.execute(tblPerson.select().where(tblPerson.c.person_id == personId)).fetchone()

        if (data is not None):
            return [dict(data.items())]
        else:
            return None
    except Exception as e:
        errormessage = utils.customError("upsertPerson", e)
        print(errormessage)
        raise

def listPerson(personID=None):
    try:
        con = get_pgcon()
        if(personID):
            data = con.execute(tblPerson.select().where(tblPerson.c.person_id == personID)).fetchone()
        else:
            data = con.execute(tblPerson.select()).fetchall()
        if (data is not None):
            if(isinstance(data,list)):
                return [dict(row.items()) for row in data]
            else:
                return [dict(data.items())]
        else:
            return None
    except Exception as e:
        errormessage = utils.customError("listPerson", e)
        print(errormessage)
        raise

def upsertEventTagMulti(listdata):
    try:
        con = get_pgcon()
        for data in listdata:
            insert_stmt = insert(tblEventTag).values(data)
            update_stmt = insert_stmt.on_conflict_do_update(
                constraint='tbl_event_tag_pk',
                set_=data)
            con.execute(update_stmt)
    except Exception as e:
        errormessage = utils.customError("Upsert Event Tag Multi", e)
        print(errormessage)
        raise

def listEventTag(eventID=None):
    try:
        con = get_pgcon()
        if(eventID):
            data = con.execute(tblEventTag.select().where(tblEventTag.c.event_id==eventID)).fetchall()
        else:
            data = con.execute(tblEventTag.select()).fetchall()
        if (data):
            if (isinstance(data, list)):
                return [dict(row.items()) for row in data]
            else:
                return [dict(data.items())]

        else:
            return None
    except Exception as e:
        errormessage = utils.customError("listEventTag", e)
        print(errormessage)
        raise


def get_pgcon():
    try:
        if 'pgcon' not in g:
            g.pgcon = engine.connect()
        return g.pgcon
    except Exception as e:
        errormessage = utils.customError("get_pgcon", e)
        print(errormessage)
        raise

if __name__=='__main__':
    c = 'tes'
