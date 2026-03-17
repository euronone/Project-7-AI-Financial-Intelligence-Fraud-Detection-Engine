resource "azurerm_container_registry" "main" {
  name                = "${var.project_name}${var.environment}acr"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku
  admin_enabled       = var.environment != "prod"
  tags                = var.tags

  dynamic "georeplications" {
    for_each = var.sku == "Premium" && var.environment == "prod" ? ["westus2"] : []
    content {
      location = georeplications.value
      tags     = var.tags
    }
  }
}
