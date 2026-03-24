# Infraestructura AWS

Esta carpeta define la infraestructura productiva con Terraform para desplegar:

- VPC basica
- subnets privadas para RDS
- ECS Fargate para API y worker
- ECR para imagenes
- RDS PostgreSQL
- SQS + DLQ
- S3 para reportes
- S3 + CloudFront para frontend
- ALB para publicar la API
- SSM Parameter Store para secretos de runtime
- IAM y CloudWatch Logs

## Requisitos

- Terraform >= 1.8
- AWS CLI autenticado
- un dominio opcional si luego quieres HTTPS custom
- un certificado ACM existente si quieres habilitar HTTPS en el ALB

## Uso rapido

```bash
cd infra
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

Si defines `alb_certificate_arn`, Terraform crea un listener HTTPS en `443`, redirige `80 -> 443` y el output `api_base_url` pasa a devolver una URL `https://...`.

## Flujo esperado

1. Crear `terraform.tfvars` a partir de `terraform.tfvars.example`
2. Ejecutar `terraform apply`
3. Copiar outputs
4. Configurar secrets en GitHub Actions
5. Hacer push a `main` para que el pipeline despliegue

## Endurecimientos de Fase 5

- RDS ahora usa subnets privadas en vez de publicas
- ECS recibe `DB_PASSWORD` y `JWT_SECRET_KEY` desde SSM Parameter Store
- la API y el worker quedan listos para construir `DATABASE_URL` desde variables separadas
- el backend usa logging estructurado JSON
