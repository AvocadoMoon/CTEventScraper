from google.auth.transport.requests import Request
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from src.publishers.mobilizon.types import MobilizonEvent, EventParameters
import os
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from src.logger import logger_name
import copy


logger = logging.getLogger(logger_name)

# Subscribe to the calendars
# https://webapps.stackexchange.com/questions/5217/how-can-i-find-the-subscribe-url-from-the-google-calendar-embed-source-code
# http://www.google.com/calendar/feeds/HERE/public/basic

# Bike Shop Source 
# bsbc.co_c4dt5esnmutedv7p3nu01aerhk@group.calendar.google.com

# Save The Sound Source
# ctenvironment@gmail.com

# Google API Documentation
# https://console.cloud.google.com/apis/credentials/consent
# https://developers.google.com/calendar/api/quickstart/python
# https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/calendar_v3.events.html#list


class ExpiredToken(Exception):
    pass


class GCalAPI:
    _apiClient: Resource
    
    def __init__(self):
        pass
    
    def init_calendar_read_client_browser(self, token_path: str):
        logger.info("Logged in Google Cal Browser")
        SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
        credentialTokens = None
        if os.path.exists(token_path):
            credentialTokens = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not credentialTokens or not credentialTokens.valid:
            try: 
                if credentialTokens and credentialTokens.expired and credentialTokens.refresh_token:
                    credentialTokens.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                            f"{os.getcwd()}/config/OAuthClientApp.json", SCOPES
                        )
                    credentialTokens = flow.run_local_server(port=9000)
                
                # When refreshed authentication token needs to be re-written, and if authenticating for the first time it needs to be just written
                with open(token_path, "w") as tokenFile:
                    tokenFile.write(credentialTokens.to_json())
            except Exception:
                raise ExpiredToken
        self._apiClient = build("calendar", "v3", credentials=credentialTokens)

    
    def init_calendar_read_client_adc(self):
        logger.info("Logged In Google Cal ADC")
        credentials, projectID = google.auth.default()
        
        self._apiClient = build("calendar", "v3", credentials=credentials)
    

    def getAllEventsAWeekFromNow(self, eventKernel: MobilizonEvent, calendarId: str,
                                 checkCacheFunction,
                                 dateOfLastEventScraped: datetime = None) -> [MobilizonEvent]:
        """Get events all events for that specific calender a week from today.

        Args:
            service (Resource): Calender resource available from creating a client with 'read calender' scope
            calendarId (str): UUID of calender. Same ID used to subscribe to a calender
            dateOfLastEventScraped (str, optional): UTC date with timedelta following isoformat. Have to add 'Z' to isoformat to indicate its UTC time. Defaults to None.
        """
        try:
            # Call the Calendar API, 'Z' indicates UTC time
            stringDateLastEvent = datetime.utcnow().astimezone().isoformat()
            if dateOfLastEventScraped is not None: 
                stringDateLastEvent = dateOfLastEventScraped.isoformat()
            logger.debug(f"Time of last event: {stringDateLastEvent}")
            weekFromNow = datetime.utcnow().astimezone() + timedelta(days=7)
            weekFromNow = weekFromNow.isoformat()
            
            events_result = (
                self._apiClient.events()
                .list(
                    calendarId=calendarId,
                    timeMin=stringDateLastEvent,
                    timeMax=weekFromNow,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            googleEvents = events_result.get("items", [])
            if len(googleEvents) == 0:
                logger.info(f"No upcoming events for calendarID {calendarId}\n")
                return googleEvents

            events = []
            for googleEvent in googleEvents:
                _process_google_event(googleEvent=googleEvent, eventsToUpload=events,
                                    checkCacheForEvent=checkCacheFunction,calendarId=calendarId,
                                    eventKernel=copy.deepcopy(eventKernel))
            
            return events
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
    
    def close(self):
        self._apiClient.close()





def _process_google_event(googleEvent: dict, eventsToUpload: [], checkCacheForEvent, 
                          calendarId: str, eventKernel):
    
    starTimeGoogleEvent = googleEvent["start"].get("dateTime")
    endTimeGooglEvent = googleEvent["end"].get("dateTime")
    title = googleEvent.get("summary")
    description = googleEvent.get("description")

    
    if None not in [starTimeGoogleEvent, endTimeGooglEvent, title, description]:
        startDateTime = datetime.fromisoformat(starTimeGoogleEvent.replace('Z', '+00:00')).astimezone()
        endDateTime = datetime.fromisoformat(endTimeGooglEvent.replace('Z', '+00:00')).astimezone()
        if not checkCacheForEvent(startDateTime.isoformat(), title, calendarId):
            eventAddress = _parse_google_location(googleEvent.get("location"), eventKernel.physicalAddress, title)
            eventKernel.beginsOn = startDateTime.isoformat()
            eventKernel.endsOn = endDateTime.isoformat()
            eventKernel.physicalAddress = eventAddress
            eventKernel.title = title
            eventKernel.description = f"Automatically scraped by Event Bot: \n\n{description}"
            eventsToUpload.append(eventKernel)
            

def _parse_google_location(location:str, default_location: EventParameters.Address, event_title: str):
    if location is None and default_location is not None:
        logger.debug("No location provided, using default")
        return default_location
    if location is None:
        return None
    tokens = location.split(",")
    address: EventParameters.Address = None
    match len(tokens):
        case 1:
            return default_location
        case 2:
            return default_location
        case 3:
            address = EventParameters.Address(locality=tokens[0], postalCode=tokens[1], street="", country=tokens[2])
        case 4:
            address = EventParameters.Address(locality=tokens[1], postalCode=tokens[2], street=tokens[0], country=tokens[3])
        case 5:
            address = EventParameters.Address(locality=tokens[2], postalCode=tokens[3], street=tokens[1], country=tokens[4])
        case _:
            return None

    # Address given is default, so don't need to call Nominatim
    if (default_location is not None and default_location.locality in location
        and default_location.street in location and default_location.postalCode in location):
        logger.debug(f"{event_title} location included with calendar, but is same as default location.")
        return default_location
    
    try:
        geo_locator = Nominatim(user_agent="Mobilizon Event Bot", timeout=10)
        geo_code_location = geo_locator.geocode(f"{address.street}, {address.locality}, {address.postalCode}")
        if geo_code_location is None:
            return None
        address.geom = f"{geo_code_location.longitude};{geo_code_location.latitude}"
        logger.info(f"{event_title}: Outsourced location was {address.street}, {address.locality}")
        return address
    except GeocoderTimedOut:
        return None
    

if __name__ == "__main__":
    gcal = GCalAPI()
    google_token_path = os.environ.get("GOOGLE_API_TOKEN_PATH")
    gcal.init_calendar_read_client_browser(google_token_path)

