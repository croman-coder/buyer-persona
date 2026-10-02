---
tipo: infraestructura
tags:
  - sistema
  - hermes
  - infraestructura
actualizado: 2026-08-07
---

# Infraestructura y Conexiones — cómo está armado todo esto

Documento de referencia: qué corre en esta máquina, dónde vive cada cosa, y qué hacer si algo se rompe. Escrito para que tanto Hermes como Claude Code entiendan el sistema completo sin tener que redescubrirlo.

Relacionado: [[🏠 Inicio]]

---

## La máquina

Linux, usuario `croman`, hostname `croman-srpy`. Todo lo de abajo corre local, sin servidor remoto — "el servidor" es esta PC.

## Hermes Agent

- **Instalado en:** `~/.hermes/hermes-agent` (v0.19.1, actualizado desde el repo de NousResearch)
- **Binario:** `~/.local/bin/hermes` → symlink a `~/.hermes/hermes-agent/venv/bin/hermes`
- **Gateway:** servicio systemd de usuario `hermes-gateway.service`, con **linger habilitado** (sobrevive a que cierres sesión). Sin el gateway corriendo, los cron jobs quedan registrados pero no disparan solos.
  - Ver estado: `hermes cron status`
  - Reinstalar si hace falta: `hermes gateway install --start-now --start-on-login`
- **Dashboard web:** `hermes dashboard` → `http://127.0.0.1:9119`
- **App de escritorio:** compilada localmente (Electron), lanzador en el menú de aplicaciones como "Hermes Agent". Requiere rebuild manual tras `hermes update` — y cada rebuild rompe el sandbox de Chromium, hay que reparar:
  ```bash
  sudo chown root:root ~/.hermes/hermes-agent/apps/desktop/release/linux-unpacked/chrome-sandbox
  sudo chmod 4755 ~/.hermes/hermes-agent/apps/desktop/release/linux-unpacked/chrome-sandbox
  ```

### Modelo

> [!success] 2026-08-15: causa raíz encontrada — era `num_ctx`, no el tamaño del modelo
> Todo lo que sigue más abajo sobre "el techo de capacidad de un 8.8B Q4" **era una hipótesis equivocada**. El modelo nunca fue el problema: le llegaba el prompt cortado.
>
> **El mecanismo.** Hermes habla con Ollama por `/v1` (compat OpenAI). Ese endpoint **no acepta `num_ctx` por request**, así que Ollama usa su default de **4096 tokens** y descarta el principio del prompt, sin avisar. El prompt del agente son ~20k tokens (system 32 KB + esquemas de herramientas 46 KB + memoria). O sea: el modelo recibía un pedazo del medio, sin la pregunta y sin la memoria. Por eso contestaba "no tengo información sobre vos" y, con las herramientas cargadas, llegó a devolver texto en francés sobre SEO.
>
> **Prueba lado a lado** (prompt de 28k tokens con un marcador al principio y la pregunta al final):
>
> | modelo | `num_ctx` | resultado |
> | --- | --: | --- |
> | `gemma4:latest` | 4096 | *"no hay ningún MARCADOR-INICIO"* — no ve el arranque |
> | `gemma4-hermes-128k` | 131072 | responde el dato correcto |
>
> **El arreglo.** No es config de Hermes ni la variable `OLLAMA_CONTEXT_LENGTH`: hay que **hornear la ventana en el modelo** con un Modelfile y usar ese modelo.
>
> ```
> FROM gemma4:latest
> PARAMETER num_ctx 131072
> PARAMETER temperature 0.3
> ```
>
> Se llama `gemma4-hermes-128k:latest` y ahora existe en las dos máquinas. En SRPY186 ya estaba desde antes — quien lo armó había resuelto este mismo problema y no quedó anotado.
>
> **Detalle que confunde al diagnosticar:** Hermes valida contra el `num_ctx` **efectivo del modelo**, no contra `model.context_length` del `config.yaml`. Por eso `granite4.1-hermes` es rechazado por el mínimo de 64K de Hermes ("has a context window of 40,960 tokens") aunque el config diga 131072: ese modelo trae `num_ctx 40960` horneado.
>
> **Segundo bug, independiente:** `agent.reasoning_effort` estaba en `high`. gemma4 tiene modo *thinking* y manda el razonamiento a un campo `thinking` aparte; el shim `/v1` entonces devuelve `content` **vacío**. Con `reasoning_effort: none` responde normal en 1,1s. Ojo: `think: false` **no** se respeta en `/v1`, solo en `/api/chat`.
>
> **Al diagnosticar:** `hermes -z` **sin `-t` no tiene herramientas ni memoria**. Cualquier conclusión sobre lo que Hermes "sabe" sacada de ahí es inválida — hay que pasar toolsets explícitos. El de archivos se llama `file` (singular); no existe ninguno llamado `obsidian`.
>
> **Verificado después del cambio:** ejecuta comandos de verdad (`hostname` → `croman-srpy`, antes inventaba ejemplos), sabe quién es Croman, lista las 10 marcas correctas, y lee notas del vault razonando sobre ellas (filtró bien "mejor margen entre marcas con más de 100 unidades" → JAC 23,0%, excluyendo KARRY que tiene 25,2% con 13 unidades).
>
> Los 4 cron jobs que llaman al LLM se re-pinnearon a `gemma4-hermes-128k:latest`. Los dashboards de Meta y Bitrix tenían **los dos bugs** y se corrigieron igual.

