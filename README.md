# 🧠 Buyer Persona 360 — Santa Rosa Automotores

Sistema que lee **Meta Ads** (85 cuentas), el **ERP de ventas**, **Bitrix24** (solo agregados) y los precios de mercado, y cada mañana regenera en un vault de **Obsidian** las fichas de quién compra cada modelo y marca (≈97 fichas), con los textos de Meta Ads, Google Ads, Email y WhatsApp de cada una, las notas «👥 Quién mira y quién decide» y las notas de campañas.

> **Para quien va a pautar:** empezá por el **Manual**, sección 4: [`Buyer Persona/Sistema/📘 Manual Buyer Persona.md`](<Buyer Persona/Sistema/📘 Manual Buyer Persona.md>). Explica qué plataforma usar para qué, cuándo juzgar una campaña y cómo leer cada ficha.

## Primeros pasos en otra computadora

1. Descomprimir la carpeta donde se quiera trabajar (no hace falta `venv`: se crea en el paso 5 si se usan los scripts).
2. **Obsidian** → *Abrir carpeta como vault* → elegir la carpeta `Buyer Persona`.
3. **Claude Code** abierto en esta carpeta: lee `CLAUDE.md` (contexto, reglas y pendientes) y carga la skill `meta-ads-santarosa`.
4. Para crear campañas: el conector oficial de Meta (`facebook-ads`) ya viene en `.mcp.json`. Claude Code pregunta si usarlo: aceptar. Después `/mcp` → `facebook-ads` → *Authenticate* con el usuario de Facebook propio (con acceso a las cuentas en el Business Manager de Santa Rosa). Ninguna clave viaja en esta copia.
5. Solo para los scripts de diagnóstico: `python3 -m venv venv && venv/bin/pip install -r requirements.txt`, `cp .env.example .env` y completar el token.

## Cómo corre

| Qué | Dónde | Cuándo |
|---|---|---|
| Pipeline completo (`main.py`) | Servidor SRPY186, timer de systemd `buyer-persona-pipeline.timer` (`scripts/run_pipeline.sh`) | Todos los días a las 06:00 |
| Chats de Messenger e Instagram (solo conteos) | `conversaciones-actores.timer` (`scripts/conversaciones_actores.py`) | Lunes 03:00 |
| Publicar el vault por git | `publicar-vault` (servidor) y `vault-sync` (notebook) | Cada hora |
| Globo 3D del vault, con login por marca | https://cerebro.santarosa.lat (repo `cerebro-santarosa`) | Se regenera con cada pipeline |

## Estructura

```
main.py                  pipeline: conectores → personas → marketing → vault
src/connectors/          Meta Ads, Google Ads, ventas (ERP), Bitrix, Datacar, stock y acciones comerciales
src/generators/          personas, textos de marketing (Google, Email, WhatsApp, Meta), centro de compra
src/exporters/           notas de Obsidian
src/learning/            memoria de audiencia (aprende corrida a corrida)
scripts/                 análisis y mantenimiento (diagnóstico de pauta, curva de aprendizaje, verificar Google…)
tests/                   pruebas de los generadores de Google Ads, Email y WhatsApp
config/settings.yaml     configuración (las claves salen del .env, nunca van acá)
Buyer Persona/           el vault de Obsidian
.claude/skills/meta-ads-santarosa/   skill de Claude para armar campañas de Meta: se carga sola al abrir Claude Code acá
CLAUDE.md                contexto y reglas para Claude Code (lo lee solo)
.mcp.json                conector oficial de Meta (facebook-ads), sin claves: cada uno inicia sesión con su usuario
docs/                    guías de conexión (Meta, Google), despliegue y recopilación automática
```

## Correrlo

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt
cp .env.example .env                  # completar con las claves reales. NUNCA se versiona
venv/bin/python3 main.py --demo       # datos de ejemplo, sin claves
venv/bin/python3 main.py              # producción (necesita las APIs)
venv/bin/python3 main.py --from-json output/raw/data_sources_<fecha>.json   # regenera sin llamar a las APIs
venv/bin/python3 tests/test_google_ads.py && venv/bin/python3 tests/test_email_whatsapp.py
```

## Reglas que no se negocian

1. **Por ley de Paraguay no se nombran marcas ni modelos de la competencia en un texto público.** La inteligencia competitiva (`Buyer Persona/Competencia/`) es solo de uso interno.
2. **Las campañas se crean siempre en PAUSA.** Se activan solo con el OK de quien las encarga.
3. **Ninguna clave va por chat ni al repo:** solo en el `.env` (ignorado por git).
4. **Nada de nombres, mails ni teléfonos de clientes** en el vault ni en el repo: solo agregados. Subir una lista de clientes a Meta o Google necesita el OK explícito de Croman.
5. **Los textos no prometen** tasas, plazos, garantías ni urgencias que no estén en la planilla de acciones comerciales de la marca. Lo concreto va en el bloque «Oferta del mes», que se confirma antes de usarlo.
6. Un conjunto de anuncios con optimización a conversaciones necesita **al menos USD 5 por día**; menos de eso no entrega.

## Qué NO está en este repo

`.env`, `data/fuentes/` (planillas del ERP, stock, objetivos), `ENCUESTA AGESTA/` (reportes del ERP con datos personales), `output/` (incluye las semillas de audiencias con contactos cifrados) y `logs/`. Están en `.gitignore`.

## Copia en GitHub

Este repo es una **copia filtrada** del repo del servidor (`srpy-servidor:/home/santarosa/git/buyer-persona.git`, que sigue siendo la fuente): no incluye `Buyer Persona/Seguridad/` (hallazgos, puertos e inventario de los servidores) ni `.github/workflows/` (el pipeline corre en el servidor, no en GitHub Actions) y cada exportación revisa que no viaje ningún secreto (`scripts/publicar_github.sh`). Se exporta **todos los días a las 08:10** desde la notebook (tarea de Hermes `github-export`, script `~/.hermes/scripts/publicar-github.sh`), después de que llega la corrida de las 06:00 del servidor; si no hubo cambios, no sube nada. **No editar acá:** la próxima exportación pisa los cambios.

Mantiene [Carlos Roman (Croman)](https://github.com/croman-coder), Innovación, Santa Rosa Paraguay S.A.
