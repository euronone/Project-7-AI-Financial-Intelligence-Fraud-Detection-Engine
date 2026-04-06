# AWS Deployment Checklist

Complete checklist for deploying FinShield to AWS with full observability.

## Pre-Deployment Setup

### AWS Account & Permissions
- [ ] AWS Account created with appropriate billing setup
- [ ] IAM user created with programmatic access
- [ ] AWS CLI configured: `aws configure`
- [ ] Verify AWS credentials: `aws sts get-caller-identity`
- [ ] Required IAM permissions: ECS, EKS, RDS, ElastiCache, CloudWatch, CloudFormation, ECR

### Local Environment
- [ ] Docker installed and running
- [ ] kubectl installed: `brew install kubectl`
- [ ] AWS CLI v2 installed
- [ ] Helm installed: `brew install helm`
- [ ] kustomize installed: `brew install kustomize`
- [ ] Git configured with SSH keys

### Repository Setup
- [ ] Repository cloned locally
- [ ] .env file created with required variables
- [ ] Git branch checked out: `development_2`
- [ ] All files committed (no uncommitted changes)

## Infrastructure Deployment

### Phase 1: Core AWS Services

#### ECR (Container Registry)
- [ ] ECR repositories created for backend and frontend
- [ ] Container images built locally and tested
- [ ] Images pushed to ECR
- [ ] Image scanning enabled
- [ ] Repository lifecycle policies configured

#### VPC Network
- [ ] VPC created (10.0.0.0/16)
- [ ] Public subnets created (2 AZs)
- [ ] Private subnets created (2 AZs)
- [ ] NAT Gateways deployed
- [ ] Internet Gateway attached
- [ ] Route tables configured
- [ ] VPC Flow Logs enabled for security monitoring

#### Secrets Manager
- [ ] Database credentials stored
- [ ] JWT secret stored
- [ ] Encryption key stored
- [ ] Redis URL stored
- [ ] API keys stored (Resend, Twilio, etc.)

### Phase 2: Database & Cache

#### RDS PostgreSQL
- [ ] RDS instance created (db.t3.small for staging)
- [ ] Database name: `finshield`
- [ ] Master user: `postgres`
- [ ] Backup retention: 7 days (staging) / 30 days (production)
- [ ] Multi-AZ: disabled (staging) / enabled (production)
- [ ] CloudWatch logs enabled
- [ ] Enhanced monitoring enabled
- [ ] Database security group configured
- [ ] Alembic migrations run: `poetry run alembic upgrade head`

#### ElastiCache Redis
- [ ] Redis cluster created (cache.t3.small for staging)
- [ ] Automatic failover: disabled (staging) / enabled (production)
- [ ] Encryption at rest: enabled
- [ ] Encryption in transit: enabled
- [ ] Cache subnet group configured
- [ ] Security group configured

### Phase 3: Container Orchestration

#### Option A: ECS Deployment
- [ ] CloudFormation stack created for ECS
- [ ] ECS Cluster created
- [ ] ALB created and configured
- [ ] Target groups created (backend + frontend)
- [ ] Task definitions created
- [ ] Backend service deployed
- [ ] Frontend service deployed
- [ ] Auto-scaling configured (CPU & memory)
- [ ] Health checks verified

#### Option B: EKS Deployment
- [ ] CloudFormation stack created for EKS
- [ ] EKS Cluster created (1.28+)
- [ ] Node groups created (2-3 nodes)
- [ ] OIDC provider configured
- [ ] kubeconfig updated: `aws eks update-kubeconfig ...`
- [ ] Cluster connectivity verified: `kubectl cluster-info`
- [ ] Metrics server installed
- [ ] AWS Load Balancer Controller installed
- [ ] Namespace created: `kubectl apply -f kubernetes/base/namespace.yaml`
- [ ] Secrets created: `kubectl create secret generic finshield-secrets ...`
- [ ] Manifests deployed: `kubectl apply -f kubernetes/`
- [ ] Deployments verified: `kubectl get deployments -n finshield`
- [ ] HPA configured for auto-scaling

### Phase 4: Monitoring & Logging

#### CloudWatch Configuration
- [ ] CloudWatch log groups created
- [ ] Log retention policies set (30 days)
- [ ] Log filtering configured
- [ ] Custom metrics enabled
- [ ] Dashboard created
- [ ] Metric filters created:
  - [ ] Fraud detection count
  - [ ] API error count
  - [ ] Model inference time

#### CloudWatch Alarms
- [ ] ECS/Container CPU alarm (>80%)
- [ ] ECS/Container Memory alarm (>85%)
- [ ] ALB latency alarm (>1s)
- [ ] ALB error rate alarm (>10 errors)
- [ ] RDS CPU alarm (>80%)
- [ ] RDS storage alarm (<10GB)
- [ ] SNS topic created for notifications
- [ ] Email subscription verified

#### Grafana Setup
- [ ] Grafana deployed to EKS/EC2
- [ ] CloudWatch data source configured
- [ ] Default dashboards imported
- [ ] Custom fraud detection dashboard created
- [ ] Admin user configured
- [ ] Alert rules configured

### Phase 5: Application Configuration

#### Backend Configuration
- [ ] Environment variables set in CloudFormation parameters
- [ ] CloudWatch logging enabled
- [ ] Metrics collection enabled
- [ ] CORS configured
- [ ] Rate limiting configured
- [ ] Health check endpoint verified
- [ ] Database migrations completed
- [ ] Sample data seeded (if applicable)

