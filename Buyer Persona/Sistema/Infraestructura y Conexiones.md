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
| GitHub CLI (`gh`) | ✅ `croman-coder` (activa) + `ymk5py-commits` + `remax360paraguay`, scope `repo` = push/PR. **Git por HTTPS no usa la cuenta activa** (desde el 16/10/2026): `~/.local/bin/git-credential-github-por-dueno` elige el token según el dueño del repo (`ymk5py-commits/*` y `remax360paraguay/*` con su cuenta, todo lo demás con `croman-coder`), así un `gh auth switch` ya no rompe los push de la otra mitad. Config en `~/.gitconfig` (`useHttpPath = true`), backup en `~/.gitconfig.antes-por-dueno-20261016`. Los comandos `gh pr`/`gh api` siguen usando la activa: para un repo de ymk5py, `GH_TOKEN=$(gh auth token --user ymk5py-commits) gh pr ...` |
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
| Formulario de contacto | `POST /api/lead` → Prospecto en Bitrix, origen `WEB_SR_SOUEAST`, Marca `293`, pool **fijo** de 4 asesores (`ADVISOR_IDS=87,109,16427,26415`: Zenón González, Matías Florentín, Alex Taranto, Rocío Cozzoli; cola justa; asesor nuevo = agregar su ID y redeploy). **Sucursal Ciudad del Este (02/10/2026, pedido de Bruno Capossela):** el formulario pide "Sucursal más cercana"; `cde` va al equipo de CDE (`CDE_ADVISOR_IDS=107,20439,35453`: Guido Riquelme, Miguel Á. Acosta y Federico López, departamento Bitrix 135 "SOUEAST & JETOUR CDE"; reserva `CDE_FALLBACK_ASSIGNEE_ID=21707` Walter Bavera, Jefe de Ventas CDE), con Ciudad = Ciudad del Este en el Prospecto; los botones de WhatsApp de los modelos preguntan Asunción (Contact Center) o CDE (`+595 991 702 176`), y Contacto lista las 4 sucursales con pin de Google Maps. Desde el alias los leads van al usuario 19 (Croman), marcados de prueba |
| Túnel | reglas `soueast.santarosa.lat`, `soueast.com.py`, `www.soueast.com.py` en `cloudflared-compras/config.yml`; hay que reiniciar los DOS conectores, de a uno |
| Deploy | manual (sin autodeploy): `POST /api/v1/deploy?uuid=<app>` con el token de `/home/santarosa/stack/.coolify-token-tasacion` |

**SEO (auditoría del 29/09/2026, publicado en la muestra, commit `0f2b7ae`):** el SEO on-page sale de `docs/seo/seo_data.py` (títulos, descripciones, H1, JSON-LD) y se aplica con `python3 docs/seo/apply.py` + `version_assets.py` + `make_sitemap.py` (detalle en `docs/seo/README.md` y en la sección "SEO" de `DEPLOY.md` del repo). Medido: recorrer las 27 páginas en el celular 211 → 98 MB (contacto 9,8 → 0,9 MB, S09 26,7 → 14,3 MB); Lighthouse celular S08 47 → 73, S09 63 → 71, contacto 63 → 78; CLS del home 0,33-0,52 → ≤ 0,014. Diseño verificado idéntico (layout de 27 páginas × 2 tamaños, capturas píxel a píxel, animación de carga a 0,02 px). Solo el dominio real se indexa (nginx manda `noindex` a la muestra; y a medios, `region/`, `cn/`, cookies y gracias también en el dominio real). **Cloudflare de `soueast.com.py` (ya configurado el 30/09/2026):** Always Use HTTPS + Automatic HTTPS Rewrites; Compression Rule que NO comprima video/imagen/pdf (si no, el video no da 206 y Safari no lo reproduce); apagar Email Obfuscation; revisar AI Crawl Control/Managed robots.txt; Search Console (TXT en la zona) + sitemap. La muestra (zona `santarosa.lat`) inyecta el beacon de Web Analytics, ofusca el correo de contacto y sirve copias viejas de 33 imágenes/PDF recomprimidos in situ hasta que Cloudflare las venza o se purguen por URL. Pendiente del cliente: razón social/RUC/dirección de Santa Rosa, teléfono oficial (sitio `+595 974 931 930` vs fichas `595975-895 632`), Instagram (`soueastparaguay` vs `@soueast.py`), garantía/precios, Pixel de Meta (GA4 ya está desde el 07/10/2026).

