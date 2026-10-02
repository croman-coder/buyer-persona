# CLAUDE.md — Carlos Roman (Croman) · Encargado de Innovación
# Santa Rosa Paraguay S.A.

> Este archivo da contexto completo a cualquier asistente de IA sobre quién soy, qué hago, qué proyectos tengo y cómo trabajo. Debe leerse al inicio de cualquier sesión.

---

## 👤 Quién soy

- **Nombre:** Carlos Roman (Croman)
- **Rol:** Encargado de Innovación de Santa Rosa Paraguay S.A.
- **Empresa:** Santa Rosa Automotores S.A. — concesionaria multimarca en Paraguay
- **Asistente:** Pablo Villalba
- **Stack tecnológico:** Python, TypeScript/Next.js, React, Firebase, Supabase, Bitrix24, Claude, Meta Marketing API, YCloud WhatsApp API

## 🚗 Santa Rosa Automotores — Marcas y contexto

### Marcas que distribuyo
Renault (monopolio PY) · Mitsubishi (⚠️ competencia con Nipon) · GWM · Jetour · JAC · Zeekr · Leapmotor · JMEV · Soueast · Renew (usados certificados)

### Competidores principales
- **Grupo Garden** — KIA (#1 del mercado), Chevrolet, Mazda, Chery, Volvo, Geely, iCAUR
- **Diesa** — Volkswagen, Honda, BYD, Porsche, Scania
- **Toyotoshi** — Toyota, Lexus, Hino
- **Automaq** — Peugeot, Citroën, John Deere, Komatsu
- **Nipon Automotores** — ⚠️ Competidor directo en Mitsubishi

### Recursos de inteligencia competitiva (en Obsidian)
- `⚔️ Benchmark Competitivo` — mapa completo de competidores con precios
- `⚔️ Battle Cards Modelo vs Modelo` — 11 batallas verificadas
- `🎯 Playbook Meta Ads` — 86 cuentas mapeadas a 6 estrategias
- `📢 Promociones Competencia` — monitoreo automático (cron diario 08:00)
- `🤖 Meta Ads Lo Que Funciona` — mejores prácticas de Meta

### Restricción legal importante
> ⚠️ Por ley de Paraguay NO se permite publicidad comparativa nombrando marcas/modelos de competencia. Los copies públicos deben usar argumentos ABSOLUTOS. La inteligencia competitiva es SOLO para uso interno.

---

## 📂 Ecosistema de Proyectos

### 🟢 ACTIVOS — Desarrollo e Innovación

| Proyecto | Ruta | Stack | Estado | Descripción |
|----------|------|-------|--------|-------------|
| **PDI Plainilla** | `~/Escritorio/PDI PLAINILLA/` | Next.js 14 + Supabase + Tailwind | En producción (v2.36) | Dashboard de pre-entrega de vehículos. 217 tests. Roles: admin, operador, lector |
| **CARBID (Renew Subastas)** | `~/Escritorio/CARBID/` | Next.js 14 + Firebase | En desarrollo | Plataforma de subastas de usados. renewsubastas.com.py |
| **CARBID iOS** | `~/Escritorio/carbid-ios/` | Capacitor | Dormido | Wrapper iOS de Renew Subastas |
| **Dashboard Fernando (Advisor)** | `~/Escritorio/DASHBOARD FERNANDO/` | Next.js 16 + ECharts + SQLite + Claude API | En producción | Inteligencia comercial sobre mercado automotor PY (CADAM/DNRA). 12 secciones |
| **Gestión de Compras** | `~/Escritorio/GESTION COMPRAS/` | Next.js 15 + Drizzle + PostgreSQL | En desarrollo | Inventario, escaneo código barras, firma digital, circuito de compras |
| **Botika (CRM SRPY)** | `~/Escritorio/CRM SRPY/` + `~/Escritorio/Agente Bot/` | Vercel + Supabase + Kimi LLM | En producción | SaaS multi-tenant de bots de ventas WhatsApp/Messenger/IG con RAG |
| **Calidad NPS** | `~/Escritorio/CALIDAD NPS/` | Node + Google Apps Script + YCloud | En producción | Encuestas NPS por WhatsApp API |
| **Bitrix Claude (MCP + Dashboard)** | `~/Escritorio/BITRIX CLAUDE/` | Next.js 14 + Gemini + Bitrix24 API | En producción | Dashboard de marketing con lenguaje natural + servidor MCP (22 herramientas) |

### 🌐 Sitios Web por Marca (Assets)

| Proyecto | Ruta | Estado | URL/Dominio |
|----------|------|--------|-------------|
| **Santa Rosa Web** | `~/Escritorio/ASSET WEB SRPY/santa-rosa-web` | Activo | santarosa.com.py |
| **Jetour Paraguay** | `~/Escritorio/ASSET WEB SRPY/jetour-paraguay` | Activo | jetour.com.py (Vercel) |
| **JMEV Web** | `~/Escritorio/ASSET WEB SRPY/JMEV WEB` | Activo | (Vercel) |
| **Leapmotor PY** | `~/Escritorio/leapmotor-paraguay/` | Dormido | leapmotor.com.py |
| **Mitsubishi Motors PY** | `~/Escritorio/ASSET WEB SRPY/mitsubishi-motors-paraguay` | Dormido | mitsubishi.com.py |
| **Renew Usados** | `~/Escritorio/ASSET WEB SRPY/renew-usados` | Activo | renew.com.py |
| **XPeng Paraguay** | `~/Escritorio/ASSET WEB SRPY/xpeng-paraguay` | Dormido | Landing preventa |
| **Landing Expo Form** | `~/Escritorio/LANDING EXPO FORM/` | Activo | Captura leads → Bitrix24 |

### 📊 Dashboards y Data

| Proyecto | Ruta | Stack | Descripción |
|----------|------|-------|-------------|
| **Buyer Persona** | `~/Escritorio/BUYER PERSONA/` | Python + Obsidian + Meta API | Pipeline de buyer personas con datos de ventas CRM + Meta Ads |
| **Croman Ads Dashboard** | `~/Escritorio/croman-ads-dashboard/` | Next.js 16 + Meta API v21 | Dashboard Meta Ads multi-cuenta. Phase 1 read-only |
| **Dashboard Meta Ads** | `~/Escritorio/Dashboard/` | BI | Dashboards BI + Bitrix |
| **Auditoría Meta** | `~/Escritorio/AUDITORIA META/` | Python (python-pptx) | Reportes PPTX de campañas |
| **Croman Ads (Scripts)** | `~/Escritorio/CROMAN ADS/` | Python | Scripts de auditoría Meta Ads Q1 2026 |

### 🤖 Agentes IA y Automatización

| Proyecto | Ruta | Descripción |
|----------|------|-------------|
| **Agentes IA** | `~/Escritorio/AGENTES IA/` | Backend de agentes IA + agency-agents (144+ personalidades) |
| **Hermes Agente** | `~/Escritorio/HERMES AGENTE/` | Registro de proyectos + automatización Hermes |
| **Agencia SRPY** | `~/Escritorio/AGENCIA SRPY/` | Bot Python + servidor YCloud |

### 🔧 Tools y Utilidades

| Proyecto | Ruta | Descripción |
|----------|------|-------------|
| **Tools iOS Builder** | `~/Escritorio/tools/` | CLI Go para compilar iOS sin Mac desde Windows/Linux |
| **PC SRPY** | `~/Escritorio/PC SRPY/` | Scripts internos, etiquetas, facturación Meta |
| **Open Design** | `~/Escritorio/OPEN DESING/` | Fork de Open Design (design system local) |
| **Hermes Agent** | `~/.hermes/` | Config de Hermes con cron jobs de monitoreo |

### 💤 Dormidos / Completados

| Proyecto | Descripción |
|----------|-------------|
| **Croman Pilates** | Landing El Estudio Pilates (Next.js + Vercel) |
| **Croman Publik** | SaaS inmobiliario para REMAX 360 PY |
| **Croman CRM** | Fork de Huly Platform (self-hosting pendiente) |
| **Croman Aura** | Agente WhatsApp "aura" (Next.js + SQLite + OpenAI) |
| **RRHH Licencias** | Digitalización de permisos RRHH (fase diseño) |
| **Press Omar** | Deck interactivo de productos SRPY |

---

## 🛠️ Stack Tecnológico

### Lenguajes y Frameworks
- **Frontend:** Next.js 14-16, React 19, Vite, Tailwind CSS, TypeScript
- **Backend:** Node.js (Express, Firebase Cloud Functions, Vercel Serverless), Python
- **Mobile:** React Native, Capacitor (iOS)
- **Database:** Supabase (PostgreSQL), Firebase (Firestore), SQLite
- **ORM:** Drizzle (compras), Supabase client directo (PDI)

### APIs y Servicios
- **Meta Marketing API v21.0** — 85+ cuentas de anuncios
- **Bitrix24 CRM** — CRM comercial + administrativo (MCP server propio)
- **YCloud WhatsApp API** — mensajería masiva + bots
- **Claude API** — dashboard advisor + agents
- **Gemini API** — dashboard marketing Bitrix
- **Kimi/GLM LLM** — bot de ventas Botika
- **Firebase** — Auth, Firestore, Cloud Functions (CARBID)
- **Vercel** — deploy de todos los Next.js

### Herramientas
- **Obsidian** — base de conocimiento principal (Buyer Persona vault)
- **Claude Code / Claude** — desarrollo y asistencia
- **Hermes Agent** — automatización y cron jobs
- **Git** — la mayoría de proyectos versionados
- **Google Sheets** — control de proyectos

---

## 📋 Control de Proyectos

Sheet maestro: [Control_Proyectos_IA](https://docs.google.com/spreadsheets/d/1sCm6lU5fFUFPN09Z87CWR2hTxzJqWiaM/edit?gid=1364459073)

### Prioridades actuales (agosto 2026)
1. **Bitrix Comercial** (95%) — cerrar JT y GWM
2. **Bitrix Adm** (95%) — carga de documentos
3. **Dashboard de Mercado** (80%) — pruebas + mostrar a Fer
4. **Dashboard Creación de Pauta** (70%) — integrar API Bitrix con asesores
5. **Dashboard Producto PY-UY** (60%) — conectar con dashboard de Ángel
6. **Buyer Persona y Tráfico Web** (60%) — completado con inteligencia competitiva

### Completados
- ✅ Agente de Ventas Leads (Renew → Bitrix)
- ✅ Dashboard Meta Ads (operativo)
- ✅ App Subasta Renew (renewsubastas.com.py)
- ✅ Dashboard PDI (v2.36, aprobado)
- ✅ Ycloud Masivo (MKT + Postventa NPS)
- ✅ Sitios web por marca (bajo demanda)

### Sin iniciar
- ⬜ Landing BOLT
- ⬜ Ycloud Asesores (evitar bloqueo WhatsApp Business)
- ⬜ Bot Asistencia Técnica (empezar con Jetour)
- ⬜ Gestión de Compras (en PRD)
- ⬜ Dashboard Renew

---

## 👥 Equipo

- **Carlos Roman (Croman)** — Encargado de Innovación (yo)
- **Pablo Villalba** — Asistente en Santa Rosa Paraguay S.A.
- **Bernardo** — Desarrollador de la empresa
- **Liza y Liz** — Logística/Importación (usan PDI)
- **Carlos (PDI)** — Operador PDI
- **Fernando (Fer)** — Revisa Dashboard de Mercado
- **Ángel** — Dashboard Producto
- **Javier / Bruno** — Marketing (Ycloud Masivo)
- **Sebastian Ricci** — Aprobó PDI (presentación 14/07)

---

## 🧠 Cómo trabajo

### Preferencias
- **Ejecución directa:** pido algo → espero resultado ejecutado y verificado → pido el siguiente paso
- **No teoría:** quiero cosas hechas, no planes abstractos
- **Paralelo:** trabajo múltiples proyectos simultáneamente
- **Verificación visual:** prefiero ver resultados en browser, no en terminal
- **Obsidian primero:** la base de conocimiento vive en Obsidian
- **Automatización:** todo lo repetible debe tener cron job o script
- **Español:** comunicación estructurada con tablas y datos concretos

### Reglas para asistentes de IA
1. Antes de proponer, ejecutá
2. Si no podés ejecutar, decí por qué y proponé alternativa
3. Verificá lo que afirmás (corré el comando, leé el archivo)
4. Conectá los puntos entre proyectos (si algo de Buyer Persona sirve para Meta Ads, usalo)
5. Mantené Obsidian actualizado como fuente de verdad
6. Por ley: NUNCA nombres marcas/modelos de competencia en copies públicos
7. Si tocás código, respetá el CLAUDE.md de cada proyecto

---

## 📁 Obsidian Vault — Buyer Persona

Ruta: `~/Escritorio/BUYER PERSONA/`

### Estructura
```
output/personas/
├── 🤖 Meta Ads Lo Que Funciona.md      ← Mejores prácticas Meta
├── ⚔️ Benchmark Competitivo.md          ← Mapa de competidores
├── ⚔️ Battle Cards Modelo vs Modelo.md  ← 11 batallas verificadas
├── 🎯 Playbook Meta Ads.md             ← 86 cuentas → 6 estrategias
├── 📢 Promociones Competencia.md        ← Auto (cron diario 08:00)
├── Persona 01-16.md                    ← 16 buyer personas con 4 capas
└── Marketing/
    ├── Meta Ads - Persona 01-10.md     ← 8 copies regenerados (legales)
    ├── Email - Persona 01-16.md
    ├── Google Ads - Persona 01-16.md
    └── WhatsApp - Persona 01-16.md
```

### Cron jobs activos (Hermes)
- **Monitor Promociones Competencia** — diario 08:00 (script Python)
- **Monitor Competencia** — cada 6h (script bash + agente)
- **Análisis Competencia Semanal** — lunes 09:00 (agente web)
- **Diario Operativa** — diario 19:00 (Obsidian)
- **Tableros Semanales** — lunes 08:00 (script)
- **Registro Proyectos** — diario 07:00 (Obsidian)

---

## 🔗 Conexiones entre proyectos

```
CRM Bitrix24 ─┬─→ Dashboard Meta Ads (CPL, costo por marca/modelo/asesor)
              ├─→ Dashboard Creación de Pauta (lookalike, retargeting)
              ├─→ Agente de Ventas (leads → Bitrix)
              ├─→ Bitrix Claude Dashboard (lenguaje natural → Gemini)
              └─→ Buyer Persona (ventas CRM + Meta Ads → personas)

Meta Ads API ─┬─→ Buyer Persona (análisis de ad creatives)
              ├─→ Croman Ads Dashboard (multi-cuenta)
              ├─→ Auditoría Meta (reportes PPTX)
              └─→ Monitor Competencia (scraping de webs competidoras)

YCloud API ───┬─→ Calidad NPS (encuestas postventa)
              ├─→ Botika (bot WhatsApp)
              └─→ Agencia SRPY (servidor mensajería)

Sitios Web ───┬─→ Bitrix24 (webhook leads → CRM)
              ├─→ Firebase (CARBID subastas)
              └─→ Vercel (deploy)
```

---
*Última actualización: 04 agosto 2026*
