import sys
import requests

class Signal:
    def __init__(self, Messenger):
        try:
            self.parent = Messenger

            self.url    = f"http://homeassistant.local{self.parent.signal_port}"
            
            self.number = self.parent.signal_numbers 

            print(self.number)

            self.headers = {
                'Content-Type': 'application/json',
            }

            self.available()
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
            self.up     = False

    def available(self):
        try:
            response = requests.get(f'{self.url}/v1/about', headers=self.headers)

            if response.ok:
                self.up     = True
                self.parent.logger.log_message("Signal Api is Up and Running")
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
            self.parent.logger.log_message(f"Signal is not available", "Warning") 
            self.up     = False

    def is_registered(self, number):
        try:
            response = requests.get(f'{self.url}/v1/search/{self.number}?numbers={number}', headers=self.headers)

            if response.ok:
                return response.json()[0]['registered']

            return False
        except KeyError:
            #Phonenumber is not valid
            return False
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
            return False

    def send_message(self, number, msg):
        if self.parent.debug:
            self.parent.logger.log_message("I would have sent '{msg}' via signal to {number} if debug was disabled")
            return True
        
        try:
            data    = {
                "number": self.number,
                'message': msg,
                'recipients': [number],
            }
            response    = requests.post(f'{self.url}/v2/send', json=data, headers=self.headers)

            if response.ok:
                self.parent.logger.log_message(f'Send Signal Message Succesfully. Timestamp { response.json()["timestamp"] }') 
                return response.json()['timestamp']

            
            self.parent.logger.log_message(f'Send Signal message failed. Error is {response.json()["error"]} ', 'error')

            return False
        except Exception as e:
            self.parent.logger.log_message(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}", "Error")
            