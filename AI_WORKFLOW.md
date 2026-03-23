# AI_WORKFLOW.md

## Herramienta usada

- Codex CLI

## Uso en esta fase

- definicion de arquitectura inicial
- comparacion de servicios AWS
- propuesta de esquema de base de datos
- estructura inicial del repositorio
- generacion del stack local con Docker Compose
- implementacion base de FastAPI, worker y frontend
- definicion de IaC con Terraform
- creacion del pipeline de GitHub Actions para CI/CD
- endurecimiento de runtime con SSM Parameter Store y subnets privadas para RDS
- incorporacion de logging estructurado y request correlation
- preparacion de handoff final con checklist y smoke test

## Correcciones necesarias

- La primera respuesta no creo archivos en disco.
- Se corrigio creando la estructura base y la documentacion inicial dentro del proyecto.
- El frontend generado por Vite fue reemplazado por una interfaz alineada al dominio del problema.
- La infraestructura productiva se simplifico a una VPC basica con subnets publicas para mantener la prueba implementable y explicable.
- Se mantuvo ECS en subnets publicas para evitar NAT Gateway y contener costo/complejidad, pero RDS si se movio a subnets privadas.
