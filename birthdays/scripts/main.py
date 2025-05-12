import sys
import os
import requests
import logger
import sys
from time import sleep
import json
import schedule
from pathlib import Path

# Import other files in the directory
import birthdays
import gmail
import logger

class Messenger:
    def __init__(self):
        global available
        global config

        self.available          = available
        self.client_id          = config.get('client_id')
        self.client_secret      = config.get('client_secret')
        self.project_id         = config.get('project_id')
        self.port               = config.get('port')
        self.log_level          = config.get('log_level')
        self.hour               = config.get('hour')
        self.minutes            = config.get('minutes')
        self.messages           = config.get('messages')
        self.signal_port        = config.get('signal_port')
        self.signal_numbers     = config.get('signal_numbers')
        self.signal_groups      = config.get('signal_groups')
        self.whatsapp_port      = config.get('whatsapp_port')
        self.whatsapp_groups    = config.get('whatsapp_groups')

        self.logger             = logger.Logger(self)
        self.logger.info("")

        if self.log_level == 'debug':
            self.debug  = True
        else:
            self.debug  = False
            
        self.logger.debug("Debug is Enabled")

        self.logger.info(f"Log level is {self.log_level}")

        # Check whatsapp
        if 'whatsapp' in available:
            self.whatsapp   = whatsapp.Whatsapp(self)
        
        # Check signal
        if 'signal' in available:
            self.signal     = signal_messenger.Signal(self)

        # Instantiate Birthay messages object
        self.birthdays  = birthdays.CelebrationMessages(self)

        # Gmail
        self.gmail      = gmail.Gmail(self)

    def connect_services(self):
        x = 60
        while not self.is_connected():
            #Write to log every minute
            if x == 60:
                x   = 0
                self.logger.warning("No internet connection")
                
            sleep(1)
            x += 1
        
        self.logger.info("Connected to the Internet")

        # Check whatsapp
        if 'whatsapp' in available:
            self.whatsapp.check_connected()

            if not self.whatsapp.api_running:
                sleep(60)
                self.whatsapp.check_connected()

            if not self.whatsapp.connected:
                self.logger.warning("Whatsapp Instance is Down")
        
        # Check signal
        if 'signal' in available:
            self.signal.available()

            if not self.signal.up:
                self.logger.warning("Signal Instance is not available")

        # Instantiate Birthay messages object
        self.birthdays  = birthdays.CelebrationMessages(self)

        # Gmail
        self.gmail.connect()

    def send(self, send=True):
        try:
            self.connect_services()

            self.logger.info('Getting Google Contacts')
            self.contacts    = self.gmail.get_contacts()
            self.logger.info('Finished Getting Google Contacts')
                
            self.birthdays.send_birthday_messages(self.contacts, send)
        except Exception as e:
            self.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

    def is_connected(self):
        try:
            requests.get(url='http://www.google.com/', timeout=30)
            return True
        except requests.ConnectionError:
            return False

    def send_message(self, msg, details):        
        try:
            # Check all phone numbers
            if 'numbers' in details:
                for number in details['numbers']:
                    self.logger.debug(f"Processing {number}")
                          
                    if 'signal' in available and self.signal.up:
                        if self.signal.is_registered(number):
                            result = self.signal.send_message(number, msg)

                            if result:
                                self.logger.info(f"Signal Message Sent To {number}")
                                return result

                    if 'whatsapp' in available and self.whatsapp.is_registered(number):
                        result = self.whatsapp.send_message(number, msg)

                        if result:
                            self.logger.info(f"Whatsapp Message Sent to {number}")
                            return result
                        
            # Send e-mail we should only come here if both signal and whatsapp failes
            if 'email' in details:
                result  = self.gmail.send_email(details['email'], msg)

                if result:
                    self.logger.info(f"E-mail Message Sent To {details['email']}")
                    return result
                
            return False
        except Exception as e:
            self.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

    def update_sensor(self, name, state, attributes):
        data    = {
            "state": state,
            "attributes": attributes,
            "unique_id:": name
        }

        url     = f"http://supervisor/core/api/states/sensor.{name}"

        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "content-type": "application/json",
        }

        response    = requests.post(url, json=data, headers=headers)
        if response.ok:
            self.logger.info(f"Updated sensor {name}")
        else:
            self.logger.error(f"Updating sensor {name} failed\n\nResponse: {response}\n\nRequest:{data}")

def daily():
    messenger.logger.info(f"Starting to send messages..")

    messenger.send()

def get_sensor_data():
    messenger.logger.info(f"Starting to check birthdays")

    messenger.send(False)

