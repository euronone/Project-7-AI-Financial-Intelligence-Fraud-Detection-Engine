# GitHub Secrets Setup for AWS Deployment

Complete guide to configure GitHub Actions with your AWS IAM credentials.

## 📋 Prerequisites

- AWS Account with IAM user created
- Access Key ID and Secret Access Key generated
- GitHub repository with admin access
- Appropriate IAM permissions for ECR, ECS, EKS, CloudFormation, RDS

---

## 🔑 Step 1: Create IAM User with Required Permissions

### Option A: Using AWS Console

1. Go to **IAM → Users → Create user**
2. Set username: `github-actions-deployer`
3. Attach policies with minimum required permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeRepositories",
        "ecr:ListImages"
      ],
      "Resource": "arn:aws:ecr:*:*:repository/finshield-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:DescribeContainerInstances",
        "ecs:UpdateService",
        "ecs:RegisterTaskDefinition"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:UpdateStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:GetTemplateSummary",
        "cloudformation:ListStackResources"
      ],
      "Resource": "arn:aws:cloudformation:*:*:stack/finshield-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:GetRole",
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::*:role/finshield-*"
    }
  ]
}
```

### Option B: Using AWS CLI

```bash
# Create IAM user
aws iam create-user --user-name github-actions-deployer

# Attach ECR permissions
aws iam attach-user-policy \
  --user-name github-actions-deployer \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

# Attach ECS permissions
aws iam attach-user-policy \
  --user-name github-actions-deployer \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceTaskExecutionRolePolicy

# Attach CloudFormation permissions
aws iam attach-user-policy \
  --user-name github-actions-deployer \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess  # Or more restrictive policy
```

---

## 🔐 Step 2: Generate Access Keys

### In AWS Console

1. Go to **IAM → Users → github-actions-deployer**
2. Click **Security credentials** tab
3. Scroll to **Access keys** section
4. Click **Create access key**
5. Choose **Application running outside AWS** (for GitHub Actions)
6. Copy and save:
   - **Access Key ID** (e.g., `AKIA...`)
   - **Secret Access Key** (e.g., `wJalo...`)
   - ⚠️ **IMPORTANT**: Save the secret key immediately (you won't see it again!)

### In AWS CLI

```bash
# Create access key
aws iam create-access-key --user-name github-actions-deployer

# Output will show:
# AccessKeyId: AKIA...
# SecretAccessKey: wJalo...
```

---

## 📝 Step 3: Add Secrets to GitHub

### Method 1: Using GitHub Web Interface

1. Go to **Repository Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Add each secret:

#### Secret 1: AWS Access Key ID
- **Name**: `AWS_ACCESS_KEY_ID`
- **Value**: `AKIA...` (from Step 2)
- Click **Add secret**

#### Secret 2: AWS Secret Access Key
- **Name**: `AWS_SECRET_ACCESS_KEY`
- **Value**: `wJalo...` (from Step 2)
- Click **Add secret**

#### Secret 3: Backend ALB Endpoint (Optional, for health checks)
- **Name**: `BACKEND_ALB_ENDPOINT`
- **Value**: Will be created by CloudFormation, update later
- Click **Add secret**

### Method 2: Using GitHub CLI

```bash
# Install GitHub CLI if not already installed
# https://cli.github.com/

# Login to GitHub
gh auth login

# Set your repository
export REPO=your-username/finshield

# Add AWS Access Key ID
gh secret set AWS_ACCESS_KEY_ID --repo $REPO

# Add AWS Secret Access Key
gh secret set AWS_SECRET_ACCESS_KEY --repo $REPO
```

### Method 3: Using GitHub REST API

```bash
# First, get your GitHub Personal Access Token
# Go to Settings → Developer settings → Personal access tokens

# Then:
curl -X POST \
  https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/actions/secrets/AWS_ACCESS_KEY_ID \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"encrypted_value":"YOUR_ENCRYPTED_VALUE"}'
```

---

## ✅ Step 4: Verify Secrets Configuration

### Check Secrets in GitHub UI

1. Go to **Settings → Secrets and variables → Actions**
2. You should see:
   - ✓ `AWS_ACCESS_KEY_ID` (masked)
   - ✓ `AWS_SECRET_ACCESS_KEY` (masked)

### Test Connection in GitHub Actions

Create a test workflow file: `.github/workflows/test-aws-connection.yml`

```yaml
name: Test AWS Connection

on: workflow_dispatch

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Verify AWS Access
        run: |
          echo "✓ Testing AWS credentials..."
          aws sts get-caller-identity
          
          echo "✓ Listing ECR repositories..."
          aws ecr describe-repositories --region us-east-1
          
          echo "✓ AWS connection successful!"
```

Run this workflow:
1. Go to **Actions** tab
2. Select **Test AWS Connection**
3. Click **Run workflow**
4. Wait for completion and verify output

---

## 🚀 Step 5: Configure Deployment Workflows

### Update Environment Variables in Workflows

The workflows already use your credentials from GitHub Secrets. Just verify:

**File**: `.github/workflows/deploy-aws-ecs.yml`
```yaml
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ env.AWS_REGION }}
```

**File**: `.github/workflows/deploy-aws-eks.yml`
```yaml
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ env.AWS_REGION }}
```

**File**: `.github/workflows/aws-infrastructure.yml`
```yaml
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ env.AWS_REGION }}
```

---

## 📊 Workflow Triggers

### Deploy to ECS
```bash
# Automatically triggers on push to main branch
git push origin main

