resource "azurerm_eventhub_namespace" "main" {
  name                = "${var.project_name}-${var.environment}-ehns"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.sku
  capacity            = var.capacity
  tags                = var.tags
}

locals {
  hubs = ["transactions", "alerts", "risk-scores", "cases"]
}

resource "azurerm_eventhub" "hubs" {
  for_each = toset(local.hubs)

  name                = each.value
  namespace_name      = azurerm_eventhub_namespace.main.name
  resource_group_name = var.resource_group_name
  partition_count     = 4
  message_retention   = 7
}

resource "azurerm_eventhub_consumer_group" "app" {
  for_each = toset(local.hubs)

  name                = "${var.project_name}-app"
  namespace_name      = azurerm_eventhub_namespace.main.name
  eventhub_name       = azurerm_eventhub.hubs[each.key].name
  resource_group_name = var.resource_group_name
}

resource "azurerm_eventhub_consumer_group" "ml" {
  for_each = toset(local.hubs)

  name                = "${var.project_name}-ml"
  namespace_name      = azurerm_eventhub_namespace.main.name
  eventhub_name       = azurerm_eventhub.hubs[each.key].name
  resource_group_name = var.resource_group_name
}

resource "azurerm_eventhub_namespace_authorization_rule" "app" {
  name                = "${var.project_name}-app-rule"
  namespace_name      = azurerm_eventhub_namespace.main.name
  resource_group_name = var.resource_group_name
  listen              = true
  send                = true
  manage              = false
}
