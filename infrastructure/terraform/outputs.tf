output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "acr_login_server" {
  value = module.acr.login_server
}

output "backend_url" {
  value = module.container_apps.backend_url
}

output "frontend_url" {
  value = module.container_apps.frontend_url
}

output "database_fqdn" {
  value     = module.database.fqdn
  sensitive = true
}

output "redis_hostname" {
  value     = module.cache.hostname
  sensitive = true
}

output "key_vault_uri" {
  value = module.security.key_vault_uri
}

output "backend_appinsights_connection_string" {
  value     = module.monitoring.backend_appinsights_connection_string
  sensitive = true
}

output "frontend_appinsights_connection_string" {
  value     = module.monitoring.frontend_appinsights_connection_string
  sensitive = true
}

output "frontdoor_endpoint_backend" {
  value = module.frontdoor.endpoint_hostname_backend
}

output "frontdoor_endpoint_frontend" {
  value = module.frontdoor.endpoint_hostname_frontend
}

output "ml_workspace_id" {
  value = module.ml.workspace_id
}

output "eventhub_namespace" {
  value = module.event_hubs.namespace_name
}

output "storage_account_name" {
  value = module.storage.storage_account_name
}
