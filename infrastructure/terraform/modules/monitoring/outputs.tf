output "log_analytics_workspace_id" {
  value = azurerm_log_analytics_workspace.main.id
}

output "log_analytics_workspace_name" {
  value = azurerm_log_analytics_workspace.main.name
}

output "backend_appinsights_id" {
  value = azurerm_application_insights.backend.id
}

output "backend_appinsights_connection_string" {
  value     = azurerm_application_insights.backend.connection_string
  sensitive = true
}

output "backend_appinsights_instrumentation_key" {
  value     = azurerm_application_insights.backend.instrumentation_key
  sensitive = true
}

output "frontend_appinsights_id" {
  value = azurerm_application_insights.frontend.id
}

output "frontend_appinsights_connection_string" {
  value     = azurerm_application_insights.frontend.connection_string
  sensitive = true
}

output "frontend_appinsights_instrumentation_key" {
  value     = azurerm_application_insights.frontend.instrumentation_key
  sensitive = true
}

output "action_group_id" {
  value = azurerm_monitor_action_group.critical.id
}
