import sys
import os
import requests
import logger
import sys
from time import sleep
import json
import schedule
import time

#pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib lxml requests num2words --break-system-packages

# Changing working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import other files in the directory
import birthdays
import whatsapp
import signal_messenger
import gmail
import logger

class Messenger:
    def __init__(self):
        # Get Options
        with open("/data/options.json", mode="r") as data_file:
            config = json.load(data_file)

        self.debug              = config.get('debug')
        self.client_id          = config.get('client_id')
        self.client_secret      = config.get('client_secret')
        self.project_id        = config.get('project_id')
        self.signal_port        = config.get('signal_port')
        self.whatsapp_port      = config.get('whatsapp_port')
        self.signal_numbers     = config.get('signal_numbers')
        self.whatsapp_groups    = config.get('whatsapp_groups')
        self.log_level          = config.get('log_level')  

        self.logger = logger.Logger(self.log_level)
        self.logger.log_message("")
        if self.debug:
            self.logger.log_message("Debug is Enabled")

        self.logger.log_message(f"Log level is {self.log_level}")

        x = 60
        while not self.is_connected():
            #Wrtie to log every minute
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
    messenger   = Messenger()

    messenger.send()

schedule.every().day.at("11:02").do(daily)

while True:
    schedule.run_pending()
    sleep(60)