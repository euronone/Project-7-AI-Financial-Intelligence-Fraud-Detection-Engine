project_name = "finshield"
environment  = "dev"
location     = "eastus2"

# Networking
vnet_cidr = "10.0.0.0/16"
subnet_cidrs = {
  container_apps    = "10.0.1.0/24"
  database          = "10.0.2.0/24"
  cache             = "10.0.3.0/24"
  private_endpoints = "10.0.4.0/24"
}

# Database
db_sku_name       = "B_Standard_B1ms"
db_storage_mb     = 32768
db_admin_username = "finshieldadmin"
db_ha_enabled     = false

# Cache
redis_sku_name = "Basic"
redis_capacity = 0
redis_family   = "C"

# Container Apps
min_replicas = 0
max_replicas = 1

# Event Hubs
eventhub_sku      = "Standard"
eventhub_capacity = 1

# Storage
storage_account_tier     = "Standard"
storage_replication_type = "LRS"

# Monitoring
alert_email        = "dev-alerts@finshield.ai"
log_retention_days = 30

# ACR
acr_sku = "Standard"

# Front Door / WAF
enable_waf = false

# ML
ml_create_compute = false
