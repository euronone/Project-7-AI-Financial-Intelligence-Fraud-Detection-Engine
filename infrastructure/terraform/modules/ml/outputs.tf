output "workspace_id" {
  value = azurerm_machine_learning_workspace.main.id
}

output "workspace_name" {
  value = azurerm_machine_learning_workspace.main.name
}

output "identity_principal_id" {
  value = azurerm_machine_learning_workspace.main.identity[0].principal_id
}
