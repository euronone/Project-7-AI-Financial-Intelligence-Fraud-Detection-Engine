# Remote state stored in S3 with DynamoDB lock table.
# Before first `terraform init`, create the bucket and table:
#
#   aws s3api create-bucket --bucket finshield-tfstate --region us-east-1
#   aws s3api put-bucket-versioning \
#       --bucket finshield-tfstate \
#       --versioning-configuration Status=Enabled
#   aws dynamodb create-table \
#       --table-name finshield-tfstate-lock \
#       --attribute-definitions AttributeName=LockID,AttributeType=S \
#       --key-schema AttributeName=LockID,KeyType=HASH \
#       --billing-mode PAY_PER_REQUEST \
#       --region us-east-1

terraform {
  backend "s3" {
    bucket         = "finshield-tfstate"
    key            = "finshield/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "finshield-tfstate-lock"
  }
}
