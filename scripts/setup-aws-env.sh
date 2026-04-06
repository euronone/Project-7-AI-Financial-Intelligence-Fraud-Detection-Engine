#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     FinShield AWS Environment Setup Script            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
for cmd in aws kubectl docker git; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}✗ $cmd is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ $cmd installed${NC}"
done

echo ""
echo -e "${YELLOW}AWS Credential Configuration${NC}"
echo "=================================="

# Verify AWS credentials
if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
USER_ARN=$(aws sts get-caller-identity --query Arn --output text)

echo -e "${GREEN}✓ AWS Credentials configured${NC}"
echo "  Account ID: $ACCOUNT_ID"
echo "  User: $USER_ARN"

echo ""
echo -e "${YELLOW}Environment Setup${NC}"
echo "=================="

# Get environment from user
read -p "Enter environment (staging/production): " ENVIRONMENT
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    echo -e "${RED}Invalid environment. Use 'staging' or 'production'${NC}"
    exit 1
fi

# Set default AWS region
REGION=${AWS_REGION:-us-east-1}
echo -e "${GREEN}✓ AWS Region: $REGION${NC}"

# Create .env file
echo ""
echo -e "${YELLOW}Creating Environment File${NC}"
echo "=========================="

ENV_FILE=".env.aws.${ENVIRONMENT}"

cat > "$ENV_FILE" << EOF
# AWS Configuration
export AWS_REGION=$REGION
export AWS_ACCOUNT_ID=$ACCOUNT_ID
export ENVIRONMENT=$ENVIRONMENT
export CLUSTER_NAME=finshield-eks-cluster-$ENVIRONMENT

# Database Configuration
# Update these with actual RDS endpoint after deployment
export DATABASE_HOST=finshield-db-$ENVIRONMENT.XXXXXXXXXXXX.rds.$REGION.amazonaws.com
export DATABASE_PORT=5432
export DATABASE_NAME=finshield
export DATABASE_USER=postgres
# IMPORTANT: Update with actual password
export DATABASE_PASSWORD=your-secure-password-here
export DATABASE_URL=postgresql+asyncpg://\$DATABASE_USER:\$DATABASE_PASSWORD@\$DATABASE_HOST:\$DATABASE_PORT/\$DATABASE_NAME

# Redis Configuration
# Update these with actual ElastiCache endpoint after deployment
export REDIS_HOST=finshield-redis-$ENVIRONMENT.XXXXXXXXXXXX.ng.0001.us-east-1.cache.amazonaws.com
export REDIS_PORT=6379
export REDIS_URL=redis://\$REDIS_HOST:\$REDIS_PORT/0

# Application Secrets
# IMPORTANT: Generate these securely
export JWT_SECRET=$(openssl rand -base64 32)
export ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Email Service (Resend)
export RESEND_API_KEY=re_XXXXXXXXXXXXXXXXXXXXXXXXXXXX

# SMS Service (Twilio)
export TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export TWILIO_AUTH_TOKEN=your-twilio-auth-token

# Firebase (optional for push notifications)
export FIREBASE_SERVICE_ACCOUNT_JSON=/path/to/firebase-service-account.json

# Application Configuration
export APP_ENV=$ENVIRONMENT
export LOG_LEVEL=$([ "$ENVIRONMENT" = "production" ] && echo "INFO" || echo "DEBUG")
export CLOUDWATCH_ENABLED=true

# CloudWatch
export CLOUDWATCH_NAMESPACE=FinShield
export ENABLE_METRICS=true

# API Configuration
export API_CORS_ORIGINS=https://finshield.ai,https://www.finshield.ai

# GitHub Actions (for CI/CD)
export GITHUB_ACTIONS=true
EOF

echo -e "${GREEN}✓ Environment file created: $ENV_FILE${NC}"
echo "  IMPORTANT: Update the following in $ENV_FILE:"
echo "    - DATABASE_PASSWORD (use a strong password)"
echo "    - DATABASE_HOST (from RDS endpoint)"
echo "    - REDIS_HOST (from ElastiCache endpoint)"
echo "    - RESEND_API_KEY"
echo "    - TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN"

echo ""
echo -e "${YELLOW}AWS ECR Setup${NC}"
echo "============="

