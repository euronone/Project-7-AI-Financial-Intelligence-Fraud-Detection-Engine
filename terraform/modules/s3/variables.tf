variable "name_prefix" { type = string }
variable "bucket_name" { type = string; default = "" }
variable "allowed_role_arns" {
  type        = list(string)
  description = "IAM role ARNs allowed to read/write model artifacts"
  default     = []
}
