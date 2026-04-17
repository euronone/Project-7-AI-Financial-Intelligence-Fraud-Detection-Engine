# ============================================================
# ECS Cluster
# ============================================================
resource "aws_ecs_cluster" "this" {
  name = "${var.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = { Name = "${var.name_prefix}-cluster" }
}

resource "aws_ecs_cluster_capacity_providers" "this" {
  cluster_name       = aws_ecs_cluster.this.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# ============================================================
# CloudWatch Log Groups
# ============================================================
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.name_prefix}/backend"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.name_prefix}/frontend"
  retention_in_days = 14
}

# ============================================================
# Application Load Balancer
# ============================================================
resource "aws_lb" "this" {
  name               = "${var.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "production"

  tags = { Name = "${var.name_prefix}-alb" }
}

resource "aws_lb_target_group" "backend" {
  name        = "${var.name_prefix}-backend-tg"
  port        = 8003
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/api/v1/health"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }

  deregistration_delay = 30
  tags = { Name = "${var.name_prefix}-backend-tg" }
}

resource "aws_lb_target_group" "frontend" {
  name        = "${var.name_prefix}-frontend-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200,301,302"
  }

  deregistration_delay = 30
  tags = { Name = "${var.name_prefix}-frontend-tg" }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener_rule" "backend_api" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern { values = ["/api/*", "/ws/*", "/docs", "/openapi.json"] }
  }
}

# ============================================================
# ECS Task Definitions
# ============================================================
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.name_prefix}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "${var.backend_image_uri}:${var.backend_image_tag}"
      essential = true

      portMappings = [{ containerPort = 8003, protocol = "tcp" }]

      environment = [
        { name = "APP_ENV",    value = var.environment },
        { name = "LOG_LEVEL",  value = "INFO" },
        { name = "REDIS_URL",  value = var.redis_url },
        { name = "ML_MODEL_PATH", value = "/app/ml/models" },
        { name = "ML_MODELS_S3_BUCKET", value = var.ml_models_bucket },
      ]

      secrets = [
        { name = "DATABASE_URL",    valueFrom = "/${var.name_prefix}/DATABASE_URL" },
        { name = "JWT_SECRET",      valueFrom = "/${var.name_prefix}/JWT_SECRET" },
        { name = "ENCRYPTION_KEY",  valueFrom = "/${var.name_prefix}/ENCRYPTION_KEY" },
        { name = "RESEND_API_KEY",  valueFrom = "/${var.name_prefix}/RESEND_API_KEY" },
        { name = "TWILIO_ACCOUNT_SID",  valueFrom = "/${var.name_prefix}/TWILIO_ACCOUNT_SID" },
        { name = "TWILIO_AUTH_TOKEN",   valueFrom = "/${var.name_prefix}/TWILIO_AUTH_TOKEN" },
        { name = "TWILIO_FROM_NUMBER",  valueFrom = "/${var.name_prefix}/TWILIO_FROM_NUMBER" },
        { name = "FIREBASE_SERVER_KEY", valueFrom = "/${var.name_prefix}/FIREBASE_SERVER_KEY" },
        { name = "SUPABASE_URL",        valueFrom = "/${var.name_prefix}/SUPABASE_URL" },
        { name = "SUPABASE_ANON_KEY",   valueFrom = "/${var.name_prefix}/SUPABASE_ANON_KEY" },
        { name = "SUPABASE_SERVICE_KEY",valueFrom = "/${var.name_prefix}/SUPABASE_SERVICE_KEY" },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "backend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8003/api/v1/health || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = { Name = "${var.name_prefix}-backend-task" }
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.name_prefix}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = "${var.frontend_image_uri}:${var.frontend_image_tag}"
      essential = true

      portMappings = [{ containerPort = 3000, protocol = "tcp" }]

      environment = [
        { name = "NODE_ENV",               value = "production" },
        { name = "NEXT_PUBLIC_API_URL",    value = "https://${var.alb_dns_name}/api/v1" },
        { name = "NEXT_PUBLIC_WS_URL",     value = "wss://${var.alb_dns_name}" },
      ]

      secrets = [
        { name = "NEXTAUTH_SECRET", valueFrom = "/${var.name_prefix}/NEXTAUTH_SECRET" },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.frontend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "frontend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:3000/ || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = { Name = "${var.name_prefix}-frontend-task" }
}

# ============================================================
# ECS Services (rolling deployment with circuit-breaker)
# ============================================================
resource "aws_ecs_service" "backend" {
  name            = "${var.name_prefix}-backend"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_tasks_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8003
  }

  deployment_controller { type = "ECS" }

  deployment_circuit_breaker {
    enable   = true
    rollback = true  # automatic rollback on failed deployment
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  health_check_grace_period_seconds = 60

  lifecycle {
    # Allow CI to update image_tag without Terraform drift
    ignore_changes = [task_definition]
  }

  depends_on = [aws_lb_listener_rule.backend_api]
}

resource "aws_ecs_service" "frontend" {
  name            = "${var.name_prefix}-frontend"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_tasks_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 3000
  }

  deployment_controller { type = "ECS" }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  health_check_grace_period_seconds = 60

  lifecycle {
    ignore_changes = [task_definition]
  }

  depends_on = [aws_lb_listener.https]
}
