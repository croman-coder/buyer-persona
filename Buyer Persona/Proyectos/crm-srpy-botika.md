---
estado: activo
firma: ea050503323796d8fd72fbf0b53325d6a7babcdf25258f040a641999cae0a0e8
git_rama: main
git_remoto: https://github.com/croman-coder/crm-santarosa.git
git_sin_subir: 2
git_ultimo_commit: '2026-09-30 0b028c1 Merge b1f-demanda: 0126 — demanda sin stock
  dentro de los 8 s de PostgREST'
hijos: []
nombre: botika
resumen: SaaS multi-tenant de bots de ventas IA para WhatsApp, Messenger e Instagram
  (LATAM) sobre Vercel serverless (api/*.js), Supabase Postgres con RLS, Kimi LLM
  y OpenAI (Whisper STT + gpt-4o-mini vision), con webhooks de YCloud y Meta Graph
  y frontend React + Vite; incluye RAG anti-alucinación, handoff humano y detección
  de comprobantes de pago por visión. Activo y sincronizado con el remoto. Antes de
  lanzar comercialmente faltan rotar las API keys, endurecer RLS y programar la purga
  mensual de PII.
resumen_pendiente: true
ruta: /home/croman/Escritorio/CRM SRPY/botika
slug: crm-srpy-botika
stack:
- docker
- git
- node
tipo: proyecto
ultima_actividad: '2026-09-30'
---

<!-- hermes:inicio -->
## Estado

| Campo | Valor |
| --- | --- |
| Estado | activo |
| Última actividad | 2026-09-30 |
| Stack | docker, git, node |
| Rama | main |
| Último commit | 2026-09-30 0b028c1 Merge b1f-demanda: 0126 — demanda sin stock dentro de los 8 s de PostgREST |
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
