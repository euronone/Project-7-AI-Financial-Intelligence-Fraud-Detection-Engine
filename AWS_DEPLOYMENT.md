# FinShield AI — AWS Deployment Guide

**Status**: ✅ **Docker images ready for production AWS deployment**  
**Target Services**: ECS, Fargate, ECR, RDS, ElastiCache  
**Estimated Setup Time**: 30-45 minutes  

---

## Overview

This guide explains how to deploy FinShield AI on AWS using Docker containers, AWS Fargate, RDS, and ElastiCache.

**Architecture**:
```
Internet
    ↓
CloudFront (CDN)
    ↓
ALB (Application Load Balancer)
    ├─ ECS Fargate (Backend) × 2-3 instances
    └─ CloudFront → S3 (Frontend static assets)
    ↓
RDS PostgreSQL (Database)
↓
ElastiCache Redis (Cache)
```

---

## Prerequisites

- AWS Account with appropriate permissions
- Docker installed locally (for testing)
- AWS CLI configured (`aws configure`)
- ECR repository created for backend and frontend images
- VPC with public and private subnets

---

## Step 1: Build & Push Docker Images to ECR

### 1a. Create ECR Repositories

```bash
# Create backend repository
aws ecr create-repository \
    --repository-name finshield-backend \
    --region us-east-1

# Create frontend repository
aws ecr create-repository \
    --repository-name finshield-frontend \
    --region us-east-1
```

### 1b. Get ECR Login Token

```bash
# Get login token (valid for 12 hours)
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
```

Replace `<ACCOUNT_ID>` with your AWS account ID.

### 1c. Build & Tag Backend Image

```bash
# Build backend image
docker build -t finshield-backend:latest ./backend

# Tag for ECR
docker tag finshield-backend:latest \
    <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/finshield-backend:latest

# Push to ECR
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/finshield-backend:latest
```

### 1d. Build & Tag Frontend Image

```bash
# Build frontend image
docker build -t finshield-frontend:latest ./frontend

# Tag for ECR
docker tag finshield-frontend:latest \
    <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/finshield-frontend:latest

# Push to ECR
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/finshield-frontend:latest
```

---

## Step 2: Create RDS PostgreSQL Database

### Option A: AWS Console
1. Go to RDS → Create Database
2. Select PostgreSQL 16
3. Configuration:
   - DB instance identifier: `finshield-db`
   - Master username: `finshield`
   - Password: Generate strong password (save to AWS Secrets Manager)
   - Instance class: `db.t4g.micro` (free tier) or `db.t4g.small` (production)
   - Storage: 20 GB (adjust as needed)
   - Multi-AZ: Yes (production)
4. Network: Select your VPC
5. Create database

### Option B: AWS CLI

```bash
aws rds create-db-instance \
    --db-instance-identifier finshield-db \
    --db-instance-class db.t4g.small \
    --engine postgres \
    --engine-version 16.2 \
    --master-username finshield \
    --master-user-password $(openssl rand -base64 32) \
    --allocated-storage 100 \
    --storage-type gp3 \
    --backup-retention-period 7 \
    --multi-az \
    --publicly-accessible false \
    --region us-east-1
```

### Store Password in AWS Secrets Manager

```bash
aws secretsmanager create-secret \
    --name finshield/db/password \
    --description "FinShield RDS Database Password" \
    --secret-string "$(openssl rand -base64 32)" \
    --region us-east-1
```

---

## Step 3: Create ElastiCache Redis Cluster

### Option A: AWS Console
1. Go to ElastiCache → Create Cache
2. Select Redis
3. Configuration:
   - Cluster name: `finshield-redis`
   - Engine version: 7.0 or latest
   - Node type: `cache.t4g.micro` (free tier) or `cache.t4g.small`
   - Nodes: 2-3 for production
   - Multi-AZ: Yes
   - Automatic failover: Yes
4. Create cluster

### Option B: AWS CLI

```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id finshield-redis \
    --cache-node-type cache.t4g.small \
    --engine redis \
    --engine-version 7.0 \
    --num-cache-nodes 2 \
    --automatic-failover enabled \
    --multi-az \
    --region us-east-1
```

---

## Step 4: Create ECS Task Definition

Create `ecs-task-definition-backend.json`:

