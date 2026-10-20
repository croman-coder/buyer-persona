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

> ⚠️ **Antes de tocar código, confirmá la URL desplegada, no el nombre de la carpeta.**
> Hay varias apps con nombres parecidos y más de una viva a la vez. En agosto 2026 esto
> causó dos errores seguidos: se trabajó sobre `BITRIX CLAUDE/` y sobre
> `croman-ads-dashboard/` creyendo que eran los dashboards de producción, y no lo son.
> Los dos dashboards de uso diario en producción son los marcados con ⭐ más abajo.
> `croman-ads-dashboard/` (Santa Rosa Ads) también corre en producción desde octubre 2026,
> pero es otra app: ver su fila.

## 📂 Ecosistema de Proyectos

### 🟢 ACTIVOS — Desarrollo e Innovación

| Proyecto | Ruta | Stack | Estado | Descripción |
|----------|------|-------|--------|-------------|
| **Tasación Renew** | `~/Escritorio/Tasacion RENEW/` | Next.js 15 + Supabase self-hosted + Coolify | En producción | Tasación de usados que reemplaza el Excel del incidente del 27%. tasacion.santarosa.lat · fases 1-3 completas, auto-deploy por cron. Estado: nota `tasacion-renew` en Obsidian |
| **PDI Plainilla** | `~/Escritorio/PDI PLAINILLA/` | Next.js 14 + Supabase + Tailwind | En producción (v2.36) | Dashboard de pre-entrega de vehículos. 217 tests. Roles: admin, operador, lector |
| **CARBID (Renew Subastas)** | `~/Escritorio/CARBID/` | Next.js 14 + Firebase | En desarrollo | Plataforma de subastas de usados. renewsubastas.com.py |
| **CARBID iOS** | `~/Escritorio/carbid-ios/` | Capacitor | Dormido | Wrapper iOS de Renew Subastas |
| **Dashboard Fernando (Advisor)** | `~/Escritorio/DASHBOARD FERNANDO/Santa-Rosa-Advisor/` | Next.js 16 + ECharts + SQLite + Claude API | En producción | **advisor.santarosa.lat** (Coolify, app `advisor-fernando`, nixpacks) · repo de Fernando `fercorrea777/Santa-Rosa-Advisor`, rama `master` (lo desplegado es `origin/master`; el 9 oct 2026 el checkout local iba 2 commits de docs por delante). Inteligencia comercial sobre mercado automotor PY (CADAM/DNRA). 12 secciones. Desde el 20 oct 2026: acceso con el **globito** (mascota animada; correo @santarosa.com.py + clave, sin OTP), menú con perfil, búsqueda Ctrl K y plegado, **foto de perfil** y `/mi-cuenta` (la foto vive en Postgres, tabla `usuario_fotos`), favicon con el monograma de Santa Rosa, y números es-PY (decimales con coma). Sistema visual en `DESIGN.md` del repo. El Copiloto (`/copiloto`: Claude Opus 4.8 con una herramienta que consulta la base) recibió una clave válida el 9 oct 2026: su `ANTHROPIC_API_KEY` era un valor de 22 caracteres que la API rechazaba con 401, y se cargó la misma clave que usa Santa Rosa Ads (si algún día se rota, hay que cambiarla en Coolify en Ads, Meta, Bitrix, Advisor y **Callbot**, y en `~/.config/monitoreo/monitoreo.env` del servidor para el analista del monitor, que se la pierde si no: queda pausado con `HTTP 401`) |
| **Gestión de Compras** | `~/Escritorio/GESTION COMPRAS/` | Next.js 15 + Drizzle + PostgreSQL + Coolify | En producción | **compras.santarosa.lat** (Coolify, app `c3alcmmxxaciv6w6xk67m9m3`, nixpacks, despliega `master`; redeploy manual con `queue_application_deployment` por tinker, ver `docs/deploy-coolify-cloudflare.md`). Solicitudes → presupuestos → aprobación → orden → depósito → factura, con firma digital y escaneo de códigos. Desde el 13 oct 2026: rediseño + app instalable y **licitaciones con sobre cerrado** (`/licitaciones`; cada proveedor cotiza por línea en `/oferta/<token>`, sin cuenta). ⚠️ **No usar `drizzle-kit push` contra producción**: las restricciones de prod tienen nombres de Postgres (`_key`/`_fkey`) distintos a los de Drizzle y el push las recrearía. Los cambios de esquema van a mano (`CREATE`/`ALTER` en una transacción) con backup antes en `~/backup-compras/`. Pedido de licitaciones y reunión con Mario: `~/Escritorio/LICITACION SRPY/PEDIDO.md` |
| **Selección SRPY (TTHH)** | `~/Escritorio/SELECCION SRPY/` | Next.js 15 + Drizzle + PostgreSQL (`srpy-postgres`) + Coolify | En producción | **talento.santarosa.lat** (Coolify, app `seleccion-srpy`, nixpacks, rama `main`). Base de talentos de Talento Humano: el formulario «Trabajá con nosotros» de santarosa.com.py (`/trabaja-con-nosotros`, en el repo de la web) manda datos y CV a esta app; TTHH los busca (también dentro del CV), filtra y exporta a Excel desde un panel con login (roles `admin` y `tthh`). Pedido de Claudia Galeano (Gerente de TTHH, 16 oct 2026); Bitrix descartado. Fase 1 en producción desde el 16 oct 2026. **Desde el 20 oct 2026 con el diseño de la Agencia IA** (marco con barra lateral curva y cápsula de destinos, tarjetas de resumen por estado, una tarjeta por candidato) y el **Recorrido** de cada candidato (línea de tiempo con qué pasó, quién y cuándo, armada con lo que ya se registra; también quién abrió o bajó su CV, para admin y TTHH). La Fase 2 (los procesos: pedido de personal, publicación del aviso, pruebas y referencias, oferta, examen médico, contrato, inducción, con Bandeja, Avisos y Reportería) y la 3 (reportes) esperan la reunión con Claudia; cada proceso nuevo lleva su propio diseño y plan. ⚠️ **Autodeploy por sondeo de `main` cada 3 min** (`~/seleccion-autodeploy/check.sh` en el servidor): sin tests y sin migraciones, así que **la migración va primero, a mano** (nunca `drizzle-kit push`). Respaldo diario 02:30 con alerta por ntfy si se atrasa más de 26 h; falta activar la copia externa (`respaldo-externo.sh` del servidor, que ya copia `~/backups`). Pendientes: SMTP de TTHH, texto legal del consentimiento (hoy borrador) y la regla del teléfono con Claudia. Estado: nota `seleccion-srpy` en Obsidian; guías en `docs/` del repo |
| **Sarpy CRM** | `~/Escritorio/CRM SRPY/botika` | Node + Supabase self-hosted + Coolify | En producción | CRM interno de Santa Rosa (leads, chat, inventario, reportes). **crm.santarosa.lat** · API crm-db.santarosa.lat · repo croman-coder/crm-santarosa · DEPLOY.md. El proyecto de Vercel `sarpy-crm` se borró el 29 sep 2026 (sin dominio, todos sus deploys fallaban): **solo Coolify** |
| **Botika (bot WhatsApp, otro fork)** | `~/Escritorio/Agente Bot/botika` | Vercel + Supabase + LLM | En producción | Fork aparte del CRM; dueño de wa-gateway-botika en Coolify. No confundir con Sarpy CRM |
| **Calidad NPS** | `~/Escritorio/CALIDAD NPS/` | Node + Google Apps Script + YCloud | En producción | Encuestas NPS por WhatsApp API |
| **Bitrix Claude (MCP + Dashboard)** | `~/Escritorio/BITRIX CLAUDE/` | Next.js 14 + Gemini + Bitrix24 API | ⚠️ Nunca desplegado | Q&A de una página con Gemini. **No confundir con el Dashboard Comercial Bitrix**, que sí está en producción. Todos los `.env` con placeholders, 2 commits. El MCP (23 tools, no 22) es un clon de terceros que solo consume Claude Code |