# Or manually from GitHub UI
# Actions → Deploy to AWS ECS → Run workflow
```

### Deploy to EKS
```bash
# Automatically triggers when Kubernetes manifests change
git add kubernetes/
git commit -m "Update k8s manifests"
git push origin main

# Or manually trigger
# Actions → Deploy to AWS EKS → Run workflow
```

### Deploy Infrastructure
```bash
# Automatically triggers when CloudFormation templates change
git add infrastructure/cloudformation/
git commit -m "Update infrastructure"
git push origin main

# Or manually trigger with environment selection
# Actions → AWS Infrastructure → Run workflow → Select staging/production
```

---

## 🔒 Security Best Practices

### ✅ DO
- ✓ Use a dedicated IAM user for GitHub Actions
- ✓ Limit IAM permissions to minimum required (least privilege)
- ✓ Rotate access keys every 90 days
- ✓ Monitor GitHub Secret access in AWS CloudTrail
- ✓ Use branch protection rules to require reviews
- ✓ Enable GitHub Secret scanning/protection
- ✓ Store secrets as GitHub Encrypted Secrets (not in code)

### ❌ DON'T
- ✗ Don't use root AWS account credentials
- ✗ Don't commit secrets to git
- ✗ Don't use overly broad IAM permissions (e.g., `*:*`)
- ✗ Don't share credentials in chat/email
- ✗ Don't hardcode secrets in workflow files
- ✗ Don't store secrets in git history (even if later deleted)

---

## 🔄 Rotating Access Keys

### Every 90 Days:

1. **Create new access key** in AWS IAM
2. **Update GitHub Secrets** with new key
3. **Test in GitHub Actions** (run test workflow)
4. **Delete old access key** from AWS IAM

```bash
# List all access keys for user
aws iam list-access-keys --user-name github-actions-deployer

# Deactivate old key (before deleting)
aws iam update-access-key \
  --user-name github-actions-deployer \
  --access-key-id AKIA_OLD_KEY_ID \
  --status Inactive

# Delete old key after confirming new key works
aws iam delete-access-key \
  --user-name github-actions-deployer \
  --access-key-id AKIA_OLD_KEY_ID
```

---

## 🛠️ Troubleshooting

### "InvalidClientTokenId" Error
```
Error: AWS credentials are invalid
Solution: 
  1. Verify Access Key ID in GitHub Secret
  2. Check Secret Access Key is complete
  3. Ensure IAM user has permissions
  4. Try creating new access keys
```

### "User: ... is not authorized"
```
Error: Insufficient permissions
Solution:
  1. Check IAM policy attached to user
  2. Add missing permissions for ECR, ECS, CloudFormation
  3. Verify user can access specified AWS region
```

### "No valid credentials could be found"
```
Error: Credentials not loaded
Solution:
  1. Verify secrets are named exactly:
     - AWS_ACCESS_KEY_ID
     - AWS_SECRET_ACCESS_KEY
  2. Check workflow file uses correct secret syntax:
     ${{ secrets.AWS_ACCESS_KEY_ID }}
  3. Verify secrets not expired or revoked
```

### CloudFormation Stack Creation Fails
```
Error: User not authorized to perform: cloudformation:CreateStack
Solution:
  1. Add CloudFormation permissions to IAM user
  2. Add IAM role creation permissions
  3. Verify account has service limits not exceeded
```

---

## 📋 Verification Checklist

- [ ] IAM user created: `github-actions-deployer`
- [ ] Access Key ID generated and copied
- [ ] Secret Access Key generated and copied securely
- [ ] IAM policies attached to user
- [ ] GitHub Secret `AWS_ACCESS_KEY_ID` created
- [ ] GitHub Secret `AWS_SECRET_ACCESS_KEY` created
- [ ] Test workflow executed successfully
- [ ] All workflows can access AWS resources
- [ ] ECR repositories accessible
- [ ] CloudFormation permissions verified
- [ ] ECS/EKS access confirmed

---

## 🚀 Next Steps

1. ✅ Configure GitHub Secrets (this guide)
2. ✅ Test AWS connection with test workflow
3. ✅ Deploy infrastructure: `Actions → AWS Infrastructure`
4. ✅ Deploy to ECS: `Actions → Deploy to AWS ECS`
5. ✅ Monitor CloudWatch dashboard
6. ✅ Set up Grafana for custom dashboards

---

## 📞 Quick Reference

**GitHub Secret Names:**
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
BACKEND_ALB_ENDPOINT (optional)
```

**AWS Regions:**
```
us-east-1 (default)
us-west-2
eu-west-1
ap-southeast-1
```

**Workflow Files:**
```
.github/workflows/deploy-aws-ecs.yml
.github/workflows/deploy-aws-eks.yml
.github/workflows/aws-infrastructure.yml
.github/workflows/test-aws-connection.yml (test)
```

---

**Last Updated**: 2026-04-06
**Status**: Ready for GitHub Actions CI/CD
