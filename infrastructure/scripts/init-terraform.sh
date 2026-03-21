#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Initialize Terraform with Azure backend and select/create workspace.
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

Initialize Terraform backend and workspace for FinShield.

Options:
  --environment   Target environment (dev|staging|prod)  (default: dev)
  --project       Project name prefix                    (default: finshield)
  -h, --help      Show this message
EOF
    exit 0
}

ENVIRONMENT="dev"
PROJECT="finshield"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --environment) ENVIRONMENT="$2"; shift 2 ;;
        --project)     PROJECT="$2";     shift 2 ;;
        -h|--help)     usage ;;
        *) log_error "Unknown option: $1"; usage ;;
    esac
done

if [[ ! "${ENVIRONMENT}" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment '${ENVIRONMENT}'. Must be dev, staging, or prod."
    exit 1
fi

RESOURCE_GROUP="${PROJECT}-${ENVIRONMENT}-tfstate-rg"
STORAGE_ACCOUNT="${PROJECT}${ENVIRONMENT}tfstate"
CONTAINER_NAME="tfstate"
STATE_KEY="${PROJECT}-${ENVIRONMENT}.tfstate"

TERRAFORM_DIR="$(cd "$(dirname "$0")/../terraform" && pwd)"

if ! command -v terraform &>/dev/null; then
    log_error "Terraform is not installed. https://developer.hashicorp.com/terraform/install"
    exit 1
fi

log_header "Terraform Init — ${ENVIRONMENT}"
log_info "Terraform dir:   ${TERRAFORM_DIR}"
log_info "Backend RG:      ${RESOURCE_GROUP}"
log_info "Storage Account: ${STORAGE_ACCOUNT}"
log_info "State Key:       ${STATE_KEY}"

# ── Init ────────────────────────────────────────────────────────────────────
log_header "1/3  terraform init"

terraform -chdir="${TERRAFORM_DIR}" init \
    -backend-config="resource_group_name=${RESOURCE_GROUP}" \
    -backend-config="storage_account_name=${STORAGE_ACCOUNT}" \
    -backend-config="container_name=${CONTAINER_NAME}" \
    -backend-config="key=${STATE_KEY}" \
    -reconfigure

log_success "Terraform initialized."

# ── Workspace ───────────────────────────────────────────────────────────────
log_header "2/3  terraform workspace"

CURRENT_WS=$(terraform -chdir="${TERRAFORM_DIR}" workspace show)

if [[ "${CURRENT_WS}" == "${ENVIRONMENT}" ]]; then
    log_info "Already on workspace '${ENVIRONMENT}'."
elif terraform -chdir="${TERRAFORM_DIR}" workspace list | grep -q "\b${ENVIRONMENT}\b"; then
    terraform -chdir="${TERRAFORM_DIR}" workspace select "${ENVIRONMENT}"
    log_success "Switched to existing workspace: ${ENVIRONMENT}"
else
    terraform -chdir="${TERRAFORM_DIR}" workspace new "${ENVIRONMENT}"
    log_success "Created and switched to workspace: ${ENVIRONMENT}"
fi

# ── Validate ────────────────────────────────────────────────────────────────
log_header "3/3  terraform validate"

terraform -chdir="${TERRAFORM_DIR}" validate
log_success "Configuration is valid."

# ── Summary ─────────────────────────────────────────────────────────────────
log_header "Summary"

echo -e "  Workspace: ${GREEN}$(terraform -chdir="${TERRAFORM_DIR}" workspace show)${NC}"
echo -e "  Backend:   ${CYAN}azurerm${NC} (${STORAGE_ACCOUNT}/${CONTAINER_NAME}/${STATE_KEY})"
echo ""
log_info "Next steps:"
echo "  terraform -chdir=${TERRAFORM_DIR} plan  -var-file=environments/${ENVIRONMENT}.tfvars"
echo "  terraform -chdir=${TERRAFORM_DIR} apply -var-file=environments/${ENVIRONMENT}.tfvars"
echo ""
