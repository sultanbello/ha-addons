ARG BUILD_FROM="alpine"
FROM $BUILD_FROM

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Copy root filesystem
#COPY rootfs /

WORKDIR /app

RUN  apk add --update curl gnupg git 
RUN apk add --update chromium ffmpeg git
RUN apk add --update nodejs npm
RUN npm i whatsapp-web.js

# Copy data for add-on
COPY run.sh /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
