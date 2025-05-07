import sys
import os
import requests
import logger
import sys
from time import sleep
import json
import schedule
import time
from pathlib import Path

TOKEN = os.getenv('SUPERVISOR_TOKEN')

url     = "http://supervisor/addons"
headers = {
  "Authorization": f"Bearer {TOKEN}",
  "content-type": "application/json",
}
response = requests.get(url, headers=headers)
if response.ok:
    print(response.text)
    print(response.json()['data']['addons'])
    addons  = response.json()['data']['addons']

    for addon in addons:
        if addon['slug'] == '06c15c6e_whatsapp':
            print(addon['state'])

# Import other files in the directory
import birthdays
import whatsapp
import signal_messenger
import gmail
import logger
import pidfile

class Messenger:
    def __init__(self):
        self.debug              = config.get('debug')
        self.client_id          = config.get('client_id')
        self.client_secret      = config.get('client_secret')
        self.project_id         = config.get('project_id')
        self.signal_port        = config.get('signal_port')
        self.whatsapp_port      = config.get('whatsapp_port')
        self.port               = config.get('port')
        self.signal_numbers     = config.get('signal_numbers')
        self.signal_groups      = config.get('signal_groups')
        self.whatsapp_groups    = config.get('whatsapp_groups')
        self.log_level          = config.get('log_level')
        self.hour               = config.get('hour')
        self.minutes            = config.get('minutes')
        self.messages           = config.get('messages')

        self.logger             = logger.Logger(self)
        self.logger.log_message("")
        self.logger.log_message("Debug is Enabled", 'debug')

        self.logger.log_message(f"Log level is {self.log_level}")

        x = 60
        while not self.is_connected():
            #Write to log every minute
            if x == 60:
                x   = 0
                self.logger.log_message("No internet connection")
                
            sleep(1)
            x += 1
        
        self.logger.log_message("Connected to the Internet")

        # Check whatsapp
        self.whatsapp   = whatsapp.Whatsapp(self)

        if not self.whatsapp.connected:
            self.logger.log_message("Whatsapp Instance is Down")
        
        # Check signal
        self.signal     = signal_messenger.Signal(self)
        if not self.signal.up:
            self.logger.log_message("Signal Instance is not available", "Warning")

        # Instantiate Birthay messages object
        self.birthdays  = birthdays.CelebrationMessages(self)

        # Gmail
        self.gmail      = gmail.Gmail(self)
        self.gmail.connect()

    def send(self):
        try:
            self.logger.log_message('Getting Google Contacts')
            self.contacts    = self.gmail.get_contacts()
            self.logger.log_message('Finished Getting Google Contacts')
                
            self.birthdays.send_birthday_messages(self.contacts)
        except Exception as e:
            self.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")

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
                    print(f"Processing {number}")
                          
                    if self.signal.up:
                        if self.signal.is_registered(number):
                            result = self.signal.send_message(number, msg)

                            if result:
                                self.logger.log_message(f"Signal Message Sent To {number}")
                                return result

                    if self.whatsapp.is_registered(number):
                        result = self.whatsapp.send_message(number, msg)

                        if result:
                            self.logger.log_message(f"Whatsapp Message Sent to {number}")
                            return result
                        
            # Send e-mail we should only come here if both signal and whatsapp failes
            if 'email' in details:
                result  = self.gmail.send_email(details['email'], msg)

                if result:
                    self.logger.log_message(f"E-mail Message Sent To {details['email']}")
                    return result
                
            return False
        except Exception as e:
            self.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")

def daily():
    print(f"Starting the sender script")
    messenger   = Messenger()

    messenger.send()

try:
    with pidfile.PIDFile("/datamain.pid"):
        print("Started")

        # Get Options
        with open("/data/options.json", mode="r") as data_file:
            config = json.load(data_file)

        creds = Path("/data/credentials.json")
        if not creds.is_file():
            print(f"Initiating first run")
            
            # First run
            messenger   = Messenger()

        if config.get('debug'):
            daily()

        print(f"Will run at {config.get('hour')}:{config.get('minutes')} daily")
        schedule.every().day.at("{:02d}:{:02d}:00".format(config.get('hour'), config.get('minutes'))).do(daily)

        while True:
            schedule.run_pending()
            sleep(1)
except pidfile.AlreadyRunningError:
    print("Already running")

print("exit")
