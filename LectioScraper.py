
from __future__ import print_function
import requests
import re
from bs4 import BeautifulSoup
import httplib2
import os
import base64

from googleapiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from googleapiclient.errors import HttpError


import datetime
from datetime import tzinfo, timedelta, datetime


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


skoleid = ""
lærerid = ""
uger = 4
c_id = ""

weekNumber = datetime.today().isocalendar()[1]
weekNumber = "{:02}".format(weekNumber)


def google_create(event, idd): #kode der bruges til at lave en event i google
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	service = discovery.build('calendar', 'v3', http=http)

	try: 
			event = service.events().insert(calendarId=c_id, body=event).execute()
	except HttpError as err:
			if err.resp.status == 409:
					event = service.events().get(calendarId=c_id, eventId=idd).execute()
					updated_event = service.events().update(calendarId=c_id, eventId=event['id'], body=event).execute()


			else:
					raise err

def getidid (ido): #definerer den enkelte skemabriks id. 
	idd = str(ido)
	
	idd = re.sub("[^0-9]", "", idd)
	idd = "lectioscraperdk" + idd
	return idd

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def splitdates(dato): #bruges til at splitte lectio skemaet op i bidder.
	dayend = dato.index('/')
	dag = str(dato)[0:dayend]
	dag = int(dag)
	monthend = dato.index('-')
	maned = str(dato)[dayend + 1:monthend]
	maned = int(maned)
	yearend = dato.index(' ')
	aar = str(dato)[monthend+1:yearend]
	aar = int(aar)
	## startime first digits
	timerbegin = str(dato).index(":") -2
	timerend = str(dato).index(":") 
	timer = str(dato)[timerbegin:timerend]
	timer = int(timer)
	# start time last digits
	minutterbegin = str(dato).index(":") +1
	minutterend = str(dato).index(":") +3
	minutter = str(dato)[minutterbegin:minutterend]
	minutter = int(minutter)
	return (aar ,maned, dag, timer, minutter)


def getugeskema(url): 
	url.status_code
	url.headers
	c = url.content
	soup = BeautifulSoup(c, "lxml")
	skemabrik = soup.find_all("a", "s2skemabrik") #finder alle skemabrikker

	#søger skemabrikkerne
	for link in skemabrik:
		ido = (link.get("href"))
		link = str(link)
		if ido:  #hvis der er id
			if "Hele dagen" not in link: #sørger for at topbrikkerne topbrikkerne kommer frem
				date = re.search("\d{1,2}/\d{1,2}-\d{4} (?:Hele dagen|\d{2}:\d{2} til "
	                      		"(?:\d{1,2}/\d{1,2}-\d{4} )?\d{2}:\d{2})", link)
				dateLenght = len(str(date[0]))
				print (dateLenght)
				if dateLenght < 27: #hvis aktiviteten kun er på en dag. 
					endDate = date[0]
					beginDate = date[0]
					dateSplit = date[0].index('til')
					dateEnd = len(date[0])
					beginDate = str(beginDate)[0:dateSplit-1]
					print(beginDate)
					year, month, day,starttimef,starttimel = splitdates(beginDate)
					endDate = str(endDate)[dateSplit+4:dateEnd]
					endDate = str(day) + "/" + str(month) + "-" + str(year) +" " + str(endDate)
					print(endDate)
					endyear, endmonth, endday,endftime,endltime = splitdates(endDate)
					
				if dateLenght > 27: #hvis aktiviteten fylder flere dage.
					print(date[0])
					endDate = date[0]
					beginDate = date[0]
					dateSplit = date[0].index('til')
					dateEnd = len(date[0])
					endDate = str(endDate)[dateSplit+4:dateEnd]
					beginDate = str(beginDate)[0:dateSplit-1]
					endyear, endmonth, endday,endftime,endltime = splitdates(endDate)
					year, month, day,starttimef,starttimel = splitdates(beginDate)
					
				
				

				#fjerner uvigtige dele af infoformationem
				link = link.replace(str(date[0]), "")
				link = (link.replace('"', ' ', 3))
				s='data-additionalinfo='
				linkfirst = link.rindex(s) + len(s) +1
				linklast = link.index('" ')
				lectioinfo = str(link)[linkfirst:linklast]
				lectioinfo = lectioinfo.replace("Ændret!", "")
				idd =  getidid(ido)
				event = {
					 'summary': lectioinfo,
					 'id': idd,
					# 'location': 'København',
					# 'description': 'A chance to hear more about Google\'s developer products.',
					 'start': {
					   'dateTime': str(datetime(year, month, day,starttimef,starttimel).isoformat('T')),
					   'timeZone': 'Europe/Copenhagen',
					 },
					 'end': {
					   'dateTime': str(datetime(endyear, endmonth, endday,endftime,endltime).isoformat('T')),
					   'timeZone': 'Europe/Copenhagen',
					   'status': 'confirmed'
					 },

				}
				if "Aflyst" not in link: #eksporterer elementer som ikke er aflyst
				
					
					print ("Følgende modul er eksporteret:")
					print (event)
					print ("")			
					google_create(event, idd)
					
													
				if "Aflyst!" in link: #sætter status til aflyst i lectio. Stopper ikke, hvis det aktiviteten allerede er slettet i google.. 
					idd =  getidid(ido)
					credentials = get_credentials()
					http = credentials.authorize(httplib2.Http())
					service = discovery.build('calendar', 'v3', http=http)
					try: 
						event = service.events().get(calendarId=c_id, eventId=idd).execute()
						event['status'] = 'cancelled'
						updated_event = service.events().update(calendarId=c_id, eventId=event['id'], body=event).execute()
					except HttpError as err:
							if err.resp.status == 404:
								print ("aflyst")
							else:
								raise err
				if "Ændret!" in link:
					idd =  getidid(ido)
					credentials = get_credentials()
					http = credentials.authorize(httplib2.Http())
					service = discovery.build('calendar', 'v3', http=http)
					try: 
						event = service.events().get(calendarId=c_id, eventId=idd).execute()
						event = {
				 			'summary': lectioinfo,
				 			'id': idd,
							# 'location': 'København',
							# 'description': 'A chance to hear more about Google\'s developer products.',
				 			'start': {
				   			'dateTime': str(datetime(year, month, day,starttimef,starttimel).isoformat('T')),
				   			'timeZone': 'Europe/Copenhagen',
				 			},
				 			'end': {
				   			'dateTime': str(datetime(endyear, endmonth, endday,endftime,endltime).isoformat('T')),
				   			'timeZone': 'Europe/Copenhagen',
				   			'status': 'confirmed'
				 			},

						}




						updated_event = service.events().update(calendarId=c_id, eventId=event['id'], body=event).execute()
					except HttpError as err:
							if err.resp.status == 404:
								print ("aflyst")
							else:
								raise err


# programmet ekseveres.
get_credentials()
i = 0
while i < uger:
	print (i)
	weekNumberGet = int(weekNumber)+i
	weekNumberGet = "{:02}".format(weekNumberGet)
	print ("Nu hentes skemaet fra uge nr." + weekNumberGet)
	url = "https://www.lectio.dk/lectio/63/SkemaNy.aspx?&week={}{}".format(str(weekNumberGet), datetime.today().year)
	url = requests.get(url, params=params,headers=headers, cookies=cookies)
	getugeskema(url)
	i = i+1