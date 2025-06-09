#!/usr/bin/with-contenv bashio

bashio::log.info "Refreshing data"

#if [ ! -f /data/pip ]; then
    bashio::log.info "Installing curl"
    apk add --update curl gnupg git 

    bashio::log.info "Installing chromium"
    apk add --update chromium ffmpeg git

    bashio::log.info "Installing nodejs"
    apk add --update nodejs npm

    bashio::log.info "Fetching rest api"
    git clone --branch "v2.4.1" --depth=1 "https://github.com/gajosu/ha-whatsapp-web-rest-api.git" /data/app

    # install production dependencies
    bashio::log.info "Installing rest api"
    npm install

    npm audit fix --force 

    npm update

    npm run build
    echo "pip done" > /data/pip
#fi

cd /app || exit 1
exec node dist/src/index.js --port="$(bashio::config 'webserver_port')"

