from flask import (
    Blueprint, request, redirect, url_for,make_response, current_app as app
)
import flask
import json, os
from flask_cors import  cross_origin
from integrated_api import utils, googleSheet

bp = Blueprint('landingPage', __name__, url_prefix='/api/v2')

@bp.route('/live-events/<string:eventType>', methods=['GET'])
def live_events(eventType='eod'):
    print(eventType)
    try:
        liveSheet = os.getenv('LIVE_SHEET', '')
        if(eventType=='webcast'):
            spreadSheetID = os.getenv('GSHEET_WEBCAST', '')
        elif(eventType=='eod'):
            spreadSheetID = os.getenv('GSHEET_EOD', '')
        else:
            return "Error, worksheet is not recognized"
        data = json.dumps(googleSheet.getProgramList(SpreadSheetID=spreadSheetID, LiveSheet=liveSheet), default=str)
        response = flask.Response(data)
        response.headers = {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        }
        return response
    except Exception as e:
        errormessage = utils.customError("live_events", e)
        print(errormessage)
        return errormessage

@bp.route('/email-verification/', methods=['POST'])
@cross_origin(allow_headers=['Content-Type'])
def email_verification():
    try:
        data = utils.getJSONBody(request.get_data(as_text=True))
        if(len(data)==0):
            return "Error, email data is empty."
        eventType = data.get('event_type', None)
        if(not eventType):
            return  "Error, event type (eod or webcast) should be set."
        if (eventType=='eod'):
            spreadSheetID = os.getenv('GSHEET_EOD', '')
        elif(eventType=='webcast'):
            spreadSheetID = os.getenv('GSHEET_WEBCAST', '')
        else:
            return "Error, event type should be in 'eod' or 'webcast'"
        liveSheet = os.getenv('LIVE_SHEET', '')

        userAgent = str(request.user_agent).lower()
        if('form.io' in userAgent):
            data = data.get('request', None)
            if(data):
                data = data.get('data', None)

        if (data):
          result = googleSheet.emailVerification(data=data, SPREADSHEET_ID=spreadSheetID, LIVE_SHEET=liveSheet)
          print(userAgent, result)
          data = json.dumps(result, default=str)
          response = flask.Response(data)
          response.headers = {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
          }
          return response
        else:
            response = flask.Response('Data request is not correct')
            response.headers = {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            }
            return response
    except Exception as e:
        errormessage = utils.customError("email_verification", e)
        print(errormessage)
        return errormessage

@bp.after_request # blueprint can also be app~~
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response

