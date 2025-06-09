#!/usr/bin/with-contenv bashio

bashio::log.info "Refreshing data"

cd /app || exit 1
exec node dist/src/index.js --port="$(bashio::config 'webserver_port')"

