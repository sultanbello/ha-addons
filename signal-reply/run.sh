#!/usr/bin/with-contenv bashio
bashio::log.info "Starting Python"

python3 -m venv /data/venv
source /data/venv/bin/activate

bashio::log.info "Checking prerequisites"

#if [ ! -f /data/pip ]; then
    bashio::log.info "Installing prerequisites"

    python3 -m ensurepip --upgrade >/dev/null

    pip install --upgrade websocket-client rel requests google-api-python-client google-auth-httplib2 google-auth-oauthlib lxml >/dev/null

    echo "pip done" > /data/pip
#fi

bashio::log.info "Starting Script"

python3 -u scripts/main.py

bashio::log.info Script finished
