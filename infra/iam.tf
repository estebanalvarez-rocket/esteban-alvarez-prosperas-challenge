data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${local.name_prefix}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "ecs_execution_inline" {
  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]
    resources = [
      aws_ssm_parameter.db_password.arn,
      aws_ssm_parameter.jwt_secret_key.arn
    ]
  }

  statement {
    actions = ["kms:Decrypt"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ecs_execution_inline" {
  name   = "${local.name_prefix}-ecs-execution-inline"
  role   = aws_iam_role.ecs_execution.id
  policy = data.aws_iam_policy_document.ecs_execution_inline.json
}

resource "aws_iam_role" "ecs_task" {
  name               = "${local.name_prefix}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

data "aws_iam_policy_document" "ecs_task_inline" {
  statement {
    actions = [
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ReceiveMessage",
      "sqs:SendMessage"
    ]
    resources = [aws_sqs_queue.jobs.arn, aws_sqs_queue.jobs_dlq.arn]
  }

  statement {
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.reports.arn,
      "${aws_s3_bucket.reports.arn}/*"
    ]
  }

  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }

  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]
    resources = [
      aws_ssm_parameter.db_password.arn,
      aws_ssm_parameter.jwt_secret_key.arn
    ]
  }
}

resource "aws_iam_role_policy" "ecs_task_inline" {
  name   = "${local.name_prefix}-ecs-task-inline"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.ecs_task_inline.json
}
