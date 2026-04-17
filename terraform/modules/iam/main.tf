# ============================================================
# ECS Task Execution Role — used by ECS agent to pull images
# and publish logs.  NOT the role your application code runs as.
# ============================================================
data "aws_iam_policy_document" "ecs_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${var.name_prefix}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
  tags               = { Name = "${var.name_prefix}-ecs-execution-role" }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow reading SSM Parameter Store secrets (for environment variables)
data "aws_iam_policy_document" "ecs_execution_extra" {
  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameters",
      "ssm:GetParameter",
      "secretsmanager:GetSecretValue",
      "kms:Decrypt",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ecs_execution_extra" {
  name   = "ssm-secrets-access"
  role   = aws_iam_role.ecs_execution.id
  policy = data.aws_iam_policy_document.ecs_execution_extra.json
}

# ============================================================
# ECS Task Role — the identity your application container runs as.
# Grant only what the app needs (S3 model read, CloudWatch logs).
# ============================================================
resource "aws_iam_role" "ecs_task" {
  name               = "${var.name_prefix}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
  tags               = { Name = "${var.name_prefix}-ecs-task-role" }
}

data "aws_iam_policy_document" "ecs_task_permissions" {
  # Read ML model artifacts from the dedicated S3 bucket
  statement {
    sid    = "S3ModelRead"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::${var.ml_models_bucket_name}",
      "arn:aws:s3:::${var.ml_models_bucket_name}/*",
    ]
  }

  # Write ML model artifacts (needed for retraining jobs)
  statement {
    sid    = "S3ModelWrite"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = ["arn:aws:s3:::${var.ml_models_bucket_name}/*"]
  }

  # CloudWatch Logs
  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ecs_task_permissions" {
  name   = "finshield-task-permissions"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.ecs_task_permissions.json
}

# ============================================================
# GitHub Actions CI/CD Role — assumed via OIDC, no long-lived keys
# ============================================================
data "aws_caller_identity" "current" {}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_policy_document" "github_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:*"]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "${var.name_prefix}-github-actions-role"
  assume_role_policy = data.aws_iam_policy_document.github_assume.json
  tags               = { Name = "${var.name_prefix}-github-actions-role" }
}

data "aws_iam_policy_document" "github_actions_permissions" {
  # ECR: push images + get auth token
  statement {
    sid    = "ECRAuth"
    effect = "Allow"
    actions = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
  statement {
    sid    = "ECRPush"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
    ]
    resources = ["arn:aws:ecr:*:${data.aws_caller_identity.current.account_id}:repository/${var.name_prefix}-*"]
  }

  # ECS: update services and describe task definitions for rollback
  statement {
    sid    = "ECSDeployment"
    effect = "Allow"
    actions = [
      "ecs:UpdateService",
      "ecs:DescribeServices",
      "ecs:DescribeTaskDefinition",
      "ecs:RegisterTaskDefinition",
      "ecs:ListTaskDefinitions",
      "ecs:DeregisterTaskDefinition",
    ]
    resources = ["*"]
  }

  # Pass role to ECS (required to register task definitions)
  statement {
    sid    = "PassRole"
    effect = "Allow"
    actions = ["iam:PassRole"]
    resources = [
      aws_iam_role.ecs_execution.arn,
      aws_iam_role.ecs_task.arn,
    ]
  }

  # S3 Terraform state bucket access
  statement {
    sid    = "TerraformState"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::finshield-tfstate",
      "arn:aws:s3:::finshield-tfstate/*",
    ]
  }

  # DynamoDB for Terraform state lock
  statement {
    sid    = "TerraformLock"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
    ]
    resources = ["arn:aws:dynamodb:*:${data.aws_caller_identity.current.account_id}:table/finshield-tfstate-lock"]
  }

  # CloudWatch Logs (read deployment logs)
  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:GetLogEvents",
      "logs:FilterLogEvents",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_actions_permissions" {
  name   = "finshield-ci-permissions"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_permissions.json
}
