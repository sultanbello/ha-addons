from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from email.mime.text import MIMEText
import os
import pickle
import base64
import sys
import json
from pathlib import Path

class Gmail:
    def __init__(self, Messenger):
        try:
            self.parent         = Messenger
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")

    def connect(self):
        self.gmail_service  = build('gmail', 'v1', credentials=self.auth())

    def auth(self):
        try:
            # If modifying these scopes, delete the file token.json.
            SCOPES      = [
                'https://www.googleapis.com/auth/contacts', 
                'https://www.googleapis.com/auth/gmail.send'
            ]

            creds               = None
            token_file          = '/data/token.pickle'
            credentials_file    = '/data/credentials.json'

            # credentials do not exist yet
            file = Path(credentials_file)
            if not file.is_file():
                self.parent.logger.log_message(f"credeting {credentials_file}", "debug")
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
                                                                "http://localhost:9090/"
                                                            ]
                        }
                }

                with open(credentials_file, "w") as f:
                    json.dump(content, f)

            # The file token.pickle stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            if os.path.exists(token_file):
                self.parent.logger.log_message(f"Tokenfile {token_file} does exist", "debug")
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)

                self.parent.logger.log_message(f"Creds: {creds}", "debug")
            else:
                self.parent.logger.log_message(f"Token file {token_file} does not exist", "debug")

            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                self.parent.logger.log_message(f"Creds are not valid", "debug")

                if creds and creds.expired and creds.refresh_token:
                    self.parent.logger.log_message(f"Refreshing token", "debug")
                    
                    creds.refresh(Request())
                else:
                    print('')
                    print('########################')
                    flow    = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                    creds   = flow.run_local_server(bind_addr="0.0.0.0", open_browser=False, port=self.parent.port)
                    print('########################')
                    print('')

                # Save the credentials for the next run
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)

            return creds
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")

    def create_email(self, to, subject, message_text):
        message             = MIMEText(message_text)
        message['to']       = to
        message['subject']  = subject

        return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

    def send_email(self, to, msg):
        if self.parent.debug:
            self.parent.logger.log_message(f"I would have sent {msg} via e-mail to {to} if debug was disabled", 'debug')
            return True
        
        message = self.create_email(to, 'Gefeliciteerd!', msg)

        return (self.gmail_service.users().messages().send(userId="me", body=message).execute())

    def get_contacts(self):
        try:
            self.parent.logger.log_message("Getting first 1000 Google contacts")

            service = build('people', 'v1', credentials = self.auth())

            # Call the People API
            fields  = 'names,emailAddresses,birthdays,relations,memberships,locales,phoneNumbers,addresses,genders,events' 
            results = service.people().connections().list(
                resourceName    = 'people/me',
                pageSize        = 1000,
                personFields    = fields
            ).execute()

            connections = results.get('connections', [])
            
            # We can only fetch 1000 contacts per query, keep going till we have them all
            while 'nextPageToken' in results:
                self.parent.logger.log_message("Fetching next page")
                pageToken   = results['nextPageToken']
                results     = service.people().connections().list(
                    resourceName    = 'people/me',
                    pageToken       = pageToken,
                    pageSize        = 1000,
                    personFields    = fields
                ).execute()
                
                connections = connections + results.get('connections', [])

            return connections
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")