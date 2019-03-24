from flask import (
    Blueprint, request
)
import flask
import json
from integrated_api import postgres, utils, googleCalendar


bp = Blueprint('api_v2', __name__, url_prefix='/api/v2')

@bp.route('/calendars/', methods=['POST', 'DELETE', 'PUT', 'GET'])
def calendars():
    try:
        requestBody = utils.getJSONBody(request.get_data(as_text=True))
        if(request.method in ('POST', 'DELETE', 'PUT')):
            if (len(requestBody) == 0):
                return "Error, you use POST, DELETE or PUT method but data empty. Check API documentation"
            else:
                if(request.method=='POST'):
                    summary = requestBody.get('summary', None)
                    if(summary):
                        timeZone = requestBody.get('time_zone', None)
                        if(timeZone):
                            created_calendar = googleCalendar.createCalendar(summary, timeZone)
                        else:
                            created_calendar = googleCalendar.createCalendar(summary)
                        data = {
                            'calendar_id' : created_calendar['id'],
                            'calendar_name' : created_calendar['summary'],
                            'platform_id': 'Google Calendar'
                        }
                        data =  postgres.upsertCalendar(data)
                        data = json.dumps(created_calendar, default=str)
                    else:
                        return "Error, creating calendar need summary and timezone"
                elif (request.method in ('DELETE', 'PUT')):
                    calendarID = requestBody.get('id', None)
                    if(calendarID):
                        if(request.method=='DELETE'):
                            edited_calendar = googleCalendar.deleteCalendar(calendarID)
                            edited_calendar = postgres.deleteCalendar(calendarID)
                        elif(request.method=='PUT'):
                            edited_calendar = googleCalendar.updateCalendar(data=requestBody)
                        else:
                            return "Error, unrecognized request method"
                        data = json.dumps(edited_calendar, default=str)
                    else:
                        return "Error, deleting or updatingcalendar need calendar ID"
        else:
            data = json.dumps(googleCalendar.listCalendar(), default=str)
        response = flask.Response(data)
        response.headers = {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        }
        return response
    except Exception as e:
        errormessage = utils.customError("calendars", e)
        return errormessage

@bp.route('/scheduled_events/', methods=['POST', 'PATCH', 'PUT', 'GET'])
def scheduled_events():
    try:
        requestBody = utils.getJSONBody(request.get_data(as_text=True))
        if (request.method in ('POST', 'DELETE', 'PUT')):
            if (len(requestBody) == 0):
                return "Error, you use POST, DELETE or PUT method but data empty. Check API documentation"
            else:
                eventID = requestBody.get('event_id', None)
                if (eventID):
                    if(request.method=='POST'):
                        data = googleCalendar.upsertEvent(requestBody)
                        data = json.dumps(data, default=str)
                        response = flask.Response(data)
                        response.headers = {
                            'Access-Control-Allow-Origin': '*',
                            'Content-Type': 'application/json'
                        }
                        return response
                    elif (request.method in ('PATCH', 'PUT')):
                        status = requestBody.get('status', None)
                        if(status in ('U', 'C')):
                            data = googleCalendar.upsertEvent(requestBody, status)
                            data = json.dumps(data, default=str)
                            response = flask.Response(data)
                            response.headers = {
                                'Access-Control-Allow-Origin': '*',
                                'Content-Type': 'application/json'
                            }
                            return response
                        else:
                            return "Error, status update should be in 'U' for update and 'C' for cancel"
                else:
                    return "Error, event ID is required."
        else:
            pass
    except Exception as e:
        errormessage = utils.customError("scheduled_events", e)
        return errormessage

@bp.route('/persons/<string:personID>', methods=['GET'])
def retrieve_person(personID):
    try:

        if (personID):
            data = postgres.listPerson(personID=personID)
        else:
            data = None
        data = json.dumps(data, default=str)
        response = flask.Response(data)
        response.headers = {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        }
        return response
    except Exception as e:
        errormessage = utils.customError("list-event", e)
        return errormessage

@bp.route('/persons/', methods=['GET', 'POST', 'PUT'])
def persons():
    try:
        print(request.method)
        print(request.args.get('personID', None))
        requestBody = utils.getJSONBody(request.get_data(as_text=True))
        if(request.method in ('POST', 'PUT')):
            if(len(requestBody)<=0):
                return "Error, you use POST or PATCH method but data empty. Check API documentation"
            if request.method == 'POST':
                if(requestBody.get('person_id',None)):
                    del requestBody['person_id']
            data = json.dumps(postgres.upsertPerson(data=requestBody), default=str)
        else:
            print(request.method)
            personID = request.args.get('personID', None)
            print(personID)
            if (personID):
                data = json.dumps(postgres.listPerson(personID=personID), default=str)
            else:
                data = json.dumps(postgres.listPerson(), default=str)
        response = flask.Response(data)
        response.headers = {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        }
        return response
    except Exception as e:
        errormessage = utils.customError("persons", e)
        return errormessage
