#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Add AWS Credentials to GitHub Secrets               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}✗ GitHub CLI is not installed${NC}"
    echo "Install from: https://cli.github.com/"
    exit 1
fi

# Verify GitHub login
if ! gh auth status &>/dev/null; then
    echo -e "${YELLOW}Logging in to GitHub...${NC}"
    gh auth login
fi

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q)
if [ -z "$REPO" ]; then
    echo -e "${RED}Error: Could not determine repository${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Repository: $REPO${NC}"
echo ""

# Get AWS credentials
echo -e "${YELLOW}AWS Credentials Setup${NC}"
echo "===================="
echo ""

read -p "Enter AWS Access Key ID (AKIA...): " AWS_ACCESS_KEY_ID
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo -e "${RED}Error: Access Key ID is required${NC}"
    exit 1
fi

read -sp "Enter AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
echo ""
if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo -e "${RED}Error: Secret Access Key is required${NC}"
    exit 1
fi

read -p "Enter AWS Account ID (optional, for reference): " AWS_ACCOUNT_ID

echo ""
echo -e "${YELLOW}Adding Secrets to GitHub...${NC}"
echo "============================"
echo ""

# Add Access Key ID
echo "Adding AWS_ACCESS_KEY_ID..."
echo "$AWS_ACCESS_KEY_ID" | gh secret set AWS_ACCESS_KEY_ID --repo "$REPO"
echo -e "${GREEN}✓ AWS_ACCESS_KEY_ID added${NC}"

# Add Secret Access Key
echo "Adding AWS_SECRET_ACCESS_KEY..."
echo "$AWS_SECRET_ACCESS_KEY" | gh secret set AWS_SECRET_ACCESS_KEY --repo "$REPO"
echo -e "${GREEN}✓ AWS_SECRET_ACCESS_KEY added${NC}"

# Optional: Store account ID as environment variable (not secret)
if [ -n "$AWS_ACCOUNT_ID" ]; then
    echo ""
    echo "Storing AWS Account ID as repository variable..."
    gh variable set AWS_ACCOUNT_ID --body "$AWS_ACCOUNT_ID" --repo "$REPO" 2>/dev/null || true
    echo -e "${GREEN}✓ AWS_ACCOUNT_ID stored${NC}"
fi

echo ""
echo -e "${YELLOW}Verifying Secrets...${NC}"
echo "==================="
echo ""

# List all secrets
SECRETS=$(gh secret list --repo "$REPO" 2>/dev/null | grep -E "AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY" || true)

if echo "$SECRETS" | grep -q "AWS_ACCESS_KEY_ID"; then
    echo -e "${GREEN}✓ AWS_ACCESS_KEY_ID is configured${NC}"
else
    echo -e "${RED}✗ AWS_ACCESS_KEY_ID not found${NC}"
    exit 1
fi

if echo "$SECRETS" | grep -q "AWS_SECRET_ACCESS_KEY"; then
    echo -e "${GREEN}✓ AWS_SECRET_ACCESS_KEY is configured${NC}"
else
    echo -e "${RED}✗ AWS_SECRET_ACCESS_KEY not found${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           GitHub Secrets Setup Complete!              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Go to GitHub: https://github.com/$REPO/settings/secrets/actions"
echo "2. Verify both secrets are listed (names will be masked)"
echo "3. Run GitHub Actions test:"
echo "   - Go to Actions tab"
echo "   - Select 'Test AWS Connection'"
echo "   - Click 'Run workflow'"
echo ""

echo -e "${YELLOW}To Deploy:${NC}"
echo "1. For ECS: Actions → Deploy to AWS ECS → Run workflow"
echo "2. For EKS: Push to kubernetes/ directory"
echo "3. For Infrastructure: Actions → AWS Infrastructure → Run workflow"
echo ""

echo -e "${YELLOW}Quick Commands:${NC}"
echo "# View all secrets (names only)"
echo "gh secret list --repo $REPO"
echo ""
echo "# View repository variables"
echo "gh variable list --repo $REPO"
echo ""
echo "# View Actions from CLI"
echo "gh run list --repo $REPO"
echo ""