**Analytics y Search Console de `soueast.com.py` (07/10/2026):** propiedad GA4 **SOUEAST PY** (`557884533`, cuenta `croman_coder`, una por marca como las demás), flujo `https://soueast.com.py` (`16061275479`), ID de medición **`G-1VHQW6N27Q`**, vinculada a la propiedad de dominio de Search Console (que ya estaba verificada y con sitemap desde el 30/09; últimos 28 días: 270 clics y 4.477 impresiones, posición media 5,7, la mayoría por "soueast", "soueast paraguay" y "soueast s06"). Código en `es/js/gtag.js` (y copia `js/gtag.js`): solo mide en `soueast.com.py`; con el aviso de cookies del proveedor mide normal salvo que el visitante lo haya cerrado con la × (entonces arranca sin cookies; igual que JAC). Eventos con los nombres estándar de las otras webs: `generate_lead { form, sucursal }` (formulario aceptado por la API, sale por beacon antes de ir a `/gracias.html`) y `click_whatsapp { location, sucursal }` (el botón de la ficha solo abre el selector; cuenta la sucursal elegida). Dimensiones personalizadas `form`, `location` y `sucursal` y conservación de eventos en 14 meses ya creadas. Verificado en producción el 07/10 con Chrome real: Tiempo real mostró `first_visit`, `page_view` y `session_start` (**Chrome headless de Playwright no cuenta**: GA4 lo filtra como bot, no sirve para esa prueba). Falta: marcar `generate_lead` y `click_whatsapp` como eventos clave cuando lleguen, y sumar SOUEAST a `SITIOS_WEB` del Dashboard de Meta (`api/_web-datos.js`; hoy su pestaña Web dice "Sin sitio web medido"). Detalle: sección "Google Analytics 4 y Search Console" de `DEPLOY.md`.

Gotchas de esta puesta en marcha:
- **El webhook de Bitrix se comparte** entre apps y limita el ritmo (`QUERY_LIMIT_EXCEEDED`, 503): cualquier script nuevo debe espaciar las llamadas (~1 s) y reintentar.
- **Cloudflare no se puede purgar desde el servidor** y cachea `css/js` por lo que diga el origen: por eso el sitio sirve css/js 1 h y `public.js?v=2`. Si se cambia un estático ya servido, cambiarle el nombre o versionar la URL.
- **`header.js` (el menú de todas las páginas) se carga como `header.js?v=2`**: si se vuelve a tocar, subir el número en todas las páginas (`sed`), porque Cloudflare lo tiene 1 h en caché y no se puede purgar desde el servidor. Lo mismo `index.css?v=2` y `car_s08.css?v=5`.
- Las variables de Coolify de esta API van como *literal* (igual que la de Zeekr); comprobar con `/api/health` (`configured:true`).
- **Zeekr** (`zeekr-leads-api`, uuid `wpcarpu6lxtqjhaqxeebrifk`) tiene el mismo filtro de sucursal desde el 02/10/2026 (en producción, release CMS `20261002-204334`): `cde` va a `CDE_ADVISOR_IDS=16001` (solo Mathias Acosta, depto. 155 "NUEVAS ENERGÍAS", desde el 06/10/2026; del 02 al 03/10 fue 21707, el Jefe de Ventas Multimarcas CDE, y del 03 al 05/10 `16001,19827`; Zeekr no tiene equipo propio en CDE; reserva `CDE_FALLBACK_ASSIGNEE_ID=21707`; la variable existe en Coolify en producción y en vista previa), con Ciudad = Ciudad del Este; los WhatsApp del sitio preguntan Asunción (`+595 971 370 006`) o CDE (`+595 972 350 200`, el del jefe de ventas multimarca desde el 06/10/2026; antes `+595 991 702 176`). La API de Coolify del servidor escucha en `http://localhost:8090` (no en el 8000).
- El robot de Bitrix reescribe el título de los leads web (`fecha - nombre - Marca - origen`).

