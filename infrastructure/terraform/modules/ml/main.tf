resource "azurerm_machine_learning_workspace" "main" {
  name                    = "mlw-${var.project_name}-${var.environment}"
  location                = var.location
  resource_group_name     = var.resource_group_name
  storage_account_id      = var.storage_account_id
  key_vault_id            = var.key_vault_id
  application_insights_id = var.application_insights_id
  tags                    = var.tags

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_machine_learning_compute_instance" "training" {
  count = var.create_compute ? 1 : 0

  name                          = "ci-${var.project_name}-${var.environment}"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.main.id
  virtual_machine_size          = "Standard_DS3_v2"
  tags                          = var.tags
}
