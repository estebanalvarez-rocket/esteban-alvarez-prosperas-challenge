# SKILL.md

## Descripcion del sistema

Proyecto de prueba tecnica para generar reportes asincronos. La API recibe solicitudes, crea jobs y publica mensajes a una cola. Un worker desacoplado consume la cola, procesa el job, persiste el estado y deja disponible un resultado descargable.

## Mapa del repositorio

- `backend/`: API FastAPI, modelos, autenticacion, acceso a datos y worker
- `frontend/`: cliente React para crear jobs y ver estados
- `local/`: archivos de Docker Compose y bootstrap local
- `infra/`: Terraform para AWS real
- `.github/workflows/`: pipelines de CI/CD
- `TECHNICAL_DOCS.md`: decisiones tecnicas y arquitectura
- `AI_WORKFLOW.md`: registro del uso de herramientas de IA
- `DELIVERY_CHECKLIST.md`: checklist final de entrega

## Patrones del proyecto

- Las rutas FastAPI viven en `backend/app/api/routes/`
- La configuracion central vive en `backend/app/core/config.py`
- La autenticacion JWT se resuelve en `backend/app/core/auth.py`
- Los modelos ORM y schemas Pydantic viven en `backend/app/models/`
- La publicacion a SQS ocurre desde `backend/app/services/job_service.py`
- El worker corre desde `backend/app/worker/runner.py`
- La infraestructura AWS vive en archivos `.tf` dentro de `infra/`
- El pipeline principal vive en `.github/workflows/ci-cd.yml`
- El runtime productivo toma secretos desde SSM Parameter Store
- La API agrega `x-request-id` y logs JSON por request

## Flujo exacto del worker

1. La API crea el job en PostgreSQL con estado `PENDING` y publica un mensaje en SQS desde `backend/app/services/job_service.py`.
2. El worker en `backend/app/worker/runner.py` consume primero la cola de alta prioridad y luego la cola estandar.
3. Antes de procesar, revisa el circuit breaker por `report_type`.
4. Si el circuit breaker esta abierto para ese tipo, no procesa el mensaje: cambia la visibilidad del mensaje por el timeout configurado y lo deja pendiente.
5. Si el circuito esta cerrado, intenta `claim_job(db, job_id)`.
6. `claim_job` hace la transicion atomica de `PENDING` a `PROCESSING` e incrementa `attempt_count`.
7. Si el job ya fue tomado por otro worker, el mensaje se elimina de SQS y no se reprocesa.
8. Si el job fue reclamado, el worker ejecuta la simulacion/generacion del reporte.
9. Si el procesamiento termina bien, sube el artefacto a S3, calcula `result_url`, ejecuta `mark_job_completed(...)` y elimina el mensaje de SQS.
10. Si el procesamiento falla y todavia no alcanzo `WORKER_MAX_RECEIVE_COUNT`, ejecuta `mark_job_retryable_failure(...)`, calcula backoff exponencial y actualiza la visibilidad del mensaje en SQS para reintento diferido.
11. Si el procesamiento falla N veces consecutivas para ese `report_type`, el circuit breaker pasa a estado `open` durante `WORKER_CIRCUIT_BREAKER_TIMEOUT_SECONDS`.
12. Si el mensaje ya alcanzo el maximo de recepciones, ejecuta `mark_job_failed(...)` y elimina el mensaje de la cola principal.
13. La cola tiene redrive policy hacia DLQ; si se decide no borrar un mensaje o el flujo cambia en AWS real, la DLQ es el ultimo resguardo para inspeccion manual.

## Como extender con un nuevo tipo de reporte

1. Agrega el nuevo `report_type` en `backend/app/services/report_simulation_service.py` dentro de `REPORT_SIMULATION_PROFILES`.
2. Define para ese tipo:
   - `label`
   - `description`
   - `outcome` (`success`, `retry_once`, `always_fail` o `flaky`)
   - `min_seconds` y `max_seconds`
3. Agrega la forma de los datos dummy en `build_dummy_rows(...)` del mismo archivo.
4. Si el nuevo reporte debe ser de alta prioridad, agrega su nombre en `HIGH_PRIORITY_REPORT_TYPES` dentro de `.env` o `.env.example`.
5. Si quieres cambiar el comportamiento de fallo/retry, ajusta `maybe_raise_simulation_error(...)`.
6. Expone el nuevo tipo en el frontend agregandolo a `frontend/src/constants/reportScenarios.ts`.
7. Verifica que el selector lo muestre correctamente desde `frontend/src/components/JobForm.tsx`.
8. Si el nuevo tipo requiere otra semantica de negocio en la API, revisa `backend/app/services/job_service.py`.
9. Corre pruebas backend con `cd backend && python -m pytest`.
10. Compila frontend con `cd frontend && npm run build`.
11. Pruebalo localmente creando un job desde la UI y verificando la transicion `PENDING -> PROCESSING -> COMPLETED/FAILED`.

## Comandos frecuentes

- levantar entorno local: `docker compose up --build`
- ver logs API: `docker compose logs -f api`
- ver logs worker: `docker compose logs -f worker`
- ver logs LocalStack: `docker compose logs -f localstack`
- apagar entorno: `docker compose down`
- tests backend: `cd backend && .venv\Scripts\python -m pytest`
- plan Terraform: `cd infra && terraform plan -var-file="terraform.tfvars"`
- apply Terraform: `cd infra && terraform apply -var-file="terraform.tfvars"`
- smoke test local: `.\local\smoke-test.ps1`

## Errores comunes

- si `POST /jobs` falla, revisar que `localstack` haya creado la cola y el bucket
- si el worker no completa jobs, revisar conectividad a PostgreSQL y SQS
- si el frontend no autentica, validar `VITE_API_BASE_URL` y CORS
- si los esquemas no existen, recrear volumenes y reiniciar `postgres`
- si GitHub Actions falla en deploy, validar secrets derivados de los outputs de Terraform
- si Terraform no corre localmente, instalar Terraform antes de usar `infra/`
- si ECS inicia pero la API no conecta a RDS, revisar `DB_HOST/DB_USER/DB_NAME` y permisos de SSM para `DB_PASSWORD`

## Estado del archivo

Actualizado hasta Fase 6 con prioridad, circuit breaker, retries, tiempo real y simulacion extensible por tipo de reporte.
