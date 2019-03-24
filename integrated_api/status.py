import datetime, re, uuid
from integrated_api import utils

def computeBussDayDiff(start, end):
    try:
        if (end > start):
            daygenerator = (start + datetime.timedelta(x + 1) for x in range((end - start).days))
            return sum(1 for day in daygenerator if day.weekday() < 5)
        else:
            print('Event date can not be the past')
            return None
    except Exception as e:
        errormessage = utils.customError("computeBussDayDiff", e)
        return errormessage

def clientStatus(eventDate):
    try:
        now = datetime.datetime.now().date()
        eventDate = str(eventDate)
        p = re.compile(r'\d{2}:\d{2}:\d{2}')
        print('p', p, p.search(str(eventDate)))
        if (p.search(eventDate)):
            eventDate = eventDate[0:eventDate.rfind(":", 0, len(eventDate))]
        eventDate = datetime.datetime.strptime(eventDate, '%Y-%m-%d %I:%M').date()
        if(eventDate>now):
            diff = computeBussDayDiff(now, eventDate)
            if(diff<=2):
                return "urgent"
            else:
                return "request"
        else:
            return "request"
    except Exception as e:
        errormessage = utils.customError("clientStatus", e)
        print(errormessage)
        return None

if __name__=='__main__':
    print(uuid.uuid4())