## Reparto de leads web por marca y sucursal

Pedido de Gerencia Comercial (mail de Bruno Capossela, 01/10/2026 "Filtros WEB Sucursal CDE - Todas las marcas"): los contactos de Ciudad del Este (CDE) van directo al equipo comercial de CDE; y (Croman, 03/10/2026) los leads de la web de Santa Rosa tienen que repartirse entre los asesores de la marca elegida, no quedar en su usuario 19 (el webhook sin asignado dejaba todo con el dueño del webhook).

| Marca | Asunción y resto del país (ids Bitrix) | Ciudad del Este (ids Bitrix) |
|---|---|---|
| Renault | 653, 23365, 75, 16373, 43585, 46889 | 19827 Pedro Ocampos (depto. 153; exclusivo Renault desde el 06/10/2026, antes 16001 y 19827) |
| Jetour | 89, 91, 93, 95, 97, 99, 101, 103, 105, 42417, 44491 | 107, 20439, 35453 (depto. 135) |
| GWM | 43, 79, 113, 117, 119, 123, 125, 127, 44489, 44493 | 121, 42415, 42413 (depto. 137) |
| Soueast | 87, 109, 16427, 26415 | 107, 20439, 35453 (depto. 135) |
| JAC | 131, 133, 135, 759 | 48313 Juan Martínez (depto. 141; exclusivo JAC desde el 06/10/2026, antes 16001 y 19827) |
| Mitsubishi | 5097, 18723, 34561 | 19829 Alberto Amarilla (depto. 139) |
| Zeekr, Leapmotor, JMEV, Xpeng | 139, 31765, 2171 | 16001 Mathias Acosta (depto. 155 "NUEVAS ENERGÍAS"; desde el 06/10/2026, antes 16001 y 19827) |
| Renew | 141, 145, 723 (desde el 03/10/2026 también en renew.com.py, antes todo iba al 723) | sin equipo en CDE: mismo equipo, con la ciudad cargada |

