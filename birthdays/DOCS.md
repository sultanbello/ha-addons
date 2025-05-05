# Birthdays Addons

## Initial Installation
Start the addon and watch the log.<br>
Copy the url displayed and paste it in your browser.<br>
Give permission to the app<br>
You will be redirected to a localhost page.<br>
Replace "localhost" with "homeassistant.local" and press enter.<br>
You should be good to go now.<br>

## How it works
Google contacts can have an birthdate, phonenumber and address set.<br>
They also can have labels<br>

If they those three are set we will fetch a random birthday message in their languague as defined in their country code from the messages array.

We first try to see if they have a valid Signal Messenger number, if not we try whatsapp, if still not we try e-mail.
If they have one or more labels and those labels are definded in either signal_groups or whatsapp_groups we also send a message

Each WhatsApp group enty should look like:
- group_name: SOMENAME1 (optional)<br>
  group_id: SOMEID1@g.us<br>
  label_id: Google tag id<br>
  languague: the group languague (EN, NL, FR etc)<br>

Each Signal group enty should look like:
- group_id: The SIGNAL Group Id<br>
  label_id: Google tag id<br>
  languague: the group languague (EN, NL, FR etc)<br>
