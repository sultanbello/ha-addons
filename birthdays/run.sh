#!/usr/bin/with-contenv bashio
echo $SUPERVISOR_TOKEN

response=$(curl -sSL -H "Authorization: Bearer $SUPERVISOR_TOKEN" http://supervisor/network/info)

http_code=$(tail -n1 <<< "$response")  # get the last line
content=$(sed '$ d' <<< "$response")   # get all but the last line which contains the status code

echo "$http_code"
echo "$content"

response=$(curl -sSL -H "Authorization: Bearer $SUPERVISOR_TOKEN" http://supervisor/addons)

http_code=$(tail -n1 <<< "$response")  # get the last line
content=$(sed '$ d' <<< "$response")   # get all but the last line which contains the status code

echo "$http_code"
echo "$content"

response=$(curl -sSL -H "Authorization: Bearer $SUPERVISOR_TOKEN" http://supervisor/addon/06c15c6e_whatsapp/info)

http_code=$(tail -n1 <<< "$response")  # get the last line
content=$(sed '$ d' <<< "$response")   # get all but the last line which contains the status code

echo "$http_code"
echo "$content"

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
