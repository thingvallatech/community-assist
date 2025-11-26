#!/bin/bash
# Community Assist - Quick Start Script

set -e

echo "========================================"
echo "  Community Assist Setup"
echo "========================================"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements-web.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo ""
    echo "WARNING: Please edit .env with your database credentials"
    echo ""
fi

# Create logs directory
mkdir -p logs

# Check if Docker is running and start database if needed
if command -v docker &> /dev/null; then
    if docker ps &> /dev/null; then
        if ! docker ps | grep -q community_assist_db; then
            echo "Starting PostgreSQL with Docker..."
            docker-compose up -d postgres
            echo "Waiting for database to be ready..."
            sleep 5
        fi
    fi
fi

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your database credentials (if using external DB)"
echo "  2. Initialize database: psql \$DATABASE_URL < src/database/init_db.sql"
echo "  3. Seed data: python -m src.main --seed-only"
echo "  4. Run web app: flask --app webapp.app run --debug"
echo ""
echo "Or run with Docker:"
echo "  docker-compose up"
echo ""