### 🌐 Sitios Web por Marca (Assets)

| Proyecto | Ruta | Estado | URL/Dominio |
|----------|------|--------|-------------|
| **Santa Rosa Web** | `~/Escritorio/ASSET WEB SRPY/santa-rosa-web` | Activo | santarosa.com.py |
| **Jetour Paraguay** | `~/Escritorio/ASSET WEB SRPY/jetour-paraguay` | Activo | jetour.com.py (**Netlify**, sitio `jetourparaguay`) |
| **JMEV Web** | `~/Escritorio/ASSET WEB SRPY/JMEV WEB` | Activo | jmev.com.py (**Netlify**, sitio `jmevpy`) |
| **Leapmotor PY** | `~/Escritorio/leapmotor-paraguay/` | Dormido | leapmotor.com.py |
| **Mitsubishi Motors PY** | `~/Escritorio/ASSET WEB SRPY/mitsubishi-motors-paraguay` | Dormido | mitsubishi.com.py |
| **Renew Usados** | `~/Escritorio/ASSET WEB SRPY/renew-usados` | Activo | renew.com.py |
| **Zeekr Paraguay** | `~/Escritorio/ASSET WEB SRPY/zeekr` | En producción (Coolify, 18 sep 2026) | **zeekr.santarosa.lat** (alias; `zeekrlife.com.py` aún apunta al sitio viejo en DreamHost hasta cambiar NS a Cloudflare). Estático generado por `build_site.py` + API de leads → Bitrix (`/api/lead`, cola asesores Zeekr). Repo `croman-coder/zeekrweb`. Listo para espejo en Cloudflare Pages |
| **JAC Paraguay** | `~/Escritorio/ASSET WEB SRPY/JAC/app` | En producción | jac.com.py · jacmotors.com.py (**Netlify**) |
| **XPeng Paraguay** | `~/Escritorio/ASSET WEB SRPY/xpeng-paraguay` | Dormido | Landing preventa |
| **Landing Expo Form** | `~/Escritorio/LANDING EXPO FORM/` | Activo | Captura leads → Bitrix24 |

