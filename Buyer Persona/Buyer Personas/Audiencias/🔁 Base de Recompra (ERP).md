---
type: audiencia-recompra
tags: [marketing, meta-ads, audiencias, recompra, fidelizacion]
---
# 🔁 Base de Recompra (ERP)

> Generado el **2026-09-18** desde `FacturacionUnidades-7343.xlsx` (ventas 2018-07 → 2025-09, 5,817 unidades con ≥12 meses).
> Sirve para la **campaña de fidelización**: mostrarle al que ya compró el modelo al que le toca subir. Los CSV (hash SHA-256, formato Custom Audience) están en `output/audiencias_meta/recompra/<Marca>/`, fuera de git.

## Unidades por marca y cohorte

| Marca | ≥ 36 meses (3+ años) | 24-36 meses (en recompra) | 18-24 meses (entra este semestre) | 12-18 meses (precalentar) | Contactables (misma secuencia) |
|---|---|---|---|---|---|
| **Renault** | 2,003 | 518 | 160 | 167 | 0 / 88 / 66 / 138 |
| **Jetour** | 150 | 411 | 253 | 274 | 0 / 155 / 183 / 224 |
| **Mitsubishi** | 744 | 146 | 83 | 72 | ⚠️ sin contacto propio (ver nota) |
| **GWM** | 0 | 53 | 125 | 190 | 0 / 43 / 105 / 156 |
| **JAC** | 0 | 0 | 22 | 32 | 0 / 0 / 22 / 32 |
| **Soueast** | 0 | 0 | 0 | 27 | 0 / 0 / 0 / 26 |
| **Leapmotor** | 0 | 9 | 6 | 11 | 0 / 3 / 6 / 11 |
| **Zeekr** | 0 | 0 | 4 | 6 | 0 / 0 / 4 / 6 |
| **JMEV** | 0 | 0 | 0 | 7 | 0 / 0 / 0 / 6 |

## Qué ofrecerle a cada uno (escalera de recompra)

| Marca | Compró | Unidades ≥18m | Invitar a |
|---|---|---|---|
| Renault | Kwid | 1,173 | Kardian |
| Renault | Duster | 378 | Boreal |
| Renault | Oroch | 311 | Oroch (renovación) |
| Renault | Kangoo | 245 | Kangoo (renovación) |
| Renault | Captur | 161 | Boreal |
| Renault | Master | 161 | Master (renovación) |
| Renault | Stepway | 125 | Kardian |
| Renault | Arkana | 34 | Boreal |
| Jetour | X70 | 459 | X90 / T2 |
| Jetour | Dashing | 216 | T2 |
| Jetour | Traveller | 101 | T2 / G700 |
| Jetour | X90 | 37 | T2 / G700 |
| Jetour | X-1 | 1 | X-1 (renovación) |
| Mitsubishi | L200 | 628 | L200 (renovación) |
| Mitsubishi | Montero | 146 | Montero (renovación) |
| Mitsubishi | Asx | 74 | Asx (renovación) |
| Mitsubishi | New L200 | 70 | New L200 (renovación) |
| Mitsubishi | Mirage | 50 | Mirage (renovación) |
| Mitsubishi | Eclipse | 5 | Eclipse (renovación) |
| GWM | H6 | 53 | Haval H7 / Tank 300 |
| GWM | Jolion | 41 | Haval H6 |
| GWM | Wingle | 30 | Poer |
| GWM | Poer | 26 | Poer (renovación) / Tank 300 |
| GWM | Haval | 14 | Haval H7 / Tank 300 |
| GWM | Tank | 12 | Tank 500 |
| GWM | Ora | 2 | Haval Jolion |
| JAC | Js4 | 5 | JS6 / T9 |
| JAC | T8 | 3 | T9 |
| JAC | E30X | 3 | E30X (renovación) |
| JAC | D8A22 | 3 | D8A22 (renovación) |
| JAC | M3 | 2 | M3 (renovación) |
| JAC | Sunray | 2 | Sunray (renovación) |
| JAC | D8Bs0 | 2 | D8Bs0 (renovación) |
| JAC | T9 | 1 | T9 (renovación) |
| Leapmotor | T03 | 10 | T03 (renovación) |
| Leapmotor | C11 | 5 | C11 (renovación) |
| Zeekr | Zeekr | 4 | Zeekr (renovación) |

## Cómo usarla

1. Subir el CSV de la cohorte a la cuenta madre de la marca como *Custom Audience → Customer list* (identificadores ya hasheados, columnas `email` y `phone`).
2. Campaña **separada** de la de generación de leads: objetivo Clientes potenciales, público = esa lista, creatividad del modelo destino (ver escalera), presupuesto propio.
3. Excluir esa misma lista de las campañas de público frío de la marca (no pagar dos veces por el mismo cliente).
4. Medir en Bitrix con el origen `Meta madre` + nombre de campaña `RECOMPRA <MARCA>`.

## Notas
- Solo el 33% de las filas del ERP trae email y el 19% teléfono: la base contactable es menor que las unidades vendidas. Mejorar la carga en el ERP agranda esta audiencia sola.
- **Mitsubishi:** el ERP tiene cargado el contacto del importador (Nipon) en casi todas las filas; no se genera CSV. Recuperar contactos reales desde Bitrix antes de usar.
- Base unificada desde julio 2018 (`scripts/unificar_ventas.py`): la cohorte de 3+ años ya existe. El email/teléfono solo viene cargado para las ventas de abr-2024 en adelante; las anteriores cuentan como unidades pero no son contactables hasta recuperar el contacto desde Bitrix.
- Un cliente que compró dos veces aparece en la cohorte de cada compra; Meta deduplica al subir.

Relacionado: [[📊 Semillas Custom Audiences - Ventas Reales]] · [[ Buyer Personas MOC]]
