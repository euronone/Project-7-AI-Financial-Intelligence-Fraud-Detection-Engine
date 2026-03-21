variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "storage_account_id" {
  type = string
}

variable "key_vault_id" {
  type = string
}

variable "application_insights_id" {
  type = string
}

variable "create_compute" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
