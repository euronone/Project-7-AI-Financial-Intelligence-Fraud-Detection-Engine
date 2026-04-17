output "cluster_name"          { value = aws_ecs_cluster.this.name }
output "cluster_arn"           { value = aws_ecs_cluster.this.arn }
output "backend_service_name"  { value = aws_ecs_service.backend.name }
output "frontend_service_name" { value = aws_ecs_service.frontend.name }
output "alb_arn"               { value = aws_lb.this.arn }
output "alb_dns_name"          { value = aws_lb.this.dns_name }
output "backend_task_def_arn"  { value = aws_ecs_task_definition.backend.arn }
output "frontend_task_def_arn" { value = aws_ecs_task_definition.frontend.arn }
