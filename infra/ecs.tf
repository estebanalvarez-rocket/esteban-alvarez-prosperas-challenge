resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.name_prefix}/api"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${local.name_prefix}/worker"
  retention_in_days = 14
}

resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"
}

locals {
  api_tls_enabled = trimspace(var.alb_certificate_arn) != ""
  api_environment = [
    { name = "APP_ENV", value = "production" },
    { name = "APP_VERSION", value = "0.1.0" },
    { name = "AWS_REGION", value = var.aws_region },
    { name = "SQS_QUEUE_URL", value = aws_sqs_queue.jobs.url },
    { name = "SQS_DLQ_URL", value = aws_sqs_queue.jobs_dlq.url },
    { name = "S3_REPORTS_BUCKET", value = aws_s3_bucket.reports.bucket },
    { name = "DB_HOST", value = aws_db_instance.postgres.address },
    { name = "DB_PORT", value = "5432" },
    { name = "DB_NAME", value = var.db_name },
    { name = "DB_USER", value = var.db_username },
    { name = "CORS_ORIGINS", value = "https://${aws_cloudfront_distribution.frontend.domain_name}" }
  ]
  worker_environment = concat(local.api_environment, [
    { name = "WORKER_CONCURRENCY", value = "2" },
    { name = "WORKER_POLL_SECONDS", value = "20" },
    { name = "WORKER_MAX_RECEIVE_COUNT", value = "3" }
  ])
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  network_mode             = "awsvpc"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${aws_ecr_repository.api.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      environment = local.api_environment
      secrets = [
        {
          name      = "DB_PASSWORD"
          valueFrom = aws_ssm_parameter.db_password.arn
        },
        {
          name      = "JWT_SECRET_KEY"
          valueFrom = aws_ssm_parameter.jwt_secret_key.arn
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name_prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  network_mode             = "awsvpc"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = "${aws_ecr_repository.worker.repository_url}:latest"
      essential = true
      command   = ["python", "-m", "app.worker.runner"]
      environment = local.worker_environment
      secrets = [
        {
          name      = "DB_PASSWORD"
          valueFrom = aws_ssm_parameter.db_password.arn
        },
        {
          name      = "JWT_SECRET_KEY"
          valueFrom = aws_ssm_parameter.jwt_secret_key.arn
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_lb" "api" {
  name               = substr(replace("${local.name_prefix}-alb", "_", "-"), 0, 32)
  internal           = false
  load_balancer_type = "application"
  subnets            = values(aws_subnet.public)[*].id
  security_groups    = [aws_security_group.alb.id]
}

resource "aws_lb_target_group" "api" {
  name        = substr(replace("${local.name_prefix}-tg", "_", "-"), 0, 32)
  port        = var.container_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    path                = "/health"
    matcher             = "200"
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.api.arn
  port              = 80
  protocol          = "HTTP"

  dynamic "default_action" {
    for_each = local.api_tls_enabled ? [1] : []
    content {
      type = "redirect"

      redirect {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }

  dynamic "default_action" {
    for_each = local.api_tls_enabled ? [] : [1]
    content {
      type             = "forward"
      target_group_arn = aws_lb_target_group.api.arn
    }
  }
}

resource "aws_lb_listener" "https" {
  count             = local.api_tls_enabled ? 1 : 0
  load_balancer_arn = aws_lb.api.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.alb_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

resource "aws_ecs_service" "api" {
  name            = "${local.name_prefix}-api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.desired_api_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = values(aws_subnet.public)[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = var.container_port
  }

  depends_on = [aws_lb_listener.http, aws_lb_listener.https]
}

resource "aws_ecs_service" "worker" {
  name            = "${local.name_prefix}-worker-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.desired_worker_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = values(aws_subnet.public)[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }
}
