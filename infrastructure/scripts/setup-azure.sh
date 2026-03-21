#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Bootstrap Azure resources required before Terraform can run:
#   - Resource group for Terraform state
#   - Storage account + blob container for remote state
#   - Service principal for GitHub Actions CI/CD
# ---------------------------------------------------------------------------

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

log_info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; }
log_header()  { echo -e "\n${BOLD}━━━ $* ━━━${NC}\n"; }

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Bootstrap Azure resources for FinShield Terraform state and CI/CD.

Options:
  --project       Project name prefix          (default: finshield)
  --location      Azure region                 (default: eastus2)
  --environment   Target environment           (default: dev)
  -h, --help      Show this message

Examples:
  $(basename "$0")
  $(basename "$0") --project finshield --environment staging --location westus2
EOF
    exit 0
}

PROJECT="finshield"
LOCATION="eastus2"
ENVIRONMENT="dev"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)     PROJECT="$2";     shift 2 ;;
        --location)    LOCATION="$2";    shift 2 ;;
        --environment) ENVIRONMENT="$2"; shift 2 ;;
        -h|--help)     usage ;;
        *) log_error "Unknown option: $1"; usage ;;
    esac
done

RESOURCE_GROUP="${PROJECT}-${ENVIRONMENT}-tfstate-rg"
STORAGE_ACCOUNT="${PROJECT}${ENVIRONMENT}tfstate"
CONTAINER_NAME="tfstate"
SP_NAME="${PROJECT}-${ENVIRONMENT}-gh-actions"

# Azure naming rules: storage account max 24 chars, lowercase alphanumeric only
if [[ ${#STORAGE_ACCOUNT} -gt 24 ]]; then
    log_error "Storage account name '${STORAGE_ACCOUNT}' exceeds 24 characters. Use a shorter --project name."
    exit 1
fi

if ! command -v az &>/dev/null; then
    log_error "Azure CLI (az) is not installed. https://aka.ms/install-azure-cli"
    exit 1
fi

if ! az account show &>/dev/null; then
    log_error "Not logged in to Azure. Run 'az login' first."
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)

log_header "FinShield Azure Bootstrap"
log_info "Project:        ${BOLD}${PROJECT}${NC}"
log_info "Environment:    ${BOLD}${ENVIRONMENT}${NC}"
log_info "Location:       ${BOLD}${LOCATION}${NC}"
log_info "Subscription:   ${BOLD}${SUBSCRIPTION_NAME}${NC} (${SUBSCRIPTION_ID})"
echo ""

# ── Resource Group ──────────────────────────────────────────────────────────
log_header "1/4  Resource Group"

if az group show --name "${RESOURCE_GROUP}" &>/dev/null; then
    log_warn "Resource group '${RESOURCE_GROUP}' already exists — skipping."
else
    az group create \
        --name "${RESOURCE_GROUP}" \
        --location "${LOCATION}" \
        --tags project="${PROJECT}" environment="${ENVIRONMENT}" purpose="terraform-state" \
        --output none
    log_success "Created resource group: ${RESOURCE_GROUP}"
fi

# ── Storage Account ─────────────────────────────────────────────────────────
log_header "2/4  Storage Account"

if az storage account show --name "${STORAGE_ACCOUNT}" --resource-group "${RESOURCE_GROUP}" &>/dev/null; then
    log_warn "Storage account '${STORAGE_ACCOUNT}' already exists — skipping."
else
    az storage account create \
        --name "${STORAGE_ACCOUNT}" \
        --resource-group "${RESOURCE_GROUP}" \
        --location "${LOCATION}" \
        --sku Standard_LRS \
        --kind StorageV2 \
        --min-tls-version TLS1_2 \
        --allow-blob-public-access false \
        --tags project="${PROJECT}" environment="${ENVIRONMENT}" purpose="terraform-state" \
        --output none
    log_success "Created storage account: ${STORAGE_ACCOUNT}"
fi

# ── Blob Container ──────────────────────────────────────────────────────────
log_header "3/4  Blob Container"

ACCOUNT_KEY=$(az storage account keys list \
    --account-name "${STORAGE_ACCOUNT}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query '[0].value' -o tsv)

if az storage container show \
    --name "${CONTAINER_NAME}" \
    --account-name "${STORAGE_ACCOUNT}" \
    --account-key "${ACCOUNT_KEY}" &>/dev/null; then
    log_warn "Blob container '${CONTAINER_NAME}' already exists — skipping."
else
    az storage container create \
        --name "${CONTAINER_NAME}" \
        --account-name "${STORAGE_ACCOUNT}" \
        --account-key "${ACCOUNT_KEY}" \
        --output none
    log_success "Created blob container: ${CONTAINER_NAME}"
fi

# ── Service Principal ───────────────────────────────────────────────────────
log_header "4/4  Service Principal for GitHub Actions"

EXISTING_SP=$(az ad sp list --display-name "${SP_NAME}" --query '[0].appId' -o tsv 2>/dev/null || true)

if [[ -n "${EXISTING_SP}" ]]; then
    log_warn "Service principal '${SP_NAME}' already exists (appId: ${EXISTING_SP})."
    log_warn "To regenerate credentials, delete it first: az ad sp delete --id ${EXISTING_SP}"
    SP_CREDENTIALS='{ "note": "Service principal already exists. Reset credentials manually if needed." }'
else
    SP_CREDENTIALS=$(az ad sp create-for-rbac \
        --name "${SP_NAME}" \
        --role Contributor \
        --scopes "/subscriptions/${SUBSCRIPTION_ID}" \
        --sdk-auth 2>/dev/null || \
    az ad sp create-for-rbac \
        --name "${SP_NAME}" \
        --role Contributor \
        --scopes "/subscriptions/${SUBSCRIPTION_ID}")
    log_success "Created service principal: ${SP_NAME}"
fi

# ── Summary ─────────────────────────────────────────────────────────────────
log_header "Setup Complete"

cat <<EOF
${GREEN}Resources created:${NC}
  Resource Group:   ${RESOURCE_GROUP}
  Storage Account:  ${STORAGE_ACCOUNT}
  Blob Container:   ${CONTAINER_NAME}
  Service Principal: ${SP_NAME}

${CYAN}Terraform backend config:${NC}
  resource_group_name  = "${RESOURCE_GROUP}"
  storage_account_name = "${STORAGE_ACCOUNT}"
  container_name       = "${CONTAINER_NAME}"
  key                  = "${PROJECT}-${ENVIRONMENT}.tfstate"

${YELLOW}GitHub Actions secrets — add these to your repository:${NC}

  AZURE_CREDENTIALS:
${SP_CREDENTIALS}

  ARM_SUBSCRIPTION_ID:    ${SUBSCRIPTION_ID}
  TFSTATE_RESOURCE_GROUP: ${RESOURCE_GROUP}
  TFSTATE_STORAGE_ACCOUNT: ${STORAGE_ACCOUNT}
  TFSTATE_CONTAINER:      ${CONTAINER_NAME}

EOF
