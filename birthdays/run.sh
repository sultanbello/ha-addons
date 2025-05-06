#!/usr/bin/with-contenv bashio

echo "Starting Python"

python3 -m venv /data/venv
source /data/venv/bin/activate

echo "Checking prerequisites"

if [ ! -f /data/pip ]; then
    echo "Installing prerequisites"

    python3 -m ensurepip --upgrade >/dev/null

    pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib lxml requests num2words schedule python-pidfile >/dev/null

    echo "pip done" > /data/pip
fi

echo "Starting Script"

python3 -u scripts/main.py

echo Script finished

