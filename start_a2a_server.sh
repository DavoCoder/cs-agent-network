#!/bin/bash
# Quick script to start the A2A server
# Usage: ./start_a2a_server.sh [port]

PORT=${1:-9999}
HOST=${A2A_SERVER_HOST:-127.0.0.1}

echo "Starting A2A Administration Agent Server on ${HOST}:${PORT}"
A2A_SERVER_PORT=${PORT} uv run python -m a2a_server
