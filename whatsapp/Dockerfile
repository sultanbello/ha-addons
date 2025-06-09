#ARG BUILD_FROM
#FROM $BUILD_FROM

FROM ghcr.io/hassio-addons/debian-base:7.8.3

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Copy root filesystem
#COPY rootfs /

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y curl gnupg git chromium-bsu ffmpeg git nodejs npm
#RUN npm i whatsapp-web.js

WORKDIR /app
RUN git clone --branch "v2.4.1" --depth=1 \
        "https://github.com/gajosu/ha-whatsapp-web-rest-api.git" /app

# install production dependencies
RUN npm install

RUN npm run build

# Copy data for add-on
COPY run.sh /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
