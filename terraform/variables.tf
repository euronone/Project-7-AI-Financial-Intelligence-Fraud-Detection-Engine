variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (staging / production)"
  type        = string
  default     = "staging"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be 'staging' or 'production'."
  }
}

variable "app_name" {
  description = "Application name used as prefix for all resources"
  type        = string
  default     = "finshield"
}

# --- Container images ---------------------------------------------------------

variable "backend_image_tag" {
  description = "Docker image tag for the backend service (set by CI to the git SHA)"
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "Docker image tag for the frontend service (set by CI to the git SHA)"
  type        = string
  default     = "latest"
}

# --- Networking ---------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "AZs to spread subnets across"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# --- ECS service sizing -------------------------------------------------------

variable "backend_cpu" {
  description = "Fargate CPU units for backend task (256 = 0.25 vCPU)"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "Fargate memory MiB for backend task"
  type        = number
  default     = 1024
}

variable "frontend_cpu" {
  description = "Fargate CPU units for frontend task"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Fargate memory MiB for frontend task"
  type        = number
  default     = 512
}

variable "backend_desired_count" {
  description = "Desired number of backend task replicas"
  type        = number
  default     = 2
}

variable "frontend_desired_count" {
  description = "Desired number of frontend task replicas"
  type        = number
  default     = 2
}

# --- S3 model artifacts -------------------------------------------------------

variable "ml_models_bucket_name" {
  description = "S3 bucket name for ML model artifacts (must be globally unique)"
  type        = string
  default     = ""  # auto-generated with random suffix if empty
}

# --- ECR lifecycle ------------------------------------------------------------

variable "ecr_image_count_to_keep" {
  description = "Number of tagged images to retain per ECR repo"
  type        = number
  default     = 10
}

variable "github_repo" {
  description = "GitHub repository in owner/repo format, e.g. myorg/finshield-ai"
  type        = string
  default     = "myorg/finshield-ai"
}

variable "acm_certificate_arn" {
  description = "ARN of ACM certificate for HTTPS on the ALB"
  type        = string
  default     = ""
}
