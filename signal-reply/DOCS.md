# Signal Listener Addon

## Initial Installation
Make sure you have [The Signal addon](https://github.com/haberda/signal-addon/tree/main) installed and set to json-rpc mode
<br>>
Start the addon and watch the log.<br>
Copy the url displayed and paste it in your browser.<br>
Give permission to the app<br>
You will be redirected to a localhost page.<br>
Replace "localhost" with "homeassistant.local" and press enter.<br>
You should be good to go now.<br>

## Sensors
This addon creates two sensors: "Signal Message Received" and "Auto Reply"<br>
The first one is 'on' if a signal message is received, turns off after 1 minute.<br>
It contains the latest Signal Message received in its attributes<br>
<br>
The second one is a binary sensor. Turn it on to enable auto replies