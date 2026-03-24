variable "project_name" {
  type        = string
  description = "Prefix para nombrar recursos"
  default     = "prosperas-reports"
}

variable "aws_region" {
  type        = string
  description = "Region AWS"
  default     = "us-east-1"
}

variable "container_port" {
  type        = number
  description = "Puerto expuesto por la API"
  default     = 8000
}

variable "api_cpu" {
  type        = number
  default     = 256
}

variable "api_memory" {
  type        = number
  default     = 512
}

variable "worker_cpu" {
  type        = number
  default     = 256
}

variable "worker_memory" {
  type        = number
  default     = 512
}

variable "desired_api_count" {
  type        = number
  default     = 1
}

variable "desired_worker_count" {
  type        = number
  default     = 1
}

variable "db_name" {
  type        = string
  default     = "reports"
}

variable "db_username" {
  type        = string
  default     = "reports_admin"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Password RDS"
}

variable "jwt_secret_key" {
  type        = string
  sensitive   = true
  description = "Secret JWT para la API"
}

variable "ssm_path_prefix" {
  type        = string
  description = "Prefijo para parametros SSM"
  default     = "/prosperas-reports"
}

variable "frontend_bucket_name" {
  type        = string
  description = "Bucket S3 para el frontend"
}

variable "alb_certificate_arn" {
  type        = string
  description = "ARN de un certificado ACM existente para habilitar HTTPS en el ALB"
  default     = ""
}
