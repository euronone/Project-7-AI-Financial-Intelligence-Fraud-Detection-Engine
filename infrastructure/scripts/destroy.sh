#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Destroy FinShield infrastructure for a given environment.
# Production requires --force to prevent accidental teardown.
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
Usage: $(basename "$0") --environment <env> [OPTIONS]

Destroy FinShield infrastructure.

Options:
  --environment   Target environment (REQUIRED: dev|staging|prod)
  --project       Project name prefix  (default: finshield)
  --force         Required to destroy prod
  -h, --help      Show this message

Examples:
  $(basename "$0") --environment dev
  $(basename "$0") --environment prod --force
EOF
    exit 0
}

ENVIRONMENT=""
PROJECT="finshield"
FORCE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --environment) ENVIRONMENT="$2"; shift 2 ;;
        --project)     PROJECT="$2";     shift 2 ;;
        --force)       FORCE=true;       shift ;;
        -h|--help)     usage ;;
        *) log_error "Unknown option: $1"; usage ;;
    esac
done

if [[ -z "${ENVIRONMENT}" ]]; then
    log_error "--environment is required."
    usage
fi

if [[ ! "${ENVIRONMENT}" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment '${ENVIRONMENT}'. Must be dev, staging, or prod."
    exit 1
fi

TERRAFORM_DIR="$(cd "$(dirname "$0")/../terraform" && pwd)"
TFVARS_FILE="${TERRAFORM_DIR}/environments/${ENVIRONMENT}.tfvars"

# ── Production safeguard ────────────────────────────────────────────────────
if [[ "${ENVIRONMENT}" == "prod" && "${FORCE}" != true ]]; then
    echo ""
    log_error "┌──────────────────────────────────────────────────────────────┐"
    log_error "│  REFUSED: Cannot destroy production without --force flag.    │"
    log_error "│                                                              │"
    log_error "│  This is a safety mechanism to prevent accidental deletion   │"
    log_error "│  of production infrastructure and data.                      │"
    log_error "│                                                              │"
    log_error "│  If you are certain, re-run with:                            │"
    log_error "│    $(basename "$0") --environment prod --force               │"
    log_error "└──────────────────────────────────────────────────────────────┘"
    echo ""
    exit 1
fi

# ── Confirmation ────────────────────────────────────────────────────────────
log_header "DESTROY — ${ENVIRONMENT}"

echo -e "${RED}${BOLD}⚠  WARNING: This will permanently destroy ALL infrastructure for '${ENVIRONMENT}'.${NC}"
echo ""
echo "  Resources to be destroyed:"
echo "    • Container Apps (frontend, backend, workers)"
echo "    • PostgreSQL database (ALL DATA WILL BE LOST)"
echo "    • Redis cache"
echo "    • Key Vault"
echo "    • Event Hubs"
echo "    • Storage accounts"
echo "    • Networking (VNet, subnets, NSGs)"
echo "    • Monitoring (Log Analytics, App Insights)"
echo ""

if [[ "${ENVIRONMENT}" == "prod" ]]; then
    echo -e "${RED}${BOLD}  *** PRODUCTION ENVIRONMENT — THIS CANNOT BE UNDONE ***${NC}"
    echo ""
fi

read -r -p "Type '${ENVIRONMENT}' to confirm destruction: " CONFIRM

if [[ "${CONFIRM}" != "${ENVIRONMENT}" ]]; then
    log_error "Confirmation mismatch. Aborting."
    exit 1
fi

echo ""
log_info "Confirmed. Proceeding with destruction..."

# ── Workspace check ─────────────────────────────────────────────────────────
CURRENT_WS=$(terraform -chdir="${TERRAFORM_DIR}" workspace show 2>/dev/null || echo "default")

if [[ "${CURRENT_WS}" != "${ENVIRONMENT}" ]]; then
    log_info "Switching to workspace '${ENVIRONMENT}'..."
    terraform -chdir="${TERRAFORM_DIR}" workspace select "${ENVIRONMENT}" 2>/dev/null || {
        log_error "Workspace '${ENVIRONMENT}' does not exist. Nothing to destroy."
        exit 1
    }
fi

# ── Destroy ─────────────────────────────────────────────────────────────────
log_header "Running terraform destroy"

DESTROY_ARGS=(-auto-approve)
if [[ -f "${TFVARS_FILE}" ]]; then
    DESTROY_ARGS+=(-var-file="${TFVARS_FILE}")
    log_info "Using tfvars: ${TFVARS_FILE}"
else
    log_warn "No tfvars file at ${TFVARS_FILE} — using defaults."
fi

terraform -chdir="${TERRAFORM_DIR}" destroy "${DESTROY_ARGS[@]}"

log_success "Infrastructure destroyed for '${ENVIRONMENT}'."

# ── Workspace cleanup ───────────────────────────────────────────────────────
log_header "Cleaning up workspace"

terraform -chdir="${TERRAFORM_DIR}" workspace select default 2>/dev/null || true

if [[ "${ENVIRONMENT}" != "default" ]]; then
    terraform -chdir="${TERRAFORM_DIR}" workspace delete "${ENVIRONMENT}" 2>/dev/null && \
        log_success "Deleted workspace: ${ENVIRONMENT}" || \
        log_warn "Could not delete workspace '${ENVIRONMENT}' (may still have state)."
fi

log_header "Done"
log_info "Environment '${ENVIRONMENT}' has been torn down."
echo ""
