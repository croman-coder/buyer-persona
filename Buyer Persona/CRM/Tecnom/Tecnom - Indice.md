---
tipo: tecnom-indice
actualizado: 2026-10-12
tags: [crm, tecnom, indice]
---
# Tecnom — índice de lo que hay en esta PC

Generado por `BUYER PERSONA/scripts/tecnom_a_obsidian.py` (se puede volver a correr cuando se bajen exports nuevos). Datos agregados en `data/fuentes/tecnom_agregado.csv` (marca, mes, origen, campaña, leads, ventas).

## Marcas con datos
- [[Tecnom - GWM]] — 4.781 leads
- [[Tecnom - JAC]] — 3.523 leads
- [[Tecnom - JETOUR (tenant)]] — 93.138 leads
- [[Tecnom - JMEV]] — 1.704 leads
- [[Tecnom - LEAPMOTOR]] — 8.302 leads
- [[Tecnom - MITSUBISHI]] — 7.811 leads
- [[Tecnom - RENAULT]] — 26.545 leads
- [[Tecnom - SOUEAST]] — 672 leads
- [[Tecnom - ZEEKR]] — 1.445 leads

## Fuentes leídas
| Archivo | Estado | Filas | Desde | Hasta |
|---|---|--:|---|---|
| Total - Total(1_1_2023 - 16_2_2026).xlsx | ok | 26.545 | 2023-02-13 | 2026-02-16 |
| Total - Total(1_1_2023 - 7_3_2026).xlsx | ok | 7.811 | 2023-01-04 | 2026-01-16 |
| Total - Total(22_3_2022 - 28_3_2026).xlsx | ok | 10.006 | 2024-04-26 | 2026-03-27 |
| Total - Jetour Tecnom (5_8_2022 - 20_9_2026).csv | ok | 93.138 | 2022-08-05 | 2026-09-20 |
| LEADS TOTALES 2025 SRPY.xlsx | ok | 10.421 | 2025-01-01 | 2025-12-11 |

## Lo que NO está (huecos conocidos)
- **Renew (usados) antes de noviembre 2025.** No hay export de Tecnom de Renew de 2024 en esta PC. Los leads de Renew que sí están son de noviembre 2025 (`RENEW (2).xlsx`), y no se volcaron aquí porque ese archivo no trae ventas ni el resto del año. Pedido pendiente: feria CADAM Usados Renew de junio 2024.
- **GWM, JAC, Zeekr y Soueast antes de 2025.** Solo está 2025 completo. El JSON de GWM de Descargas es la lista de usuarios, no de consultas. Soueast tiene exports por vendedor (abril 2024 a abril 2026) bajados en la carpeta `SOUEAST` que no se incluyeron.
- **Ventas por campaña.** La venta es la que cargó el vendedor en Tecnom. La facturación real del ERP no trae el canal de origen (ver [[Ventas Reales - abril 2024 a abril 2026]]).
- Los datos personales de los leads quedan solo en los Excel originales; Obsidian solo tiene conteos.
