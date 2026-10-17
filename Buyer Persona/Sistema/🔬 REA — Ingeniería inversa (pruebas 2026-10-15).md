---
tipo: evaluacion
tema: REA (Reverse Engineer Anything) aplicado a proyectos Santa Rosa
actualizado: 2026-10-16
tags: [rea, competencia, seguridad, monitoreo, bitrix, herramientas]
---

# 🔬 REA — Ingeniería inversa (pruebas 2026-10-15)

REA (`morluto/rea`, MIT) es un servidor MCP + CLI que inspecciona sitios, apps, binarios y bases SQLite **sin código fuente**. Instalado el 15/10/2026 en la notebook:

- MCP registrado en Claude Code a nivel usuario (`~/.claude.json`, backup en `~/.claude.json.rea.backup`) + skill `reverse-engineer-anything`.
- CLI global `rea` 6.5.0 (`npm install -g rea-agents@6.5.0`). Actualizar: `rea update`.
- Clon del repo y resultados crudos: `~/Escritorio/CROMAN/REA/` (`rea/` y `pruebas/`).

> ⚠️ Lo que sale de sitios de competencia es **solo para uso interno** (ley PY de publicidad comparativa). REA no autoriza copiar código de terceros.

Relacionado: [[📈 Inteligencia de Mercado — Avances]] · [[⚔️ Benchmark Competitivo]] · [[📢 Promociones Competencia]] · [[Infraestructura y Conexiones]]

## Resultados

### Monitor de competencia (`scripts/gama_precios_competencia.py`)

Captura con `rea capture-browser-scenario` (Chrome headless, 8 s, red + cuerpos) de Kia, Chery y Hyundai, los tres marcados `js: True`.

| Sitio | Hallazgo | Acción sugerida |
|---|---|---|
| Kia | `https://www.kia.com.py/modelos` responde **301 → portada** (`kia.com.py`). `kia.com.py/modelos` da 404. La portada en HTML simple ya trae los 14 modelos | `url: https://kia.com.py`, `js: False` |
| Hyundai | Portada + `footer.html?v=4.8` (HTML simple) traen los 10 modelos | `js: False` y leer `footer.html` |
| Chery | Sitio Next.js. La portada en HTML simple trae M7, T2, T4, T7, T8 (falta Himla, que sale de subpáginas) | `js: False` en portada |

En la carga de portada (ventana de 8 s) ninguno llamó a una API propia con precios. Coincide con `precios: {}` en `output/competencia/gama_precios.json` (copia local del 04/09).

**Stack de marketing observado (solo uso interno):**

| Sitio   | Herramientas                                                                                                                                                                             |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Kia     | Meta Pixel, TikTok Pixel, Google Ads (2 cuentas), GA4 (2 propiedades), Campaign Manager/Floodlight (2 anunciantes), **Customer.io** (automatización CRM), MS Clarity, Adobe/programática |
| Hyundai | Meta, TikTok, Google Ads (4 IDs de conversión), **Adobe Audience Manager / DSP** + programática (OpenX, Index, BidSwitch)                                                                |
| Chery   | Meta, TikTok, Google Ads (1), GA4. Básico                                                                                                                                                |

### Monitoreo SRPY — binarios Go de los contenedores

`rea inspect-go-binary` sobre binarios copiados con `docker cp` (sin modificar el servidor):

| Binario | Go | Versión / build |
|---|---|---|
| beszel-agent / beszel-hub | 1.27.1 | devel, 17 / 40 dependencias |
| traefik (coolify-proxy) | 1.26.5 | v3.6.25, 349 dependencias |
| netdata go.d.plugin | 1.26.5 | 188 dependencias |
| cloudflared (compras) | 1.26.4 | imagen `:latest` pero compilado el **22/07/2026** (commit 3a2b45c2): el tag "latest" quedó viejo |
| coolify-sentinel | — | **sin metadatos Go** (static-pie): Trivy tampoco ve sus dependencias, es un punto ciego |

Trivy (`cerebro/fuentes/trivy.py`) ya escanea las imágenes, así que REA solo suma en los puntos ciegos y en la antigüedad de los binarios.

### Dashboard Comercial Bitrix (bitrix.santarosa.lat)

REA encontró **14 rutas `/api/...`** en el código servido antes del login. Prueba GET sin sesión: 12/12 → `401 Sesión requerida`. `/api/chat` → 405 a GET y `requireUser` en el código para POST. Se saltearon `auth/recuperar` y `avisos/probar` (pueden enviar mensajes). Ojo: el CLAUDE.md global dice "5 endpoints con requireUser"; hoy son más.

### Bitrix24 (portal `santarosapy.bitrix24.es`) — cerrado sin HAR (16/10)

**No hace falta ingeniería inversa.** Los webhooks que ya usan las apps (en Coolify) tienen los permisos `crm`, `disk`, `task`, `bizproc` y `documentgenerator`: la carga de documentos se puede automatizar con la **API REST oficial** (`crm.deal.update` con el campo de archivo en base64, `disk.*`), sin depender de las llamadas internas de la interfaz.

**Lo que mostró la API (solo metadatos y conteos, 16/10):** «carga de documentos» de Bitrix Adm son **44 campos de archivo** del negocio. Son los legajos de crédito numerados para persona física, persona con RUC y sociedad: cédula del titular y del codeudor, boletas de IPS, título o contrato de alquiler, cédula verde, solicitud firmada, factura de servicio, certificado tributario, estatutos, etc. **Casi no se usan:**