> ⚠️ **JAC — tres cosas que ya hicieron perder tiempo:**
> 1. La raíz del repo (`croman-coder/jac-paraguay`) es la subcarpeta **`JAC/app/`**, no `JAC/`. `JAC/app/app/` es el App Router.
> 2. Desde el **7 sep 2026 despliega solo en Netlify** (sitio `jacwebpy`). Se desconectó y borró el proyecto `app` de Vercel, y se paró la app `jac-paraguay` de Coolify — `jac.santarosa.lat` y `app-nine-bice-13.vercel.app` ahora dan 404 a propósito.
> 3. Netlify **necesita el `netlify.toml`** con `@netlify/plugin-nextjs` declarado. Sin eso publica `.next` como carpeta estática y **todas las rutas dan 404** (el síntoma: `/BUILD_ID` responde 200).
> 4. **Hay un panel en `jac.com.py/admin`** (desde el 21 sep 2026) para que el equipo edite talleres, sucursales y números de contacto sin tocar código. Los datos viven en `content/data/*.json`; **cada guardado es un commit en `main`** por la API de GitHub y Netlify redespliega solo. Si editás esos JSON a mano y alguien guarda desde el panel al mismo tiempo, GitHub rechaza al segundo (por sha). Qué se puede editar: `content/admin-schema.ts`. Variables en Netlify (scope `functions`, secretas): `ADMIN_PASSWORD`, `ADMIN_SESSION_SECRET`, `GITHUB_TOKEN`. ⚠️ El `GITHUB_TOKEN` es hoy el OAuth clásico de `gh` (scope `repo`, todos los repos): **conviene cambiarlo por un token de grano fino limitado a `jac-paraguay` con Contents: Read & Write**.

### 📊 Dashboards y Data

