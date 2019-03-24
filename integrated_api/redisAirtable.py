import redis
from flask import current_app as app, g, jsonify
import requests, json, time, pdb, os

def get_redisdb():
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    if 'reds' not in g:
        g.reds = redis.from_url(redis_url)
    return g.reds


def flush_redis(e=None):
    reds = g.pop('reds', None)
    if reds is not None:
        reds.flushdb()

def storeInRedis(jsonrecord, datasetName):
    try:
        reds = get_redisdb()
        reds.set(datasetName, json.dumps(jsonrecord))

    except Exception as e:
        print(e)

def pullAndStoreAirtableData(tableName, varURL):
    try:
        print("will pull from airtable for data:", tableName)

        url = varURL + tableName + "?view=Grid%20view"

        headers = {
            'Authorization': "Bearer " + os.getenv("AIRTABLE_KEY","")
        }

        response = requests.request("GET", url, headers=headers)
        records_airtable = []
        if(response.status_code==200):
            data_json = json.loads(response.content)

            if ('records' in data_json.keys()):
                records_airtable = data_json['records']
                if ('offset' in data_json.keys()):
                    offset = data_json['offset']
                else:
                    offset = None

                while (offset is not None):
                    next_url = url + '?offset=' + offset
                    time.sleep(5)
                    response = requests.request("GET", next_url, headers=headers)
                    data_json = json.loads(response.content)
                    if ('records' in data_json.keys()):
                        records_airtable = records_airtable + data_json['records']
                    if ('offset' in data_json.keys()):
                        offset = data_json['offset']
                    else:
                        offset = None
            storeInRedis(records_airtable, tableName)
    except Exception as e:
        print(e)

def getDataset(datasetName):
    #to get all data: Attendees, Events, Event_Attendees, Video_URL
    try:
        reds = get_redisdb()
        data = reds.get(datasetName)
        if (data is None or len(data)==0) :
            pullAndStoreAirtableData(datasetName,os.getenv('AIRTABLE_URL',""))
            data = reds.get(datasetName)
        return json.loads('{ "records":' + data.decode('utf-8') + '}')
    except Exception as e:
        print(e)

def addRecord(databaseName, tableName, record):
    try:
        if (record is not None):
            url = databaseName + tableName
            headers_airtable = {
                'Authorization': "Bearer " + os.getenv("AIRTABLE_KEY", ""),
                'Content-type': "application/json"
            }
            response = requests.request("POST", url, data=record, headers=headers_airtable)
        else:
            print('request Body is None')

        return 'ok, add record' + str(response.status_code)
    except Exception as e:
        print(e)

#edit record in Airtable
def editRecord(databaseName, tableName, record, additionalParams=None):
    try:
        if (record is not None):
            url = databaseName + tableName
            if(additionalParams is not None):
                url = url + '/' + additionalParams
            headers_airtable = {
                'Authorization': "Bearer " + os.getenv("AIRTABLE_KEY", ""),
                'Content-type': "application/json"
            }
            response = requests.request("PUT", url, data=record, headers=headers_airtable)
        else:
            print('request Body is None')

        return 'ok, edit record' + str(response.status_code)
    except Exception as e:
        print(e)
