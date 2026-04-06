# FinShield AWS Deployment Guide

Complete guide for deploying FinShield to AWS using ECS, EKS, CloudWatch, and Grafana.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Quick Start](#quick-start)
4. [ECS Deployment](#ecs-deployment)
5. [EKS Deployment](#eks-deployment)
6. [Monitoring Setup](#monitoring-setup)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
- AWS CLI v2: `brew install awscli` or `choco install awscliv2`
- kubectl: `brew install kubectl` or `choco install kubernetes-cli`
- Helm: `brew install helm` or `choco install kubernetes-helm`
- Docker: `brew install docker` or `choco install docker`
- kustomize: `brew install kustomize` or `choco install kustomize`

### AWS Account Setup

1. **Create AWS Account** (if not already done)
   ```bash
   # Log in to AWS Console
   # Create IAM user with programmatic access
   ```

2. **Configure AWS CLI**
   ```bash
   aws configure
   # Enter AWS Access Key ID
   # Enter AWS Secret Access Key
   # Default region: us-east-1
   # Default output format: json
   ```

3. **Create S3 Bucket for Terraform State** (optional but recommended)
   ```bash
   aws s3 mb s3://finshield-terraform-state-$(date +%s)
   ```

4. **Create ECR Repositories**
   ```bash
   aws ecr create-repository --repository-name finshield-backend --image-scanning-configuration scanOnPush=true
   aws ecr create-repository --repository-name finshield-frontend --image-scanning-configuration scanOnPush=true
   ```

### Required Environment Variables

```bash
# AWS Configuration
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ENVIRONMENT=staging  # or production

# Database
export DATABASE_URL="postgresql+asyncpg://user:password@rds-endpoint:5432/finshield"
export REDIS_URL="redis://redis-endpoint:6379/0"

# Application Secrets
export JWT_SECRET="your-jwt-secret-here"
export ENCRYPTION_KEY="your-encryption-key-here"
export RESEND_API_KEY="your-resend-api-key"
export TWILIO_ACCOUNT_SID="your-twilio-sid"
export TWILIO_AUTH_TOKEN="your-twilio-token"
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    AWS Region: us-east-1                │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Application Load Balancer           │  │
│  │  (Handles HTTPS, routing, health checks)        │  │
│  └──────┬───────────────────────────────┬──────────┘  │
│         │                               │             │
│  ┌──────▼────────────┐        ┌─────────▼──────┐    │
│  │  ECS/EKS Backend  │        │ ECS/EKS Frontend
│  │  (FastAPI)        │        │ (Next.js)       │    │
│  │  ├─ CloudWatch    │        ├─ CloudWatch     │    │
│  │  └─ Auto-Scaling  │        └─ Auto-Scaling   │    │
│  └─────────┬─────────┘        └────────┬────────┘    │
│            │                           │             │
│  ┌─────────▼───────────────────────────▼──────┐     │
│  │    RDS PostgreSQL + ElastiCache Redis      │     │
│  │    (Managed database & cache)              │     │
│  └────────────────────────────────────────────┘     │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  CloudWatch Monitoring & Grafana             │  │
│  │  ├─ Real-time metrics                       │  │
│  │  ├─ Log aggregation                         │  │
│  │  ├─ Alarms & notifications                  │  │
│  │  └─ Custom dashboards                       │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Clone Repository
```bash
git clone <repo-url>
cd finshield
```

### 2. Set Environment Variables
```bash
source scripts/setup-env.sh
# Or manually export the variables from Prerequisites section
```

### 3. Deploy Infrastructure

For **ECS** deployment:
```bash
chmod +x scripts/deploy-aws.sh
./scripts/deploy-aws.sh
```

For **EKS** deployment:
```bash
chmod +x scripts/deploy-eks.sh
./scripts/deploy-eks.sh
```

### 4. Configure DNS
```bash
# Get ALB/EKS endpoint
aws cloudformation describe-stacks --stack-name finshield-ecs-$ENVIRONMENT \
  --query 'Stacks[0].Outputs[?OutputKey==`ALBEndpoint`].OutputValue' \
  --output text

# Create Route 53 record pointing to ALB
aws route53 change-resource-record-sets --hosted-zone-id <zone-id> \
  --change-batch file://route53-change.json
```

---

## ECS Deployment

### Architecture

ECS Fargate provides a serverless container orchestration platform.

```
Application Load Balancer
    ↓
┌───────────────────────────────────────────┐
│         ECS Cluster (Fargate)             │
│  ┌──────────────────────────────────────┐ │
│  │   Backend Service (Min: 1, Max: 10)  │ │
│  │   ├─ Task CPU: 256-512 mCPU         │ │
│  │   ├─ Task Memory: 512MB-1GB         │ │
│  │   └─ Auto-scaling: CPU & Memory     │ │
│  └──────────────────────────────────────┘ │
│  ┌──────────────────────────────────────┐ │
│  │  Frontend Service (Min: 1, Max: 8)  │ │
│  │  ├─ Task CPU: 256 mCPU              │ │
│  │  ├─ Task Memory: 512MB              │ │
│  │  └─ Auto-scaling: CPU & Memory      │ │
│  └──────────────────────────────────────┘ │
└───────────────────────────────────────────┘
```

### Deploy to ECS

1. **Build and Push Images**
   ```bash
   ./scripts/deploy-aws.sh
   ```

2. **Monitor Deployment**
   ```bash
   # Watch ECS service
   watch -n 1 'aws ecs describe-services \
     --cluster finshield-cluster \
     --services finshield-backend-service finshield-frontend-service \
     --query "services[*].[serviceName,status,runningCount,desiredCount]"'

   # Check task logs
   aws logs tail /ecs/finshield-backend-staging --follow
   ```

3. **Verify Health**
   ```bash
   curl http://<ALB-endpoint>/api/v1/health
   ```

### Update Service

```bash
# Update backend service with new image
aws ecs update-service \
  --cluster finshield-cluster \
  --service finshield-backend-service \
  --force-new-deployment
```

---

## EKS Deployment

### Architecture

EKS provides managed Kubernetes cluster.

```
AWS Load Balancer Controller (Ingress)
    ↓
┌───────────────────────────────────────────┐
│    EKS Cluster (3 Node Groups)            │
│  ┌──────────────────────────────────────┐ │
│  │ finshield-backend Deployment         │ │
│  │ Replicas: 2-10 (HPA enabled)        │ │
│  └──────────────────────────────────────┘ │
│  ┌──────────────────────────────────────┐ │
│  │ finshield-frontend Deployment        │ │
│  │ Replicas: 2-8 (HPA enabled)         │ │
│  └──────────────────────────────────────┘ │
│  ┌──────────────────────────────────────┐ │
│  │ Monitoring Namespace                 │ │
│  │ ├─ Prometheus                        │ │
│  │ ├─ Grafana                           │ │
│  │ └─ Loki (optional)                   │ │
│  └──────────────────────────────────────┘ │
└───────────────────────────────────────────┘
```

### Prerequisites for EKS

1. **Create EKS Cluster** (using CloudFormation or eksctl)
   ```bash
   eksctl create cluster \
     --name finshield-eks-cluster \
     --region us-east-1 \
     --nodegroup-name finshield-nodes \
     --nodes 3 \
     --nodes-min 3 \
     --nodes-max 10
   ```

2. **Install AWS Load Balancer Controller**
   ```bash
   helm repo add eks https://aws.github.io/eks-charts
   helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
     -n kube-system \
     --set clusterName=finshield-eks-cluster
   ```

3. **Install Metrics Server** (for HPA)
   ```bash
   kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
   ```

### Deploy to EKS

1. **Update kubeconfig**
   ```bash
   aws eks update-kubeconfig \
     --region us-east-1 \
     --name finshield-eks-cluster
   ```

2. **Run Deployment Script**
   ```bash
   export DATABASE_URL="..."  # Set required env vars
   ./scripts/deploy-eks.sh
   ```

3. **Verify Deployment**
   ```bash
   kubectl get all -n finshield
   kubectl get hpa -n finshield
   kubectl logs -f deployment/finshield-backend -n finshield
   ```

4. **Expose Services**
   ```bash
   # For testing (port-forward)
   kubectl port-forward -n finshield svc/finshield-backend-service 8000:8000

   # For production (use Ingress)
   kubectl apply -f kubernetes/base/ingress.yaml
   ```

---

## Monitoring Setup

### CloudWatch Dashboards

Automatically created by CloudFormation:

```bash
# View dashboard
aws cloudwatch get-dashboard --dashboard-name finshield-main-dashboard

# Open in console
open "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=finshield-main-dashboard"
```

### Key Metrics

| Metric | Namespace | Use Case |
|--------|-----------|----------|
| `FraudDetectionCount` | FinShield | Track fraud detections |
| `FraudScore` | FinShield | Monitor score distribution |
| `APILatency` | FinShield | API performance |
| `ModelInferenceTime` | FinShield | ML model performance |
| `APIErrorCount` | FinShield | Error tracking |
| `CPUUtilization` | AWS/ECS | Container CPU |
| `MemoryUtilization` | AWS/ECS | Container memory |

### Custom Alarms

Pre-configured alarms:
- ECS High CPU (>80%)
- ECS High Memory (>85%)
- ALB High Latency (>1s)
- ALB High Error Rate (>10 errors/5min)
- RDS Low Storage (<10GB)

### Grafana Setup

1. **Deploy Grafana**
   ```bash
   kubectl apply -f infrastructure/grafana/grafana-deployment.yaml
   ```

2. **Access Grafana**
   ```bash
   kubectl port-forward -n monitoring svc/grafana 3000:3000
   # Open http://localhost:3000
   # Default credentials: admin / <GF_SECURITY_ADMIN_PASSWORD>
   ```

3. **Add CloudWatch Data Source**
   - Configuration → Data Sources → Add CloudWatch
   - Use IAM role attached to EKS nodes
   - Select region: us-east-1

4. **Import Dashboards**
   - Dashboards → Import
   - Use provided dashboard JSONs from `infrastructure/grafana/`

### CloudWatch Logs Insights Queries

Pre-configured queries:

```
# Fraud analysis by decision
fields @timestamp, @message, fraud_score, decision
| filter ispresent(fraud_score)
| stats count() as total,
        sum(case when decision = 'BLOCK' then 1 else 0 end) as blocked
        by decision

# API latency percentiles
fields @duration
| filter @duration > 0
| stats pct(@duration, 50) as p50,
        pct(@duration, 95) as p95,
        pct(@duration, 99) as p99

# Error rate
fields @message
| filter @message like /ERROR|EXCEPTION/
| stats count() as errors by bin(5m)
```

---

## Troubleshooting

### Common Issues

#### 1. ECS Tasks Not Starting
```bash
# Check task logs
aws logs tail /ecs/finshield-backend-staging --follow

# Describe task
aws ecs describe-task-definition --task-definition finshield-backend-task

# Check CloudFormation stack
aws cloudformation describe-stack-events --stack-name finshield-ecs-staging
```

#### 2. Database Connection Issues
```bash
# Test RDS connection
psql -h <RDS-endpoint> -U postgres -d finshield

# Check security groups
aws ec2 describe-security-groups --filters Name=group-name,Values=finshield-db-sg
```

#### 3. High Latency
```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace FinShield \
  --metric-name APILatency \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# Scale up ECS service
aws ecs update-service \
  --cluster finshield-cluster \
  --service finshield-backend-service \
  --desired-count 5
```

#### 4. Out of Memory
```bash
# Check current task memory
aws ecs describe-task-definition \
  --task-definition finshield-backend-task \
  --query 'taskDefinition.containerDefinitions[0].memory'

# Increase memory (register new task definition)
aws ecs register-task-definition \
  --cli-input-json file://task-definition-updated.json
```

### Health Checks

```bash
# ECS service health
aws ecs describe-services \
  --cluster finshield-cluster \
  --services finshield-backend-service \
  --query 'services[0].[serviceName,status,runningCount,desiredCount,deployments[0].status]'

# EKS pod health
kubectl get pods -n finshield -o wide
kubectl describe pod <pod-name> -n finshield

# Database connectivity
aws rds describe-db-instances \
  --db-instance-identifier finshield-db \
  --query 'DBInstances[0].[DBInstanceIdentifier,DBInstanceStatus,AvailabilityZone]'

# Load balancer health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>
```

---

## Rollback Procedures

### ECS Rollback
```bash
# Get previous task definition
aws ecs describe-services \
  --cluster finshield-cluster \
  --services finshield-backend-service \
  --query 'services[0].deployments'

# Update service to previous task definition
aws ecs update-service \
  --cluster finshield-cluster \
  --service finshield-backend-service \
  --task-definition finshield-backend-task:N
```

### EKS Rollback
```bash
# Undo deployment
kubectl rollout undo deployment/finshield-backend -n finshield
kubectl rollout status deployment/finshield-backend -n finshield
```

---

## Cost Optimization

### ECS Cost Saving
- Use Fargate Spot for non-critical environments
- Right-size task CPU/memory
- Use lifecycle policies for ECR images

### EKS Cost Saving
- Use EC2 Spot instances for node groups
- Enable cluster autoscaler
- Use Compute Savings Plans

### Database Cost Saving
- Use RDS Savings Plans for reserved capacity
- Enable Multi-AZ only for production
- Use read replicas for read-heavy workloads

---

## Support & Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [Grafana Documentation](https://grafana.com/docs/)

---

**Last Updated**: 2026-04-06
**Status**: Production Ready
