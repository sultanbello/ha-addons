# alpine image
# ARG BUILD_FROM

# FROM $BUILD_FROM
FROM ghcr.io/hassio-addons/debian-base:7.8.3

#ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

#install node 14 and npm
RUN apt-get update && apt-get install -y curl gnupg

#Node installation
RUN apt -y install nodejs npm git

# Node package manager
RUN npm install -g n

# Upgrade to latest stable version
RUN apt-get install -y nodejs git

#install chromiun
RUN apt-get install -y chromium ffmpeg git

# Copy root filesystem
#COPY rootfs /

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