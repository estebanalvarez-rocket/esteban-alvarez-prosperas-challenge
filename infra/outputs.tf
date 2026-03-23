output "api_base_url" {
  value = "http://${aws_lb.api.dns_name}"
}

output "frontend_url" {
  value = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "api_ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "api_ecr_repository_name" {
  value = aws_ecr_repository.api.name
}

output "worker_ecr_repository_url" {
  value = aws_ecr_repository.worker.repository_url
}

output "worker_ecr_repository_name" {
  value = aws_ecr_repository.worker.name
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "api_service_name" {
  value = aws_ecs_service.api.name
}

output "worker_service_name" {
  value = aws_ecs_service.worker.name
}

output "frontend_bucket_name" {
  value = aws_s3_bucket.frontend.bucket
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.frontend.id
}

output "ssm_db_password_parameter_name" {
  value = aws_ssm_parameter.db_password.name
}

output "ssm_jwt_secret_parameter_name" {
  value = aws_ssm_parameter.jwt_secret_key.name
}
