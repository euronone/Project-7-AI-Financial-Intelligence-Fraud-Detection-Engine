resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-${var.project_name}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = var.retention_days
  tags                = var.tags
}

resource "azurerm_application_insights" "backend" {
  name                = "ai-${var.project_name}-${var.environment}-backend"
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = var.tags
}

resource "azurerm_application_insights" "frontend" {
  name                = "ai-${var.project_name}-${var.environment}-frontend"
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = var.tags
}

resource "azurerm_monitor_action_group" "critical" {
  name                = "ag-${var.project_name}-${var.environment}-critical"
  resource_group_name = var.resource_group_name
  short_name          = "critical"
  tags                = var.tags

  email_receiver {
    name          = "admin"
    email_address = var.alert_email
  }
}

resource "azurerm_monitor_metric_alert" "high_error_rate" {
  name                = "alert-${var.project_name}-${var.environment}-high-error-rate"
  resource_group_name = var.resource_group_name
  scopes              = [azurerm_application_insights.backend.id]
  severity            = 1
  frequency           = "PT5M"
  window_size         = "PT15M"
  tags                = var.tags

  criteria {
    metric_namespace = "microsoft.insights/components"
    metric_name      = "requests/failed"
    aggregation      = "Count"
    operator         = "GreaterThan"
    threshold        = 50
  }

  action {
    action_group_id = azurerm_monitor_action_group.critical.id
  }
}

resource "azurerm_monitor_metric_alert" "slow_response" {
  name                = "alert-${var.project_name}-${var.environment}-slow-response"
  resource_group_name = var.resource_group_name
  scopes              = [azurerm_application_insights.backend.id]
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"
  tags                = var.tags

  criteria {
    metric_namespace = "microsoft.insights/components"
    metric_name      = "requests/duration"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 5000
  }

  action {
    action_group_id = azurerm_monitor_action_group.critical.id
  }
}

resource "azurerm_monitor_scheduled_query_rules_alert_v2" "fraud_spike" {
  name                = "alert-${var.project_name}-${var.environment}-fraud-spike"
  resource_group_name = var.resource_group_name
  location            = var.location
  scopes              = [azurerm_application_insights.backend.id]
  severity            = 1
  tags                = var.tags

  evaluation_frequency = "PT5M"
  window_duration      = "PT30M"

  criteria {
    query = <<-QUERY
      customEvents
      | where name == "FraudDetected"
      | summarize count() by bin(timestamp, 5m)
    QUERY

    time_aggregation_method = "Count"
    operator                = "GreaterThan"
    threshold               = 100

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  action {
    action_groups = [azurerm_monitor_action_group.critical.id]
  }
}
