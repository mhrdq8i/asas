#!/bin/bash

# Apply database migrations
echo "Applying database migrations..."
alembic upgrade head

# Start the main command (passed from docker-compose)
exec "$@"