```json
{
  "family": "finshield-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/finshield-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "APP_ENV",
          "value": "production"
        },
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        },
        {
          "name": "PORT",
          "value": "8000"
        },
        {
          "name": "CORS_ORIGINS",
          "value": "https://finshield.example.com"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:finshield/db/url::"
        },
        {
          "name": "REDIS_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:finshield/redis/url::"
        },
        {
          "name": "JWT_SECRET",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:finshield/jwt/secret::"
        },
        {
          "name": "ENCRYPTION_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:finshield/encryption/key::"
        },
        {
          "name": "RESEND_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:finshield/resend/api-key::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/finshield-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 40
      }
    }
  ],
  "executionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/finshieldTaskRole"
}
```

Register task definition:

```bash
aws ecs register-task-definition \
    --cli-input-json file://ecs-task-definition-backend.json \
    --region us-east-1
```

---

## Step 5: Create Application Load Balancer

### ALB for Backend

```bash
# Create ALB
aws elbv2 create-load-balancer \
    --name finshield-alb \
    --subnets subnet-xxxxx subnet-yyyyy \
    --security-groups sg-xxxxx \
    --scheme internet-facing \
    --type application \
    --region us-east-1

# Create target group
aws elbv2 create-target-group \
    --name finshield-backend-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-xxxxx \
    --target-type ip \
    --health-check-path /api/v1/health \
    --region us-east-1

# Create listener
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:... \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:... \
    --region us-east-1
```

---

## Step 6: Create ECS Service

```bash
aws ecs create-service \
    --cluster finshield \
    --service-name finshield-backend \
    --task-definition finshield-backend:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=backend,containerPort=8000 \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[sg-xxxxx],assignPublicIp=DISABLED}" \
    --region us-east-1
```

---

## Step 7: Store Secrets in AWS Secrets Manager

```bash
# Database URL
aws secretsmanager create-secret \
    --name finshield/db/url \
    --secret-string "postgresql+asyncpg://finshield:PASSWORD@finshield-db.xxxxx.us-east-1.rds.amazonaws.com:5432/finshield" \
    --region us-east-1

# Redis URL
aws secretsmanager create-secret \
    --name finshield/redis/url \
    --secret-string "redis://finshield-redis.xxxxx.ng.0001.use1.cache.amazonaws.com:6379/0" \
    --region us-east-1

# JWT Secret
aws secretsmanager create-secret \
    --name finshield/jwt/secret \
    --secret-string "$(openssl rand -base64 32)" \
    --region us-east-1

# Encryption Key
aws secretsmanager create-secret \
    --name finshield/encryption/key \
    --secret-string "$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
    --region us-east-1

# Resend API Key
aws secretsmanager create-secret \
    --name finshield/resend/api-key \
    --secret-string "re_xxxxx" \
    --region us-east-1
```

---

## Step 8: Setup CloudFront for Frontend

### S3 Bucket for Static Assets

```bash
# Create bucket
aws s3 mb s3://finshield-frontend --region us-east-1

# Build frontend and upload
cd frontend
npm run build
aws s3 sync out/ s3://finshield-frontend/ --delete
```

### CloudFront Distribution

```bash
# Create distribution pointing to S3 and ALB origin
aws cloudfront create-distribution \
    --origin-domain-name finshield-frontend.s3.amazonaws.com \
    --default-cache-behavior ViewerProtocolPolicy=redirect-to-https \
    --region us-east-1
```

---

## Step 9: Setup Custom Domain (Route 53)

```bash
# Create hosted zone (if not exists)
aws route53 create-hosted-zone \
    --name finshield.example.com \
    --caller-reference $(date +%s)

# Create alias record pointing to ALB
aws route53 change-resource-record-sets \
    --hosted-zone-id Z1234567890ABC \
    --change-batch '{
      "Changes": [{
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "finshield.example.com",
          "Type": "A",
          "AliasTarget": {
            "HostedZoneId": "Z35SXDOTRQ7X7K",
            "DNSName": "finshield-alb-123456.us-east-1.elb.amazonaws.com",
            "EvaluateTargetHealth": false
          }
        }
      }]
    }'
```

---

## Step 10: Setup SSL Certificate

```bash
# Request certificate
aws acm request-certificate \
    --domain-name finshield.example.com \
    --validation-method DNS \
    --region us-east-1

# Update ALB listener to use HTTPS
aws elbv2 modify-listener \
    --listener-arn arn:aws:elasticloadbalancing:... \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=arn:aws:acm:us-east-1:...:certificate/... \
    --region us-east-1
```

---

## Step 11: Monitor and Logging

### CloudWatch Logs

```bash
# Create log group
aws logs create-log-group \
    --log-group-name /ecs/finshield-backend \
    --region us-east-1

# Set retention (30 days)
aws logs put-retention-policy \
    --log-group-name /ecs/finshield-backend \
    --retention-in-days 30 \
    --region us-east-1
```