- Fuente: departamentos de cada marca (15 Renault, 17 Jetour, 19 GWM, 27 Soueast, 29 Zeekr, 31 JAC, 33 Leapmotor, 35 Renew, 37 JMEV, 39 Mitsubishi, 143 Xpeng; CDE: 133 Multimarcas, 135 Soueast+Jetour, 137 GWM, 139 Mitsubishi, 141 JAC, 153 Renault, 155 Nuevas Energías = Leap/Zeekr/Xpeng/JMEV; releídos el 06/10/2026) y las colas "<MARCA> Meta Ads - Cuenta Madre" (quienes reciben leads de verdad: algunos no tienen cargo ASESOR, como Elias Ortellado y Federico López). Leído del Bitrix real el 03/10/2026.
- Respaldo si no hay nadie: el ejecutivo de la marca (Gastón Lareo 51 Renault, Jennifer Omaña 41 Jetour, Emilio Núñez 45 GWM, Luis Baez 73 Soueast/Zeekr/Leapmotor/JMEV/Xpeng, Nahuel Cantele 147 JAC/Mitsubishi, Eduardo Vigorito 63 Renew) o, en CDE, Walter Bavera 21707 (Jefe de Ventas Multimarcas CDE, `wbavera@santarosa.com.py`). WhatsApp/teléfono de CDE **por marca (mail de Bruno del 06/10/2026)**: Jetour y Soueast `+595 974 772 246` (línea propia de su equipo en CDE); Mitsubishi, Zeekr, JMEV, Leapmotor, JAC y Renault `+595 972 350 200` (jefe de ventas de la sucursal multimarca); **GWM sin definir** (sigue `+595 991 702 176`, el de antes; se le consulta a Bruno). Hasta el 05/10/2026 todas usaban `+595 991 702 176` (supuesto, no confirmado).
- En el prospecto: `ASSIGNED_BY_ID` explícito, `ADDRESS_CITY` = Ciudad del Este (CDE) y "Sucursal elegida" en los comentarios. Cola justa por origen `WEB_SR_<MARCA>` (compartida entre santarosa.com.py y el sitio propio de la marca).
- Dónde está hecho: **todo en producción desde el 03/10/2026** (Renew no aplica el filtro de CDE: sin equipo allá; pero **renew.com.py reparte desde el 03/10/2026 entre 141, 145 y 723** por `netlify/functions/lead.mjs` + `lib/lead-routing.mjs`, con la variable secreta `BITRIX_WEBHOOK_URL` en Netlify y `?check=1` para comprobar; el formulario de la ficha y el de `/contacto` crean el prospecto y avisan al visitante (y a GA4, evento `lead_error`) si no se pudo registrar; QA: `scripts/qa-leads.mjs`). soueast.com.py y zeekrlife.com.py (APIs de Coolify; Zeekr con CDE = 16001 desde el 06/10, antes 16001 y 19827); santarosa.com.py (`netlify/functions/lead.ts`, `lib/leadRouting.ts`); Leapmotor (Vercel, `api/lead.js` + `lib/leadRouting.js`); Mitsubishi (pools fijos en el navegador, `src/services/bitrixService.ts`); JAC (`content/asesores.ts`, panel `/admin`); **Jetour y JMEV**: su formulario de contacto solo abría WhatsApp y ahora crea el prospecto en Bitrix por `POST /api/lead` (`src/app/api/lead/route.ts` + `src/lib/leads/`, 18 y 17 tests; variable secreta `BITRIX_WEBHOOK_URL` en Netlify, contexto production; `GET /api/lead?check=1` debe decir `"bitrix":"ok"`). Todos los WhatsApp de ventas abren el selector de sucursal (CDE `+595 991 702 176`, **sin confirmar por escrito**). Ver la memoria de cada proyecto.
- **Actualización 06/10/2026 (2.º mail de Bruno, todo en producción el mismo día):** (1) Jetour y Soueast: contacto de CDE `+595 974 772 246` en la web y en la ficha de sucursales de santarosa.com.py ("ya contamos con un equipo y línea asignada a esa sucursal"; sus vendedores no cambian). (2) Sucursal Multimarcas: el número del jefe de ventas `+595 972 350 200` es el contacto de CDE de MMC, Zeekr, JMEV, Leap, JAC y Renault (webs propias de las marcas y santarosa.com.py). (3) Regla de asignación: Pedro Ocampos exclusivo Renault · Alberto Amarilla exclusivo MMC · Juan Martínez exclusivo JAC · Mathias Acosta Leap/Zeekr/JMEV/LeapMotor/Xpeng; en las webs, los pools de CDE quedaron así (la distribución real de los leads de Meta ya era esta desde ~28/09). Sitios tocados: SOUEAST, Jetour, Santa Rosa, JAC, JMEV, Mitsubishi, Leapmotor, Zeekr (Renew no tiene equipo en CDE; la web oficial de Renault y XPeng quedan afuera). También: arreglos de desborde en celular de JAC, JMEV, Mitsubishi y Leapmotor, y SOUEAST sin los talleres GOLDEN ARROW y TALLER PAMOSA. **Ojo:** el sitio de JAC y el de Leapmotor no revisan si el asesor está activo en Bitrix (con pools de uno, si Juan o Mathias se dan de baja hay que sacarlos de la lista y redesplegar).
- **Pendiente (Croman):** el webhook de la web de Santa Rosa (`/rest/19/…`) estuvo publicado en el JS del sitio y sigue siendo el que usa la función; no tiene permiso `user`. Crear uno nuevo en Bitrix (permisos crm y user), cargarlo en la variable `BITRIX_WEBHOOK_URL` de Netlify (contexto production), comprobar `https://santarosa.com.py/api/lead?check=1` (debe decir `"bitrix":"ok"`), mandar un lead de prueba y recién ahí borrar el viejo.
- **Pendiente:** mirar en Bitrix los primeros leads reales de santarosa.com.py, Jetour y JMEV (que ninguna regla de la cola pise el `ASSIGNED_BY_ID`; los orígenes `WEB_SR_JETOUR` y `WEB_SR_GWM` parecían tener distribución propia). Los pines/ubicaciones por marca los está actualizando Evelyn con los datos que le pasan las marcas; lo corregido aparte: 3 pines de CDE que abrían en Asunción (santarosa.com.py, SOUEAST y JAC) y el de JAC a 7 km del local.
- **Renew, hallazgo (03/10/2026):** en Bitrix no hay ningún lead de la web de Renew desde el 02/07/2026 (antes 5 en marzo, 23 en abril, 13 en mayo); lo más probable es que el webhook viejo, el que estuvo en el JS público hasta el 24/09, esté inválido. Con la variable nueva queda funcionando. **Pendiente (Croman):** en Bitrix (Recursos para desarrolladores → Otros → Webhook entrante) revisar si ese webhook viejo todavía existe y borrarlo. El webhook compartido de Coolify hoy lo usan también Jetour, JMEV y Renew (variable `BITRIX_WEBHOOK_URL` en cada sitio de Netlify), además de las APIs de Zeekr y SOUEAST: al rotarlo hay que actualizar todos.

