#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
REGION=${AWS_REGION:-us-east-1}
ENVIRONMENT=${ENVIRONMENT:-staging}
CLUSTER_NAME=finshield-eks-cluster
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo -e "${YELLOW}=== FinShield EKS Deployment ===${NC}"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"
echo "Cluster: $CLUSTER_NAME"

# Update kubeconfig
echo -e "${YELLOW}Updating kubeconfig...${NC}"
aws eks update-kubeconfig \
    --region $REGION \
    --name $CLUSTER_NAME

# Verify cluster connectivity
echo -e "${YELLOW}Verifying cluster connectivity...${NC}"
if kubectl cluster-info 2>/dev/null; then
    echo -e "${GREEN}✓ Cluster is accessible${NC}"
else
    echo -e "${RED}Error: Cannot access cluster${NC}"
    exit 1
fi

# Create namespace
echo -e "${YELLOW}Creating Kubernetes namespace...${NC}"
kubectl apply -f kubernetes/base/namespace.yaml

# Create secrets
echo -e "${YELLOW}Creating Kubernetes secrets...${NC}"
kubectl create secret generic finshield-secrets \
    --from-literal=database-url="$DATABASE_URL" \
    --from-literal=jwt-secret="$JWT_SECRET" \
    --from-literal=encryption-key="$ENCRYPTION_KEY" \
    --from-literal=redis-url="$REDIS_URL" \
    -n finshield \
    --dry-run=client -o yaml | kubectl apply -f -

# Apply Kubernetes manifests
echo -e "${YELLOW}Deploying Kubernetes manifests...${NC}"
cd kubernetes
kustomize build overlays/$ENVIRONMENT > final-manifest.yaml
kubectl apply -f final-manifest.yaml
cd ..

# Wait for deployments
echo -e "${YELLOW}Waiting for deployments to be ready...${NC}"
kubectl rollout status deployment/finshield-backend -n finshield --timeout=5m
kubectl rollout status deployment/finshield-frontend -n finshield --timeout=5m

# Get service endpoints
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo -e "${YELLOW}Service Endpoints:${NC}"
kubectl get svc -n finshield -o wide

echo ""
echo -e "${YELLOW}Pod Status:${NC}"
kubectl get pods -n finshield

echo ""
echo -e "${YELLOW}Deployment Status:${NC}"
kubectl get deployments -n finshield

echo ""
echo "Next steps:"
echo "1. Configure AWS Load Balancer Controller for ingress"
echo "2. Set up Grafana for monitoring (see infrastructure/grafana/)"
echo "3. Configure auto-scaling policies"
echo "4. Monitor logs: kubectl logs -f deployment/finshield-backend -n finshield"
