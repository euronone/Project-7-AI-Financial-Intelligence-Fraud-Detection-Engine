resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${var.project_name}-${var.environment}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = var.log_analytics_workspace_id
  infrastructure_subnet_id   = var.subnet_id
  tags                       = var.tags
}

resource "azurerm_user_assigned_identity" "backend" {
  name                = "id-${var.project_name}-${var.environment}-backend"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_user_assigned_identity" "frontend" {
  name                = "id-${var.project_name}-${var.environment}-frontend"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_container_app" "backend" {
  name                         = "${var.project_name}-${var.environment}-backend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.backend.id]
  }

  registry {
    server   = var.acr_login_server
    identity = azurerm_user_assigned_identity.backend.id
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "http"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = "backend"
      image  = var.backend_image
      cpu    = 0.5
      memory = "1Gi"

      dynamic "env" {
        for_each = var.backend_env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      liveness_probe {
        transport = "HTTP"
        path      = "/health"
        port      = 8000
        initial_delay    = 10
        interval_seconds = 30
      }

      readiness_probe {
        transport = "HTTP"
        path      = "/health"
        port      = 8000
        interval_seconds = 10
      }

      startup_probe {
        transport = "HTTP"
        path      = "/health"
        port      = 8000
        interval_seconds  = 5
        failure_count_threshold = 30
      }
    }

    http_scale_rule {
      name                = "http-scaling"
      concurrent_requests = "50"
    }
  }
}

resource "azurerm_container_app" "frontend" {
  name                         = "${var.project_name}-${var.environment}-frontend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.frontend.id]
  }

  registry {
    server   = var.acr_login_server
    identity = azurerm_user_assigned_identity.frontend.id
  }

  ingress {
    external_enabled = true
    target_port      = 3000
    transport        = "http"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = "frontend"
      image  = var.frontend_image
      cpu    = 0.25
      memory = "0.5Gi"

      dynamic "env" {
        for_each = var.frontend_env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      liveness_probe {
        transport        = "HTTP"
        path             = "/"
        port             = 3000
        initial_delay    = 10
        interval_seconds = 30
      }

      readiness_probe {
        transport        = "HTTP"
        path             = "/"
        port             = 3000
        interval_seconds = 10
      }
    }
  }
}
