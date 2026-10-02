---
tipo: avances
tema: inteligencia de mercado, competencia y buyer persona
actualizado: 2026-09-04
tags: [avances, competencia, mercado, buyer-persona, hermes]
---

# 📈 Inteligencia de Mercado — Avances

Registro de qué se mejoró en la lógica de competencia y buyer persona, qué produce hoy cada pieza y qué queda pendiente. Lo mantiene Claude Code a pedido de Croman; los cron jobs de Hermes **no se tocaron**, solo los scripts que ejecutan.

Relacionado: [[📊 Mercado por Modelo 2026]] · [[💰 Precios por Modelo]] · [[⚔️ Bitácora de Competencia]] · [[📊 Mercado Automotor PY 2026]] · [[Infraestructura y Conexiones]]

## 2026-09-04 — Diagnóstico y tres mejoras

### Qué había

| Pieza | Estado real encontrado |
| --- | --- |
| Monitor de competencia en el **servidor** | Corría una copia del 6/8 con los dos bugs ya arreglados en la notebook el 18/8. Resultado: 6 escaneos seguidos **byte a byte idénticos** (3.394 bytes cada uno) y ningún evento en la Bitácora — el servidor no tenía ni la carpeta `Competencia/`. |
| Repo del servidor | 8 commits atrás de la notebook y, tras la corrida del pipeline de hoy, **438 notas nuevas sin commitear** (57 personas por modelo con sus 4 notas de marketing). El servidor veía el vault del 6 de agosto. |
| `tableros_semanales.sh` | Ruta fija `/home/croman/...`: en el servidor moría con "No existe" (exit 1) todos los lunes desde la migración. |
| venv del servidor | Sin `bs4`, sin `pandas`, sin `pip`: el pipeline no podía correr allá. El pin `facebook-business==21.0.4` de `requirements.txt` **no existe en PyPI**. |
| `src/catalog/` (catálogo de 96 modelos) | **Nunca estuvo en git**: existía solo en la notebook. Es lo que usan el generador de personas y ahora el scraper para reconocer modelos — en el servidor el pipeline de personas no podía ni importar. Trackeado hoy. |
| Precios de la competencia | Solo existían en las Battle Cards, tomados a mano el 04/08. Nada los refrescaba. |
| Mercado por modelo | La nota de mercado era por marca; los datos por modelo (puesto por segmento, rivales, tecnología, localidad, importaciones) estaban en el Advisor pero no en el vault. |

### Qué se hizo

**1. Paridad notebook ↔ servidor.** Commit y push de las 438 notas; pull en el servidor (ya tiene las 57 personas por modelo y la Bitácora). Los tres scripts con rutas fijas (`monitor-competencia.sh`, `tableros_semanales.sh`, `monitor_competencia.py`) ahora resuelven la ruta solos y son el **mismo archivo** en las dos máquinas. Venv del servidor recreado (`python3-venv` instalado) con las dependencias del proyecto; pin de `facebook-business` corregido a 21.0.5.

Verificado: el monitor arreglado en el servidor detectó 9 "cambios" en su primera corrida (efecto esperado del cambio de método de hash) y **0 en la segunda** — el hash de oferta es estable, como en la notebook.

**2. Mercado por modelo desde CADAM** — `~/.hermes/scripts/mercado-modelos-a-obsidian.py`, enganchado al mismo wrapper que el cron `mercado-obsidian` (lunes 08:30), así se refresca solo. Escribe [[📊 Mercado por Modelo 2026]] con:
- cada modelo propio: unidades del año, mismos meses del año anterior, variación, **puesto dentro de su segmento** (ej. Jetour X50: 32º de 326 SUV), rivales directos del segmento y **enlace a su buyer persona** (44 personas enlazadas);
- podio de cada segmento con los propios marcados (Santa Rosa tiene 7,4% del SUV, 17,3% de camiones, 19,9% de furgones);
- tecnología: el mercado es 12,5% electrificado, Santa Rosa 31,5%;
- dónde se matricula (Asunción 77,7%, CDE 8,8%, Coronel Oviedo 4,5%...);
- importaciones por modelo, propias y del mercado, como indicador adelantado.

**3. Gama y precios publicados, por modelo** — `scripts/gama_precios_competencia.py` en el repo, enganchado al final del monitor de competencia (cron cada 6 h). Lee 18 webs (7 propias + 11 de competencia), usa Chrome headless para las que se arman por JavaScript, y escribe [[💰 Precios por Modelo]] + `output/competencia/precios_historico.csv` (histórico) + eventos en la Bitácora cuando un modelo aparece/desaparece de una web o un precio cambia.

Verificado contra las Battle Cards (precios tomados a mano el 04/08): **Nissan 8 de 8 exactos, Renault 5 de 5, GWM 8 de 8, Mitsubishi L200 exacto**. 29 precios en total en la primera corrida. Misma corrida en el servidor: 29 precios, 130 s. Cuando no hay novedad el script no imprime nada (patrón watchdog del cron), verificado con una segunda corrida.

