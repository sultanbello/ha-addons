ARG BUILD_FROM="alpine"
FROM $BUILD_FROM

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Copy root filesystem
#COPY rootfs /

WORKDIR /app
ENV CHROME_BIN="/usr/bin/chromium-browser" \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD="true"
RUN apk add --update curl gnupg git
RUN apk add --no-cache chromium@edge
ENV PUPPETEER_EXECUTABLE_PATH="/usr/bin/chromium-browser"
RUN apk add --update ffmpeg git
RUN apk add --update nodejs npm
RUN npm i whatsapp-web.js

# Copy data for add-on
COPY run.sh /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