# Create ECR repositories
for repo in finshield-backend finshield-frontend; do
    if aws ecr describe-repositories --repository-names $repo --region $REGION 2>/dev/null; then
        echo -e "${GREEN}✓ ECR repository exists: $repo${NC}"
    else
        echo "Creating ECR repository: $repo"
        aws ecr create-repository \
            --repository-name $repo \
            --region $REGION \
            --image-scanning-configuration scanOnPush=true \
            --image-tag-mutability IMMUTABLE > /dev/null
        echo -e "${GREEN}✓ Created ECR repository: $repo${NC}"
    fi
done

echo ""
echo -e "${YELLOW}CloudFormation Stack Names${NC}"
echo "=========================="

echo "VPC Stack: finshield-vpc-$ENVIRONMENT"
echo "ECS Stack: finshield-ecs-$ENVIRONMENT"
echo "EKS Stack: finshield-eks-$ENVIRONMENT"
echo "RDS Stack: finshield-rds-$ENVIRONMENT"
echo "Monitoring Stack: finshield-monitoring-$ENVIRONMENT"

echo ""
echo -e "${YELLOW}S3 Bucket for Terraform State (Optional)${NC}"
echo "========================================"

TERRAFORM_BUCKET=finshield-terraform-state-$ACCOUNT_ID-$REGION
if aws s3 ls "s3://$TERRAFORM_BUCKET" 2>/dev/null; then
    echo -e "${GREEN}✓ Terraform state bucket exists: $TERRAFORM_BUCKET${NC}"
else
    read -p "Create Terraform state bucket? (y/n): " CREATE_BUCKET
    if [[ $CREATE_BUCKET == "y" ]]; then
        aws s3 mb "s3://$TERRAFORM_BUCKET" --region $REGION
        aws s3api put-bucket-versioning \
            --bucket $TERRAFORM_BUCKET \
            --versioning-configuration Status=Enabled
        echo -e "${GREEN}✓ Created bucket: $TERRAFORM_BUCKET${NC}"
    fi
fi

echo ""
echo -e "${YELLOW}AWS Secrets Manager${NC}"
echo "==================="

# Create secrets
echo "Creating secrets in AWS Secrets Manager..."

source "$ENV_FILE" 2>/dev/null || true

# Database secret
aws secretsmanager create-secret \
    --name "finshield/db/url" \
    --description "Database connection URL for FinShield $ENVIRONMENT" \
    --secret-string "$DATABASE_URL" \
    --region $REGION 2>/dev/null || \
    aws secretsmanager update-secret \
        --secret-id "finshield/db/url" \
        --secret-string "$DATABASE_URL" \
        --region $REGION

echo -e "${GREEN}✓ Stored database URL in Secrets Manager${NC}"

# JWT secret
aws secretsmanager create-secret \
    --name "finshield/jwt/secret" \
    --description "JWT secret for FinShield $ENVIRONMENT" \
    --secret-string "$JWT_SECRET" \
    --region $REGION 2>/dev/null || \
    aws secretsmanager update-secret \
        --secret-id "finshield/jwt/secret" \
        --secret-string "$JWT_SECRET" \
        --region $REGION

echo -e "${GREEN}✓ Stored JWT secret in Secrets Manager${NC}"

# Encryption key
aws secretsmanager create-secret \
    --name "finshield/encryption/key" \
    --description "Encryption key for FinShield $ENVIRONMENT" \
    --secret-string "$ENCRYPTION_KEY" \
    --region $REGION 2>/dev/null || \
    aws secretsmanager update-secret \
        --secret-id "finshield/encryption/key" \
        --secret-string "$ENCRYPTION_KEY" \
        --region $REGION

echo -e "${GREEN}✓ Stored encryption key in Secrets Manager${NC}"

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Setup Complete!                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo "1. Update $ENV_FILE with actual credentials"
echo "2. Load environment: source $ENV_FILE"
echo "3. Deploy infrastructure: ./scripts/deploy-aws.sh"
echo "4. Check AWS_DEPLOYMENT_GUIDE.md for detailed instructions"
echo ""
echo -e "${YELLOW}Quick Reference:${NC}"
echo "  View environment: cat $ENV_FILE"
echo "  Verify AWS access: aws sts get-caller-identity"
echo "  Check ECR repos: aws ecr describe-repositories --region $REGION"
echo "  View secrets: aws secretsmanager list-secrets --region $REGION"
echo ""