#### Frontend Configuration
- [ ] Environment variables set (API URL, etc.)
- [ ] Build process tested locally
- [ ] Docker image built and pushed
- [ ] Health check endpoint configured
- [ ] CDN caching configured (if applicable)

### Phase 6: Network & DNS

#### DNS Configuration
- [ ] Route 53 hosted zone created
- [ ] Domain registered or transferred
- [ ] DNS records created for:
  - [ ] finshield.ai → ALB/Load Balancer
  - [ ] api.finshield.ai → Backend ALB
  - [ ] www.finshield.ai → Frontend ALB

#### SSL/TLS Certificates
- [ ] ACM certificate requested for *.finshield.ai
- [ ] Certificate validation completed
- [ ] Certificate attached to ALB listener
- [ ] HTTPS redirect configured
- [ ] HSTS header configured

### Phase 7: Deployment & Testing

#### GitHub Actions CI/CD
- [ ] GitHub Actions workflows configured
- [ ] AWS credentials stored as secrets
- [ ] ECR login workflow tested
- [ ] ECS deployment workflow tested
- [ ] EKS deployment workflow tested
- [ ] Build caching configured

#### Smoke Tests
- [ ] Backend health check passes: `curl https://api.finshield.ai/api/v1/health`
- [ ] Frontend loads: `https://finshield.ai`
- [ ] Database connectivity verified
- [ ] Redis connectivity verified
- [ ] CloudWatch logs appearing
- [ ] Metrics appearing in dashboard

#### Load Testing (Production)
- [ ] Locust load test configured
- [ ] Target: 1,000 TPS
- [ ] P95 latency: <200ms
- [ ] Error rate: <1%
- [ ] Auto-scaling verified under load

### Phase 8: Security & Compliance

#### Security Configuration
- [ ] Security groups properly configured
- [ ] VPC Flow Logs enabled
- [ ] CloudTrail enabled for audit logging
- [ ] Secrets encrypted at rest
- [ ] Database encrypted at rest
- [ ] Data encrypted in transit (TLS 1.3)
- [ ] IAM roles use least privilege
- [ ] No hardcoded credentials in code
- [ ] API key rotation configured

#### Compliance
- [ ] ISO 27001 controls implemented
- [ ] SOC 2 Type II compliance checklist
- [ ] GDPR compliance verified (data retention, consent)
- [ ] PCI-DSS compliance (if handling card data)
- [ ] Security policy documented

### Phase 9: Backup & Disaster Recovery

#### Backup Configuration
- [ ] RDS automated backups: 7 days (staging) / 30 days (production)
- [ ] RDS backup window: 03:00-04:00 UTC
- [ ] Cross-region backup enabled (production)
- [ ] Test backup restoration procedure
- [ ] ECR image retention: 30 days
- [ ] EBS snapshots: enabled

#### Disaster Recovery Plan
- [ ] RTO (Recovery Time Objective): 1 hour
- [ ] RPO (Recovery Point Objective): 15 minutes
- [ ] Failover procedure documented
- [ ] Database failover tested
- [ ] Multi-region failover plan (production)

## Post-Deployment Validation

### Functional Testing
- [ ] Create test transaction via API
- [ ] Verify fraud detection working
- [ ] Check transaction in database
- [ ] Verify alerts created
- [ ] Test customer lookup
- [ ] Test fraud scoring endpoint
- [ ] Verify all API endpoints responding

### Performance Validation
- [ ] API response time: <200ms (p95)
- [ ] Database query time: <100ms
- [ ] Model inference time: <50ms
- [ ] Page load time: <2s
- [ ] CloudWatch metrics flowing
- [ ] Grafana dashboard operational

### Monitoring Validation
- [ ] CloudWatch dashboard populated
- [ ] Log aggregation working
- [ ] Custom metrics appearing
- [ ] Alarms configured and tested
- [ ] Grafana queries working
- [ ] Email notifications working

## Documentation & Handoff

### Documentation
- [ ] README updated with AWS deployment info
- [ ] Architecture diagram updated
- [ ] Deployment guide completed: AWS_DEPLOYMENT_GUIDE.md
- [ ] Runbook created for common operations
- [ ] Troubleshooting guide completed
- [ ] API documentation updated

### Team Training
- [ ] Team trained on AWS console navigation
- [ ] Deployment process documented and reviewed
- [ ] On-call procedures defined
- [ ] Escalation paths documented
- [ ] Access granted to all team members

### Monitoring Setup
- [ ] Team added to CloudWatch alarms
- [ ] Slack/email notifications configured
- [ ] On-call rotation established
- [ ] Incident response plan documented

## Maintenance & Operations

### Regular Tasks
- [ ] Weekly log review
- [ ] Monthly cost optimization review
- [ ] Quarterly security audit
- [ ] Backup restoration test (monthly)
- [ ] Database maintenance window scheduled
- [ ] Dependency updates scheduled

### Optimization
- [ ] Review slow queries (>100ms)
- [ ] Optimize CloudWatch queries
- [ ] Review cost trends
- [ ] Evaluate reserved instances or savings plans
- [ ] Review auto-scaling metrics

---

## Sign-Off

- **Deployment Date**: _______________
- **Deployed By**: _______________
- **Reviewed By**: _______________
- **Approved For Production**: _______________

---

**Last Updated**: 2026-04-06
**Status**: Complete and Ready for Use
