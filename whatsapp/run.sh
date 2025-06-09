#!/usr/bin/with-contenv bashio

bashio::log.info "Refreshing data"

#if [ ! -f /data/pip ]; then
    bashio::log.info "Installing curl"
    apk add --update curl gnupg git 

    bashio::log.info "Installing chromium"
    apk add --update chromium ffmpeg git

    bashio::log.info "Installing nodejs"
    apk add --update nodejs npm

    npm i whatsapp-web.js

    echo "pip done" > /data/pip
#fi

cd /app || exit 1
exec node dist/src/index.js --port="$(bashio::config 'webserver_port')"

