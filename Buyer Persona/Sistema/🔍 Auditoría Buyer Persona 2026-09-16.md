---
tipo: auditoria
fecha: 2026-09-16
alcance: pipeline Buyer Persona + Obsidian + Hermes + audiencias Meta
tags:
  - buyer-persona
  - auditoria
  - meta-ads
  - remarketing
---

# 🔍 Auditoría Buyer Persona — 16 sep 2026

Relacionado: [[Infraestructura y Conexiones]] · [[📈 Inteligencia de Mercado — Avances]] · [[Buyer Personas MOC]] · [[📊 Semillas Custom Audiences - Ventas Reales]] · [[Mapa de cuentas Meta]]

## 1. Estado actual (verificado, no de memoria)

| Componente | Estado | Evidencia |
|---|---|---|
| Pipeline diario | ✅ corre en servidor SRPY186, timer systemd 06:00 | `last_status.txt`: OK 2026-09-16 06:00 · 21 min · 73 personas · 376 .md |
| Personas | ✅ 10 marcas + 6 tipos + **57 modelos reales** | catálogo validado contra 3.933 anuncios (`validate_model_catalog.py`) |
| Meta Ads | ✅ 85 cuentas, 20 páginas, **17.819 leads/90d** | conector con page tokens, rate-limit con backoff |
| Copy real por modelo | ✅ 57 modelos con análisis propio | `ad_copy_analyzer` + `AD_DERIVED_INSIGHTS` (Leapmotor/Renault curado a mano) |
| Placement / formato | ✅ por marca | "Reels/Stories concentra X%" en Estrategia de cada nota |
| Leads reales agregados | ✅ sin PII | modelo pedido, forma de pago, ciudad, interés |
| Audiencias existentes | ✅ 12 notas, una por marca | 166 audiencias mapeadas, 49 lookalikes |
| Semillas ventas reales | ⚠️ **generadas, NO subidas a Meta** | 2.305 emails + 1.467 teléfonos SHA-256 en `output/audiencias_meta/` |
| Ventas reales en pipeline | ❌ **sigue el CSV demo** | `settings.yaml: sales_history: data/sample_sales/ventas.csv` (notebook y servidor) |
| Embudo Bitrix | ❌ deshabilitado en `settings.yaml` (`funnel.enabled: false`) | nota `📊 Embudo de Ventas` existe pero sale de CSV de embudo, no de Bitrix vivo |
| Google Ads | ❌ sin credenciales | conector escrito, `enabled: false` |
| Vault | ✅ 15 carpetas, git cada hora servidor→notebook | último commit 09:15 hoy |
| Hermes (notebook) | ✅ 4 jobs activos, todos `ok` hoy | registro-proyectos 07:00 · promociones 08:00 · competencia semanal lun 09:00 · diario-operativa 19:00 |
| Interconexión | ✅ marca ↔ modelos ↔ marketing ↔ audiencias ↔ MOC | wikilinks bidireccionales |

## 2. Lo que está mal o a medias (ordenado por impacto)

### 🔴 P1 — Demografía de las 73 personas es FICTICIA
El histórico de ventas que alimenta edad, género, ciudad y ticket **es el CSV de ejemplo que se generó en la fase demo**. Cada nota lleva un aviso amarillo por esto. Mientras tanto el ERP real (`ENCUESTA AGESTA/FacturacionUnidades-7343.xlsx`, **10.167 unidades, abr-2024 → abr-2026**) está en el disco y solo se usa para las semillas de lookalike.

Lo que el ERP sí tiene y hoy se desperdicia:

