# See https://developers.google.com/people/quickstart/python
# http://googleapis.github.io/google-api-python-client/docs/dyn/people_v1.people.html


####################        IMPORTS         #####################################
from num2words import num2words
import random
import datetime
import sys
import lxml.etree
import urllib.request

class CelebrationMessages():
    def __init__(self, Messenger):
        self.parent     = Messenger

        self.now        = datetime.datetime.now()

        self.messages   = {}
        for message in self.parent.messages:
            # add an empty array if the current languague is not there yet
            if not message['languague'].lower() in self.messages:
                self.messages[message['languague'].lower()] = []

            # Add the message to the languague array
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

        # Fetch a list of country - languagues
        self.country_languagues()

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

            # Country
            if addresses and addresses[0].get("countryCode") != None:
                details['country'] = (addresses[0].get("countryCode")).upper()
            else:
                # this person has a birthday but no country set
                if 'name' in details and 'birthday' in details:
                    self.parent.logger.log_message(f"Please set a country for {details['name']} at https://contacts.google.com/{person.get('resourceName', '').replace('people', 'person')}", "Warning")

            # Languague
            if person.get('userDefined') != None:
                for data in person.get('userDefined'):
                    if data.get('key') == 'languague':
                        details['languague']    = data.get('value').upper()
                        self.parent.logger.log_message(f"{details['name']} has a personal languague set", 'debug')

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
                            
                            if details['country'] == "NL":
                                msg             = f"Gefeliciteerd met jullie"
                            else:
                                msg             = f"Congratulations with your" 

                            if year != None:
                                age = self.now.year - year
                                age_in_words    = num2words(age, to = 'ordinal',  lang = self.get_languague(details['country']))
                                
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
            # personal languague set, and there is a message in that languague
            if 'languague' in details and details['languague'] in self.messages[languague]:
                languague   = details['languague']
            else:
                languague   = self.get_languague(details['country'])

            # Personall message
            msg         = random.choice(self.messages[languague]).replace("%firstname%", details['firstname'])
            self.parent.send_message(msg, details) 
            
            
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
    
    def send_group_message(self, details):
        try:                    
            # check the groups in Google this person is a member of
            if 'memberships' in details:
                for membership in details['memberships']:
                    label_id = membership.get('contactGroupMembership').get('contactGroupId')

                    if 'signal_messenger' in self.parent.available and label_id in self.group_ids['signal']:
                        languague   = self.group_ids['signal'][label_id]['languague']
                        msg         = random.choice(self.messages[languague]).replace("%firstname%", details['firstname'])
                        group_id    = self.group_ids['signal'][label_id]['group_id']

                        self.parent.signal.send_message(group_id, msg)

                    if 'whatsapp' in self.parent.available and label_id in self.group_ids['whatsapp']:
                        languague   = self.group_ids['whatsapp'][label_id]['languague']
                        msg         = random.choice(self.messages[languague]).replace("%firstname%", details['firstname'])
                        group_id    = self.group_ids['whatsapp'][label_id]['group_id']

                        self.parent.whatsapp.send_message(group_id, msg)
                        
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")

    def send_birthday_messages(self, contacts):
        try:
            i = 0
            self.parent.logger.log_message("Getting birthday messages")        
        
            for person in contacts:
                details  = self.check_contact(person)
            
            dict(sorted(self.names.items()))

            birthdays   = {}

            for name, details in self.names.items():
                if 'country' not in details:
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
                            
                            birthdays[details['name']]  =   details
                                        
                    except Exception as e:
                        self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
            
            # update the birthdate sensor
            if len(birthdays) == 0:
                state   = 'off'
            else:
                state   = 'on'

            self.parent.update_sensor('todays_birthdays', state, birthdays)

            self.parent.logger.log_message(birthdays, 'debug')

            self.parent.logger.log_message("Finished sending birthday mesages")
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")

    def country_languagues(self):
        url         = "https://raw.githubusercontent.com/unicode-org/cldr/master/common/supplemental/supplementalData.xml"
        langxml     = urllib.request.urlopen(url)
        langtree    = lxml.etree.XML(langxml.read())

        self.languages = {}
        for t in langtree.find('territoryInfo').findall('territory'):
            langs = {}
            for l in t.findall('languagePopulation'):
                # If this is an official languague
                if bool(l.get('officialStatus')):
                    langs[l.get('type')] = float(l.get('populationPercent'))
            self.languages[t.get('type')] = langs

    def get_languague(self, country_code):
        if country_code in self.languages:
            # all the official languagues of this country
            languagues  = self.languagues.get(country_code)

            for languague in languagues:
                # we have a message in this languague
                if languague in self.messages:
                    return languague
            
            # we should only come here if we do not have a message in the languague needed
            self.parent.logger.log_message(f"Could not find a message in any of the languagues for country {country_code}.\nDefaulting to English", "Warning")
            return 'EN'
        
         # we should only come here if we do not have a message in the languague needed
        self.parent.logger.log_message(f"Invalid country {country_code}.\nDefaulting to English languague", "error")
        return 'EN'
        
