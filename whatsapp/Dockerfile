ARG BUILD_FROM="alpine"
FROM $BUILD_FROM

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Copy root filesystem
#COPY rootfs /

WORKDIR /app

RUN apt-get update
RUN apt-get install curl gnupg -y
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get install nodejs npm -y
RUN npm i whatsapp-web.js

# Copy data for add-on
COPY run.sh /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
