output "vnet_id" {
  value = azurerm_virtual_network.main.id
}

output "vnet_name" {
  value = azurerm_virtual_network.main.name
}

output "subnet_ids" {
  value = {
    container_apps    = azurerm_subnet.container_apps.id
    database          = azurerm_subnet.database.id
    cache             = azurerm_subnet.cache.id
    private_endpoints = azurerm_subnet.private_endpoints.id
  }
}

output "private_dns_zone_ids" {
  value = {
    postgres = azurerm_private_dns_zone.postgres.id
    redis    = azurerm_private_dns_zone.redis.id
    keyvault = azurerm_private_dns_zone.keyvault.id
  }
}
