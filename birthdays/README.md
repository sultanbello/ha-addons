# Birthdays

_An addon to fetch Google Contacts and send them a message on their birthday_

## Initial Installation
Start the addon and watch the log.
Copy the url displayed and paste it in your browser.
Give permission to the app
You will be redirected to a localhost page.
Replace "localhost" with "homeassistant.local" and press enter.
You should be good to go now

## Description
This addon will fetch your Google Contacts using the [people api](https://developers.google.com/people).
If it is the birthday of one or more of them it will send a message via [Signal](https://github.com/haberda/signal-addon) [WhatsApp](https://github.com/gajosu/whatsapp-ha-addon/) or Gmail.
It will only do so once a day

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armhf Architecture][armhf-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports i386 Architecture][i386-shield]

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg