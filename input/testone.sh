#!/usr/bin/env sh

#I USED AN LLM TO WRITE THIS SCRIPT


# Exit immediately if no argument is passed
if [ -z "$1" ]; then
    echo "Error: No data file specified."
    echo "Usage: $0 <path-to-json-file>"
    exit 1
fi

DATA_PATH="$1"

# Check if the file exists
if [ ! -f "$DATA_PATH" ]; then
    echo "Error: File '$DATA_PATH' not found."
    exit 1
fi

# Execute curl request referencing the local JSON path
curl --request POST \
    --url http://192.168.40.159:8080/restate/call/OrderIngestion/submitOrder \
    --header 'Accept: application/json' \
    --header 'Content-Type: application/json' \
    --header 'idempotency-key: ' \
    --data "@$DATA_PATH"
