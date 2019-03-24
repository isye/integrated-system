from __future__ import print_function
import datetime, os
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from integrated_api import utils, postgres
from flask import current_app as app, g

SCOPES = 'https://www.googleapis.com/auth/calendar'

def get_calendar_service():
    try:
        if 'calservice' not in g:
            token_path = os.getenv('GCALENDAR_TOKEN','')
            credential_path = os.getenv('GCALENDAR_CREDENTIALS','')
            store = file.Storage(token_path)
            creds = store.get()
            if not creds or creds.invalid:
                flow = client.flow_from_clientsecrets(credential_path, SCOPES)
                creds = tools.run_flow(flow, store)
            g.calservice = build('calendar', 'v3', http=creds.authorize(Http()))
            return g.calservice
    except Exception as e:
        errormessage = utils.customError("get_calendar_service", e)
        print(errormessage)
        raise

def createCalendar(summary, timeZone='America/New_York'):
    try:
        calendar = {
            'summary': summary,
            'timeZone': timeZone
        }
        service = get_calendar_service()
        created_calendar_list_entry = service.calendars().insert(body=calendar).execute()
        return created_calendar_list_entry
    except Exception as e:
        errormessage = utils.customError("createCalendar", e)
        print(errormessage)
        raise

def deleteCalendar(calendarID):
    try:
        service = get_calendar_service()
        deleted_calendar_list_entry = service.calendars().delete(calendarId=calendarID).execute()
        return deleted_calendar_list_entry
    except Exception as e:
        errormessage = utils.customError("deleteCalendar", e)
        print(errormessage)
        raise

def updateCalendar(data):
    try:
        service = get_calendar_service()
        updated_calendar = service.calendars().update(calendarId=data['id'], body=data).execute()
        return updated_calendar
    except Exception as e:
        errormessage = utils.customError("updateCalendar", e)
        print(errormessage)
        raise

def listCalendar():
    try:
        service = get_calendar_service()
        listCalendar = []
        page_token = None
        while True:
            calendars = service.calendarList().list(pageToken=page_token).execute()
            listCalendar.append(calendars)
            page_token = calendars.get('nextPageToken')
            if not page_token:
                break
        return listCalendar
    except Exception as e:
        errormessage = utils.customError("listCalendar", e)
        print(errormessage)
        raise


