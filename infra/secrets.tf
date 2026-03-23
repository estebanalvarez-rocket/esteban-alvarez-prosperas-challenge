resource "aws_ssm_parameter" "db_password" {
  name  = "${var.ssm_path_prefix}/db_password"
  type  = "SecureString"
  value = var.db_password
}

resource "aws_ssm_parameter" "jwt_secret_key" {
  name  = "${var.ssm_path_prefix}/jwt_secret_key"
  type  = "SecureString"
  value = var.jwt_secret_key
}
