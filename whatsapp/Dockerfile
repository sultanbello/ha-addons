ARG BUILD_FROM="alpine"
FROM $BUILD_FROM

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Copy root filesystem
#COPY rootfs /

WORKDIR /data/app

# Copy data for add-on
COPY run.sh /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
