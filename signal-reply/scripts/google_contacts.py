from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
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
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

        self.creds          = self.auth()

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

    def connect(self):
        self.gmail_service  = build('gmail', 'v1', credentials=self.creds)
    
    def link(uri, label=None):
        if label is None:
            label = uri
        
        parameters = ''
        escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'
        
        return escape_mask.format(parameters, uri, label)

    def auth(self):
        try:
            # If modifying these scopes, delete the file token.json.
            SCOPES      = [
                'https://www.googleapis.com/auth/contacts'
            ]

            creds               = None
            token_file	        = '/share/google/token.pickle'
            credentials_file	= '/share/google/credentials.json'

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
                self.parent.logger.debug(f"Tokenfile {token_file} does exist")
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)

                self.parent.logger.debug(f"Creds: {creds.to_json()}")
            else:
                self.parent.logger.debug(f"Token file {token_file} does not exist")

            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                self.parent.logger.debug(f"Creds are not valid")

                if creds and creds.expired and creds.refresh_token:
                    self.parent.logger.debug(f"Refreshing token")

                    creds.refresh(Request())
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

            return creds
        except Exception as e:
            self.auth_running = False
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

    def get_contacts(self):
        # Only fetch once every 24 hours
        if 'time' in self.connections and self.connections['time'] > time.time() - 8640000:
            return self.connections['connections']

        try:
            self.parent.logger.info("Getting first 1000 Google contacts")

            service = build('people', 'v1', credentials = self.creds)

            # Call the People API
            fields  = 'names,memberships,locales,phoneNumbers,addresses,userDefined' 
            results = service.people().connections().list(
                resourceName    = 'people/me',
                pageSize        = 1000,
                personFields    = fields
            ).execute()

            connections = results.get('connections', [])
            
            # We can only fetch 1000 contacts per query, keep going till we have them all
            while 'nextPageToken' in results:
                self.parent.logger.info("Fetching next page")
                pageToken   = results['nextPageToken']
                results     = service.people().connections().list(
                    resourceName    = 'people/me',
                    pageToken       = pageToken,
                    pageSize        = 1000,
                    personFields    = fields
                ).execute()
                
                connections = connections + results.get('connections', [])

            # Store for future use
            self.connections['time']        = time.time()

            phonenumbers            = {}
            
            #self.parent.logger.debug(connections)
            for contact in connections:
                self.parent.logger.debug(f"Processing {contact}")
                
                if 'phoneNumbers' in contact and 'memberships' in contact:
                    for membership in contact['memberships']:
                        if membership.get('contactGroupMembership').get('contactGroupId')   == self.parent.google_label:
                            self.parent.logger.debug(f"Adding {contact.get('names')}")
                            
                            data    = {}
                            if 'names' in contact:
                                data['name']    = contact.get('names')[0]['givenName']

                            if 'addresses' in contact:
                                data['country']    = contact.get('addresses')[0].get('countryCode')

                            # personal languague set, and there is a message in that languague
                            if 'languague' in contact and contact['languague'] in self.messages[languague]:
                                data['languague']   = contact['languague']
                            else:
                                data['languague']   = self.get_languague(data['country'])
                            
                            for nr in contact['phoneNumbers']:
                                phonenumbers[nr.get('canonicalForm')]    = data


            self.connections['phonenumbers'] = phonenumbers
            self.parent.logger.debug(self.connections)

            return connections
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

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
                return 'EN'
            
            # we should only come here if we do not have a message in the languague needed
            self.parent.logger.error(f"Invalid country {country_code}.\nDefaulting to English languague")
            return 'EN'
        except Exception as e:
            self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")
        
