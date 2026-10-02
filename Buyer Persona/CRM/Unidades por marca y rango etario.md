---
tipo: analisis-etario
solicitado_por: Valentina (Gerencia de Marketing)
fecha: 2026-08-21
fuentes: [ERP FacturacionUnidades-7343.xlsx, Meta Marketing API v21.0]
periodo_ventas: 2024-04-02 a 2026-04-30
periodo_meta: ultimos 90 dias
tags: [ventas, edad, meta, estimacion]
---

# Unidades por marca y rango etario

> [!danger] La edad del comprador NO se registra en ningun sistema
> Verificado el 2026-08-21 sobre las tres fuentes posibles:
> - **ERP** (`FacturacionUnidades-7343.xlsx`): sus 29 columnas no incluyen edad, fecha de nacimiento ni cedula. Se buscó en las 12.254 cadenas del archivo: cero RUC, cero fechas de nacimiento.
> - **Encuesta AGESTA**: tiene sexo derivado del nombre, pero no edad. Lo que parecia edad era *antiguedad* de la relacion.
> - **CRM Bitrix**: el campo `BIRTHDATE` **existe** y esta practicamente vacio — 4 contactos cargados de 50.334. No falta la herramienta, falta el habito. Ver [[Capturar la edad del comprador]].
>
> Por lo tanto **la tabla 3 de esta nota es una estimacion modelada, no una medicion.** Las tablas 1 y 2 si son datos reales.

## 1. Unidades vendidas por marca — DATO REAL

Facturacion del ERP, abril 2024 a abril 2026. Esto es lo que efectivamente se vendio.

| Marca | Unidades | Ticket medio USD |
| --- | --: | --: |
| JETOUR | 1.360 | 25.977 |
| GREATWALL | 801 | 29.470 |
| RENAULT | 710 | 19.548 |
| MITSUBISHI | 383 | 28.762 |
| JAC | 144 | 24.453 |
| SOUEAST | 135 | 26.897 |
| LEAPMOTOR | 35 | 26.351 |
| JMC | 30 | 8.587 |
| JMEV | 28 | 13.978 |
| ZEEKR | 23 | 40.696 |
| KARRY | 13 | 10.260 |
| **Total** | **3.662** | |

## 2. Alcance por edad en Meta Ads — DATO REAL

Ultimos 90 dias, 63 cuentas con actividad de las 85 mapeadas. **Esto es quien VIO los avisos, no quien compro.**

| Marca | 18-24 | 25-34 | 35-44 | 45+ | Total | % 18-24 |
| --- | --: | --: | --: | --: | --: | --: |
| Jetour | 454.800 | 990.760 | 627.721 | 741.076 | 2.815.049 | 16,2% |
| GWM | 373.722 | 742.897 | 513.028 | 487.665 | 2.118.201 | 17,6% |
| Renault | 226.977 | 307.007 | 213.626 | 279.369 | 1.027.416 | **22,1%** |
| JAC | 47.199 | 284.813 | 187.411 | 185.662 | 705.157 | 6,7% |
| XPeng | 51.515 | 237.770 | 161.058 | 241.092 | 691.634 | 7,4% |
| Soueast | 114.350 | 184.284 | 147.940 | 167.458 | 614.130 | 18,6% |
| Renew | 96.960 | 201.196 | 144.739 | 158.768 | 601.736 | 16,1% |
| Leapmotor | 67.485 | 173.240 | 130.749 | 191.618 | 563.134 | 12,0% |
| Mitsubishi | 28.610 | 211.490 | 133.942 | 137.424 | 511.651 | 5,6% |
| Zeekr | 6.160 | 182.737 | 130.836 | 120.058 | 439.856 | **1,4%** |
| JMEV | 23.546 | 43.231 | 31.240 | 25.535 | 123.561 | 19,1% |
| **Total** | **1.501.793** | | | | **10.320.105** | **14,6%** |

**Lectura util para pauta:** Renault (22,1%), JMEV (19,1%) y Soueast (18,6%) son las marcas cuyo aviso mas llega a jovenes. Zeekr (1,4%) y Mitsubishi (5,6%) practicamente no.

## 3. Unidades estimadas 18-25 — ESTIMACION, NO MEDICION

> [!warning] Estos numeros salen de un modelo, no de un registro
> Nadie conto estas ventas. Se calculan asi:
>
> `unidades × (% alcance 18-24 en Meta) × factor de conversion etaria`
>
> El **factor de conversion** existe porque un joven ve avisos mucho mas de lo
> que compra autos: el poder adquisitivo no acompaña. Se modela con el precio —
> `(25.000 / ticket)^1.6 × 0,30` — de modo que cuanto mas caro el vehiculo,
> menor la proporcion de compradores jovenes. **Ese 0,30 es un supuesto, no un
> dato observado.**
>
> Si el supuesto esta mal, todos los numeros de esta tabla estan mal en la
> misma proporcion.

| Marca | Unidades reales | % 18-24 Meta | Factor | **Estimado 18-25** |
| --- | --: | --: | --: | --: |
| JETOUR | 1.360 | 16,2% | 0,28 | ~62 |
| RENAULT | 710 | 22,1% | 0,30 | ~47 |
| GREATWALL | 801 | 17,6% | 0,23 | ~33 |
| SOUEAST | 135 | 18,6% | 0,27 | ~7 |
| MITSUBISHI | 383 | 5,6% | 0,24 | ~5 |
| JAC | 144 | 6,7% | 0,30 | ~3 |
| JMEV | 28 | 19,1% | 0,30 | ~2 |
| LEAPMOTOR | 35 | 12,0% | 0,28 | ~1 |
| ZEEKR | 23 | 1,4% | 0,14 | ~0 |
| JMC, KARRY | 43 | sin pauta en Meta | — | — |
| **Total** | **3.662** | | | **~159 (4,3%)** |

El orden importa mas que los valores: **Jetour y Renault concentran el segmento joven**, Renault con menos volumen total pero la mayor proporcion. Zeekr y Mitsubishi quedan afuera.

## Como hacerlo real

El plan esta en [[Capturar la edad del comprador]].

Resumen: **Bitrix ya tiene el campo** (`BIRTHDATE`, estandar en contactos) y esta
vacio — 4 contactos cargados de 50.334. No hay que desarrollar nada, hay que
empezar a pedirlo en la venta. Recien con seis meses a un año de datos esta
nota se puede rehacer con numeros medidos en vez de estimados.

Relacionado: [[Ventas Reales - abril 2024 a abril 2026]] · [[Campañas Meta - ultimos 90 dias]] · [[Mapa de cuentas Meta]]