| Embudo | Negocios desde 17/08 | Con algún archivo |
|---|---|---|
| GWM Ventas | 506 | 3 |
| Jetour | 134 | 0 |
| Renault | 92 | 0 |
| Soueast | 91 | 1 |
| JAC | 82 | 1 |
| **Renew** | 60 | **9** |
| Mitsubishi | 50 | 0 |
| Resto (JMEV, Zeekr, Leapmotor, XPeng, posventa…) | 44 | 0 |
| **Total** | **1.059** | **14 (1,3 %)** |

38 de los 44 campos nunca se usaron en 60 días. Los documentos viajan por fuera de Bitrix (WhatsApp, mail, papel).

**Se probó y se quitó (16/10):** se armó una tarjeta «Legajos de crédito» en Administración → Facturación (v2.160) y un link de carga de documentos para el cliente (v2.161). Croman decidió que **no los quiere** y se sacaron de producción en la **v2.162**: el tablero volvió al código de la 2.159, las rutas `/legajo*` y `/api/legajo*` dan 404, y la clave `LEGAJO_SECRETO` se borró de Coolify. Nunca se usaron ni se escribió un solo archivo en Bitrix. El código sigue en el historial de git (`34949e4` la tarjeta, `0d5a1b4` el link; revertir `5452d28` lo trae de vuelta). Los números de arriba (14 de 1.059 negocios con algún archivo) quedan como dato de referencia, sin ninguna acción pendiente. De paso, el verificador de rutas (`7dc382f`) ahora ignora `version.json`, que cita rutas quitadas desde el CHANGELOG: producción da 28/28 protegidas, 0 avisos.

**De paso:** dos webhooks con casi todos los permisos del portal se comparten entre 7 apps. Lo sano sería un webhook por app con solo lo que usa. Además, el MCP `bitrix24` de Claude Code no conecta porque apunta a `~/Escritorio/BITRIX CLAUDE/` (la carpeta se movió a `~/Escritorio/BITRIX/BITRIX CLAUDE/`) y no tiene `.env` con webhook.

### Advisor (`data/cadam.db`)

`rea inspect-sqlite-database`: 23 tablas, 27 índices, 5 vistas (`v_snapshot_actual`, `v_matriculacion`, `v_importacion`, `v_importacion_nev`, `v_importacion_camion`). La copia local es del 22/07. Aporta poco porque el repo ya tiene el esquema.

## Cómo se integra (no es un menú aparte)

REA es una herramienta de taller: la usa Claude Code (MCP) y la pueden usar scripts (`rea` CLI). Sus resultados van a los lugares que ya existen:

1. **A demanda en Claude Code**: "analizá el sitio/app X". Sin menú.
2. **Cron semanal de competencia (Hermes)** ✅ 2026-10-16: `scripts/stack_marketing_competencia.py` (commits `185908ea` y `5856ffd0`, 11 tests) corre los **lunes 05:00 en el servidor** (job `742252864a6f`, sin agente). Abre la portada de los 18 sitios del monitor en Chrome y clasifica los pedidos a terceros. Escribe [[🛰️ Stack de Marketing — Competencia]] (enlazada desde [[⚔️ Benchmark Competitivo]]) y anota altas, bajas y cuentas nuevas en [[⚔️ Bitácora de Competencia]]. Una herramienta se da de baja recién después de dos semanas sin verla. En el servidor no hay Node, así que no usa REA: usa Chrome con `--log-net-log`, que en kia.com.py encuentra los mismos dominios. Primera corrida: 18/18 sitios en 69 s.
3. **Prueba post-deploy del Dashboard Bitrix** ✅ 2026-10-15: `scripts/verificar-rutas-protegidas.mjs` (commit `29940ea`, 10 tests). Junta las rutas de `api/` con las que nombra el código servido (REA + HTML) y exige 401/403 sin sesión. `desplegar-coolify.sh` la corre al final, también con `--solo-verificar`. Producción: 28/28 rutas protegidas. No frena el deploy (ya está hecho cuando corre): sale con 1 y avisa.
4. **Monitoreo** ✅ 2026-10-16: el escaneo de Trivy de los domingos (`seguridad-trivy`, 03:00) revisa además cada imagen **en uso** (`cerebro/fuentes/imagenes.py`, commits `be6bfa1` y `e66aec5` de `monitoreo-srpy`). Los eventos van al informe diario como «revisar»:
   - **Desactualizada:** el registro publica otro digest para el mismo tag. En lugar de mirar la fecha, compara contra el registro. Primera medición: 13 de 77 imágenes, entre ellas `cloudflared:latest`, `postgres:17`, `pgvector:pg17`, `portainer`, `vaultwarden`, `metabase` y las 3 de Wazuh.
   - **Punto ciego:** el binario principal es un ELF estático que Trivy no inventarió. Medido: **`coollabsio/sentinel`** y **`postgrest`** (Haskell). Los otros estáticos (`cloudflared`, `traefik`, `portainer`, `pgweb`, `gotrue`, `pgbackweb`) Trivy sí los ve.

   REA no corre en el servidor (no hay Node): se usa el registro de Docker y la lectura del encabezado ELF.
   Plan para actualizar las 13: [[🔄 Plan de actualización de imágenes (oct 2026)]] (empieza por `cloudflared`, sin corte).

**Monitor de competencia** ✅ 2026-10-15: Kia (`kia.com.py`), Chery y Hyundai pasaron a `js: False` (commit `0fbb3c3c`, aplicado en el servidor). Misma gama; Kia pasó de 1 a 13 páginas; los tres sitios, de ~197 s a ~26 s.
