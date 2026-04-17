variable "name_prefix"               { type = string }
variable "environment"               { type = string }
variable "aws_region"                { type = string }
variable "vpc_id"                    { type = string }
variable "public_subnet_ids"         { type = list(string) }
variable "private_subnet_ids"        { type = list(string) }
variable "alb_security_group_id"     { type = string }
variable "ecs_tasks_security_group_id" { type = string }
variable "ecs_execution_role_arn"    { type = string }
variable "ecs_task_role_arn"         { type = string }
variable "backend_image_uri"         { type = string }
variable "backend_image_tag"         { type = string; default = "latest" }
variable "frontend_image_uri"        { type = string }
variable "frontend_image_tag"        { type = string; default = "latest" }
variable "backend_cpu"               { type = number; default = 512 }
variable "backend_memory"            { type = number; default = 1024 }
variable "frontend_cpu"              { type = number; default = 256 }
variable "frontend_memory"           { type = number; default = 512 }
variable "backend_desired_count"     { type = number; default = 2 }
variable "frontend_desired_count"    { type = number; default = 2 }
variable "acm_certificate_arn"       { type = string }
variable "redis_url"                 { type = string; default = "" }
variable "ml_models_bucket"          { type = string; default = "" }
variable "alb_dns_name"              { type = string; default = "" }
