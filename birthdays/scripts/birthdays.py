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

        self.group_ids  = {
            "169b51d90910e33d": {
                "name":         "Fam Harmsen", 
                "languague":    "NL", 
                "platform":     "whatsapp"
            },
            "59e818140f151ed8": {
                "name":         "Fam v.d. Wart", 
                "languague":    "NL", 
                "platform":     "whatsapp"
            },
            "12fce5118f53a6e8": {
                "name":         "Thuisfront Team Harmsen", 
                "languague":    "NL", 
                "platform":     "whatsapp"
            },
        } 

        self.NTgroupId   = 'FTrLH0chjLDIzNHeAMMGmHMTwEjx6p/XJ97/IRDgSE0='

        self.teamMembers   = [
            #Kano
            "Martin Barley",
            "Lid Barley",
            "Elias Barley",
            "Simeon Barley",
            "Arabella Barley",
            "John Hunt",
            "Abigail Hunt",
            "Mesele Koroto",
            "Buzunesh Shanga",
            "Markos Kalore",
            "Tibarek Markos",
            "Sebele Markos",
            "Feven Markos",
            "David Markos",
            "Legesse Hailemariam",
            "Tarikua Gode",
            "Mikiyas Hailemariam",
            "Abigiya Hailemariam",
            "Nahum Hailemariam"
            
            #Retired
            "Randy Wildman",
            "Adena Wildman",
            
            #Potiskum
            "Amanuel Atta",
            "Meselech Godaro",
            "Betselot Amanuel",
            "Eyael Amanuel",
            "Assefa Darebo",
            "Etfwork Debalke",
            "Hailelule Assefa",
            "Alazar Assefa",
            "Saron Assefa",
            "Biruk Assefa",
            "Sherry Thomas",
            "Yakubu Balewa",
            "Agnes Balewa",
            "Jabes Yakubu",
            "David Yakubu",
            "Joshua Yakubu",
        ]

        # English Messages
        self.messages    = [
            "Happy birthday %firstname%!\n\nMay this new year be full of blessings\n\nEwald&Lianne",
            "Happy birthday %firstname%!\n\nHave a wonderfull day\n\nEwald & Lianne",
            "Happy birthday %firstname%!🎂 🎉🎈\n\nEwald&Lianne",
            "Happy birthday %firstname%!🎊🎂🥳\n\nEwald&Lianne",
            "Happy birthday %firstname%!\n\nMay this new year be full of blessings\n\nLianne & Ewald",
            "Happy birthday %firstname%!\n\nHave a wonderfull day\n\nLianne & Ewald",
            "Happy birthday %firstname%!🎂 🎉🎈\n\nLianne & Ewald",
            "Happy birthday %firstname%!🎊🎂🥳\n\nLianne & Ewald",
            "Happy birthday %firstname%!\n\nMay this new year be full of blessings\n\nFrom the Harmsens",
            "Happy birthday %firstname%!\n\nHave a wonderfull day\n\nFrom the Harmsens",
            "Happy birthday %firstname%!🎂 🎉🎈\n\nFrom the Harmsens",
            "Happy birthday %firstname%!🎊🎂🥳\n\nFrom the Harmsens",
        ]

        self.dutchMessages   = [
            "Gefeliciteerd met je verjaardag %firstname%!🎂 🎉🎈",
            "Gefeliciteerd met je verjaardag %firstname%!🎊🎂🥳",
            "Gefeliciteerd met je verjaardag %firstname%!\n\nFijne dag!",
            "Gefeliciteerd met je verjaardag %firstname%!\n\nEen hele fijne dag toegewenst\n\nEwald & Lianne",
            "Gefeliciteerd met je verjaardag %firstname%!\n\nEen hele fijne dag toegewenst\n\nLianne & Ewald",
        ]

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

            if addresses:
                details['languague'] = addresses[0].get("countryCode")
                if details['languague'] != "NL":
                    details['languague'] = "EN"
            else:
                # this person has a birthday but no country set
                if 'name' in details and 'birthday' in details:
                    self.parent.logger.log_message(f"Please set a country for {details['name']} at https://contacts.google.com/search/Zefanja", "Warning")

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
                    self.parent.logger.log_message(f"I found another person with the name {details['name']}")
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
                                if details['languague'] == "NL":
                                    age_in_words    = num2words(age, to = 'ordinal',  lang ='nl')
                                else:
                                    age_in_words    = num2words(age, to = 'ordinal')
                                
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
            # Personall message
            if details['languague'] == "NL":
                msg         = random.choice(self.dutchMessages)
            else:
                msg         = random.choice(self.messages)
            
            self.parent.send_message(msg.replace("%firstname%", details['firstname']), details) 
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
    
    def send_group_message(self, details):
        try:

            # Send Northern Team Message if needed
            if details['name'] in self.teamMembers and self.parent.signal.up:
                msg     = random.choice(self.messages).replace("%firstname%", details['firstname'])
                self.parent.logger.log_message(f"Sending {msg} to {self.NTgroupId}")
                self.parent.signal.send_group_message(msg, self.NTgroupId)
                self.parent.logger.log_message(f"Finished sending {msg} to {self.NTgroupId}")
                    
            # check the groups in Google this person is a member of
            if 'memberships' in details:
                for membership in details['memberships']:
                    group_id = membership.get('contactGroupMembership').get('contactGroupId')
                    if group_id in self.group_ids:
                        group_name = self.group_ids[group_id]['name']
                        
                        if self.group_ids[group_id]['languague'] == "NL":
                            msg         = random.choice(self.dutchMessages)
                        else:
                            msg         = random.choice(self.messages)

                        self.parent.whatsapp.send_message(group_name, msg.replace("%firstname%", details['firstname']))
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")

    def congratulate_relatives(self, details):
        try:
            # Do not send messages to relatives of adults
            if not 'relations' in details or not 'birthyear' in details or details['age'] > 18:
                self.parent.logger.log_message(f"Not sending message to relative, age:{details['age']}")
                return
            
            #Loop over all the relations the birthday user has.
            for relation in details['relations']:
                relation_type    = relation.get('type')

                self.parent.logger.log_message(f"Type is {relation_type}")
                if relation_type == 'father' or relation_type == 'mother' or relation_type == 'vader' or relation_type == 'moeder':
                    #Get the name of this relative
                    relation_name = relation.get('person')
                    self.parent.logger.log_message(f"Preparing a message to {relation_name}")

                    relation_object = self.names[relation_name]

                    # make sure this is the correct person, by check the relation has also a relation with the other person
                    for r in relation_object['relations']:
                        if r['person'] == details['name']:
                            self.parent.send_message(f"Gefeliciteerd met de verjaardag van {details['firstname']}!", relation_object) 
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

                            self.congratulate_relatives(details)
                                        
                    except Exception as e:
                        self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
            self.parent.logger.log_message("Finished sending birthday mesages")
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
