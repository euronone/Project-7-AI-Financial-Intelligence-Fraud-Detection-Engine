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

variable "tags" {
  type    = map(string)
  default = {}
}