| Proyecto | Ruta | Stack | Descripción |
|----------|------|-------|-------------|
| **Buyer Persona** | `~/Escritorio/BUYER PERSONA/` | Python + Obsidian + Meta API + Bitrix24 | Pipeline con Meta real (85 cuentas, 17.800+ leads/90d vía page tokens) + embudo CRM Bitrix (solo agregados) + tableros de Campañas/Asesores. Cron `tableros-semanales` lunes 8:00, no consume GLM |
| **⭐ Dashboard Meta Ads** (PRODUCCIÓN) | `~/Escritorio/Dashboard/Dashboard META-*/Dashboard META/` | JS vanilla + Supabase propio (proxy `/supabase`) + Coolify | **dashboardmeta.santarosa.lat** (Coolify, desde el 18 sep 2026) · repo `dashboard-meta-ads`. Un `index.html` de ~12.700 líneas, 12 secciones. Auth Supabase (roles brand/manager/super_admin). Las contraseñas legacy se sacaron el 14/8 y la lista de usuarios el 16/9: el HTML público solo trae la anon key (pública por diseño, RLS verificado el 20/9). **El proyecto de Vercel `dashboard-meta-ads` se borró el 29 sep 2026**: `santarosaparaguay.com.py` da 404 `DEPLOYMENT_NOT_FOUND` a propósito y ya no queda publicada la clave del Supabase de la nube (el dominio sigue en la cuenta de Vercel y su correo entra por MX a AWS SES, no se tocó) |
| **⭐ Dashboard Comercial Bitrix** (PRODUCCIÓN) | `~/Escritorio/Dashboard/Dashboard Bitrix-*/Dashboard Bitrix/` | JS vanilla + ECharts + Coolify | **bitrix.santarosa.lat** · repo `santa-rosa-dashboard-bitrix` · 265 commits, 461 tests. 16 secciones. Login por Supabase (misma cuenta que Meta Ads); **todas** las rutas de `/api` piden sesión (28 al 16 oct 2026). `desplegar-coolify.sh` lo comprueba al final de cada deploy con `scripts/verificar-rutas-protegidas.mjs` (exige 401/403 sin sesión; a mano: `--solo-verificar`). ⚠️ **El proyecto de Vercel se borró el 10 sep 2026** a pedido de Croman: `santa-rosa-dashboard-bitrix.vercel.app` da 404 a propósito y ya no auto-despliega. Deploy: `./scripts/desplegar-coolify.sh` |
| **Santa Rosa Ads** (`croman-ads-dashboard`) | `~/Escritorio/croman-ads-dashboard/` | Next.js 16 + Meta API v21 + Claude API | **ads.santarosa.lat** (Coolify, app `santa-rosa-ads`, desde el 5 oct 2026; con login). App de pautas: campañas, anuncios, presupuestos, Google Ads, salud del pixel/CAPI y cola de aprobación. **NO es el dashboard de Meta que uso** (ese es dashboardmeta.santarosa.lat). Repo `croman-coder/APP-DE-PAUTAS`: Coolify despliega la rama **`rediseno-ads`** y un sondeo del servidor la redespliega sola cada 3 min (manual: `./scripts/desplegar-coolify.sh`). Ojo: el checkout local puede estar en otra rama (el 9 oct 2026 estaba en `diseno-ads`, desviada de la desplegada): mirá `git branch -vv` antes de asumir que lo local es lo desplegado. El proyecto viejo de Vercel (`cromanads.vercel.app`) quedó pausado: da 503 `DEPLOYMENT_PAUSED`. El asistente flotante usa la API de Claude (`ANTHROPIC_API_KEY` ya cargada en Coolify) con **Haiku 5.5** por defecto (`CHAT_MODEL`, desde el 9 oct 2026); "Generar pauta con IA" usa Sonnet 5.5 (`AI_MODEL`) |
| **Auditoría Meta** | `~/Escritorio/AUDITORIA META/` | Python (python-pptx) | Reportes PPTX de campañas |
| **Croman Ads (Scripts)** | `~/Escritorio/CROMAN ADS/` | Python | Scripts de auditoría Meta Ads Q1 2026 |

### 🤖 Agentes IA y Automatización

