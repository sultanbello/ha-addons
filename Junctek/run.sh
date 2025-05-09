#!/usr/bin/with-contenv bashio

# nginx -g "daemon off;error_log /dev/stdout debug;" &

echo "Starting Python"

python3 -m venv /data/venv
source /data/venv/bin/activate

echo "Checking prerequisites"
#if [ ! -f /data/pip ]; then
    echo "Installing prerequisites"

    python3 -m ensurepip --upgrade >/dev/null

    pip install --upgrade bleak requests paho.mqtt >/dev/null

    echo "pip done" > /data/pip
#fi

echo "Starting Script..."

python3 -u scripts/main.py

echo Script finished

