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
                whatsapp            = __import__(name_slug)
            else:
                signal_messenger    = __import__(name_slug)

# Import other files in the directory
import birthdays
import gmail
import logger
import pidfile

class Messenger:
    def __init__(self):
        global available

        self.available          = available

        self.debug              = config.get('debug')
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
        if 'whatsapp' in available:
            self.whatsapp   = whatsapp.Whatsapp(self)

            if not self.whatsapp.connected:
                self.logger.log_message("Whatsapp Instance is Down")
        
        # Check signal
        if 'signal_messenger' in available:
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
                    self.logger.log_message(f"Processing {number}", 'debug')
                          
                    if 'signal_messenger' in available and self.signal.up:
                        if self.signal.is_registered(number):
                            result = self.signal.send_message(number, msg)

                            if result:
                                self.logger.log_message(f"Signal Message Sent To {number}")
                                return result

                    if 'whatsapp' in available and self.whatsapp.is_registered(number):
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
            self.logger.log_message(f"Updated sensor {name}")
        else:
            self.logger.log_message(f"Updating sensor {name} failed\n\nResponse: {response}\n\nRequest:{data}", "Error")

def daily():
    print(f"Starting the sender script")
    messenger   = Messenger()

    messenger.send()

try:
    with pidfile.PIDFile("/datamain.pid"):
        print("Started Script")

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
