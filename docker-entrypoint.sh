#!/bin/bash
set -e

echo "============================================"
echo "Tor Crawler - Docker Entrypoint"
echo "============================================"

# Wait for Tor to be ready
echo "Waiting for Tor proxy to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl --socks5-hostname ${TOR_PROXY_HOST:-tor}:${TOR_PROXY_PORT:-9050} \
           --connect-timeout 5 \
           https://check.torproject.org/api/ip >/dev/null 2>&1; then
        echo "✓ Tor proxy is ready!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for Tor... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Error: Tor proxy not available after $MAX_RETRIES attempts"
    echo "Make sure Tor service is running"
    exit 1
fi

# Check if config file exists
if [ ! -f "config.yaml" ]; then
    echo "❌ Error: config.yaml not found"
    echo "Please mount your config.yaml file or create one"
    exit 1
fi

echo "============================================"
echo "Starting Tor Crawler..."
echo "Data will be saved to: /app/data"
echo "============================================"
echo ""

# Execute the crawler with all passed arguments
exec python main.py "$@"
