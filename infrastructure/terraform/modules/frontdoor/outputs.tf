output "profile_id" {
  value = azurerm_cdn_frontdoor_profile.main.id
}

output "endpoint_hostname_backend" {
  value = azurerm_cdn_frontdoor_endpoint.backend.host_name
}

output "endpoint_hostname_frontend" {
  value = azurerm_cdn_frontdoor_endpoint.frontend.host_name
}
