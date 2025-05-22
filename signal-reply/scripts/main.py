#pip install websocket-client
# pip install rel

import websocket
import json
import rel
import os
import logger
import requests

class SocketListener:

	def __init__(self):
		self.token 		= os.getenv('SUPERVISOR_TOKEN')

		file_path		= '/data/options.json'
		if os.path.exists(file_path):
			print(f"File '{file_path}' exists.")
		else:
			print(f"File '{file_path}' does not exist.")
			file_path	= os.path.dirname(os.path.realpath(__file__))+file_path
				
		# Get Options
		with open(file_path, mode="r") as data_file:
			config = json.load(data_file)

			self.log_level          = config.get('log level')
			self.signal_port        = config.get('signal_port')
			self.signal_number     	= config.get('signal_number')

			self.logger             = logger.Logger(self)
			self.logger.info("")

			if self.log_level == 'debug':
				self.debug  = True
			else:
				self.debug  = False
				
			self.logger.debug("Debug is Enabled")

			self.logger.info(f"Log level is {self.log_level}")

			self.socket = f'ws://homeassistant.local:{self.signal_port}/v1/receive/{self.signal_number}'

			ws = websocket.WebSocketApp(self.socket, on_open = self.on_open, on_close = self.on_close, on_message = self.on_message, on_error = self.on_error)

			ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
			rel.signal(2, rel.abort)  # Keyboard Interrupt
			rel.dispatch()

	def on_open(self, ws):
		self.logger.info('Opened Connection')

	def on_close(self, ws, close_status_code, close_msg):
		self.logger.info("### closed: {close_msg} ###")

	def on_message(self, ws, message):
		message	= json.loads(message)
		
		if "dataMessage" in message['envelope'] and message['envelope']['dataMessage']['message'] != None:
			self.logger.debug(f"Received '{message['envelope']['dataMessage']['message']}' from {message['envelope']['sourceName']} ({message['envelope']['sourceNumber']})")
			
			if 'groupInfo' in message['envelope']['dataMessage']:
				self.logger.debug(f"Message is posted in the '{message['envelope']['dataMessage']['groupInfo']['groupName']}' group with id {message['envelope']['dataMessage']['groupInfo']['groupId']}")

			self.logger.debug(f"Timestamp is {message['envelope']['dataMessage']['timestamp']}")
			
			if 'quote' in message['envelope']['dataMessage']:
				self.logger.debug(f"Message is a response to '{message['envelope']['dataMessage']['quote']['text']}' with timestamp {message['envelope']['dataMessage']['quote']['id']}")

			self.update_sensor( 'signal_message_received', 'on', message['envelope'])
		
	def on_error(self, ws, err):
		self.logger.error(f"Got a an error: {err}")

	def update_sensor(self, name, state, attributes):
		data    = {
			"state": 		state,
			"attributes": 	attributes,
			"unique_id:": 	name
		}

		url     = f"http://supervisor/core/api/states/sensor.{name}"

		headers = {
			"Authorization": f"Bearer {self.token}",
			"content-type": "application/json",
		}

		response    = requests.post(url, json=data, headers=headers)
		if response.ok:
			self.logger.info(f"Updated sensor {name}")
		else:
			self.logger.error(f"Updating sensor {name} failed\n\nResponse: {response}\n\nRequest:{data}")


SocketListener()