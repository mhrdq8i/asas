#!/bin/bash
# Docker management script for the asas project
# This script runs docker-compose from the docker directory

# Default command
COMMAND=${1:-"up -d"}

echo "Running Docker Compose command: $COMMAND"

# Run docker-compose (script is already in docker directory)
if docker compose $COMMAND; then
    echo "Command completed successfully!"
else
    echo "Error running Docker Compose command"
    exit 1
fi

# Show helpful information
if [[ "$COMMAND" == "up -d" ]] || [[ "$COMMAND" == "up --build -d" ]]; then
    echo ""
    echo "Application is starting up..."
    echo "Access points:"
    echo "  - Web Application: http://localhost:80"
    echo "  - API Direct: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo ""
    echo "To stop the application, run: ./docker-run.sh down"
fi
