# Prosperas Challenge - Plataforma de Reportes Asíncronos

Base funcional de una plataforma SaaS para procesar reportes asíncronos utilizando **FastAPI**, **React (Vite)**, **PostgreSQL** y servicios **AWS** (emulados con LocalStack en desarrollo).

[![ci-cd](https://github.com/<OWNER>/<REPO>/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/<OWNER>/<REPO>/actions/workflows/ci-cd.yml)

**URL de Producción:** [https://<REEMPLAZAR-CLOUDFRONT-DOMAIN>](https://<REEMPLAZAR-CLOUDFRONT-DOMAIN>)

---

## 🚀 1. Levantamiento Local (Desarrollo)

La forma más rápida de iniciar el proyecto es utilizando **Docker Compose**, que levanta automáticamente la API, el Worker, el Frontend, PostgreSQL y LocalStack (emulando SQS y S3).

### Requisitos previos
- Docker y Docker Compose instalado.

### Pasos para iniciar
1. **Clonar el repositorio.**
2. **Crear archivo de variables de entorno:**
   ```bash
   cp .env.example .env
   ```
3. **Levantar los servicios:**
   ```bash
   docker compose up --build
   ```

### URLs Locales
- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **LocalStack (AWS Emulado):** [http://localhost:4566](http://localhost:4566)

---

### ☁️ 2. Despliegue a Producción (AWS)

El despliegue está automatizado mediante **Terraform** para la gestión de infraestructura y **GitHub Actions** para el ciclo de vida de CI/CD.

#### Diseño del Pipeline de CI/CD

El pipeline en `.github/workflows/ci-cd.yml` ha sido diseñado bajo los siguientes pilares de ingeniería:

1.  **Separación de Responsabilidades (Stage-based CI)**:
    *   **Backend CI**: Ejecuta un análisis estático con `ruff` (linter ultrarrápido) y corre la suite de tests con `pytest`. Esto asegura que el código cumple con los estándares de calidad y funcionalidad antes de cualquier intento de despliegue.
    *   **Frontend CI**: Valida que la aplicación React sea capaz de compilarse correctamente (`npm run build`). Catching build errors here saves time in the deployment stage.
    *   **Infrastructure CI**: Realiza un `terraform validate` para asegurar que los cambios estructurales en AWS sean sintácticamente correctos. En Pull Requests, intenta generar un `terraform plan` informativo.

2.  **Despliegue Continuo (CD) Seguro**:
    *   **Automatización Full-Stack**: El job de `deploy` solo se activa tras el éxito de todas las fases de CI y solo sobre la rama `main`.
    *   **Inmutabilidad de Contenedores**: Cada commit en `main` genera una nueva imagen en **Amazon ECR** con el tag del `SHA` de GitHub, permitiendo una trazabilidad total entre la versión del código y el binario en ejecución en **ECS Fargate**.
    *   **Eficiencia en el Frontend**: Se sincroniza directamente con **S3** y se gatilla una invalidación de cache en **CloudFront** para asegurar que los usuarios reciban la última versión sin latencia.
    *   **Orquestación de ECS**: Se fuerza un `new-deployment` en los servicios de API y Worker, garantizando que ECS reemplace los contenedores sin tiempo de inactividad (*rolling update*).

3.  **Seguridad**:
    *   Uso de **GitHub Secrets** para credenciales sensibles.
    *   Inyección de secretos de runtime mediante **SSM Parameter Store** (gestionado por Terraform), evitando exponer variables en texto plano en la infraestructura.

#### Configuración de GitHub Secrets

Para que el pipeline sea funcional, configura los siguientes **Secrets** en tu repositorio:

| Categoria | Secret Name | Descripción |
|---|---|---|
| **AWS Auth** | `AWS_ACCESS_KEY_ID` | Access Key de AWS IAM |
| | `AWS_SECRET_ACCESS_KEY` | Secret Key de AWS IAM |
| **Repositorios** | `API_ECR_REPOSITORY` | Nombre del repo ECR (p.ej. `reports-api`) |
| | `WORKER_ECR_REPOSITORY` | Nombre del repo ECR (p.ej. `reports-worker`) |
| **Front/CDN** | `FRONTEND_BUCKET_NAME` | Nombre del bucket S3 para el Frontend |
| | `CLOUDFRONT_DISTRIBUTION_ID` | ID de la distribución de CloudFront |
| **Capa App** | `ECS_CLUSTER_NAME` | Nombre del cluster ECS |
| | `ECS_API_SERVICE_NAME` | Nombre del servicio ECS para la API |
| | `ECS_WORKER_SERVICE_NAME` | Nombre del servicio ECS para el Worker |
| | `PROD_API_BASE_URL` | URL del ALB para que el Frontend se conecte |

---

---

## 🛠️ Ejecución sin Docker (Opcional)

Si prefieres correr los servicios manualmente para depuración:

1. **Servicios de Datos:** Asegúrate de tener PostgreSQL y LocalStack corriendo locales.
2. **Backend & Worker:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # o .venv\Scripts\activate en Windows
   pip install -r requirements.txt
   python -m app.db_init      # Inicializa tablas
   uvicorn app.main:app --reload  # Levanta API
   # En otra terminal activa el venv y corre:
   python -m app.worker.runner    # Levanta Worker
   ```
3. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 📂 Documentación Adicional

- [TECHNICAL_DOCS.md](./TECHNICAL_DOCS.md): Detalles de arquitectura, esquema de DB y lógica del worker.
- [DELIVERY_CHECKLIST.md](./DELIVERY_CHECKLIST.md): Guía de pasos finales antes de la entrega oficial.
- [INFO.md](./INFO.md): Información general del proyecto.

## 🧪 Tests y Calidad

Para ejecutar los tests del backend localmente:
```bash
cd backend
pytest
```

---
© 2026 Prosperas Challenge - [SateLab Academy](https://satelab.space)
