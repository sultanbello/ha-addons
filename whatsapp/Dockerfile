#ARG BUILD_FROM
#FROM $BUILD_FROM

FROM ghcr.io/hassio-addons/debian-base:7.8.3

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Copy root filesystem
#COPY rootfs /

WORKDIR /app
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y curl gnupg git chromium ffmpeg git nodejs npm
RUN npm i whatsapp-web.js

# Copy data for add-on
COPY run.sh /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