## Search Console: avisos de indexación (07/10/2026)

Los correos "Nuevos motivos que impiden la indexación" de las 13 propiedades de marketing@santarosa.com.py **no son todos errores**: redirecciones y 404 de URLs del sitio anterior (WordPress, Joomla, ASP, PHP), variantes `www`/`http`/`?fbclid=`, feeds y archivos `_next/static` viejos son normales. Los errores reales se corrigieron el mismo día (commits y causas en la memoria `indexacion-search-console-07-10-2026`):

| Sitio | Problema real | Estado |
|---|---|---|
| Renew | sitemap y canónicas sin barra final que redirigen, id de la ficha con mayúsculas (Netlify lo pasa a minúscula y no hallaba el archivo), ficha "no encontrada" mientras cargaba Firestore (soft 404) | corregido (barra final, id en minúscula, ficha embebida en el HTML, 404 real) |
| XPeng | sitemap con 4 URLs `#fragmento`; Google había elegido como canónica `xpeng-paraguay.vercel.app` (borrada): 0 páginas indexadas | sitemap limpio; falta pedir indexación de la portada |
| Mitsubishi, Leapmotor | cualquier dirección devolvía la portada con 200 (comodín a `index.html`): URLs viejas como "alternativa con canónica" | rutas reales con 200, páginas viejas con 301, resto 404 |
| Renew Subastas | 47 "duplicada sin canónica": `/es/login?from=<subasta>` y páginas legales | canonical propio en login y legales |
| Jetour, Santa Rosa, Zeekr | URLs viejas que daban 404 con equivalente | redirecciones 301/308 |

Regla para sitios SPA con `_redirects`/`vercel.json`: **listar las rutas reales y dejar que lo demás dé 404**; al agregar una página hay que sumarla ahí y al sitemap. En la consola (07/10/2026, con visto bueno de Croman): "Validar corrección" iniciada en los motivos corregidos, indexación solicitada para `xpengcars.com.py`, sitemaps de Renew y XPeng reenviados y sitemaps viejos con error quitados (Mitsubishi, JAC, jacmotors). Los resultados tardan días o semanas en reflejarse: mirar el estado de cada validación.

## Controlador de TV (pantallas de sucursales) en Coolify — 2026-10-12

Panel para elegir qué pasa cada TV de las sucursales, con horario de encendido, y reproductor para Raspberry Pi. Alternativa propia a una cotización de USD 800/mes. Repo `croman-coder/controlador-de-tv` (privado), carpeta `~/Escritorio/CONTROLADOR DE TV/`. Detalle completo en su `README.md`.

