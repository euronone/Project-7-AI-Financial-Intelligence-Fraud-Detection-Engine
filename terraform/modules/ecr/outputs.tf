output "backend_repository_url" {
  value = aws_ecr_repository.this["backend"].repository_url
}
output "frontend_repository_url" {
  value = aws_ecr_repository.this["frontend"].repository_url
}
output "registry_id" {
  value = aws_ecr_repository.this["backend"].registry_id
}
