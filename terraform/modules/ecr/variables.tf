variable "name_prefix" { type = string }
variable "image_count_to_keep" { type = number; default = 10 }
variable "ci_role_arns" {
  type        = list(string)
  description = "IAM role ARNs allowed to push images (GitHub Actions role, etc.)"
  default     = []
}
