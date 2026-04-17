locals {
  name_prefix = "${var.app_name}-${var.environment}"
}

# ── VPC ───────────────────────────────────────────────────────────────────────
module "vpc" {
  source             = "./modules/vpc"
  name_prefix        = local.name_prefix
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}

# ── ECR ───────────────────────────────────────────────────────────────────────
module "ecr" {
  source              = "./modules/ecr"
  name_prefix         = local.name_prefix
  image_count_to_keep = var.ecr_image_count_to_keep
  ci_role_arns        = [module.iam.github_actions_role_arn]
}

# ── IAM ───────────────────────────────────────────────────────────────────────
module "iam" {
  source                = "./modules/iam"
  name_prefix           = local.name_prefix
  ml_models_bucket_name = module.s3.bucket_name
  github_repo           = var.github_repo
}

# ── S3 (ML model artifacts) ───────────────────────────────────────────────────
module "s3" {
  source      = "./modules/s3"
  name_prefix = local.name_prefix
  bucket_name = var.ml_models_bucket_name
  allowed_role_arns = [
    module.iam.ecs_task_role_arn,
    module.iam.github_actions_role_arn,
  ]
}

# ── ECS (cluster + services + ALB) ────────────────────────────────────────────
module "ecs" {
  source      = "./modules/ecs"
  name_prefix = local.name_prefix
  environment = var.environment
  aws_region  = var.aws_region

  vpc_id                      = module.vpc.vpc_id
  public_subnet_ids           = module.vpc.public_subnet_ids
  private_subnet_ids          = module.vpc.private_subnet_ids
  alb_security_group_id       = module.vpc.alb_security_group_id
  ecs_tasks_security_group_id = module.vpc.ecs_tasks_security_group_id

  ecs_execution_role_arn = module.iam.ecs_execution_role_arn
  ecs_task_role_arn      = module.iam.ecs_task_role_arn

  backend_image_uri  = module.ecr.backend_repository_url
  backend_image_tag  = var.backend_image_tag
  frontend_image_uri = module.ecr.frontend_repository_url
  frontend_image_tag = var.frontend_image_tag

  backend_cpu            = var.backend_cpu
  backend_memory         = var.backend_memory
  frontend_cpu           = var.frontend_cpu
  frontend_memory        = var.frontend_memory
  backend_desired_count  = var.backend_desired_count
  frontend_desired_count = var.frontend_desired_count

  acm_certificate_arn = var.acm_certificate_arn
  ml_models_bucket    = module.s3.bucket_name
}