### Alcance real del scraping, medido

| Sitio | Precio publicado | Gama (modelos) |
| --- | --- | --- |
| GWM, Jetour, Renault, Mitsubishi (propias) | ✅ | ✅ |
| Nissan | ✅ solo renderizando JS en las fichas (Chrome) | ✅ |
| Geely | ⚠️ 1-2 fichas | ✅ |
| Kia, Chery, Hyundai, Diesa, Automaq, Garden, Toyotoshi, DLS | ❌ no publican precio, ni con JS | ✅ |
| Nipon (Mitsubishi) | — | — **web suspendida por el hosting** (`suspendedpage.cgi`, visto hoy) |

De los que no publican precio sale la gama: cuándo aparece un modelo nuevo o desaparece uno. Para sus precios la única fuente sigue siendo la investigación manual (Battle Cards).

### Decisión 2026-09-04: produce el servidor, la notebook hace pull

Se resolvió el problema de las dos máquinas generando lo mismo. Reparto final:

| Genera | Dónde | Cron | Publica |
| --- | --- | --- | --- |
| Monitor de competencia + gama y precios | servidor | cada 6 h | `publicar-vault` (servidor, cada hora a los :15) |
| Tableros semanales (personas, campañas, asesores, embudo) | servidor | lunes 08:00 | idem |
| Mercado CADAM por marca y por modelo | servidor | lunes 08:30 | idem |
| **Pipeline diario de personas** (Meta + Bitrix → 57 personas por modelo, marketing, audiencias) | servidor | timer systemd `buyer-persona-pipeline.timer`, 06:00 (tarda ~23 min) | idem |
| Registro de proyectos (`Proyectos/`) | notebook | diario 07:00 | `vault-sync` (notebook, cada hora a los :45) |
| Jobs con agente (promociones, análisis semanal, diario operativo) | notebook | como estaban | idem |

- **El productor escondido.** El pipeline diario no era ningún cron de Hermes: era un timer de systemd en la notebook (`buyer-persona-pipeline.timer`, diario 06:00, `Persistent=true` — por eso corrió hoy a las 08:28, al prender). Quedó **deshabilitado en la notebook e instalado en el servidor** con la misma definición. Con eso el código de personas por modelo, que estaba solo en la copia de trabajo de la notebook (sin commitear), se versionó para que el servidor genere lo mismo.
- Los dos lados hacen `git pull --rebase --autostash` antes de commitear, y **escriben archivos distintos**, así que no hay conflictos. Si alguna vez chocan, los scripts se niegan a pisar y avisan.
- Pausados (no borrados): en la notebook `Monitor Competencia`, `tableros-semanales`, `mercado-obsidian`; en el servidor los tres jobs con agente que fallaban por modelo sin fijar. Quedaron en la notebook porque ahí funcionan con su propia GPU; en el servidor pondrían otro modelo en la placa del bot de ventas.
- Verificado de punta a punta: el servidor generó las notas de mercado, las publicó (commit `676a121`), la notebook las trajo y publicó lo suyo (`413ce20`).
- Cadena diaria: 06:00 pipeline (termina ~06:25) → 07:15 publicación → 07:45 la notebook lo tiene. Los lunes además: 08:00 tableros → 08:30 mercado → 09:15 publicación → 09:45 en la notebook. El `Advisor · Benchmark competitivo` de la notebook pasó de 07:45 a **10:00** (lunes), así arma el benchmark con lo que el servidor publicó a las 09:15 y la notebook trajo a las 09:45; lo que escribe en el vault sale por `vault-sync` a las 10:45.
- `graph.json` de Obsidian dejó de versionarse: cambia con cada sesión y generaba un commit por hora.

- **El benchmark semanal no llegaba a Obsidian.** `advisor-benchmark.sh` (notebook, lunes) rearma Benchmark, Battle Cards, Embudo, Evidencia Meta y Pauta Meta — con su propio scraper con navegador — pero los escribía solo en `output/personas/`, fuera del vault y de git. En Obsidian seguían los del 25/08 con los del 03/09 ya generados. Copiados los cinco al vault hoy y el script ahora los deja también en `Buyer Personas/`.

### Pendientes

- El histórico de precios recién arranca hoy: la detección de cambios de precio empieza a servir a partir de la segunda corrida.
- Los 19 scripts sueltos de análisis en `scripts/` (`dedup_personas.py`, `validate_model_catalog.py`, …) siguen sin trackear en git, solo en la notebook. Algunos tocan datos de Bitrix; decidir cuáles versionar.

### Cómo correr a mano

```bash
# mercado por modelo (usa el conector al Advisor por ssh)
python3 ~/.hermes/scripts/mercado-modelos-a-obsidian.py --anio 2026

# gama y precios (desde el repo; --dry-run imprime sin escribir)
cd ~/Escritorio/BUYER\ PERSONA && venv/bin/python scripts/gama_precios_competencia.py --dry-run
```
