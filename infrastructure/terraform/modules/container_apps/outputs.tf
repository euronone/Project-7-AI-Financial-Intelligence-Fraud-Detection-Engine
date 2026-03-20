output "environment_id" {
  value = azurerm_container_app_environment.main.id
}

output "backend_fqdn" {
  value = azurerm_container_app.backend.ingress[0].fqdn
}

output "frontend_fqdn" {
  value = azurerm_container_app.frontend.ingress[0].fqdn
}

output "backend_url" {
  value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "frontend_url" {
  value = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

output "backend_identity_principal_id" {
  value = azurerm_user_assigned_identity.backend.principal_id
}

output "frontend_identity_principal_id" {
  value = azurerm_user_assigned_identity.frontend.principal_id
}

output "backend_identity_id" {
  value = azurerm_user_assigned_identity.backend.id
}

output "frontend_identity_id" {
  value = azurerm_user_assigned_identity.frontend.id
}
