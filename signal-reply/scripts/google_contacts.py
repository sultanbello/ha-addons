from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.api_core import exceptions
import os
import pickle
import sys
import json
from pathlib import Path
import time
import urllib
import lxml.etree

class Contacts:
    def __init__(self, parent):
        try:
            self.parent     = parent

            self.creds      = self.auth()

            # Fetch a list of country - languagues
            self.country_languagues()

            self.messages   = {}
            for message in self.parent.messages:
                # add an empty array if the current languague is not there yet
                if not message['languague'].lower() in self.messages:
                    self.messages[message['languague'].lower()] = []

                # Add the message to the languague array
                self.messages[message['languague'].lower()].append(message['message'])

            self.connections    = {}

            self.get_contacts()
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

    def auth(self):
        try:
            # If modifying these scopes, delete the file token.json.
            SCOPES      = [
                'https://www.googleapis.com/auth/contacts', 
                'https://www.googleapis.com/auth/gmail.send'
            ]

            creds               = None
            token_file	        = '/data/token.pickle'
            credentials_file	= '/data/credentials.json'
            
            if self.parent.local:
                token_file	        = os.path.dirname(os.path.realpath(__file__))+'\\data\\token.pickle'
                credentials_file	= os.path.dirname(os.path.realpath(__file__))+'\\data\\credentials.json' 

            # credentials do not exist yet
            file = Path(credentials_file)
            if not file.is_file():
                self.parent.logger.debug(f"Creating {credentials_file}")
                content = {
                    "installed":
                        {
                            "client_id":                    self.parent.client_id,
                            "project_id":                   self.parent.project_id,
                            "auth_uri":                     "https://accounts.google.com/o/oauth2/auth",
                            "token_uri":                    "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url":  "https://www.googleapis.com/oauth2/v1/certs",
                            "client_secret":                self.parent.client_secret,
                            "redirect_uris":
                                [
                                    "http://localhost",
                                    "http://localhost:{self.parent.port}/"
                                ]
                        }
                }

                with open(credentials_file, "w") as f:
                    json.dump(content, f)

            # The file token.pickle stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            if os.path.exists(token_file):
                #self.parent.logger.debug(f"Tokenfile {token_file} does exist")
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)

                #self.parent.logger.debug(f"Creds: {creds.to_json()}")
            else:
                self.parent.logger.debug(f"Token file {token_file} does not exist")

            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                self.parent.logger.debug(f"Creds are not valid")

                if creds and creds.expired and creds.refresh_token:
                    self.parent.logger.debug(f"Refreshing token")
                    try:
                        creds.refresh(Request())
                    except exceptions.RetryError as e:
                        # Handles errors when retries have been exhausted
                        self.parent.logger.error(f"Retry error: {e}")
                        time.sleep(10)
                        return self.auth()
                        
                    except exceptions.GoogleAPICallError as e:
                        # Handles any other API errors
                        self.parent.logger.error(f"An API error occurred: {e}")
                    except Exception as e:
                        # Handles any other exceptions
                        self.parent.logger.error(f"An unexpected error occurred: {e}")
                else:
                    self.parent.logger.debug(f'Listening for token on port {self.parent.port}')
                    self.parent.logger.info('########################')
                    flow    = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)

                    try:
                        creds   = flow.run_local_server(bind_addr="0.0.0.0", open_browser=False, port=self.parent.port, timeout_seconds=600)
                    except Exception as e:
                        self.parent.logger.error(e)
                        self.parent.logger.error("Please restart this addon and try again")
            
                    self.parent.logger.info('########################')
                    self.parent.logger.info('')

                self.parent.logger.debug(f"Creds refresh token: {creds.refresh_token}")

                self.parent.logger.debug(f"Creds: {creds.to_json()}")

                # Save the credentials for the next run
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)

            self.service = build('people', 'v1', credentials = creds)

            return creds
        except Exception as e:
            self.auth_running = False
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

    def get_contacts(self):
        try:
            # Only fetch once every 24 hours
            #if 'time' in self.connections and self.connections['time'] > time.time() - 86400:
                #return self.connections['connections']
    
            if self.parent.google_label == '':
                return False
    
            # Get Google Labels
            result  = self.get_labels()
    
            if not result:
                return False

            self.parent.logger.info(f"Getting Google contacts belonging to the label '{self.parent.google_label}'")

            # Call the People API
            fields  = 'names,locales,phoneNumbers,addresses,userDefined'
            results = self.service.people().getBatchGet(resourceNames=self.members, personFields=fields).execute()["responses"]

            # Store for future use
            self.connections['time']        = time.time()

            phonenumbers            = {}
            
            #self.parent.logger.debug(connections)
            for result in results:
                contact = result.get('person', [])
                
                if 'phoneNumbers' in contact:                    
                    data    = {}
                    if 'names' in contact:
                        data['name']        = contact.get('names')[0].get('displayName')
                        data['firstname']   = contact.get('names')[0].get('givenName')

                    if 'addresses' in contact:
                        data['country']    = contact.get('addresses')[0].get('countryCode')

                    # personal languague set, and there is a message in that languague
                    if 'languague' in contact and contact['languague'] in self.messages['languague']:
                        data['languague']   = contact['languague']
                    else:
                        data['languague']   = self.get_languague(data.get('country'))
                    
                    for nr in contact['phoneNumbers']:
                        phonenumbers[nr.get('canonicalForm')]    = data


            self.connections['phonenumbers'] = phonenumbers

        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

    def get_labels(self):
        if self.parent.google_label == '':
            self.parent.logger.debug(f'No label set')
            return False
        
        results     = self.service.contactGroups().list(pageSize=1000).execute()
        labels      = results.get('contactGroups', [])

        if not labels:
            self.parent.logger.warning('No contact labels found.')

            return False
        else:
            # Find the requested group
            for label in labels:
                # This is the group we want
                if label.get('name').lower() == self.parent.google_label.lower():
                    # Get the members of this group
                    self.members = self.service.contactGroups().get(resourceName=label.get('resourceName'), maxMembers=1000).execute()['memberResourceNames']

                    self.parent.logger.debug(f'Label "{self.parent.google_label}" found')
                    
                    return self.members
                
        self.parent.logger.error(f'Label "{self.parent.google_label}" not found!')

        return False

    def country_languagues(self):
        try:
            url         = "https://raw.githubusercontent.com/unicode-org/cldr/master/common/supplemental/supplementalData.xml"
            langxml     = urllib.request.urlopen(url)
            langtree    = lxml.etree.XML(langxml.read())

            self.languagues = {}
            for t in langtree.find('territoryInfo').findall('territory'):
                langs = {}
                for l in t.findall('languagePopulation'):
                    # If this is an official languague
                    if bool(l.get('officialStatus')):
                        langs[l.get('type')] = float(l.get('populationPercent'))
                self.languagues[t.get('type')] = langs
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

    def get_languague(self, country_code):
        try:
            if country_code in self.languagues:
                # all the official languagues of this country
                languagues  = self.languagues.get(country_code)

                for languague in languagues:
                    # we have a message in this languague
                    if languague in self.messages:
                        return languague
                
                # we should only come here if we do not have a message in the languague needed
                self.parent.logger.warning(f"Could not find a message in any of the languagues for country {country_code}.\nDefaulting to English")
                return 'en'
            
            # we should only come here if we do not have a message in the languague needed
            self.parent.logger.error(f"Invalid country {country_code}. Defaulting to English languague")
            return 'en'
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")
        