| Columna ERP | Para qué sirve en la persona |
|---|---|
| Marca, Modelo, Versión | ventas reales por modelo → ranking real, no por pauta |
| Lista, Monto, Neto | ticket promedio **real** por modelo |
| Local / Local de Vendedor | sucursal → proxy de ciudad real (ASU/CDE/Encarnación…) |
| Tipo Cliente | persona física vs empresa (B2B vs B2C) |
| Tipo Venta | contado vs financiado → **valida el hallazgo de "la cuota manda"** |
| Vendedor / Supervisor | cruza con Scorecard Asesores |
| RETOMA (Marca Ret., Modelo/Versión) | **qué auto entregan al comprar** → señal de conquista (de qué marca vienen) |
| Prospecto: Medio / Fuente | **origen real del lead que cerró** → atribución Meta vs otros |

Lo que NO tiene: edad ni género. Eso queda de Meta (demografía por cuenta) — correcto, es la única fuente.

### 🔴 P2 — Semillas de ventas reales sin subir → 0 lookalikes de compradores reales
Jetour (marca #1 en pauta y en semilla: 955 emails) tiene **0 lookalikes**. Los 49 lookalikes existentes salen de engagement/web/formularios, no de quien **compró**. El token tiene `ads_management` → se puede hacer **por API**, sin subir CSV a mano: crear Custom Audience `VENTAS REALES <MARCA> — base`, empujar hashes, y crear Lookalike PY 1%.

Bloqueo conocido: Mitsubishi (524/525 filas con contacto de Nipon) → **no subir**. Recuperar contactos reales desde Bitrix (script `recuperar_mitsubishi_bitrix.py` ya existe, verificar resultado).

### 🟠 P3 — Personas de modelo ordenadas por pauta, no por venta
Hoy el ranking de modelos = cantidad de anuncios. Con el ERP conectado el orden pasa a ser por **unidades vendidas**, que es lo que importa para asignar presupuesto de remarketing. Además aparece la brecha "mucho anuncio / poca venta" (candidatos a pausar) y "poca pauta / mucha venta" (candidatos a escalar).

### 🟠 P4 — Embudo Bitrix apagado
`funnel.enabled: false`. La nota de embudo sale de un CSV estático. Con Bitrix vivo se cierra el círculo lead Meta → deal Bitrix → factura ERP, y la persona deja de ser "quién pregunta" para ser "quién compra".

### 🟡 P5 — Curación manual solo en 2 marcas
`AD_DERIVED_INSIGHTS` tiene Leapmotor y Renault leídos a mano; el resto usa reglas automáticas (correctas pero genéricas). Con 57 modelos ya no escala leer a mano — alternativa: pasar el copy real de cada modelo por Claude una vez por semana y guardar el resultado como override.

### 🟡 P6 — Ruido en el catálogo de cuentas
El análisis de copy reporta 14 "marcas" incluyendo `JAC/Renault`, `Multimarcas`, `Karry`, `Renew`, `XPeng` — cuentas compartidas o fuera del portfolio que hoy entran al pipeline. No rompe nada, pero ensucia agregados por marca.

### 🟡 P7 — Google Ads
Conector listo, sin credenciales. Sigue siendo la única fuente de intención de búsqueda (qué modelo googlea la gente antes de pedir cotización).

## 3. Cómo se usa esta infraestructura con Meta (flujo operativo)

```
ERP (facturas reales) ──┐
Meta (leads + copy) ────┼──► Personas por marca/modelo ──► Estrategia por modelo
Bitrix (deals) ─────────┘            │
                                     ├──► Audiencias/ (qué ya existe, no duplicar)
                                     ├──► Semillas → Custom Audience → Lookalike PY 1%
                                     └──► Marketing/ (copies legales por persona)
```

**Por modelo, la nota te dice** (ej. `Persona 28 - Modelo Leapmotor C10`):
1. **A quién** → edad/género/ciudad (hoy demo → con ERP real)
2. **Qué le duele** → copy real analizado ("ansiedad de autonomía", "cuota mensual")
3. **Dónde** → placement real ("Reels/Stories 73%")
4. **Con qué público** → `Audiencias Meta - <Marca>` lista lo que ya existe + semilla de ventas reales
5. **Con qué mensaje** → `Marketing/Meta Ads - Persona 28` (copy sin nombrar competencia)

**Remarketing con ventas reales (lookalike):**
1. Semilla = compradores reales de esa marca (hash SHA-256, sin PII visible)
2. Custom Audience por marca en su cuenta madre
3. Lookalike Paraguay 1% (luego 1-2%) → prospecting de "gente que se parece a quien ya compró"
4. Exclusión = la misma semilla (no gastar en quien ya compró) + leads abiertos en Bitrix
5. Medir: CPL del lookalike vs CPL de intereses (hoy: Kardian $4.68 mejor CPL Renault)

## 4. Ejecutado el mismo día (16 sep, tarde)

| # | Acción | Estado |
|---|---|---|
| 1 | ERP → pipeline (`erp_normalizer.py`, `sales.format: erp`), 4.243 unidades reales, sin PII | ✅ notebook + servidor |
| 1b | Edad/género desde la audiencia real de Meta por marca (el ERP no los tiene); fuente visible en la nota | ✅ |
| 2 | Semillas + lookalikes por API | ⏸️ **no todavía** (decisión de negocio) |
| 3 | Modelos ordenados por unidades vendidas + **brecha pauta/venta** (sub/sobre-pautado, lanzamiento) | ✅ |
| 4 | Bitrix como conector del pipeline (agregados, con reintento) → sección "Embudo CRM" por marca | ✅ |
| 5 | Exclusión de cuentas fuera de portfolio (Karry, Multimarcas, JAC/Renault) → 81 cuentas, 12 marcas | ✅ |
| 6 | Manual: [[📘 Manual Buyer Persona]] | ✅ |
| 7 | Google Ads | ⏸️ sin credenciales |
| — | Curación manual de copy para más marcas (P5) | pendiente, baja prioridad: el análisis automático ya cubre 57 modelos |

**Hallazgos que aparecieron al conectar datos reales:**
- Kwid = 42% de las ventas Renault con 19% de su pauta → **sub-pautado**. Kardian y Koleos, al revés.
- Jetour X50: 89 ventas en los últimos 90 días del ERP con solo 71 anuncios → segundo sub-pautado por volumen reciente.
- Bitrix (90 días): 18.600 leads, 188 deals, pero conversión lead→convertido entre 0% y 0.5% y 3.535 leads "sin marca". **El CRM no está cerrando el ciclo**: los asesores no marcan convertidos ni ligan deals. Es higiene de CRM, no del pipeline — hasta que se corrija, el "Embudo CRM" de cada nota va a mostrar números bajos que son reales.
- Mitsubishi en el ERP tiene 525 ventas pero contacto de Nipon: sirve para volumen/precio, no para audiencias.
- El ERP llega hasta el 30-abr-2026: los modelos lanzados después (Zeekr 7X, Outlander, JMEV EV2) aparecen como "🆕 lanzamiento", no como sobre-pautados.

## 5. Plan original (referencia)

| # | Acción | Tipo | Esfuerzo | Impacto |
|---|---|---|---|---|
| 1 | Conector ERP: `FacturacionUnidades.xlsx` → CSV normalizado (sin PII) → `sales_history` | local, reversible | 2-3 h | 🔴 saca el aviso amarillo de las 73 notas, demografía real |
| 2 | Subir semillas + crear lookalikes por API (9 marcas, excl. Mitsubishi) | **toca cuentas Meta vivas** — confirmar antes | 1-2 h | 🔴 primer remarketing sobre compradores reales |
| 3 | Re-rankear modelos por unidades vendidas + brecha pauta/venta | local | 1 h | 🟠 |
| 4 | Prender `funnel` con Bitrix (agregados) | local | 2 h | 🟠 |
| 5 | Filtro de cuentas fuera de portfolio en `_parse_accounts` | local | 30 min | 🟡 |
| 6 | Manual de uso (nota `Sistema/📘 Manual Buyer Persona`) | doc | 1-2 h | pedido para después |
| 7 | Google Ads | necesita credenciales | — | 🟡 |
