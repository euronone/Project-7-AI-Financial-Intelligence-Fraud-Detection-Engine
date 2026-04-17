locals {
  repos = ["backend", "frontend"]
}

resource "aws_ecr_repository" "this" {
  for_each             = toset(local.repos)
  name                 = "${var.name_prefix}-${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = { Name = "${var.name_prefix}-${each.key}" }
}

resource "aws_ecr_lifecycle_policy" "this" {
  for_each   = aws_ecr_repository.this
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last ${var.image_count_to_keep} tagged images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v", "sha-"]
          countType     = "imageCountMoreThan"
          countNumber   = var.image_count_to_keep
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Remove untagged images older than 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = { type = "expire" }
      }
    ]
  })
}

# Allow CI role to push images
data "aws_iam_policy_document" "ecr_push" {
  for_each = aws_ecr_repository.this

  statement {
    sid    = "AllowCIPush"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = var.ci_role_arns
    }

    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
    ]
  }
}

resource "aws_ecr_repository_policy" "this" {
  for_each   = aws_ecr_repository.this
  repository = each.value.name
  policy     = data.aws_iam_policy_document.ecr_push[each.key].json
}
