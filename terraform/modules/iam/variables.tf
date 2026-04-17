variable "name_prefix" { type = string }
variable "ml_models_bucket_name" { type = string }
variable "github_repo" {
  type        = string
  description = "GitHub repository in owner/repo format, e.g. myorg/finshield"
}
