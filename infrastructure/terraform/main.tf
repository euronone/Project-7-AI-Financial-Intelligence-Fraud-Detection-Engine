locals {
  common_tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }

  tenant_id = var.tenant_id != "" ? var.tenant_id : data.azurerm_client_config.current.tenant_id

  backend_image  = var.backend_image != "" ? var.backend_image : "${module.acr.login_server}/${var.project_name}-backend:latest"
  frontend_image = var.frontend_image != "" ? var.frontend_image : "${module.acr.login_server}/${var.project_name}-frontend:latest"
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location
  tags     = local.common_tags
}

module "networking" {
  source = "./modules/networking"

  project_name = var.project_name
  environment  = var.environment
  location     = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  vnet_cidr    = var.vnet_cidr
  subnet_cidrs = var.subnet_cidrs
  tags         = local.common_tags
}

module "security" {
  source = "./modules/security"

  project_name        = var.project_name
  environment         = var.environment
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = local.tenant_id
  key_vault_secrets   = {}
  subnet_id           = module.networking.subnet_ids["private_endpoints"]
  private_dns_zone_id = module.networking.private_dns_zone_ids["keyvault"]
  tags                = local.common_tags
}

module "acr" {
  source = "./modules/acr"

  project_name        = var.project_name
  environment         = var.environment
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = var.acr_sku
  tags                = local.common_tags
}

module "database" {
  source = "./modules/database"

  project_name        = var.project_name
  environment         = var.environment
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = module.networking.subnet_ids["database"]
  private_dns_zone_id = module.networking.private_dns_zone_ids["postgres"]
  sku_name            = var.db_sku_name
  storage_mb          = var.db_storage_mb
  admin_username      = var.db_admin_username
  admin_password      = var.db_admin_password
  ha_enabled          = var.db_ha_enabled
  tags                = local.common_tags
}

module "cache" {
  source = "./modules/cache"

  project_name        = var.project_name
  environment         = var.environment
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = module.networking.subnet_ids["private_endpoints"]
  private_dns_zone_id = module.networking.private_dns_zone_ids["redis"]
  sku_name            = var.redis_sku_name
  capacity            = var.redis_capacity
  family              = var.redis_family
  tags                = local.common_tags
}

module "event_hubs" {
  source = "./modules/event_hubs"

  project_name        = var.project_name
  environment         = var.environment
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = var.eventhub_sku
  capacity            = var.eventhub_capacity
  tags                = local.common_tags
}

module "storage" {
  source = "./modules/storage"

  project_name        = var.project_name
  environment         = var.environment
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  account_tier        = var.storage_account_tier
  replication_type    = var.storage_replication_type
  tags                = local.common_tags
}

module "monitoring" {
  source = "./modules/monitoring"

  project_name        = var.project_name
  environment         = var.environment
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  alert_email         = var.alert_email
  retention_days      = var.log_retention_days
  tags                = local.common_tags
}

module "container_apps" {
  source = "./modules/container_apps"

  project_name        = var.project_name
  environment         = var.environment
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = module.networking.subnet_ids["container_apps"]
  acr_login_server    = module.acr.login_server
  backend_image       = local.backend_image
  frontend_image      = local.frontend_image
  min_replicas        = var.min_replicas
  max_replicas        = var.max_replicas
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id

  backend_env_vars = {
    DATABASE_URL                   = "postgresql://${var.db_admin_username}:${var.db_admin_password}@${module.database.fqdn}:5432/finshield?sslmode=require"
    REDIS_URL                      = "rediss://:${module.cache.primary_access_key}@${module.cache.hostname}:6380/0"
    EVENTHUB_CONNECTION_STRING     = module.event_hubs.primary_connection_string
    AZURE_STORAGE_CONNECTION_STRING = module.storage.primary_connection_string
    APPLICATIONINSIGHTS_CONNECTION_STRING = module.monitoring.backend_appinsights_connection_string
    KEY_VAULT_URI                  = module.security.key_vault_uri
    ENVIRONMENT                    = var.environment
  }

  frontend_env_vars = {
    NEXT_PUBLIC_API_URL            = "https://${var.project_name}-${var.environment}-backend.${azurerm_resource_group.main.location}.azurecontainerapps.io"
    APPLICATIONINSIGHTS_CONNECTION_STRING = module.monitoring.frontend_appinsights_connection_string
    ENVIRONMENT                    = var.environment
  }

  tags = local.common_tags
}

module "ml" {
  source = "./modules/ml"

  project_name        = var.project_name
  environment         = var.environment
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  storage_account_id  = module.storage.storage_account_id
  key_vault_id        = module.security.key_vault_id
  application_insights_id = module.monitoring.backend_appinsights_id
  create_compute      = var.ml_create_compute
  tags                = local.common_tags
}

module "frontdoor" {
  source = "./modules/frontdoor"

  project_name        = var.project_name
  environment         = var.environment
  resource_group_name = azurerm_resource_group.main.name
  backend_fqdn        = module.container_apps.backend_fqdn
  frontend_fqdn       = module.container_apps.frontend_fqdn
  enable_waf          = var.enable_waf
  tags                = local.common_tags
}
