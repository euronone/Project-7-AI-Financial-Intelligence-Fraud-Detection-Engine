#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGION=${AWS_REGION:-us-east-1}
ENVIRONMENT=${ENVIRONMENT:-staging}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo -e "${YELLOW}=== FinShield AWS Deployment ===${NC}"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"
echo "Account ID: $ACCOUNT_ID"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
for cmd in aws kubectl docker git; do
    if ! command_exists $cmd; then
        echo -e "${RED}Error: $cmd is not installed${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All prerequisites met${NC}"

# Create ECR repositories
echo -e "${YELLOW}Creating ECR repositories...${NC}"
for repo in finshield-backend finshield-frontend; do
    if ! aws ecr describe-repositories --repository-names $repo --region $REGION 2>/dev/null; then
        echo "Creating ECR repository: $repo"
        aws ecr create-repository \
            --repository-name $repo \
            --region $REGION \
            --image-scanning-configuration scanOnPush=true
        echo -e "${GREEN}✓ Created $repo${NC}"
    else
        echo -e "${GREEN}✓ $repo already exists${NC}"
    fi
done

# Login to ECR
echo -e "${YELLOW}Logging in to ECR...${NC}"
aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build and push Docker images
echo -e "${YELLOW}Building and pushing Docker images...${NC}"
for service in backend frontend; do
    echo "Building $service image..."
    docker build -t finshield-$service:latest \
        -t $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/finshield-$service:latest \
        -f $service/Dockerfile ./$service

    echo "Pushing $service image..."
    docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/finshield-$service:latest
    echo -e "${GREEN}✓ Pushed finshield-$service${NC}"
done

# Deploy CloudFormation stacks
echo -e "${YELLOW}Deploying CloudFormation stacks...${NC}"

for template in vpc ecs monitoring; do
    STACK_NAME=finshield-$template-$ENVIRONMENT
    TEMPLATE_FILE=infrastructure/cloudformation/$template.yaml

    if [ ! -f "$TEMPLATE_FILE" ]; then
        echo -e "${RED}Error: $TEMPLATE_FILE not found${NC}"
        exit 1
    fi

    echo "Deploying $STACK_NAME..."

    if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION 2>/dev/null; then
        ACTION="update"
        aws cloudformation update-stack \
            --stack-name $STACK_NAME \
            --template-body file://$TEMPLATE_FILE \
            --region $REGION \
            --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
            --capabilities CAPABILITY_NAMED_IAM || true
    else
        ACTION="create"
        aws cloudformation create-stack \
            --stack-name $STACK_NAME \
            --template-body file://$TEMPLATE_FILE \
            --region $REGION \
            --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
            --capabilities CAPABILITY_NAMED_IAM
    fi

    echo "Waiting for CloudFormation ${ACTION}..."
    aws cloudformation wait stack-${ACTION}-complete \
        --stack-name $STACK_NAME \
        --region $REGION 2>/dev/null || true

    echo -e "${GREEN}✓ $STACK_NAME deployed${NC}"
done

# Get ALB endpoint
echo -e "${YELLOW}Retrieving deployment information...${NC}"
ALB_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name finshield-ecs-$ENVIRONMENT \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBEndpoint`].OutputValue' \
    --output text)

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "ALB Endpoint: ${ALB_ENDPOINT:-Not available yet}"
echo ""
echo "Next steps:"
echo "1. Configure Route 53 DNS to point to ALB"
echo "2. Set up SSL certificate in ACM"
echo "3. Configure application secrets in AWS Secrets Manager"
echo "4. Access CloudWatch dashboard for monitoring"
