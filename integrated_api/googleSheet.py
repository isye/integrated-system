from __future__ import print_function
import datetime, os
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from integrated_api import utils
from flask import current_app as app, g

SCOPES = 'https://www.googleapis.com/auth/spreadsheets'

def getSheetService():
    try:
        if 'sheetservice' not in g:
            token_path = os.getenv('GSHEET_TOKEN', '')
            credential_path = os.getenv('GSHEET_CREDENTIALS', '')
            store = file.Storage(token_path)
            creds = store.get()
            if not creds or creds.invalid:
                flow = client.flow_from_clientsecrets(credential_path, SCOPES)
                creds = tools.run_flow(flow, store)
            g.sheetservice = build('sheets', 'v4', http=creds.authorize(Http()))
        return g.sheetservice
    except Exception as e:
        errormessage = utils.customError("getSheetService", e)
        print(errormessage)
        raise

def getProgramList(SpreadSheetID, LiveSheet):
    try:
        liveValues = getSheetValues(SpreadSheetID, LiveSheet)
        if (liveValues and len(liveValues) > 1):
            keys = liveValues[0]
            values = liveValues[1:]
            values = [v for v in values if len(v)>1 and len(v[1])>0]
            programList = [{keys[i]: r[i] for i in range(0, len(keys))} for r in values]
            return programList
        else:
            return None
    except Exception as e:
        errormessage = utils.customError("getProgramList", e)
        print(errormessage)
        raise

def getSheetValues(SpreadSheetID, SheetRange):
    try:
        print(SpreadSheetID, SheetRange)
        service = getSheetService()
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SpreadSheetID, range=SheetRange).execute()
        values = result.get('values', [])
        return values
    except Exception as e:
        errormessage = utils.customError("getSheetValues", e)
        print(errormessage)
        raise

def writeHistory(data, SPREADSHEET_ID, RANGE_NAME):
    try:
        service = getSheetService()
        sheetRequest = service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
                                                         valueInputOption='RAW',
                                                         insertDataOption='INSERT_ROWS', body=data)
        response = sheetRequest.execute()
        return response
    except Exception as e:
        errormessage = utils.customError("writeHistory", e)
        print(errormessage)
        raise

def emailVerification(data, SPREADSHEET_ID, LIVE_SHEET):
    try:
        program_id = str(data.get('program_id', None)).strip()
        email = str(data.get('email', None)).strip().lower()
        first_name = str(data.get('first_name', ''))
        last_name = str(data.get('last_name', ''))
        now = datetime.datetime.utcnow()
        now = now.strftime("%a, %d %b %Y %H:%M:%S")
        status = 'N'
        service = getSheetService()
        if(program_id and email):
            sheet = service.spreadsheets()
            liveValues = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=LIVE_SHEET).execute()
            liveValues = liveValues.get('values', None)
            if(liveValues):
                liveValues = liveValues[1:]
                liveValues = [v for v in liveValues if len(v) > 1 and len(v[1]) > 0]
                record = [l for l in liveValues if (l[4].strip()==program_id.strip())]
                if (len(record)>0):
                    #check email
                    emailValues = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=program_id).execute()
                    emailValues = emailValues.get('values', None)
                    if(emailValues):
                        emailValues = emailValues[1:]
                        emailValues = [e[0].lower() for e in emailValues]
                        if(email in emailValues):
                            acLink = str(record[0][2]).strip()
                            if(acLink and acLink.startswith("http")):
                                status = 'Y'
                                acLink = acLink + '?guestName=' + first_name + '%20' + last_name + '&proto=true'
                                msg = acLink
                            else:
                                msg =  "Link EOD/Webcast is not found"
                        else:
                            msg =  "This email address is not registered for this event. The email address must be entered exactly as it was upon registration."
                else:
                    msg =  "Incorrect Program ID, please check your email notification and try again."
            else:
                msg = "There is no LIVE information. Check LIVE sheet."
        else:
            msg = "There is no Program ID information in the data"
        data = [now +" GMT", first_name, last_name, email, status, program_id]

        data = {"values": [data]}

        sheetRequest = service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID, range='History',
                                                              valueInputOption='RAW',
                                                              insertDataOption='INSERT_ROWS', body=data)
        sheetRequest.execute()
        return msg
    except Exception as e:
        errormessage = utils.customError("emailVerification", e)
        print(errormessage)
        raise

if __name__ == '__main__':
    now = datetime.datetime.utcnow()
    print(now, type(now), now.strftime("%a, %d %b %Y %H:%M:%S"))