> [!info] Decisión 2026-08-07: modelo local como primario, queda así
> `model.provider` pasó de `zai` a **`ollama`**, apuntando a un servidor propio en la red local: `http://192.168.221.87:11435/v1`, modelo `granite4.1-hermes:latest`. GLM quedó como `fallback_providers[0]`. Decisión tomada con evidencia — no revisar de nuevo salvo que empiece a fallar en uso real.
>
> **Veredicto de la batería de pruebas (5 casos, comparado contra GLM cuando tenía cuota):**
> - **Prompts triviales/ambiguos de una palabra ("decí ok"):** falla mal y consistente — reproducido 2 veces, ambas alucinando (una vez "es checo", otra vez que traduce a "December"). Inventa con confianza total.
> - **Prompts reales con contexto** (resumir un proyecto con datos dados, formato JSON, admitir que no sabe algo): anduvo bien 4 de 4 — español correcto, sin inventar datos, JSON válido (aunque envuelto en \`\`\`json cuando se pidió sin texto extra).
> - **Tool-calling** (lo que más importa — es el modo en que Hermes opera todo el tiempo): limpio, 0.7s, `tool_call` bien formado.
> - Conclusión: el modo de falla es específico a prompts cortos/sin contexto, que no es como Hermes arma sus prompts reales (los crons siempre mandan contexto). Para el uso real (crons con contexto, tool-calling) el modelo local rinde bien.
>
> **Riesgo a vigilar:** GLM (el fallback) estuvo sin cuota varias veces esta semana. Si el local falla mientras GLM también está sin cuota, no hay red de contención — no es un problema de hoy, pero vale la pena que alguien lo note si empieza a pasar seguido.
>
> **Bug aparte, menor, no bloqueante:** `/v1/models` en ese mismo servidor tiene el chunked-encoding roto — conecta y da HTTP 200 pero corta la transferencia (`curl` exit 18). El server se identifica como `BaseHTTP/0.6 Python/3.12.3`, no es el HTTP server nativo de Ollama — probablemente un proxy casero delante. No afecta el chat ni el tool-calling, pero cualquier herramienta que liste modelos contra ese endpoint (`hermes doctor`, selector de modelo) puede colgarse ahí.

> [!warning] 2026-08-07 (más tarde): reporte real de "sigue sin responder bien"
> El veredicto de arriba fue con prompts sintéticos cortos. En uso real (prompt completo de Hermes, ~32.000 tokens con system prompt + 40+ herramientas + memoria) el reporte es que la calidad no convence. Un test en vivo (`hermes -z`, pregunta real de negocio) sí salió bien — no se pudo reproducir el fallo en el momento, puede ser intermitente o específico a cierto tipo de tarea.
>
> **Dato duro encontrado, más creíble que cualquier otra explicación:** el modelo real es **8.8B parámetros, cuantizado a Q4_K_M** (4 bits) — confirmado vía `ollama show` en el puerto nativo (11434). Es un modelo chico y comprimido. Con el prompt real de Hermes siendo tan grande (32k tokens, decenas de herramientas), tiene sentido que un modelo de este tamaño pierda calidad bajo esa carga aunque conteste bien preguntas sueltas — no es un bug, es un techo de capacidad esperable para 8.8B en Q4.
>
> **Bug real corregido:** Hermes no podía detectar el context length del modelo (el probe fallaba, probablemente por el mismo bug de `/v1/models` de arriba) y asumía 256.000 tokens por default. El real es **131.072** (confirmado vía `ollama show`, campo `granite.context_length`). Corregido con `model.context_length: 131072` en `config.yaml` — sin esto, Hermes podía pensar que tenía el doble de espacio real disponible.
>
> **Sigue abierto:** si el problema persiste después de este fix, el techo de capacidad de un 8.8B Q4 frente al prompt completo de Hermes es la explicación más probable — en ese caso la opción real es un modelo local más grande (o menos cuantizado), no un ajuste de config.

> [!danger] 2026-08-14: 5 de 7 cron jobs quedaron `[paused]` una semana entera, arreglado
> Chequeo de rutina encontró que `hermes cron list` (sin `--all`) solo mostraba 2 jobs activos, y **ambos estaban fallando**: `registro-proyectos` bloqueado por la guardia de seguridad `#44585` ("global inference config drifted... Skipped to prevent unintended spend" — el job se creó con `zai`/`glm-5.2` pinneado implícito, el switch a Ollama local lo dejó desincronizado), y `PDI - Sync Cars` (job ajeno a esta sesión) fallando por falta de `CRON_SECRET` en `/home/croman/.config/pdi/sync-cars.env`.
>
> Con `hermes cron list --all` aparecieron 5 jobs en `[paused]`: `diario-operativa`, `tableros-semanales`, `Monitor Competencia`, `Monitor Promociones Competencia`, y `Analisis Competencia Semanal`. Los primeros 4 tenían historial de haber corrido bien antes; el último **nunca tuvo ni un solo intento registrado**, ni antes de esta semana — problema previo y aparte, no se tocó.
>
> **Causa de fondo no confirmada del todo:** los logs muestran varios reinicios del gateway vía SIGTERM/systemd esa tarde del 06-08 (16:05, 16:15, 16:31, 17:04, 18:00...), pero ningún log dice explícitamente "job pausado" — probablemente efecto colateral de esos reinicios repetidos, no algo deliberado. No se investigó más a fondo el porqué de los reinicios en sí.
>
> **Arreglado 2026-08-14:**
> - `registro-proyectos` y `diario-operativa` (los dos jobs que llaman al LLM) pinneados explícito a `provider=custom model=granite4.1-hermes:latest` — `hermes cron edit <id> --provider custom --model granite4.1-hermes:latest` — esto los saca de la guardia de deriva para siempre, ya no importa si el modelo global vuelve a cambiar.
> - Los 4 jobs legítimos, reactivados: `hermes cron resume <id>`.
> - `Analisis Competencia Semanal` y `PDI - Sync Cars` quedaron sin tocar — el primero por no tener ningún historial que confirme que alguna vez funcionó, el segundo por ser de otro proyecto que no conozco a fondo (falta credencial en un archivo fuera de este vault).
>
> **Lección para la próxima vez que el modelo global cambie:** cualquier job de cron que llame al LLM y no esté pinneado va a bloquearse solo la próxima corrida — no es un bug, es la guardia `#44585` funcionando como debe. Pinnearlo explícito con `--provider`/`--model` en cuanto se confirme el cambio de modelo, no esperar a que falle.

> [!danger] Aparte: redacción de secretos desactivada desde 2026-08-06
> `HERMES_REDACT_SECRETS=false` — cada arranque del gateway lo repite como warning: "API keys and tokens may appear verbatim in chat output, session JSONs, and logs." No se tocó (no se sabe si fue deliberado), pero vale la pena decidir si se re-habilita: `security.redact_secrets: true` en `config.yaml`.

### GLM (z.ai Coding Plan) — ahora fallback, no primario

- **Proveedor:** `zai`, modelo `glm-5.2`
- **Endpoint correcto:** `https://api.z.ai/api/coding/paas/v4` (el genérico `.../paas/v4` sin `coding` da HTTP 429 "insufficient balance" — es un plan distinto, no el mismo saldo)

> [!warning] Gotcha ya resuelto dos veces — si vuelve a fallar con 404 o 429, revisar acá primero
> Hay **tres lugares** donde esta URL puede quedar mal, y basta con que uno esté desactualizado para romper todo:
> 1. `~/.hermes/config.yaml` → `model.base_url`
> 2. `~/.hermes/.env` → `GLM_BASE_URL`
> 3. `~/.hermes/auth.json` → `credential_pool.zai[0].base_url` (cache del probe automático — se regenera solo y puede volver a corromperse con un punto de más al final: `.../v4.`)
>
> Si aparece `HTTP 404: path "/v4./chat/completions"`, es el punto de más en alguno de los tres. Corregir los tres y reiniciar el gateway (`hermes gateway restart`).

- **Límite de uso:** cuota rodante de 5 horas. Se agota rápido con `reasoning_effort: ultra` en tareas de resumen masivo (ej. resumir 30+ proyectos de una).
- **`agent.reasoning_effort`** está en `high` (bajado desde `ultra` el 2026-08-04 por esto mismo). Para una sesión puntual más profunda: `/reasoning ultra` dentro del chat, no toca el global.

---

## Registro de Proyectos

Escanea `~/Escritorio` y publica notas de cada proyecto en el vault, automático.

- **Código:** `~/Escritorio/HERMES AGENTE/` (repo git propio, rama `master` — **no es** el clon de hermes-agent, ese se borró por redundante; el Hermes real vive en `~/.hermes/hermes-agent`)
- **Estado mecánico:** `~/.hermes/registro-proyectos/registro.json` + `firmas.json`
- **Salida:** `Proyectos/*.md` en este vault + `[[Proyectos]]` como índice
- **Cron `registro-proyectos`** (`c2032f300983`) — diario 7:00 — escanea, detecta qué proyecto cambió desde el último resumen, y delega a subagentes el resumen de los que están stale
- **Diseño clave:** `resumen` (texto del LLM) se recupera del frontmatter viejo si el scan no trae uno nuevo — sobrevive indefinidamente. `resumen_pendiente` es SIEMPRE cómputo fresco (firma cambió O la nota no tiene resumen) — nunca se arrastra un valor viejo. Esta distinción costó 3 rondas de fix, no simplificar.
- **88 tests**, `.venv` propio en el repo con Python 3.12

## Buyer Persona (Meta Ads + Bitrix + leads reales)

- **Código:** `~/Escritorio/BUYER PERSONA/` (repo git propio)
- **Credenciales:** `.env` en la raíz del proyecto — `META_ADS_ACCESS_TOKEN` (System User, 85 cuentas), `META_ADS_AD_ACCOUNT_IDS` (act_id:Marca, las 85), `BITRIX_WEBHOOK_URL`
- **Pipeline:** `python main.py` — baja Meta Ads (demografía, campañas, leads por página vía page access token — **no** por cuenta publicitaria, ahí no existe `leadgen_forms`) + histórico de ventas → genera personas en `output/personas/` → copia al vault
- **Tableros adicionales:** `scripts/generar_tablero_meta.py` (Campañas + Scorecard Asesores) y `scripts/tablero_bitrix.py` (embudo CRM, solo agregados, sin PII)
- **Cron `tableros-semanales`** (`af1a7b81bba8`) — lunes 8:00, modo `--no-agent` (no consume GLM, es Python puro) — corre los tres pasos en cadena
  - El stub que dispara el cron vive en `~/.hermes/scripts/tableros_semanales.sh` y hace `exec` hacia el script real en el repo (Hermes exige que el script esté físicamente dentro de `~/.hermes/scripts/`, bloquea symlinks — guard anti symlink-escape en `cron/scheduler.py`)

## Diario de operativa + memoria

- **Cron `diario-operativa`** (`73badacc69e0`) — diario 19:00, con skill `obsidian`
- Busca en `session_search` qué pasó en el día, cruza con `registro.json`, escribe `Operativa/AAAA-MM-DD.md`, y guarda en `~/.hermes/memories/` **solo aprendizajes durables** (nunca hechos de un solo día)

## Otros cron jobs activos (pre-existentes, no de esta sesión)

- `Monitor Competencia` (`5722c3e69cee`) — cada 360 min
- `Analisis Competencia Semanal` (`ba49663d1735`) — lunes 9:00
- Monitor de Promociones — diario 08:00 → `~/Escritorio/BUYER PERSONA/output/competencia/📢 Promociones Competencia.md`

## Ver todo junto

```bash
hermes cron list      # todos los jobs, últimas corridas, próximas
hermes cron status    # gateway vivo o no
hermes cron runs <id> # historial de un job puntual
```

---

## Conexiones GitHub / Vercel / Firebase

Verificado 2026-08-05 — Hermes corre con `terminal.backend: local`, hereda exactamente estas credenciales (no son promesas, son sesiones reales ya logueadas en esta máquina):

| Herramienta | Estado |
|---|---|
| GitHub CLI (`gh`) | ✅ `croman-coder` (activa) + `ymk5py-commits` + `remax360paraguay`, scope `repo` = push/PR |
| Vercel CLI | ✅ `croman-coder` |
| Firebase CLI | ✅ `rey.asocia@gmail.com` |

Implica poder de escritura real (push, deploy a producción) sin aprobación intermedia — a tener en cuenta antes de dejar un cron dispare acciones de este tipo sin supervisión.

## Claude Code ↔ Hermes

Dos agentes separados, sin conexión directa hoy. Se puede armar: Hermes tiene herramienta de terminal, puede invocar `claude -p "..."` en modo headless para delegar tareas de código pesadas. Sin memoria compartida entre invocaciones salvo `--resume`. Requiere `--allow-dangerously-skip-permissions` para correr sin intervención en un cron — usar solo en directorio acotado.

## Asistente flotante en los dashboards (2026-08-14)

Orbe abajo a la derecha que abre un chat sobre los datos que el usuario tiene en pantalla. Está en los dos tableros de producción. Solo lectura.

### Arquitectura — tres piezas

| Archivo | Rol |
|---|---|
| `bot-widget.js` | **Compartido, byte a byte idéntico en ambos.** No sabe nada del tablero: pide `window.__botContext()`, `__botAuthHeaders()` y `__botReady` |
| `bot-context.js` | **Adaptador de cada tablero.** Arma un objeto ya agregado con sección activa, filtros, período y datos |
| `api/chat.js` | Endpoint. Exige sesión. Lo único que cambia entre tableros es la constante `PERFIL` |

Para llevarlo a otra app: copiar el widget sin tocarlo y escribir el adaptador. Si aparece la tentación de editar el widget para un tablero puntual, va en el adaptador.

Los dos dashboards declaran su estado con `let`/`const` top-level, que **no** llegan a `window`. El widget se carga como `<script>` clásico después del resto, y así lee `STATE`/`DataEngine` por nombre directo. Como módulo ES no los vería.

### Decisiones que salieron de medir, no de suponer

> [!important] Nunca mandarle filas crudas al modelo — precalcular los rankings
> Con 40-60 filas sin procesar, el modelo se equivoca de renglón (dijo `CAMP_0029` cuando era `CAMP_0035`). Responde castellano fluido con nombres y montos reales, y está mal — el peor modo de falla para decidir plata, porque parece correcta.
>
> Con los rankings resueltos en JavaScript (`peor_cpl`, `mas_leads`, `sin_ventas`) y una instrucción de usarlos: **6/6**. La respuesta pasa a ser correcta por construcción; el modelo solo redacta una conclusión ya calculada.
>
> Efecto lateral: el prompt bajó de ~4.300 a ~1.900 tokens. Menos contexto y más preciso a la vez.

> [!warning] `num_ctx` de Ollama: 4096 por defecto, sin importar lo que declare el modelo
> Un modelo que declara 128k de contexto **no** significa que Ollama le asigne 128k en runtime. El default es 4096 y todo lo que pasa de ahí se trunca en silencio: el modelo devuelve vacío.
>
> Esto explica el "Hermes responde mal" de meses: su prompt de sistema son ~32k tokens, o sea que venía funcionando con sus instrucciones **cortadas al 12%**.
>
> Se arregla del lado del servidor con `OLLAMA_CONTEXT_LENGTH`. Ojo: el `model.context_length` de la config de Hermes es otra cosa — es Hermes diciéndose cuánto puede mandar, no lo que Ollama asigna.

> [!tip] Elegir el modelo por tiempo de carga, no por tamaño
> `gemma4:26b` (18 GB) tarda **102s** en cargar desde frío — más que cualquier timeout razonable, y por eso el asistente devolvía 502. `gemma4:latest` (~10 GB) carga en **19s** y responde en **0,33s** en caliente contra 2,2s.
>
> Acierta lo mismo, porque con los rankings precalculados el tamaño dejó de importar para la precisión. Se manda `keep_alive: 2h` en cada request para que no se descargue (Ollama lo hace a los 5 min).

### Gotchas de red

- **Vercel no alcanza la red interna ni el tailnet.** El proveedor se elige por entorno (`LLM_PROVIDER=local|anthropic`), no por código, justamente por esto.
- **Cloudflare bloquea el `User-Agent` de `Python-urllib` con 403.** `undici` (el fetch nativo de Node, el que usa Vercel) pasa sin problema. Me costó minutos creyendo que el túnel se había caído.
- **`vercel env pull` devuelve las variables vacías** cuando el proyecto las marca sensibles. Un valor vacío ahí no significa que esté vacía en Vercel.

### Seguridad — lo que se cerró y lo que queda

Cerrado el 2026-08-14:

- Proxy `/api/bitrix` reenviaba **cualquier** método REST sin autenticación → whitelist de 12 métodos de solo lectura + sesión obligatoria.
- Webhook de Bitrix hardcodeado en 5 archivos servidos públicos → sacado, va por env var. **Token rotado, dar el viejo por comprometido.**
- Dashboard Comercial sin login → Supabase Auth, reusando el mismo proyecto que el de Meta (una cuenta para los dos).
- 9 contraseñas en texto plano en el HTML público del dashboard de Meta → removidas. Consecuencia asumida: si Supabase se cae, nadie entra.
- El asistente iba a recibir `STATE.conversions` y `STATE.bitrixMatch` enteros, que traen nombre, teléfono y email de clientes → solo van los agregados.

> [!danger] Sigue abierto: `ollama.santarosa.lat` sin autenticación
> Responde HTTP 200 a cualquiera en internet. Expone 11 modelos, incluidos los `:cloud` que **consumen cuota paga** de la cuenta de Ollama.
>
> No se puede simplemente cerrar: los bots de los dos dashboards dependen de ese túnel. La solución es Cloudflare Access con service token — el código ya manda `CF-Access-Client-Id` y `CF-Access-Client-Secret` si están en el entorno.
>
> Requiere el panel de Cloudflare o sudo en la máquina; no se pudo hacer desde la sesión.

---

## Mantenimiento del vault Buyer Persona — 2026-08-25

> [!check] Limpieza y arreglos estructurales ejecutados
>
> **Doble árbol eliminado.** `Buyer Persona/Buyer Personas/` era copia byte-idéntica de `output/personas/` (86 personas + 344 Marketing + 10 Audiencias, 0 diffs). Se archivó en `_ARCHIVO/Buyer Personas duplicado pre-2026-08-25`. Fuente de verdad única: **`output/personas/`**. El resto del árbol `Buyer Persona/` (Sistema, Operativa, CRM, Proyectos, Competencia) sigue siendo el vault activo — no tocar.
>
> **Numeración 1–72 sin colisiones.** Había 14 números con dos modelos distintos y 7 modelos duplicados (regeneraciones viejas sin borrar). Dedup: quedó siempre la versión más nueva; 70 archivos viejos en `_ARCHIVO/personas-duplicadas/`. MOC verificado: los 72 wikilinks resuelven.
>
> **Causa raíz corregida** en `src/generators/persona_generator.py`: la numeración salía de `len(personas)+1` y un modelo que entraba/salía del catálogo desplazaba todo. Ahora cada modelo conserva su número de disco (`_numero_existente`) y los nuevos toman el siguiente libre real.
>
> **Monitor de promociones (.py) roto desde ~18/08**: fallaba con `ModuleNotFoundError: bs4` dentro de la corrida del agente cron, que reportaba "ok" igual. Arreglos: `beautifulsoup4` agregada a requirements.txt, `.venv` propio del proyecto creado con uv, cron diario actualizado para usar `scripts/py.sh` (wrapper que limpia `PYTHONPATH`/`VIRTUAL_ENV` de Hermes — sin eso numpy/pandas explotan por mezclar binarios py3.11/py3.12). El informe ahora también copia a `output/personas/📢 Promociones Competencia.md`.
>
> **Incidente durante el arreglo:** un bootstrap de pip mal dirigido instaló paquetes en el venv de Hermes y bajó 4 pins suyos (jinja2/dotenv/yaml/requests). Fue restaurado a sus versiones exactas (`3.1.6 / 1.2.2 / 6.0.3 / 2.33.0`). Verificado.
>
> **venv legacy (`venv/`)**: reparado (numpy reinstalado, facebook-business 21.0.5, bs4) para que `run_pipeline.sh` siga funcionando. OJO: el paquete se importa como `facebook_business`, no `facebook`.

> [!warning] Pendientes detectados (requieren decisión de negocio o de Croman)
>
> 1. **Pipeline diario 06:00 casi nunca corre**: la máquina enciende ~08:27, después del horario del crontab. Sin anacron ni systemd timer con `Persistent=true`. Opciones: mover a systemd user timer persistente, o correr al arranque.
> 2. **Mitsubishi sin audiencia posible**: las 525 ventas del ERP tienen email/teléfono corporativo de Nipon (`impor@nipon.com.py`, 524/525 filas). Recuperar contactos reales desde Bitrix antes de pensar en semillas.
> 3. **Google Ads connector** escrito pero sin credenciales (`docs/COMO_CONECTAR_GOOGLE_ADS.md` tiene los pasos).

> [!warning] CORRECCIÓN 2026-08-25 (tarde): el árbol archivado ERA el vault visible
> El dedup de la mañana archivó `Buyer Persona/Buyer Personas/` creyendo que era una copia muerta, pero **era la vista del vault de Obsidian** (el `.obsidian` vive en `Buyer Persona/`). Resultado: las notas desaparecieron de Obsidian.
>
> **Resuelto:** se restauró la carpeta con el contenido NUEVO y limpio desde `output/personas/` (72 personas / 56 modelos / 288 Marketing / 12 Audiencias). No se perdió contenido: lo restaurado es más nuevo que lo archivado.
>
> **Regla a partir de ahora:** `output/personas/` es la fuente que genera el pipeline; `Buyer Persona/Buyer Personas/` es su espejo dentro del vault de Obsidian. El config (`obsidian_vault: Buyer Persona`) ya copia automáticamente los archivos regenerados al vault — NO volver a archivar ni borrar el espejo.

## Ollama en el servidor — 2026-09-06: destrabe, lista blanca y modelo abliterated

> [!bug] Lo que se encontró: el 27B no era lento, **no cargaba**
> Desde el **1/9 18:01** Ollama (v0.32.14, RTX 5070 12 GB) no había cargado **ningún** modelo nuevo: solo servía `gemma4-hermes`, que nunca expira porque el `healthcheck-bots.sh` (cron `*/5`) lo mantiene caliente. Cualquier pedido a otro modelo — el Qwen 3.8 27B Uncensored, `qwen3.8-hermes`, hasta `granite4.1:8b` en CPU puro — quedaba encolado en silencio hasta que el cliente se cansaba (15 min, `BrokenPipeError` en el log del proxy: 2/9, 4/9, 6/9). Ni una línea del scheduler en el journal. Es el mismo trabe del 1/9 (`Stopping...` durante una hora); la única carga posterior del 27B (25/66 capas en GPU, 9,7 GB en CPU) lo dejó así 5 días.
>
> Internet y RAM no tenían nada que ver: el túnel agrega ~300 ms; el servidor tiene 62 GB de RAM con 35 libres. El límite es la VRAM: 12,2 GB = gemma **5,0** + contenedor `voice-agent` (Coolify, 2,1 GB) + 5,0 libres. El 27B Q4_K_M pesa 17 GB.

**Qué se hizo (todo medido):**

| Paso | Resultado |
| --- | --- |
| `sudo systemctl restart ollama` (22:37; `sudo -n` cubre `systemctl`) | gemma recargó en **2,6 s a 137 tok/s**; granite en CPU cargó en 7,6 s (antes colgaba) |
| **Lista blanca en el proxy** `ollama-noreason-proxy.py` (env `NOREASON_ALLOW`, drop-in `~/.config/systemd/user/ollama-noreason.service.d/allow.conf`) | Modelo fuera de la lista → **404 `model_not_found` en 0,00 s** con mensaje claro (404 y no 503: los clientes OpenAI reintentan los 5xx en loop). `GET /v1/models` y `/api/tags` devuelven solo los permitidos, así Codex/OpenCode no los ofrecen. Respaldo `.bak4-20260906` |
| Permitidos | `gemma4-hermes`, `gemma4-hermes-abliterated`, `gemma4-hermes-128k`, `gemma4:latest`, `granite4.1-hermes`, `granite4.1:8b`. Afuera a propósito: Qwen 27B Uncensored, `qwen3.8-hermes`, `qwen3.8:27b`, `gemma4:26b` |
| **Gemelo sin censura** `gemma4-hermes-abliterated:latest` (`FROM huihui_ai/gemma-4-abliterated:latest` + mismo Modelfile que gemma4-hermes: `num_ctx 40960`, temp 0.3) | 8B Q4_K_M, **4.998 MiB de VRAM (igual que gemma4-hermes), 100 % GPU, 130 tok/s**, tool calls OK, español correcto. Solo uno de los dos gemma cabe residente junto al `voice-agent`; cambiar de uno a otro cuesta ~2,6-3 s |
| Respaldo `gemma4-hermes-original:latest` | Copia del actual, para volver con `ollama cp` si `gemma4-hermes` se apunta al abliterated |
| Notebook `~/.hermes/config.yaml`, provider `ollama-srpy186` | Tenía `default_model: …Uncensored`; ahora `gemma4-hermes:latest` y la lista solo con permitidos (respaldo `config.yaml.bak-20260906-allow`) |

**Regla:** el proxy (11435, el que sale por `llm.santarosa.lat`) es la única puerta con lista blanca. El 11434 sigue abierto en la LAN/Tailscale sin filtro — no apuntar clientes directo ahí.

**Decidido (b), opt-in — 2026-09-06.** El bot de ventas, el Hermes del servidor y el healthcheck siguen con `gemma4-hermes:latest` (original). Quien necesite sin censura pide `gemma4-hermes-abliterated:latest` por `https://llm.santarosa.lat/v1` con la misma clave; aparece en `/v1/models`. Medido por el túnel: pedido opt-in **3,4 s**, el bot pidiendo gemma justo después **3,2 s** (cambio de modelo incluido), vuelta **3,6 s** — muy por debajo del timeout de 30 s del bot. Por `/v1` Ollama ignora `keep_alive`: el abliterated queda residente 5 min tras el último uso, y gemma vuelve solo con el siguiente mensaje del bot o el refresco del healthcheck (`/api/chat` cada 5 min con 30 m). `gemma4-hermes-original` se borró: no hacía falta para la (b). Se descartó la (a) porque dejaba al bot que habla con clientes sin filtros de rechazo.

## Qué modelo local puede ser "más inteligente" — medido el 2026-09-06

Pregunta de Croman: un modelo mejor para el bot de ventas y los dashboards, con los recursos del servidor (RTX 5070 12 GB, 62 GB RAM, i9 285K). Se bajaron tres candidatos y se corrió la **misma batería** contra cada uno, en el servidor, con el razonamiento apagado como hace el proxy (`reasoning_effort=none`): arreglar un bash con el bug del `[ … ] && echo` (exit 1 en cron), una función Python con las 4 reglas precio↔modelo del scraper (7 casos), un SQL top-3 por segmento sobre una tabla con columna `mes` (hay que sumar el año), y **una conversación de bot de ventas con 3 herramientas** (precio/stock, tasación de usado, agendar).

| Modelo | Tamaño | Dónde corre | tok/s | bash | python | SQL | **bot** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `gemma4-hermes` 8B (actual) | 9,6 GB → 5,0 GB VRAM | 100 % GPU | 137 | OK (cambió stdout→log sin pedirlo) | 5/7 | mal | **0/2 herramientas** — promete "consultar" y no consulta |
| **`gemma4:12b`** | 7,6 GB → 8,9 GB VRAM a 40960 ctx | 97 % GPU / 3 % CPU | **60** (69 a 32768) | OK | **6/7** | mal | **2/2 herramientas, 2/2 datos**: "El Jetour X50 sale USD 21.990 y tenemos 3 unidades… por tu Kwid 2019 te podemos tomar USD 7.800…" |
| `granite4.1:30b` (MoE A3B) | 17 GB | 20/65 capas en GPU, 11,7 GB en RAM | 4,3 | mal | 2/7 | mal | 0/2 |
| `qwen3.6:35b-a3b` (MoE A3B) | 21 GB | 32 % GPU / 68 % RAM | **50** | OK | 2/7 (regex mal agrupada) | mal | 0/2 |

**Conclusiones:**
- **`gemma4:12b` es el único que se comporta como un bot inteligente**: llama a las dos herramientas correctas en el primer turno y redacta con los datos reales, breve, sin nombrar competencia. Entra en la placa junto al `voice-agent` (10.908 MiB usados de 12.227) y va a 60 tok/s.
- Los MoE demuestran que la RAM sirve (Qwen a 50 tok/s con el 68 % del modelo en RAM), pero **no son más listos** en estas tareas: peor python, sin herramientas. Granite además es lento (4 tok/s: Ollama solo le pasó 20 de 65 capas a la GPU).
- **Ningún modelo local en 12 GB acierta el SQL** con agregación por mes: todos rankean filas sueltas en vez de `SUM … GROUP BY`. Para consultas contra CADAM sigue el Advisor con Claude API. Los asistentes flotantes de los dashboards no dependen de esto porque los rankings van precalculados en JS (ver "Asistente flotante", 2026-08-14).
- **Razonamiento encendido no ayuda**: el 12B con `--think` tarda 4-7× más (bot 7-9 s por turno contra 1,2-1,5) y empeora en la batería (pierde los datos en la respuesta). Dejar el proxy como está.
- Dos nombres con el mismo modelo **comparten el runner** (probado con un alias: mismo `ollama ps`, misma VRAM). Eso permite que `gemma4-hermes:latest` (bot, Hermes, proxy) y `gemma4:latest` (dashboards por `ollama.santarosa.lat`) sean el mismo residente de 12B.
- Queda creado `gemma4-hermes-12b:latest` (`FROM gemma4:12b` + `num_ctx 40960`, temp 0.3) listo para apuntar. `granite4.1:30b` se borró; `qwen3.6:35b-a3b` quedó en disco (21 GB) por si sirve para otra cosa. Batería: `/tmp/bench.py` y `/tmp/grade.py` en el servidor (copias en el scratchpad de la sesión).

### Cambio hecho — 2026-09-06 23:26: el 12B es el modelo de todos

Decisión de Croman tras el benchmark. Se re-apuntaron los **nombres** al modelo probado (`gemma4-hermes-12b`, digest `5d7be4071851`, `FROM gemma4:12b` + `num_ctx 40960`, temp 0.3), sin tocar Vercel, Coolify ni ninguna config de cliente:

| Nombre | Quién lo usa | Antes | Ahora | Respaldo |
| --- | --- | --- | --- | --- |
| `gemma4-hermes:latest` | bot de ventas (Vercel, por `llm.santarosa.lat`), Hermes servidor y notebook, healthcheck | 8B | **12B** | `gemma4-hermes-8b:latest` |
| `gemma4:latest` | referencias viejas de los dashboards | 8B (biblioteca) | 12B | `gemma4-8b:latest` (o `ollama pull gemma4`) |
| `gemma4-hermes-128k:latest` | asistentes flotantes de los dashboards (`LLM_MODEL` en Vercel y en el espejo de Meta, por el proxy) | 8B a 131072 ctx | 12B a **40960** ctx (su prompt son ~1.900 tokens; el nombre quedó viejo) | `gemma4-hermes-128k-8b:latest` |

Los tres nombres comparten el digest → **un solo runner residente**: probado pidiendo por cada nombre, `ollama ps` muestra una sola entrada y la VRAM no se mueve (10.912 MiB con el voice-agent). Carga desde caché 6,7 s, 60 tok/s, 3 % en CPU. Verificado por el camino real: bot por el túnel 2,6 s, tool calls OK, healthcheck OK, alias del dashboard 0,79 s.

**Vuelta atrás** (un comando por nombre): `ollama cp gemma4-hermes-8b:latest gemma4-hermes:latest`, idem `gemma4-8b → gemma4`, `gemma4-hermes-128k-8b → gemma4-hermes-128k`.

**Efectos a saber:**
- `gemma4-hermes-abliterated` (8B, opt-in) sigue existiendo y **no cabe junto al 12B**: cuando alguien lo usa, el bot recarga el 12B en el siguiente mensaje (6,7 s, antes 2,6 s).
- El bot pasó de 137 a 60 tok/s; un mensaje entero sigue saliendo en 1-2 s. A cambio usa las herramientas.
- Los dashboards en producción (Vercel) tienen `LLM_PROVIDER/MODEL/BASE_URL/API_KEY/KEEP_ALIVE` definidos (valores cifrados); el espejo de Meta en Coolify tiene `LLM_MODEL=gemma4-hermes-128k:latest` y `LLM_BASE_URL=http://192.168.221.87:11435/v1` (el proxy, con lista blanca). En 7 días ningún pedido de dashboard llegó al proxy: el asistente flotante no se estaba usando.
- Quedan en disco `gemma4:12b` (base), `gemma4-hermes-12b` (el probado), `qwen3.6:35b-a3b` (21 GB, sin uso) y `gemma4:26b` (17 GB, no entra). Se pueden borrar los dos últimos.

### Corrección 2026-09-09: el cambio de contexto del 6/9 rompió Hermes

Al apuntar los tres nombres al 12B, `gemma4-hermes-128k:latest` pasó de **131072 a 40960** de contexto. Lo documenté como inofensivo mirando solo los dashboards (su prompt son ~1.900 tokens) — **error**: ese modelo existía precisamente para Hermes, que **exige un mínimo de 64.000 tokens** y se niega a arrancar por debajo:

> `Failed to initialize agent: Model gemma4-hermes:latest has a context window of 40,960 tokens, which is below the minimum 64,000 required by Hermes Agent.`

Durante 3 días el Hermes de la notebook y el del servidor no pudieron usar el modelo local.

**Arreglado:** `gemma4-hermes-128k:latest` ahora es el 12B con `num_ctx 65536`. Medido en la placa de 12 GB (con el `voice-agent` ocupando 2 GB):

| Contexto | Capas en GPU | Velocidad |
| --- | --- | --- |
| 40.960 (`gemma4-hermes`, bot y dashboards) | 49/49 | 60 tok/s |
| **65.536 (`gemma4-hermes-128k`, Hermes)** | **45/49** | **45 tok/s** |
| 131.072 (`gemma4-hermes-12b-128k`, disponible) | 38/49 | 27 tok/s |

Por eso 65.536 y no 131.072: supera el mínimo de Hermes y deja casi todo en GPU. Verificado con `hermes chat` en las dos máquinas (responden "ok"); el modelo de 40.960 reproduce el error exacto.

También corregidos: `~/.hermes/config.yaml` de la notebook (provider `ollama-srpy186`: `default_model` y `context_length: 65536` real, no declarado de más) y del servidor (`model.default`). Respaldos `.bak-20260909-ctx` en ambas.

**Regla:** cualquier modelo que vaya a usar Hermes necesita `num_ctx >= 64000` horneado en su Modelfile. Los endpoints `/v1` de Ollama ignoran `options.num_ctx`, así que no se puede arreglar desde el cliente.

## Sarpy CRM en Coolify — 2026-09-25

Migración completa (Vercel + Supabase nube → Coolify + Supabase self-hosted, servidor SRPY186), verificada el 25/9. Detalle técnico completo: `DEPLOY.md` en el repo (`~/Escritorio/CRM SRPY/botika`).

| Qué | Dónde |
|---|---|
| App | https://crm.santarosa.lat |
| API de Supabase (navegador y servidor) | https://crm-db.santarosa.lat |
| App en Coolify | `qtsfwjopef5qx15mo58i3ut0`, proyecto SRPY, production, build pack `dockerfile`, puerto 3000, healthcheck `/healthz` |
| Stack de Supabase | `/home/santarosa/stack/supabase-crm/` — contenedores `crm-supabase-*`, red `supabase-crm_default` |
| Puertos (solo `127.0.0.1`) | Kong 8107 · Kong HTTPS 8547 · Studio 8108 · Postgres 5438 · pooler 6548 |
| Studio | solo por `ssh -L 8108:127.0.0.1:8108 srpy-servidor` → http://localhost:8108 |
| Túnel | reglas `crm` y `crm-db` en `/home/santarosa/cloudflared-compras/config.yml` |
| Deploy automático | `~/crm-autodeploy/check.sh` cada 3 min (sondea `main`) |
| Crons | tareas programadas de Coolify: `lead-health` 06:00 PY, `meta-leads` cada 5 min |
| Backups | `~/.local/bin/backup-supabase.sh` 03:15, `~/backups/supabase/crm_db_*.dump`, 14 días |
| Secretos | `.env` del stack (chmod 600), tokens en `/home/santarosa/stack/`. Punteros en `/home/santarosa/stack/CREDENCIALES.md` |

Vercel (`sarpy-crm`) y el Supabase de la nube (`cisayjvdxngjfvvgbgro`) ya no se usan; quedan vivos solo hasta la baja (Tarea 14 del plan de migración).

## SOUEAST Paraguay (web) en Coolify — 2026-09-29

Producción propia del sitio que hizo el proveedor (26 páginas: las 25 del proveedor + el S08 que armamos nosotros; mismos videos/imágenes/animaciones). Estático (nginx) + API de leads. Detalle técnico: `DEPLOY.md` y `docs/DNS-SOLICITUD.md` en el repo (`~/Escritorio/ASSET WEB SRPY/SOUEAST WEB`, GitHub `croman-coder/soueastweb`, privado).

| Qué | Dónde |
|---|---|
| Muestra | https://soueast.santarosa.lat/es/ (noindex) |
| Producción | **`soueast.com.py` en producción desde el 30/09/2026**: NIC.py delegó a `clayton.ns.cloudflare.com` / `rihana.ns.cloudflare.com`, certificado Universal SSL (vence 29/12/2026, lo renueva Cloudflare), `python3 docs/seo/verify_live.py https://soueast.com.py` con 183 controles y 0 problemas, API del formulario por el dominio real. **Cloudflare y Search Console hechos el 30/09/2026 (con Claude in Chrome):** regla de compresión (sin compresión para video/PDF/imágenes/woff2), purga del caché de la zona, TXT `google-site-verification` en la zona (no borrarlo), propiedad de dominio verificada y `sitemap.xml` leído por Google (Correcto, 19 páginas). http→https y correo de contacto resueltos en el servidor (nginx con `CF-Visitor`, `<!--email_off-->`), sin tocar los ajustes de seguridad del panel. **Descubrimiento:** el video no daba `Range`/206 (no anda en Safari/iPhone) por el middleware `gzip` de Traefik en Coolify, no por Cloudflare: se apagó con `PATCH /api/v1/applications/<uuid> {"is_gzip_enabled": false}` + redeploy + purga. **Probablemente afecta a las otras apps de Coolify** (Zeekr muestra el mismo síntoma). Detalle en `DEPLOY.md` → "Dominio real" |
| App web en Coolify | `4cjljajaotiqvuxvy8rpb404` (`soueast-web`), dockerfile, puerto 80 |
| App API en Coolify | `94khjrukfopdxaejdubw5haq` (`soueast-leads-api`), `/api/Dockerfile`, puerto 8000, bajo `/api` de los mismos hosts |
| Modelo S08 PHEV | agregado el 29/09/2026 (el proveedor no lo tiene): `/es/s08/` con visor 360° en 4 colores, video de 45 s y ficha `/es/pdf/S08.pdf`; en el menú superior, el desplegable (ahora 4 modelos) y el carrusel del home. También el **Taller Juank** (Encarnación) en `/es/dealer/`. Cómo está armado y de dónde salió cada archivo: sección "SOUEAST S08 PHEV" de `DEPLOY.md` |
| Formulario de contacto | `POST /api/lead` → Prospecto en Bitrix, origen `WEB_SR_SOUEAST`, Marca `293`, pool **fijo** de 4 asesores (`ADVISOR_IDS=87,109,16427,26415`: Zenón González, Matías Florentín, Alex Taranto, Rocío Cozzoli; cola justa; asesor nuevo = agregar su ID y redeploy). Desde el alias los leads van al usuario 19 (Croman), marcados de prueba |
| Túnel | reglas `soueast.santarosa.lat`, `soueast.com.py`, `www.soueast.com.py` en `cloudflared-compras/config.yml`; hay que reiniciar los DOS conectores, de a uno |
| Deploy | manual (sin autodeploy): `POST /api/v1/deploy?uuid=<app>` con el token de `/home/santarosa/stack/.coolify-token-tasacion` |

**SEO (auditoría del 29/09/2026, publicado en la muestra, commit `0f2b7ae`):** el SEO on-page sale de `docs/seo/seo_data.py` (títulos, descripciones, H1, JSON-LD) y se aplica con `python3 docs/seo/apply.py` + `version_assets.py` + `make_sitemap.py` (detalle en `docs/seo/README.md` y en la sección "SEO" de `DEPLOY.md` del repo). Medido: recorrer las 27 páginas en el celular 211 → 98 MB (contacto 9,8 → 0,9 MB, S09 26,7 → 14,3 MB); Lighthouse celular S08 47 → 73, S09 63 → 71, contacto 63 → 78; CLS del home 0,33-0,52 → ≤ 0,014. Diseño verificado idéntico (layout de 27 páginas × 2 tamaños, capturas píxel a píxel, animación de carga a 0,02 px). Solo el dominio real se indexa (nginx manda `noindex` a la muestra; y a medios, `region/`, `cn/`, cookies y gracias también en el dominio real). **Cloudflare de `soueast.com.py` (ya configurado el 30/09/2026):** Always Use HTTPS + Automatic HTTPS Rewrites; Compression Rule que NO comprima video/imagen/pdf (si no, el video no da 206 y Safari no lo reproduce); apagar Email Obfuscation; revisar AI Crawl Control/Managed robots.txt; Search Console (TXT en la zona) + sitemap. La muestra (zona `santarosa.lat`) inyecta el beacon de Web Analytics, ofusca el correo de contacto y sirve copias viejas de 33 imágenes/PDF recomprimidos in situ hasta que Cloudflare las venza o se purguen por URL. Pendiente del cliente: razón social/RUC/dirección de Santa Rosa, teléfono oficial (sitio `+595 974 931 930` vs fichas `595975-895 632`), Instagram (`soueastparaguay` vs `@soueast.py`), garantía/precios, GA4.

Gotchas de esta puesta en marcha:
- **El webhook de Bitrix se comparte** entre apps y limita el ritmo (`QUERY_LIMIT_EXCEEDED`, 503): cualquier script nuevo debe espaciar las llamadas (~1 s) y reintentar.
- **Cloudflare no se puede purgar desde el servidor** y cachea `css/js` por lo que diga el origen: por eso el sitio sirve css/js 1 h y `public.js?v=2`. Si se cambia un estático ya servido, cambiarle el nombre o versionar la URL.
- **`header.js` (el menú de todas las páginas) se carga como `header.js?v=2`**: si se vuelve a tocar, subir el número en todas las páginas (`sed`), porque Cloudflare lo tiene 1 h en caché y no se puede purgar desde el servidor. Lo mismo `index.css?v=2` y `car_s08.css?v=5`.
- Las variables de Coolify de esta API van como *literal* (igual que la de Zeekr); comprobar con `/api/health` (`configured:true`).
- El robot de Bitrix reescribe el título de los leads web (`fecha - nombre - Marca - origen`).