| Proyecto | Ruta | Descripción |
|----------|------|-------------|
| **Agentes IA** | `~/Escritorio/AGENTES IA/` | Backend de agentes IA + agency-agents (144+ personalidades) |
| **Hermes Agente (registro)** | `~/Escritorio/HERMES AGENTE/` | Escanea `~/Escritorio` diario (7:00), publica estado de cada proyecto en el vault. 10 tareas, 88 tests, mergeado a `master`. No confundir con el install real de Hermes en `~/.hermes/hermes-agent/` |
| **Agencia SRPY** | `~/Escritorio/AGENCIA SRPY/` | Bot Python + servidor YCloud |
| **Monitoreo SRPY** | `~/Escritorio/MONITOREO SRPY/` | Monitor de seguridad y salud del servidor: Wazuh + Beszel + Trivy + Netdata, cerebro Python (gemma → Claude Haiku por la API de Anthropic), Obsidian `Seguridad/`, portal monitoreo.santarosa.lat (Cloudflare Access; mapa reagraph + métricas en vivo). Repo privado `croman-coder/monitoreo-srpy`, rama `main`. Spec y plan en `docs/superpowers/`; operación en `docs/operacion.md` |

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
- **Claude API** — dashboard advisor + agents + asistente flotante de los tableros Meta, Bitrix y Ads (Haiku 5.5 por defecto desde el 9 oct 2026)
- **Gemini API** — dashboard marketing Bitrix
- **Kimi/GLM LLM** — bot de ventas Botika
- **Firebase** — Auth, Firestore, Cloud Functions (CARBID)
- **Vercel** — deploy de varios Next.js (⚠️ **no** JAC, Jetour ni JMEV, que están en Netlify)
- **Netlify** (equipo santarosapy) — sitios de marca y la subasta: jac.com.py, jacmotors.com.py, jetour.com.py, jmev.com.py, santarosa.com.py, mitsubishi.com.py, xpengcars.com.py, renew.com.py y renewsubastas.com.py. Plan Pro con 3.000 créditos por ciclo; **cada deploy a producción cuesta 15** (se agotaron el 26 sep 2026)
- **Coolify** (servidor SRPY186, `ssh srpy-servidor`) — 11 apps en `*.santarosa.lat`: tasación, compras, bitrix, meta-ads, PDI, advisor, prospectos, GWM, cotizador, callbot, crm

### Herramientas
- **Obsidian** — base de conocimiento principal (Buyer Persona vault)
- **Claude Code / Claude** — desarrollo y asistencia
- **Hermes Agent** — automatización y cron jobs
- **REA** (`morluto/rea`) — ingeniería inversa de sitios, apps, binarios y SQLite sin código fuente. MCP en Claude Code + CLI `rea` (solo en la notebook; el servidor no tiene Node). Pruebas y usos: nota `Sistema/🔬 REA — Ingeniería inversa` en el vault
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
6. **Buyer Persona y Tráfico Web** (85%) — Meta+Bitrix reales integrados, tableros automatizados; falta Google Ads (conector ya escrito, sin credenciales)

### Completados
- ✅ Agente de Ventas Leads (Renew → Bitrix)
- ✅ Dashboard Meta Ads (operativo)
- ✅ App Subasta Renew (renewsubastas.com.py)
- ✅ Dashboard PDI (v2.36, aprobado)
- ✅ Ycloud Masivo (MKT + Postventa NPS)
- ✅ Sitios web por marca (bajo demanda)
- ✅ Gestión de Compras (compras.santarosa.lat; licitaciones con sobre cerrado desde el 13/10/2026, reglas finales pendientes de la reunión con Mario)
- ✅ Selección SRPY, Fase 1 (talento.santarosa.lat; base de talentos de TTHH, publicada el 16/10/2026; Fases 2 y 3 esperan la reunión con Claudia)

### Sin iniciar
- ⬜ Landing BOLT
- ⬜ Ycloud Asesores (evitar bloqueo WhatsApp Business)
- ⬜ Bot Asistencia Técnica (empezar con Jetour)
- ⬜ Dashboard Renew

