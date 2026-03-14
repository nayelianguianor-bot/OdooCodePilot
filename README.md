# OdooCodePilot 🚀

Plataforma de validación automática de deployments para proyectos Odoo.

## ¿Qué hace?
- Detecta módulos modificados en cada commit
- Valida sintaxis Python y XML automáticamente
- Bloquea el push si hay errores
- Notifica al equipo con un reporte detallado
- Despliega a AWS solo si todo está limpio

## Stack
- Odoo 17
- Python 3
- PostgreSQL 15
- Docker
- n8n (automatización)

## Estructura
OdooCodePilot/
├── addons/          # Módulos personalizados de Odoo
├── pipeline/        # Scripts de validación
├── docs/            # Documentación
└── docker-compose.yml

## Inicio rápido
```bash
docker compose up -d
```
Abre http://localhost:8069