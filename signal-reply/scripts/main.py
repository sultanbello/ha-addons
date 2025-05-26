#pip install websocket-client
# pip install rel

import websocket
import json
import rel
import os
import requests
import logger
import google_contacts
import sys

class SocketListener:

	def __init__(self):
		try:
			self.token 		= os.getenv('SUPERVISOR_TOKEN')

			file_path		= '/data/options.json'
			if not os.path.exists(file_path):
				file_path	= os.path.dirname(os.path.realpath(__file__))+file_path
					
			# Get Options
			with open(file_path, mode="r") as data_file:
				config = json.load(data_file)

				self.log_level          = config.get('log level')
				self.signal_port        = config.get('signal_port')
				self.signal_number     	= config.get('signal_number')
				self.messages           = config.get('messages')
				self.google_label     	= config.get('google_label')
				self.client_id          = config.get('client_id')
				self.client_secret      = config.get('client_secret')
				self.project_id         = config.get('project_id')
				self.port         		= config.get('port')

			self.logger             = logger.Logger(self)
			self.logger.info("")

			if self.google_label != '':
				self.contacts			= google_contacts.Contacts(self)

			if self.log_level == 'debug':
				self.debug  = True
			else:
				self.debug  = False
				
			self.logger.debug("Debug is Enabled")

			self.logger.info(f"Log level is {self.log_level}")

			self.sensor		= {}
			self.auto_reply	= 'switch.signal_auto_reply'

			# Create auto reply sensor
			state			= 'off'
			attributes		= {}

			self.sensor_path		= '/data/sensor.json'
			if os.path.exists(self.sensor_path):
				with open(self.sensor_path, "r") as f:
					try:
						self.sensor = json.load(f)
						self.logger.debug(f"Red {self.sensor} from {self.sensor_path}")
						state		= self.sensor.get('state')
						attributes	= self.sensor.get('attributes')
					except:
						pass

			self.update_sensor(self.auto_reply, state, attributes)

			self.socket = f'ws://homeassistant.local:{self.signal_port}/v1/receive/{self.signal_number}'

			ws = websocket.WebSocketApp(self.socket, on_open = self.on_open, on_close = self.on_close, on_message = self.on_message, on_error = self.on_error)

			ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
			rel.signal(2, rel.abort)  # Keyboard Interrupt
			rel.dispatch()
		except Exception as e:
			self.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

	def on_open(self, ws):
		self.logger.info('Opened Connection To Signal Rest Api')

	def on_close(self, ws, close_status_code, close_msg):
		self.logger.info("### closed: {close_msg} ###")

	def on_message(self, ws, message):
		try:
			message	= json.loads(message)
			
			if "dataMessage" in message['envelope'] and message['envelope']['dataMessage']['message'] != None:
				self.logger.debug(f"Received '{message['envelope']['dataMessage']['message']}' from {message['envelope']['sourceName']} ({message['envelope']['sourceNumber']})")
				
				if 'groupInfo' in message['envelope']['dataMessage']:
					self.logger.debug(f"Message is posted in the '{message['envelope']['dataMessage']['groupInfo']['groupName']}' group with id {message['envelope']['dataMessage']['groupInfo']['groupId']}")

				self.logger.debug(f"Timestamp is {message['envelope']['dataMessage']['timestamp']}")
				
				if 'quote' in message['envelope']['dataMessage']:
					self.logger.debug(f"Message is a response to '{message['envelope']['dataMessage']['quote']['text']}' with timestamp {message['envelope']['dataMessage']['quote']['id']}")

				self.update_sensor( 'sensor.signal_message_received', 'on', message['envelope'])
				
				self.get_sensor(self.auto_reply)
				
				self.logger.debug(self.sensor)
				
				if self.sensor.get('state') == 'on':
					self.logger.info('Auto reply is on')
					
					# find contact by phonenumber
					nr	= message['envelope']['sourceNumber']
					
					if 'quote' in message['envelope']['dataMessage'] and message['envelope']['dataMessage']['quote']['authorNumber'] == self.signal_number:
						self.logger.debug(f"Message is a response to '{message['envelope']['dataMessage']['quote']}' with timestamp {message['envelope']['dataMessage']['quote']['id']}")

					if(
						self.google_label == '' or 
						(
							'phonenumbers' in self.contacts.connections and 
							nr in self.contacts.connections['phonenumbers']
						)
					):
						self.logger.debug(f'Preparing reply to {nr}')

						# get the first message from the list
						message	=	self.messages[0]['message']
						
						# Determine the languague based on the contact from Google
						if self.google_label != '':
							languague	= list(self.contacts.messages.keys())[0]

							details		= self.contacts.connections['phonenumbers'][nr]

							# There is a message in the required languague
							if 'languague' in details and details['languague'] in self.contacts.messages:
								languague   = details['languague']
							elif 'en' in self.contacts.messages:
								languague   = 'en'
							else:
								languague	= list(self.contacts.messages.keys())[0]

							message	= self.contacts.messages[languague]
						
						self.send_message(nr, message)
					else:
						self.logger.debug(self.contacts.connections)
		except Exception as e:
			self.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")
		
	def on_error(self, ws, err):
		self.logger.error(f"Got a an error: {err}")

	def update_sensor(self, name, state, attributes):
		try:
			attributes['friendly_name']	= name.split('.')[1].replace('_', ' ').capitalize()

			data    = {
				"state": 		state,
				"attributes": 	attributes,
				"unique_id:": 	name
			}

			url     = f"http://supervisor/core/api/states/{name}"

			headers = {
				"Authorization": f"Bearer {self.token}",
				"content-type": "application/json",
			}

			response    = requests.post(url, json=data, headers=headers)

			self.logger.debug(f"url: {url}")
			self.logger.debug(f"data: {data}")
			self.logger.debug(f"response: {response}")
			if response.ok:
				self.logger.info(f"Updated sensor {name}")
			else:
				self.logger.error(f"Updating sensor {name} failed\n\nResponse: {response}\n\nRequest:{url} - {data}")
		except Exception as e:
			self.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")
	
	def get_sensor(self, id):
		try:
			url     = f"http://supervisor/core/api/states/{id}"
			
			headers = {
				"Authorization": f"Bearer {self.token}",
				"content-type": "application/json",
			}

			response    = requests.get(url,  headers=headers)

			self.logger.debug(f"url: {url}")
			self.logger.debug(f"response: {response}")
			if response.ok:
				json_response = response.json()
				self.logger.debug(json_response)
				
				# only update if needed
				if self.sensor != json_response:
					self.sensor = json_response
					
					with open(self.sensor_path, "w") as f:
						json.dump(json_response, f)

				return self.sensor
			else:
				self.logger.error(f"Updating sensor {id} failed\n\nResponse: {response}\n\nRequest:{id}")
		except Exception as e:
			self.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

		return False

	def send_message(self, number, msg):
		if self.parent.debug:
			self.parent.logger.debug(f"I would have sent '{msg}' via signal to {number} if debug was disabled")
			return True
			
		try:
			headers = {
				'Content-Type': 'application/json',
			}
			
			data    = {
				"number": self.signal_number,
				'message': msg,
				'recipients': [number]
			}
			
			response    = requests.post(f'{self.url}/v2/send', json=data, headers=headers)
			
			if response.ok:
				self.parent.logger.info(f'Send Signal Message Succesfully. Timestamp { response.json()["timestamp"] }') 
				return response.json()['timestamp']
				
			self.parent.logger.error(f'Send Signal message failed. Error is {response.json()["error"]} ')
			
			return False
		except Exception as e:
			self.parent.logger.error(f"{str(e)} on line {sys.exc_info()[-1].tb_lineno}")

SocketListener()