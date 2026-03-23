# Prosperas Challenge - Plataforma de Reportes Asincronos

Base funcional de una plataforma SaaS para procesar reportes asincronos con **FastAPI**, **React (Vite)**, **PostgreSQL** y servicios **AWS**. En desarrollo local se usan emulaciones con **LocalStack**.

[![ci-cd](https://github.com/estebanalvarez-rocket/esteban-alvarez-prosperas-challenge/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/estebanalvarez-rocket/esteban-alvarez-prosperas-challenge/actions/workflows/ci-cd.yml)

**URL de produccion:** `https://d227v7gzn2191h.cloudfront.net`

**API publica:** `http://prosperas-reports-alb-1153874681.us-east-1.elb.amazonaws.com`

## Levantamiento local

La forma mas rapida de ejecutar el proyecto es con Docker Compose. Esto levanta API, worker, frontend, PostgreSQL y LocalStack.

### Requisitos

- Docker
- Docker Compose

### Pasos

1. Clona el repositorio.
2. Crea el archivo de entorno:

```bash
cp .env.example .env
```

3. Levanta los servicios:

```bash
docker compose up --build
```

### URLs locales

- Frontend: `http://localhost:3000`
- API y Swagger: `http://localhost:8000/docs`
- LocalStack: `http://localhost:4566`

## Despliegue a produccion

La infraestructura se administra con **Terraform** y el pipeline con **GitHub Actions** desde `.github/workflows/ci-cd.yml`.

### Pipeline CI/CD

1. Backend CI:
   ejecuta `ruff` y `pytest`.
2. Frontend CI:
   valida `npm run build`.
3. Infrastructure CI:
   ejecuta `terraform validate` y, en pull requests, `terraform plan`.
4. Deploy:
   publica imagenes en ECR, actualiza servicios en ECS Fargate, sincroniza frontend a S3 e invalida CloudFront.

### Secrets necesarios

| Categoria    | Secret Name                  | Descripcion                |
| ------------ | ---------------------------- | -------------------------- |
| AWS Auth     | `AWS_ACCESS_KEY_ID`          | Access Key del usuario IAM |
| AWS Auth     | `AWS_SECRET_ACCESS_KEY`      | Secret Key del usuario IAM |
| Repositorios | `API_ECR_REPOSITORY`         | Repo ECR de la API         |
| Repositorios | `WORKER_ECR_REPOSITORY`      | Repo ECR del worker        |
| Front/CDN    | `FRONTEND_BUCKET_NAME`       | Bucket S3 del frontend     |
| Front/CDN    | `CLOUDFRONT_DISTRIBUTION_ID` | Distribucion CloudFront    |
| Capa App     | `ECS_CLUSTER_NAME`           | Cluster ECS                |
| Capa App     | `ECS_API_SERVICE_NAME`       | Servicio ECS de la API     |
| Capa App     | `ECS_WORKER_SERVICE_NAME`    | Servicio ECS del worker    |
| Capa App     | `PROD_API_BASE_URL`          | URL publica de la API      |

## Ejecucion sin Docker

Si prefieres correr el sistema manualmente:

### Backend y worker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.db_init
uvicorn app.main:app --reload
```

En otra terminal:

```bash
cd backend
source .venv/bin/activate  # en Windows: .venv\Scripts\activate
python -m app.worker.runner
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Documentacion adicional

- [TECHNICAL_DOCS.md](./TECHNICAL_DOCS.md): arquitectura, modelo de datos y flujo del worker
- [AI_WORKFLOW.md](./AI_WORKFLOW.md): registro del uso de herramientas de IA

## Tests y calidad

### Backend

```bash
cd backend
pytest
ruff check app tests
```

### Frontend

```bash
cd frontend
npm run build
```
