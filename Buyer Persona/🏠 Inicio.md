---
tipo: inicio
tags: [inicio]
---

# 🏠 Santa Rosa — Centro de mando

Todo lo que Hermes mantiene al día, en un solo lugar.

## 📊 Marketing

- [[Buyer Persona Real - Meta 90 dias|Buyer Persona real]] — 17.819 leads de 90 días
- [[Campañas Meta - ultimos 90 dias|Campañas y CPL]] — inversión y costo por lead por marca
- [[Scorecard Asesores - ultimos 90 dias|Scorecard de asesores]] — quién invierte y quién genera
- [[Mapa de cuentas Meta]] — las 85 cuentas del portfolio
- [[Buyer Personas MOC]] — personas por marca y segmento (demo + reales)

## 💰 Ventas

- [[Ventas Reales - abril 2024 a abril 2026|Ventas reales 2024-2026]] — 3.662 unidades, USD 93,6M, margen por marca (fuente: ERP)
- [[Embudo Bitrix - ultimos 90 dias|Embudo CRM]] — leads y deals de Bitrix

## 🗂 Proyectos

- [[Tablero Proyectos.base|Tablero de proyectos]] — vista viva por estado
- [[Proyectos]] — índice generado por el registro (se actualiza 7:00)

## 📔 Operativa

- Carpeta `Operativa/` — diario automático de fin de día (19:00): decisiones, problemas, pendientes

## 🔍 Investigación

- [[CarDoc — Benchmark para replicar en Paraguay]] — ⚠️ ya opera en PY, hay 2 competidores directos

## ⚙️ Sistema

- [[Infraestructura y Conexiones]] — cómo está armado todo: Hermes, cron jobs, GLM, GitHub/Vercel/Firebase

## ⚙️ Cómo se mantiene

| Qué | Cuándo | Quién |
| --- | --- | --- |
| Registro de proyectos | 7:00 diario | cron `registro-proyectos` |
| Diario de operativa + memoria | 19:00 diario | cron `diario-operativa` |
| Buyer persona / campañas / asesores | al correr el pipeline | `main.py` + `scripts/generar_tablero_meta.py` |
| Consolidación de skills | semanal | curator de Hermes |
