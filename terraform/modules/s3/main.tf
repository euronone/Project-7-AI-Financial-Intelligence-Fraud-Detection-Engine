resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  bucket_name = var.bucket_name != "" ? var.bucket_name : "${var.name_prefix}-ml-models-${random_id.suffix.hex}"
}

resource "aws_s3_bucket" "ml_models" {
  bucket        = local.bucket_name
  force_destroy = false

  tags = { Name = local.bucket_name, Purpose = "ML model artifacts" }
}

# Block ALL public access
resource "aws_s3_bucket_public_access_block" "ml_models" {
  bucket                  = aws_s3_bucket.ml_models.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning — allows rollback to previous model artifacts
resource "aws_s3_bucket_versioning" "ml_models" {
  bucket = aws_s3_bucket.ml_models.id
  versioning_configuration { status = "Enabled" }
}

# Server-side encryption with AES-256
resource "aws_s3_bucket_server_side_encryption_configuration" "ml_models" {
  bucket = aws_s3_bucket.ml_models.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Lifecycle: transition old model versions to cheaper storage after 30 days
resource "aws_s3_bucket_lifecycle_configuration" "ml_models" {
  bucket = aws_s3_bucket.ml_models.id

  rule {
    id     = "archive-old-model-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }

  rule {
    id     = "delete-incomplete-multipart"
    status = "Enabled"
    abort_incomplete_multipart_upload { days_after_initiation = 7 }
  }
}

# Bucket policy: restrict access to ECS task role + CI role only
data "aws_iam_policy_document" "bucket_policy" {
  # Deny any access not from our approved roles
  statement {
    sid    = "DenyUnauthorizedAccess"
    effect = "Deny"
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    actions   = ["s3:*"]
    resources = [
      aws_s3_bucket.ml_models.arn,
      "${aws_s3_bucket.ml_models.arn}/*",
    ]
    condition {
      test     = "StringNotEquals"
      variable = "aws:PrincipalArn"
      values   = concat(var.allowed_role_arns, [
        # Always allow the account root as a safety valve
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      ])
    }
  }
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket_policy" "ml_models" {
  bucket = aws_s3_bucket.ml_models.id
  policy = data.aws_iam_policy_document.bucket_policy.json
  depends_on = [aws_s3_bucket_public_access_block.ml_models]
}
