#!/bin/bash
# FinShield AI - Quick Start Script
# This guide provides step-by-step instructions to start the entire system

# ============================================================================
# PREREQUISITE: Docker Desktop Installation
# ============================================================================
# If you don't have Docker installed, download it from:
# https://www.docker.com/products/docker-desktop
# 
# After installation, verify it's working:
#   docker --version
#   docker ps
# ============================================================================

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  FinShield AI - Quick Start Guide${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Step 1: Start Infrastructure Services
echo -e "${BLUE}Step 1: Starting Infrastructure Services${NC}"
echo "   - PostgreSQL 16 (Database)"
echo "   - Redis 7 (Cache & Message Queue)"
echo "   - MailHog (Email Testing)"
echo

read -p "Do you want to start Docker services? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}▶ Starting Docker Compose...${NC}"
    docker compose up -d
    sleep 5  # Give services time to start
    
    # Verify services
    echo -e "${GREEN}✓ Checking running containers...${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}"
    echo
fi

# Step 2: Backend Setup
echo -e "${BLUE}Step 2: Backend Setup & Migration${NC}"
echo "   - Running database migrations"
echo "   - Seeding test data"
echo

read -p "Do you want to migrate database and seed data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd backend
    echo -e "${GREEN}▶ Running migrations...${NC}"
    poetry run alembic upgrade head
    echo
    
    echo -e "${GREEN}▶ Seeding test data...${NC}"
    poetry run python scripts/seed_data.py
    echo -e "${GREEN}✓ Database ready!${NC}"
    cd ..
    echo
fi

# Step 3: Start Backend Server
echo -e "${BLUE}Step 3: Start Backend Server${NC}"
echo "   URL: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo

read -p "Start backend server? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}▶ Starting FastAPI backend...${NC}"
    echo -e "${YELLOW}(Server running on port 8000 - don't close this window)${NC}"
    cd backend
    poetry run uvicorn app.main:app --reload --port 8000
fi

# Note: In Windows, use these commands in separate PowerShell windows:
# 
# Window 1 - Docker services (if not using Docker Desktop)
#   docker compose up -d
#
# Window 2 - Backend
#   cd backend
#   poetry run alembic upgrade head
#   poetry run python scripts/seed_data.py
#   poetry run uvicorn app.main:app --reload --port 8000
#
# Window 3 - Frontend
#   cd frontend
#   npm run dev
#
# Then open http://localhost:3000 in your browser
