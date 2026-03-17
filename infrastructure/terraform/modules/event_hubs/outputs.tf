output "namespace_id" {
  value = azurerm_eventhub_namespace.main.id
}

output "namespace_name" {
  value = azurerm_eventhub_namespace.main.name
}

output "primary_connection_string" {
  value     = azurerm_eventhub_namespace_authorization_rule.app.primary_connection_string
  sensitive = true
}

output "hub_ids" {
  value = { for k, v in azurerm_eventhub.hubs : k => v.id }
}
