variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "backend_fqdn" {
  type = string
}

variable "frontend_fqdn" {
  type = string
}

variable "enable_waf" {
  type    = bool
  default = false
}

variable "tags" {
  type    = map(string)
  default = {}
}
