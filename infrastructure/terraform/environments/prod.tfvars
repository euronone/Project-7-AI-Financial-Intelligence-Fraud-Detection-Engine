project_name = "finshield"
environment  = "prod"
location     = "eastus2"

# Networking
vnet_cidr = "10.2.0.0/16"
subnet_cidrs = {
  container_apps    = "10.2.1.0/24"
  database          = "10.2.2.0/24"
  cache             = "10.2.3.0/24"
  private_endpoints = "10.2.4.0/24"
}

# Database
db_sku_name       = "GP_Standard_D4s_v3"
db_storage_mb     = 131072
db_admin_username = "finshieldadmin"
db_ha_enabled     = true

# Cache
redis_sku_name = "Premium"
redis_capacity = 1
redis_family   = "P"

# Container Apps
min_replicas = 3
max_replicas = 10

# Event Hubs
eventhub_sku      = "Standard"
eventhub_capacity = 4

# Storage
storage_account_tier     = "Standard"
storage_replication_type = "RAGRS"

# Monitoring
alert_email        = "prod-alerts@finshield.ai"
log_retention_days = 90

# ACR
acr_sku = "Premium"

# Front Door / WAF
enable_waf = true

# ML
ml_create_compute = true