def upsertEvent(eventdata, status=None):
    try:
        eventID = eventdata.get('event_id', None)
        added_attendee = eventdata.get('attendees', None)
        producer_email = None
        if (eventID):
            details_event = postgres.getEventDetail(eventID)
            service = get_calendar_service()
            if (details_event and len(details_event) > 0):
                producer_email = [{'email': e.get('email', None)} for e in details_event if
                                  e.get('email', None) is not None]
                if (added_attendee and len(added_attendee) > 0):
                    producer_email.append(added_attendee)
                formatted_event = formatDataEvent(details_event[0])
            else:
                return "Error, Event data or Producer data does not exist for that event ID. Contact developer."
            clientCal = postgres.getCalendarID(eventID)
            clientCal = clientCal.get('calendar_id', None)
            dataTagEvent = []
            if (clientCal):
                clientEvent = formatted_event
                producerCal = postgres.getCalendarID()
                producerCal = producerCal.get('calendar_id', None)
                print('producerCal', producerCal)
                if(not status):
                    clientEvent['summary'] = "Attendees - " + details_event[0].get('event_name')
                    clientEvent['description'] = os.getenv('GCALENDAR_ATTENDEES_LINK', '/') + eventID
                    if (added_attendee and len(added_attendee) > 0):
                        clientEvent['attendees'] = added_attendee
                    event_created = service.events().insert(calendarId=clientCal, body=clientEvent, sendUpdates='all', sendNotifications=True).execute()
                    if (event_created):
                        id_event_attendees = event_created.get('id', None)
                        dataTagEvent.append({
                            'event_id': eventID,
                            'tag_type': 'system',
                            'tag_name': 'Attendee invite',
                            'tag_value': id_event_attendees
                        })

                    print(event_created)
                    clientEvent['summary'] = "Speakers - " + details_event[0].get('event_name')
                    clientEvent['description'] = os.getenv('GCALENDAR_SPEAKERS_LINK', '/') + eventID

                    event_created = service.events().insert(calendarId=clientCal, body=clientEvent, sendUpdates='all', sendNotifications=True).execute()
                    if (event_created):
                        id_event_speakers = event_created.get('id', None)
                        dataTagEvent.append({
                            'event_id': eventID,
                            'tag_type': 'system',
                            'tag_name': 'Speaker invite',
                            'tag_value': id_event_speakers
                        })
                    print(event_created)
                    if (producerCal):
                        prodEvent = formatted_event
                        if (producer_email) :
                            prodEvent['attendees'] = producer_email
                        prodEvent['summary'] = "Producer - " + details_event[0].get('event_name')
                        prodEvent['description'] = os.getenv('GCALENDAR_PRODUCERS_LINK', '/') + eventID
                        print('prodEvent', prodEvent)
                        event_created = service.events().insert(calendarId=producerCal, body=prodEvent,  sendUpdates='all', sendNotifications=True).execute()
                        if (event_created):
                            id_event_producers = event_created.get('id', None)
                            dataTagEvent.append({
                                'event_id': eventID,
                                'tag_type': 'system',
                                'tag_name': 'Producer invite',
                                'tag_value': id_event_producers
                            })
                        print(event_created)
                    else:
                        return "Error, Calendar ID for Producer does not exist in database. Contact developer."
                    if (dataTagEvent and len(dataTagEvent) > 0):
                        print(len(dataTagEvent), dataTagEvent)
                        postgres.upsertEventTagMulti(dataTagEvent)

                else:
                    eventIDs = postgres.listEventTag(eventID)
                    event_id_producer = None
                    if (eventIDs and len(eventIDs) > 0):
                        for e in eventIDs:
                            if (e.get('tag_type', '').lower() == 'system'):
                                if (e.get('tag_name', '').lower() == 'attendee invite'):
                                    event_id_attendee = e.get('tag_value', None)
                                elif (e.get('tag_name', '').lower() == 'speaker invite'):
                                    event_id_speaker = e.get('tag_value', None)
                                elif (e.get('tag_name', '').lower() == 'producer invite'):
                                    event_id_producer = e.get('tag_value', None)
                    if (clientCal and event_id_attendee and event_id_speaker):
                        clientEvent = formatted_event
                        if (status == 'U'):
                            clientEvent['summary'] = "[UPDATE] Attendees - " + details_event[0].get('event_name')
                        else:
                            clientEvent['summary'] = "[CANCEL] Attendees - " + details_event[0].get('event_name')
                        clientEvent['description'] = os.getenv('GCALENDAR_ATTENDEES_LINK', '/') + eventID
                        service.events().update(calendarId=clientCal, eventId=event_id_attendee,body=clientEvent,sendUpdates='all',sendNotifications=True).execute()

                        if (status == 'U'):
                            clientEvent['summary'] = "[UPDATE] Speakers - " + details_event[0].get('event_name')
                        else:
                            clientEvent['summary'] = "[CANCEL] Speakers - " + details_event[0].get('event_name')
                        clientEvent['description'] = os.getenv('GCALENDAR_SPEAKERS_LINK', '/') + eventID
                        service.events().update(calendarId=clientCal, eventId=event_id_speaker,body=clientEvent, sendUpdates='all',sendNotifications=True).execute()
                        print('producerCal', producerCal)
                        print('event_id_producer', event_id_producer)
                        if (producerCal and event_id_producer):
                            prodEvent = formatted_event
                            if (producer_email):
                                prodEvent['attendees'] = producer_email
                            if (status == 'U'):
                                prodEvent['summary'] = "[UPDATE] Producer - " + details_event[0].get('event_name')
                            else:
                                prodEvent['summary'] = "[CANCEL] Producer - " + details_event[0].get('event_name')
                            prodEvent['description'] = os.getenv('GCALENDAR_PRODUCERS_LINK', '/') + eventID
                            print('prodEvent', prodEvent)
                            service.events().update(calendarId=producerCal, eventId=event_id_producer, body=prodEvent, sendUpdates='all',sendNotifications=True).execute()
                        else:
                            return "Error, Calendar ID for Producer does not exist in database. Contact developer."
                    else:
                        return "Error, Google event ID for that event ID does not exist. Contact developer."
            else:
                return "Error, Calendar ID for client does not exist in database. Contact developer"
            return "OK"
        else:
            return None
    except Exception as e:
        errormessage = utils.customError("insert_event", e)
        print(errormessage)
        raise


def formatDataEvent(dataEvent):
    try:
        summary = dataEvent.get('event_name', 'TEST')
        start = dataEvent.get('event_start', None)
        duration = dataEvent.get('duration_minutes', None)
        timeZone = dataEvent.get('time_zone', None)
        if (not(start or duration or summary)):
            return None
        else:
            ianaTimezone = convertTimeZone(timeZone)
            if(not ianaTimezone):
                ianaTimezone = 'America/New_York'
            end = start + datetime.timedelta(minutes=duration)
            start = start.strftime('%Y-%m-%dT%H:%M:%S')
            end = end.strftime('%Y-%m-%dT%H:%M:%S')
            formattedEventData = {
                'summary': summary,
                'start': {
                    'dateTime': start,
                    'timeZone': ianaTimezone,
                },
                'end': {
                    'dateTime': end,
                    'timeZone': ianaTimezone,
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ]
                },
                'sendNotifications': True,
                'sendUpdates': 'all'
            }
            return formattedEventData
    except Exception as e:
        errormessage = utils.customError("formatDataEvent", e)
        print(errormessage)
        raise

def convertTimeZone(timezone):
    try:
        mapTZ = {
            'EST': 'America/New_York',
            'CET': 'Europe/Paris'
        }
        return mapTZ.get(timezone,None)
    except Exception as e:
        errormessage = utils.customError("convertTimeZone", e)
        print(errormessage)
        raise

if __name__ == '__main__':
    print('main')
