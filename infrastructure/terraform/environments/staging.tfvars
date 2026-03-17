project_name = "finshield"
environment  = "staging"
location     = "eastus2"

# Networking
vnet_cidr = "10.1.0.0/16"
subnet_cidrs = {
  container_apps    = "10.1.1.0/24"
  database          = "10.1.2.0/24"
  cache             = "10.1.3.0/24"
  private_endpoints = "10.1.4.0/24"
}

# Database
db_sku_name       = "GP_Standard_D2s_v3"
db_storage_mb     = 65536
db_admin_username = "finshieldadmin"
db_ha_enabled     = false

# Cache
redis_sku_name = "Standard"
redis_capacity = 1
redis_family   = "C"

# Container Apps
min_replicas = 1
max_replicas = 2

# Event Hubs
eventhub_sku      = "Standard"
eventhub_capacity = 2

# Storage
storage_account_tier     = "Standard"
storage_replication_type = "GRS"

# Monitoring
alert_email        = "staging-alerts@finshield.ai"
log_retention_days = 60

# ACR
acr_sku = "Standard"

# Front Door / WAF
enable_waf = false

# ML
ml_create_compute = true