### En evaluación
- 🔍 **Inspección técnica precompra (tipo CarDoc)** — ⚠️ ya opera en Paraguay (`cardoc.com.py`, cobertura nacional) y hay un segundo competidor independiente (AutoCheckParaguay). No es terreno vacío. Detalle: `[[CarDoc — Benchmark para replicar en Paraguay]]` en Obsidian

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
- **Mario** — Compras; define las reglas de las licitaciones (las 10 preguntas de `PEDIDO.md`)
- **Claudia Galeano** — Gerente de Talento Humano; pidió la base de talentos (Selección SRPY) y define las etapas y los perfiles en la reunión de la semana del 19/10/2026

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
- **Diario Operativa** — diario 19:00 (Obsidian) — `73badacc69e0`
- **Stack de Marketing Competencia** — lunes 05:00, **en el servidor** (script `stack-marketing.sh`, sin agente) — `742252864a6f`. Qué herramientas carga cada web del mercado (pixel, programática, CRM): nota `Competencia/🛰️ Stack de Marketing — Competencia` + altas/bajas en la Bitácora. Código: `BUYER PERSONA/scripts/stack_marketing_competencia.py`
- **Tableros Semanales** — lunes 08:00 (script, `--no-agent`, no consume GLM) — `af1a7b81bba8`
- **Registro Proyectos** — diario 07:00 (Obsidian) — `c2032f300983`
- **vault-sync** — cada hora a los :45 (script `~/.hermes/scripts/sincronizar-vault.sh`, sin agente) — `f2a6e4f0466f`. Trae el vault del servidor, publica lo de la notebook y, desde el 13 oct 2026, copia este `~/CLAUDE.md` a `CLAUDE.md - Croman Innovacion.md` del vault si cambió

**Topología desde el 4 de septiembre 2026 — el servidor produce, la notebook hace pull.** El servidor (SRPY186) corre los crons por script (monitor de competencia + gama/precios, tableros semanales, mercado CADAM) y publica el vault por git cada hora (`publicar-vault`). El pipeline diario de personas (06:00) es un **timer de systemd** (`buyer-persona-pipeline.timer`), no un cron de Hermes — hoy vive en el servidor. La notebook corre solo lo que no puede hacer el servidor (registro de proyectos y los jobs con agente en su GPU) y sincroniza cada hora (`vault-sync`). Los duplicados quedaron **pausados**, no borrados. Detalle: nota `Sistema/📈 Inteligencia de Mercado — Avances` en el vault.

Detalle completo de infraestructura (gateway, GLM, gotchas, GitHub/Vercel/Firebase): `[[Infraestructura y Conexiones]]` en Obsidian.

---

## 🔗 Conexiones entre proyectos

```
CRM Bitrix24 ─┬─→ Dashboard Meta Ads (CPL, costo por marca/modelo/asesor)
              ├─→ Dashboard Creación de Pauta (lookalike, retargeting)
              ├─→ Agente de Ventas (leads → Bitrix)
              ├─→ Dashboard Comercial Bitrix (santa-rosa-dashboard-bitrix)
              └─→ Buyer Persona (ventas CRM + Meta Ads → personas)

Meta Ads API ─┬─→ Buyer Persona (análisis de ad creatives)
              ├─→ Dashboard Meta Ads (santarosaparaguay.com.py)
              ├─→ Auditoría Meta (reportes PPTX)
              └─→ Monitor Competencia (scraping de webs competidoras)

YCloud API ───┬─→ Calidad NPS (encuestas postventa)
              ├─→ Botika (bot WhatsApp)
              └─→ Agencia SRPY (servidor mensajería)

Sitios Web ───┬─→ Bitrix24 (webhook leads → CRM)
              ├─→ Firebase (CARBID subastas)
              ├─→ Netlify (deploy — la mayoría: JAC, Jetour, JMEV, Santa Rosa, Mitsubishi, XPeng, Renew)
              ├─→ Coolify (deploy — Zeekr)
              └─→ Vercel (deploy — Leapmotor)
```

---
*Última actualización: 20 octubre 2026*
