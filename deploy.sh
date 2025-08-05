#!/bin/bash

# Zentry Cloud Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

echo -e "${GREEN}🚀 Deploying Zentry Cloud - Environment: $ENVIRONMENT${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if required environment variables are set for production
if [ "$ENVIRONMENT" = "production" ]; then
    required_vars=("DATABASE_URL" "SUPABASE_URL" "SUPABASE_KEY" "JWT_SECRET_KEY" "CORS_ORIGINS" "NEXT_PUBLIC_API_URL")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo -e "${RED}❌ Required environment variable $var is not set${NC}"
            exit 1
        fi
    done
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Creating .env file from template${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please update .env file with your configuration${NC}"
fi

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f $COMPOSE_FILE down

# Pull latest images
echo -e "${YELLOW}📥 Pulling latest images...${NC}"
docker-compose -f $COMPOSE_FILE pull

# Build and start containers
echo -e "${YELLOW}🔨 Building and starting containers...${NC}"
docker-compose -f $COMPOSE_FILE up --build -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check service health
echo -e "${YELLOW}🏥 Checking service health...${NC}"

# Check backend health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    docker-compose -f $COMPOSE_FILE logs backend
fi

# Check frontend health (if not production)
if [ "$ENVIRONMENT" != "production" ]; then
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is healthy${NC}"
    else
        echo -e "${RED}❌ Frontend health check failed${NC}"
        docker-compose -f $COMPOSE_FILE logs frontend
    fi
fi

# Show running containers
echo -e "${GREEN}📋 Running containers:${NC}"
docker-compose -f $COMPOSE_FILE ps

# Show logs
echo -e "${GREEN}📝 Recent logs:${NC}"
docker-compose -f $COMPOSE_FILE logs --tail=20

echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo -e "${GREEN}🌐 Backend API: http://localhost:8000${NC}"
if [ "$ENVIRONMENT" != "production" ]; then
    echo -e "${GREEN}🌐 Frontend: http://localhost:3000${NC}"
fi
echo -e "${GREEN}📚 API Documentation: http://localhost:8000/docs${NC}"