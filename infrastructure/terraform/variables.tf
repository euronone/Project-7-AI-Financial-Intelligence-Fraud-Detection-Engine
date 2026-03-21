variable "project_name" {
  type    = string
  default = "finshield"
}

variable "environment" {
  type    = string
  default = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "location" {
  type    = string
  default = "eastus2"
}

variable "vnet_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "subnet_cidrs" {
  type = map(string)
  default = {
    container_apps    = "10.0.1.0/24"
    database          = "10.0.2.0/24"
    cache             = "10.0.3.0/24"
    private_endpoints = "10.0.4.0/24"
  }
}

variable "db_sku_name" {
  type    = string
  default = "B_Standard_B1ms"
}

variable "db_storage_mb" {
  type    = number
  default = 32768
}

variable "db_admin_username" {
  type    = string
  default = "finshieldadmin"
}

variable "db_admin_password" {
  type      = string
  sensitive = true
}

variable "db_ha_enabled" {
  type    = bool
  default = false
}

variable "redis_sku_name" {
  type    = string
  default = "Basic"
}

variable "redis_capacity" {
  type    = number
  default = 0
}

variable "redis_family" {
  type    = string
  default = "C"
}

variable "backend_image" {
  type    = string
  default = ""
}

variable "frontend_image" {
  type    = string
  default = ""
}

variable "min_replicas" {
  type    = number
  default = 1
}

variable "max_replicas" {
  type    = number
  default = 1
}

variable "eventhub_sku" {
  type    = string
  default = "Standard"
}

variable "eventhub_capacity" {
  type    = number
  default = 1
}

variable "storage_account_tier" {
  type    = string
  default = "Standard"
}

variable "storage_replication_type" {
  type    = string
  default = "LRS"
}

variable "alert_email" {
  type    = string
  default = "alerts@finshield.ai"
}

variable "log_retention_days" {
  type    = number
  default = 30
}

variable "acr_sku" {
  type    = string
  default = "Standard"
}

variable "enable_waf" {
  type    = bool
  default = false
}

variable "ml_create_compute" {
  type    = bool
  default = false
}

variable "tenant_id" {
  type    = string
  default = ""
}