| Qué | Dónde |
|---|---|
| URL | https://pantallas.santarosa.lat (`/panel/`, `/player/`) |
| App en Coolify | `controlador-de-tv`, uuid `5fsamj4xltqcsjtejbop8bqs`, Dockerfile, puerto 3000, volumen en `/data` (SQLite + videos) |
| Acceso al repo | deploy key de solo lectura `controlador_tv_deploy` (Coolify) / `coolify-controlador-de-tv` (GitHub) |
| Contraseña del panel | `/home/santarosa/stack/CREDENCIALES.md` |
| Túnel | regla `pantallas.santarosa.lat` → `http://coolify-proxy:80` en `cloudflared-compras/config.yml` (backup `config.yml.bak-antes-pantallas-20261012-142027`); los dos conectores reiniciados de a uno y las apps de producción verificadas después |
| DNS | CNAME `pantallas` al túnel `505fc6ac-…`, creado con `cloudflared tunnel route dns` desde la notebook |
| Deploy | **automático desde el 12/10/2026**: `~/pantallas-autodeploy/check.sh` cada 3 min (sondea `main` con la llave `~/.ssh/pantallas_deploy`, deploy key de solo lectura `autodeploy-srpy186` en GitHub). Probado: push 15:04 → detectado 15:06 → desplegado antes de las 15:07. Inmediato: `./scripts/desplegar-coolify.sh` (token `.coolify-token-tasacion`) |
| Respaldo | **diario 3:35** (12/10/2026): `~/.local/bin/backup-pantallas.sh` → `~/backups/pantallas/` (base con `VACUUM INTO` + espejo de `media/`, 14 días, verifica integridad, avisa por ntfy si falla). Mismo patrón que `backup-directus.sh`. Restauración probada; pasos en el encabezado del script |

**Pendiente de todo el servidor:** el respaldo externo cifrado (`respaldo-externo.sh`, restic a un bucket S3) **no está activo**: no hay línea en el cron ni `~/.config/restic/env`. Hoy todos los respaldos (Supabase, Directus, Ads, otras bases, Pantallas) viven en el mismo disco que los datos. Al activarlo, `~/backups` entra completo (incluida `pantallas`).

Gotchas que sirven para otras apps:
- **SQLite en modo WAL**: los datos recientes viven en el archivo `-wal` y el `.db` puede pesar 4 KB; copiar solo el `.db` da una base **sin tablas**. Respaldar siempre con `VACUUM INTO` (o `.backup`) dentro del contenedor. Al restaurar, borrar el `-wal` y `-shm` viejos.
- **Healthcheck de Coolify con imágenes `node:*-slim`**: el de Coolify usa `curl`/`wget`, que no vienen en la imagen, y el deploy falla por "unhealthy". O se apaga el de Coolify y se usa un `HEALTHCHECK` del Dockerfile escrito en Node (lo que se hizo acá), o se instala curl en la imagen.
- **IP del cliente detrás del túnel**: Traefik descarta el `X-Forwarded-For` que manda cloudflared, así que en cualquier app de Coolify `req.ip` (o equivalente) es la IP interna del túnel, aunque se ajuste `trust proxy`. La IP real llega en `CF-Connecting-IP`; Cloudflare rechaza con 403 si un cliente intenta mandarla. Cualquier límite de intentos por IP en otras apps de Coolify tiene este mismo problema.
- La API de Coolify (4.3.23) permite crear la app con `POST /applications/private-deploy-key`, el volumen con `POST /applications/{uuid}/storages` (`type: persistent`) y las variables con `POST /applications/{uuid}/envs`; las variables se duplican solas como copias para las vistas previas.

## Gestión de Compras en Coolify — 2026-10-13

