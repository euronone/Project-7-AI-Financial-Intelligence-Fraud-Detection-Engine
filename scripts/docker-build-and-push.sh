#!/bin/bash
# FinShield AI — Docker Build and Push to AWS ECR Script
# Usage: ./scripts/docker-build-and-push.sh [environment]
# Example: ./scripts/docker-build-and-push.sh production

set -e

# Configuration
ENVIRONMENT=${1:-development}
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}FinShield AI Docker Build & Push${NC}"
echo -e "${YELLOW}================================${NC}"
echo "Environment: $ENVIRONMENT"
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "ECR Registry: $ECR_REGISTRY"
echo ""

# Verify prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}✗ Docker not found${NC}"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo -e "${RED}✗ AWS CLI not found${NC}"; exit 1; }
echo -e "${GREEN}✓ All prerequisites satisfied${NC}"
echo ""

# Login to ECR
echo -e "${YELLOW}Logging into AWS ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REGISTRY
echo -e "${GREEN}✓ Logged into ECR${NC}"
echo ""

# Build Backend
echo -e "${YELLOW}Building backend image...${NC}"
cd backend
docker build -t finshield-backend:latest .
echo -e "${GREEN}✓ Backend built${NC}"

# Tag Backend
echo -e "${YELLOW}Tagging backend image...${NC}"
docker tag finshield-backend:latest ${ECR_REGISTRY}/finshield-backend:latest
docker tag finshield-backend:latest ${ECR_REGISTRY}/finshield-backend:${ENVIRONMENT}
docker tag finshield-backend:latest ${ECR_REGISTRY}/finshield-backend:$(date +%Y%m%d-%H%M%S)
echo -e "${GREEN}✓ Backend tagged${NC}"

# Push Backend
echo -e "${YELLOW}Pushing backend image to ECR...${NC}"
docker push ${ECR_REGISTRY}/finshield-backend:latest
docker push ${ECR_REGISTRY}/finshield-backend:${ENVIRONMENT}
echo -e "${GREEN}✓ Backend pushed to ECR${NC}"
echo ""

# Build Frontend
echo -e "${YELLOW}Building frontend image...${NC}"
cd ../frontend
docker build -t finshield-frontend:latest .
echo -e "${GREEN}✓ Frontend built${NC}"

# Tag Frontend
echo -e "${YELLOW}Tagging frontend image...${NC}"
docker tag finshield-frontend:latest ${ECR_REGISTRY}/finshield-frontend:latest
docker tag finshield-frontend:latest ${ECR_REGISTRY}/finshield-frontend:${ENVIRONMENT}
docker tag finshield-frontend:latest ${ECR_REGISTRY}/finshield-frontend:$(date +%Y%m%d-%H%M%S)
echo -e "${GREEN}✓ Frontend tagged${NC}"

# Push Frontend
echo -e "${YELLOW}Pushing frontend image to ECR...${NC}"
docker push ${ECR_REGISTRY}/finshield-frontend:latest
docker push ${ECR_REGISTRY}/finshield-frontend:${ENVIRONMENT}
echo -e "${GREEN}✓ Frontend pushed to ECR${NC}"
echo ""

# Summary
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Build and push completed!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Backend Image:"
echo "  - ${ECR_REGISTRY}/finshield-backend:latest"
echo "  - ${ECR_REGISTRY}/finshield-backend:${ENVIRONMENT}"
echo ""
echo "Frontend Image:"
echo "  - ${ECR_REGISTRY}/finshield-frontend:latest"
echo "  - ${ECR_REGISTRY}/finshield-frontend:${ENVIRONMENT}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update ECS task definition with the new image URLs"
echo "2. Create/update ECS service: aws ecs update-service --cluster finshield --service finshield-backend --force-new-deployment"
echo "3. Monitor deployment: aws ecs describe-services --cluster finshield --services finshield-backend"