try:
    if len(sys.argv) == 2:
        running_local       = sys.argv[1]
    else:
        import pidfile
        running_local       = False

    if running_local:
        config  = {'client_id': '1018721936279-hgd1c0cap7c38c9132f78ne50dff6pci.apps.googleusercontent.com', 'client_secret': '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', 'project_id': 'gmail-1615801131703', 'hour': 9, 'minutes': 45, 'messages': [{'message': 'Happy birthday %firstname%!\nMay this new year be full of blessings\nEwald&Lianne', 'languague': 'En'}, {'message': 'Happy birthday %firstname%! Have a wonderfull day\nEwald & Lianne', 'languague': 'En'}, {'message': 'Happy birthday %firstname%!🎂 🎉🎈\nEwald&Lianne', 'languague': 'En'}, {'message': 'Happy birthday %firstname%!🎊🎂🥳\nEwald&Lianne', 'languague': 'En'}, {'message': 'Happy birthday %firstname%!\nMay this new year be full of blessings\nLianne & Ewald', 'languague': 'En'}, {'message': 'Happy birthday %firstname%!\nHave a wonderfull day\nLianne & Ewald', 'languague': 'En'}, {'message': 'Happy birthday %firstname%!🎂 🎉🎈\nLianne & Ewald', 'languague': 'En'}, {'message': 'Happy birthday %firstname%!🎊🎂🥳\nLianne & Ewald', 'languague': 'En'}, {'message': 'Happy birthday %firstname%!\n   \xa0\nMay this new year be full of blessings\nFrom the Harmsens', 'languague': 'En'}, {'message': 'Happy birthday %firstname%!\nHave a wonderfull day\nFrom the Harmsens', 'languague': 'En'}, {'message': 'Happy birthday %firstname%!🎂 🎉🎈\n\nFrom the Harmsens', 'languague': 'En'}, {'message': 'Happy birthday %firstname%!🎊🎂🥳\nFrom the Harmsens', 'languague': 'En'}, {'message': 'Gefeliciteerd met je verjaardag %firstname%!🎂 🎉🎈', 'languague': 'NL'}, {'message': 'Gefeliciteerd met je verjaardag %firstname%!🎊🎂🥳', 'languague': 'NL'}, {'message': 'Gefeliciteerd met je verjaardag %firstname%!\nFijne dag!', 'languague': 'NL'}, {'message': 'Gefeliciteerd met je verjaardag %firstname%!\nEen hele fijne dag toegewenst\nEwald & Lianne', 'languague': 'NL'}, {'message': 'Gefeliciteerd met je verjaardag %firstname%!\nEen hele fijne dag toegewenst\nLianne & Ewald', 'languague': 'NL'}], 'signal_numbers': ['+2349045252526'], 'signal_groups': [{'group_id': 'FTrLH0chjLDIzNHeAMMGmHMTwEjx6p/XJ97/IRDgSE0=', 'label_id': '67709b318999ea56', 'languague': 'en'}], 'whatsapp_groups': [{'group_name': 'Fam v.d. Wart', 'group_id': '31610742567-1407596543@g.us', 'label_id': '59e818140f151ed8', 'languague': 'NL'}, {'group_name': 'Fam Harmsen', 'group_id': '31610742567-1401264746@g.us', 'label_id': '169b51d90910e33d', 'languague': 'NL'}, {'group_name': 'Thuisfront Team Harmsen', 'group_id': '31610742567-1563642823@g.us', 'label_id': '12fce5118f53a6e8', 'languague': 'NL'}], 'log_level': 'debug', 'signal_port': 8080, 'whatsapp_port': 3000, 'port': 9090}

        available   = {'signal':'started', 'whatsapp':'started'}

        whatsapp            = __import__('whatsapp')
        signal_messenger    = __import__('signal_messenger')
    else:
        TOKEN   = os.getenv('SUPERVISOR_TOKEN')

        url     = "http://supervisor/addons"
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "content-type": "application/json",
        }
        response    = requests.get(url, headers=headers)

        available   = {}
        if response.ok:
            addons  = response.json()['data']['addons']

            for addon in addons:
                if addon['slug'] == '06c15c6e_whatsapp' or addon['slug'] == '1315902c_signal_messenger':
                    name_slug               = addon['slug'].split('_')[1]
                    available[name_slug]    = addon['state']

                    if name_slug == 'whatsapp':
                        print("Importing whatsapp.py")
                        whatsapp            = __import__(name_slug)
                    else:
                        print("Importing signal_messenger.py")
                        signal_messenger    = __import__('signal_messenger')

        # Get Options
        with open("/data/options.json", mode="r") as data_file:
            config = json.load(data_file)

    messenger   = Messenger()

    #with pidfile.PIDFile("/datamain.pid"):
    messenger.logger.info("Started Script")

    creds = Path("/data/credentials.json")
    if not creds.is_file():
        messenger.logger.info(f"Initiating first run")
        
        # First run
        messenger.connect_services()

    # run without actually sending
    if messenger.debug:
        daily()
    else:
        # fill the birthdays sensor
        get_sensor_data()

    messenger.logger.info(f"Will run at {config.get('hour')}:{config.get('minutes')} daily")
    schedule.every().day.at("{:02d}:{:02d}:00".format(config.get('hour'), config.get('minutes'))).do(daily)

    # Run ad midnight to fill the sensor data
    schedule.every().day.at("00:00:00").do(get_sensor_data)

    while True:
        schedule.run_pending()
        sleep(1)
except pidfile.AlreadyRunningError:
    messenger.logger.error("Already running")
except Exception as e:
    print(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

messenger.logger.info("Exitting")