### CloudWatch Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
    --alarm-name finshield-high-cpu \
    --alarm-description "Alert when CPU exceeds 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --region us-east-1
```

---

## Step 12: Auto Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/finshield/finshield-backend \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 2 \
    --max-capacity 10 \
    --region us-east-1

# Create scaling policy
aws application-autoscaling put-scaling-policy \
    --policy-name finshield-scaling-policy \
    --service-namespace ecs \
    --resource-id service/finshield/finshield-backend \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration \
    "TargetValue=70.0,PredefinedMetricSpecification={PredefinedMetricType=ECSServiceAverageCPUUtilization}" \
    --region us-east-1
```

---

## Verification Checklist

- [ ] ECR repositories created and images pushed
- [ ] RDS database created and accessible
- [ ] ElastiCache Redis cluster created
- [ ] Secrets stored in AWS Secrets Manager
- [ ] ECS task definition registered
- [ ] ALB created and healthy
- [ ] ECS service running with 2+ tasks
- [ ] CloudFront distribution active
- [ ] Custom domain resolves
- [ ] SSL certificate installed
- [ ] Health checks passing
- [ ] Logs flowing to CloudWatch

---

## Local Testing Before Deployment

### Test Docker Images Locally

```bash
# Start services locally
docker-compose -f docker-compose.yml up -d

# Wait for services to be ready
sleep 10

# Test backend health
curl http://localhost:8000/api/v1/health

# Test frontend
curl http://localhost:3000

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

---

## Production Deployment Checklist

- [ ] **Security**
  - [ ] All secrets in AWS Secrets Manager
  - [ ] IAM roles properly configured
  - [ ] Security groups restrict traffic
  - [ ] SSL/TLS enabled on ALB

- [ ] **Database**
  - [ ] RDS backup retention set to 7+ days
  - [ ] Multi-AZ enabled
  - [ ] Monitoring enabled
  - [ ] Database encryption at rest

- [ ] **Backend**
  - [ ] Health checks configured
  - [ ] Auto-scaling enabled
  - [ ] CloudWatch alarms set
  - [ ] Log retention configured

- [ ] **Frontend**
  - [ ] CloudFront distribution active
  - [ ] S3 bucket locked down
  - [ ] Cache invalidation working
  - [ ] Custom domain working

---

## Troubleshooting

### Task fails to start
```
Check CloudWatch logs:
aws logs tail /ecs/finshield-backend --follow

Common issues:
- Database not ready (wait longer in startup script)
- Missing secrets in Secrets Manager
- Security group blocking database/cache access
```

### Health check failing
```
Check task logs for startup errors:
docker logs <container_id>

Verify dependencies:
- Can reach RDS endpoint
- Can reach ElastiCache endpoint
- All environment variables set
```

### High latency
```
Check CloudWatch metrics:
- ECS task CPU/memory usage
- RDS connections and CPU
- ElastiCache evictions

Solutions:
- Scale up ECS task size
- Add RDS read replicas
- Increase ElastiCache memory
```

---

## Cost Estimation (Monthly)

| Service | Size | Cost |
|---------|------|------|
| **ECS Fargate** | 2 × 512 CPU, 1GB RAM | $30-50 |
| **RDS PostgreSQL** | db.t4g.small | $25-30 |
| **ElastiCache Redis** | cache.t4g.small | $20-25 |
| **ALB** | 1 ALB | $15-20 |
| **CloudFront** | ~100GB transfer | $10-20 |
| **Data Transfer** | Inter-region | $0-10 |
| **Secrets Manager** | 5 secrets | $2 |
| **CloudWatch** | Logs + monitoring | $5-10 |
| **Route 53** | 1 hosted zone | $0.50 |
| **Total** | Production-grade | **$100-170/month** |

---

## Next Steps

1. ✅ Build and push Docker images
2. ✅ Create RDS and ElastiCache
3. ✅ Setup ECS cluster and services
4. ✅ Configure ALB and Route 53
5. ✅ Setup SSL/TLS
6. ✅ Monitor and scale
7. ⏳ Continuous integration (GitHub Actions)
8. ⏳ Automated deployments
9. ⏳ Disaster recovery plan

---

## Support

- AWS Documentation: https://docs.aws.amazon.com/
- Docker Docs: https://docs.docker.com/
- Next.js Deployment: https://nextjs.org/docs/deployment
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/

---

**Deployment Ready**: ✅ All Docker images optimized for AWS production deployment.