Rediseño + app instalable + **licitaciones con sobre cerrado** en producción desde el 13/10/2026 (`master` = `a6d6744`, PRs #3 y #2). Detalle de lo hecho: [[gestion-compras]]. Runbook: `docs/deploy-coolify-cloudflare.md` y `docs/onboarding-backend.md` §7 en el repo (`~/Escritorio/GESTION COMPRAS`, GitHub `croman-coder/gestion-compras`, privado).

| Qué | Dónde |
|---|---|
| URL | https://compras.santarosa.lat · página pública del proveedor `/oferta/<token>` (sin sesión, `noindex`, `no-referrer`) |
| App en Coolify | `c3alcmmxxaciv6w6xk67m9m3`, nixpacks, puerto 3000, rama `master` |
| Base | Postgres 17 `srpy-postgres` (stack `srpy-infra`, no es de Coolify), base `compras`, usuario `srpy`, host 5433; la app entra por `192.168.221.87:5433` |
| Deploy | **manual**: `queue_application_deployment()` por `php artisan tinker` dentro del container `coolify` (los tokens `~/.coolify-api-token` y `~/.coolify-token` dan 401). Antes: comprobar `git_branch = master` y las labels que va a generar |
| Backups | **diario 3:50**: `~/.local/bin/respaldar-otras-bases.sh` → `~/backups/otras-bases/srpy-postgres__compras_<fecha>.dump`. Además, a mano antes de tocar el esquema: `~/backup-compras/` (el último, `compras-pre-licitaciones-2026-10-13-1533.sql`) |
| Rollback | imágenes viejas en el server (`docker images \| grep c3alcmmxxaciv`; antes del 13/10 corría `f768866`) |

Gotchas:
- **No usar `drizzle-kit push` contra producción**: prod tiene las restricciones con nombres de Postgres (`_key`, `_fkey`) y el código con nombres de Drizzle; mismas columnas, pero el push las borraría y recrearía. Comparar esquema (columnas, índices, restricciones y enums contra la base de test) y aplicar sólo lo nuevo, en una transacción.
- `custom_labels` de la app está en base64 y hoy coincide con las labels generadas y las del container. El 11/08 unas labels viejas ahí tiraron el sitio (404): revisarlas antes de cada redeploy.
- La ruta `/oferta/` no tiene límite de intentos; si se agrega, la IP real llega en `CF-Connecting-IP` (gotcha de la sección anterior).


## Cerebro Santa Rosa: cómo llega lo del vault (agregado el 16-oct-2026)

> Pedido de Croman: **todo lo que se actualiza en el vault tiene que figurar en Cerebro además de Obsidian.**

- **Cerebro** (`cerebro.santarosa.lat`) lee el vault **del servidor** (montado en `/vault`) y arma su índice **una sola vez**: lo que se agrega después no aparece hasta que se rearma.
- **Antes** solo se rearmaba a las 06:00, con el pipeline diario. Lo agregado durante el día esperaba hasta el día siguiente.
- **Ahora** `~/.hermes/scripts/refrescar-cerebro.sh` (servidor) rearma el índice **sin reiniciar el contenedor**, y lo llaman:
  - `publicar-vault.sh` del servidor, cada vez que el vault cambia (lo que trajo la notebook o lo que publica el servidor);
  - `sincronizar-vault.sh` de la notebook, que apenas publica le avisa al servidor por SSH: lo de la notebook figura en Cerebro en segundos y no a la hora siguiente.
- **Qué ve Cerebro** (`~/cerebro-santarosa/brain.config.json`): **todo el vault, salvo `Seguridad`**. Siete fuentes: Buyer Personas, Pauta y competencia (Campañas + Competencia), Sistema y memoria, Fichas técnicas (Marcas), Tableros e investigación (Asesores, Informes Semanales, Investigación y CRM), **Cuentas Meta** (1.345 notas de anuncios) y **Resto del vault** (Proyectos, Operativa, las notas sueltas de la raíz y **cualquier carpeta nueva que se cree**: no hay que tocar la configuración). El 16-oct-2026 pasó de 682 a **2.151 notas**, con 4.596 enlaces.
- **`Seguridad` queda afuera a propósito** (hallazgos abiertos, inventario del servidor, puertos): es lo más delicado del vault y tampoco va a la copia de GitHub. Para sumarla solo a `super_admin` hay que cambiar el portero (`alcance.mjs`) y reconstruir su imagen; para sumarla a todos los managers alcanza con quitarla de `exclude` en «Resto del vault».
- **Quién ve qué:** `manager` y `super_admin` ven todo; un `brand` solo lo que el portero le permite (su carpeta en Buyer Personas, las Campañas que nombran su marca y dos notas de Sistema). Una carpeta nueva queda cerrada para las marcas por defecto.
- **Si algo no aparece:** `ssh srpy-servidor bash ~/.hermes/scripts/refrescar-cerebro.sh` (dice cuántas notas tiene el índice).
- Respaldos de lo que se cambió: `brain.config.json.bak-20261016`, `publicar-vault.sh.bak-20261016` y `sincronizar-vault.sh.bak-20261016`.
