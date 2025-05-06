# See https://developers.google.com/people/quickstart/python
# http://googleapis.github.io/google-api-python-client/docs/dyn/people_v1.people.html


####################        IMPORTS         #####################################
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from num2words import num2words
from time import sleep
import random
import logger
import datetime
import sys

class CelebrationMessages():
    def __init__(self, Messenger):
        self.parent     = Messenger

        self.now        = datetime.datetime.now()

        self.messages   = {}
        for message in self.parent.messages:
            if not message['languague'].lower() in self.messages:
                self.messages[message['languague'].lower()] = []

            self.messages[message['languague'].lower()].append(message['message'])

        self.group_ids  = {}
        self.group_ids['signal']    = {}
        for group in self.parent.signal_groups:
            self.group_ids['signal'][group['label_id']] = group

        self.group_ids['whatsapp']    = {}
        for group in self.parent.whatsapp_groups:
            self.group_ids['whatsapp'][group['label_id']] = group

        # build number -> name dict
        self.numbers    = {}
        self.names      = {}

    # Checks a persons details and returns an dict of them
    def check_contact(self, person):
        try:
            details = {}

            # Names
            names = person.get('names', [])
            if names:
                details['name']         = str(names[0].get('displayName'))
                details['firstname']    = str(names[0].get('givenName'))
                details['id']           = names[0].get('metadata',).get('source').get('id')

            addresses       = person.get('addresses', [])
            
            # birthday
            birthdays = person.get('birthdays', [])
            if birthdays:
                details['birthyear']    = birthdays[0].get('date').get("year")
                details['birthmonth']   = birthdays[0].get('date').get("month")
                details['birthday']     = birthdays[0].get('date').get("day")

                if details['birthyear'] != None:
                    details['age']          = self.now.year - details['birthyear']

            if addresses and addresses[0].get("countryCode") != None:
                details['languague'] = (addresses[0].get("countryCode")).lower()
            else:
                # this person has a birthday but no country set
                if 'name' in details and 'birthday' in details:
                    self.parent.logger.log_message(f"Please set a country for {details['name']} at https://contacts.google.com/{person.get('resourceName', '').replace('people', 'person')}", "Warning")

            # E-mail address
            email = person.get('emailAddresses')
            if email != None:
                details['email'] = email[0]['value']

            # Events
            events = person.get('events')
            if events != None:
                details['events'] = events

            # Memberships
            memberships = person.get('memberships')
            if memberships != None:
                details['memberships'] = memberships

            # Relations
            relations = person.get('relations')
            if relations != None:
                details['relations'] = relations

            # Phone numbers
            phonenumbers = person.get("phoneNumbers")
            
            if phonenumbers != None:
                numbers = []
                for p in phonenumbers:
                    # Send warning for user without a phone number
                    if p.get('canonicalForm') == None:
                        if 'birthday' in details:
                            self.parent.logger.log_message("Please set a proper phonenumber for " + details['name'] + str(p), "Warning")
                    # only add a number once
                    elif p['canonicalForm'] not in numbers:
                        numbers.append(p['canonicalForm'])

                        # Store the phone number
                        self.numbers[p['canonicalForm']]  = details

                if len(numbers) > 0:
                    details['numbers']   = numbers
            
            if 'id' in details:
                #if we have a duplicate name
                if details['name'] in self.names:
                    if details.get('birthyear') == self.names[details['name']].get('birthyear'):
                        self.parent.logger.log_message(f"I found another person with the name {details['name']} and the same age, please check", 'warning')
                    self.names[details['name'] + '_1'] = details
                else:
                    self.names[details['name']] = details

            return details
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
    
    def send_event_message(self, details):
        try:
            #Check for anniversaries
            if not 'events' in details:
                return
            
            for event in details['events']:
                try:
                    # This event happens today
                    if event.get('date').get("month") == self.now.month and event.get('date').get("day") == self.now.day:
                        # Send an event message
                        try:
                            eventtype   = event.get('type')
                            year        = event.get('date').get("year")
                            
                            if details['languague'] == "NL":
                                msg             = f"Gefeliciteerd met jullie"
                            else:
                                msg             = f"Congratulations with your" 

                            if year != None:
                                age = self.now.year - year
                                age_in_words    = num2words(age, to = 'ordinal',  lang = details['languague'])
                                
                                msg += f" {age_in_words}"

                            msg += f" {eventtype.lower()} {details['firstname']}!"

                            self.parent.send_message(msg, details)             
                        except Exception as e:
                            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
                except Exception as e:
                    self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")

    def send_personal_message(self, details):
        try:
            if details['languague'] in self.messages:
                # Personall message
                msg         = random.choice(self.messages[details['languague']])
                self.parent.send_message(msg.replace("%firstname%", details['firstname']), details) 
            else:
                self.parent.logger.log_message(f"No message set for languague { details['languague']}", "Error")
            
            
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
    
    def send_group_message(self, details):
        try:                    
            # check the groups in Google this person is a member of
            if 'memberships' in details:
                for membership in details['memberships']:
                    label_id = membership.get('contactGroupMembership').get('contactGroupId')

                    if label_id in self.group_ids['signal']:
                        msg         = random.choice(self.messages[self.group_ids['signal'][label_id]['languague']])

                        self.parent.signal.send_message(self.group_ids['whatsapp'][label_id]['group_id'], msg.replace("%firstname%", details['firstname']))

                    if label_id in self.group_ids['whatsapp']:
                        msg         = random.choice(self.messages[self.group_ids['whatsapp'][label_id]['languague']])

                        self.parent.whatsapp.send_message(self.group_ids['whatsapp'][label_id]['group_id'], msg.replace("%firstname%", details['firstname']))
                        
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")

    def send_birthday_messages(self, contacts):
        try:
            i = 0
            self.parent.logger.log_message("Getting birthday messages")        
        
            for person in contacts:
                details  = self.check_contact(person)
            
            dict(sorted(self.names.items()))

            for name, details in self.names.items():
                if 'languague' not in details:
                    if 'name' in details:
                        #self.parent.logger.log_message(f'Not sending messages to {details['name']} because I am not sure which languague to use')
                        pass
                    else:
                        self.parent.logger.log_message(f"No valid details found for {details} {person['resourceName']}")

                    continue

                self.send_event_message(details)
                
                if 'birthday' in details:
                    try:
                        #Check if birthday
                        if details['birthmonth'] == self.now.month and details['birthday'] == self.now.day:
                            self.parent.logger.log_message('Today is the birthday of ' + details['name'])

                            self.send_personal_message(details)

                            self.send_group_message(details)
                                        
                    except Exception as e:
                        self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
            self.parent.logger.log_message("Finished sending birthday mesages")
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
