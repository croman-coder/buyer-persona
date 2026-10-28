---
estado: activo
firma: 6f01f50677ffa21f17e379c003a28405cd18fc679c1f0638c191252780f7cdd3
git_rama: main
git_remoto: https://github.com/croman-coder/crm-santarosa.git
git_sin_subir: 2
git_ultimo_commit: '2026-10-05 9ea19d5 docs: pool de PostgREST aplicado el 5/10 (ajuste
  de Postgres completo)'
hijos: []
nombre: botika
resumen: null
resumen_pendiente: true
ruta: /home/croman/Escritorio/CRM SRPY/botika
slug: crm-srpy-botika
stack:
- docker
- git
- node
tipo: proyecto
ultima_actividad: '2026-10-19'
---

<!-- hermes:inicio -->
## Estado

| Campo | Valor |
| --- | --- |
| Estado | activo |
| Última actividad | 2026-10-19 |
| Stack | docker, git, node |
| Rama | main |
| Último commit | 2026-10-05 9ea19d5 docs: pool de PostgREST aplicado el 5/10 (ajuste de Postgres completo) |
| Sin subir | 2 |
| Ruta | `/home/croman/Escritorio/CRM SRPY/botika` |
<!-- hermes:fin -->

## Nota manual (no la toca Hermes)

**En producción en Coolify desde el 25/9/2026:** https://crm.santarosa.lat (app) ·
https://crm-db.santarosa.lat (API, Supabase self-hosted en el servidor SRPY186).
Ya no es Vercel/Supabase nube — esos quedan vivos solo hasta la baja (Tarea 14 del
plan de migración). Detalle técnico: `DEPLOY.md` en el repo.

**Premisa:** Sarpy CRM reemplaza a Bitrix24 — no es una pantalla sobre Bitrix, es
el sistema de registro y cierre.

**Siguiente paso:** Parte B (estructura y usuarios desde Bitrix), y después apagar
Bitrix (fuentes de leads, historial, tableros).
