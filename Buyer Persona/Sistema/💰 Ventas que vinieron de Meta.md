---
type: ventas-meta
updated: 2026-11-01
tags: [meta-ads, ventas, atribucion, interno]
---
# 💰 Ventas que vinieron de Meta

> [!info] Qué es
> Cada venta del ERP a un cliente final se busca entre los leads de formulario de Meta de los 120 días anteriores: primero por teléfono o mail, y si no por nombre, solo cuando ese nombre no aparece en otra venta. Se actualiza en cada corrida. **No se guarda ningún nombre, teléfono ni mail: solo totales.** Uso interno.

**Ventas evaluadas:** 94 a clientes finales, del 2026-09-02 al 2026-09-11 (último dato del ERP) · **leads de Meta:** 29.181, del 2026-08-03 al 2026-11-01.

**En total, 9 de 94 ventas (10 %) tuvieron un lead previo de Meta.** Del lead a la venta pasan 8 días (mediana; la mitad, entre 4 y 11).

> [!warning] El ERP casi no trae teléfono ni mail en estas ventas (4 %)
> Entonces el cruce depende del nombre, que es menos seguro. Antes de agosto de 2026 el reporte de facturación traía teléfono o mail en el 41 % de las ventas: pedir que se vuelvan a exportar esas columnas.

## Por marca

| Marca | Ventas | Con lead de Meta | % | Por teléfono o mail | Por nombre | Ventas con teléfono o mail en el ERP | Del lead a la venta |
|---|---|---|---|---|---|---|---|
| Jetour | 46 | 2 | 4 % | 0 | 2 | 0 % | 8 días |
| GWM | 18 | 2 | 11 % | 0 | 2 | 0 % | 18 días |
| Soueast | 11 | 0 | 0 % | 0 | 0 | 0 % | — |
| Renew | 7 | 2 | 29 % | 1 | 1 | 43 % | 4 días |
| Renault | 5 | 1 | 20 % | 0 | 1 | 20 % | 13 días |
| JAC | 4 | 1 | 25 % | 0 | 1 | 0 % | 2 días |
| Mitsubishi | 2 | 1 | 50 % | 0 | 1 | 0 % | 8 días |
| Zeekr | 1 | 0 | 0 % | 0 | 0 | 0 % | — |

## De dónde vino el lead

| Marca | Campaña de la marca | Campaña de un asesor | Campaña de otra marca | Formulario sin anuncio | Campaña de una cuenta que no se lee |
|---|---|---|---|---|---|
| Jetour | 2 | 0 | 0 | 0 | 0 |
| GWM | 0 | 1 | 0 | 0 | 1 |
| Renew | 0 | 0 | 2 | 0 | 0 |
| Renault | 1 | 0 | 0 | 0 | 0 |
| JAC | 0 | 1 | 0 | 0 | 0 |
| Mitsubishi | 1 | 0 | 0 | 0 | 0 |

## La venta es de una marca y el lead de otra

La gente compara por segmento y precio, no por marca: el lead de una marca termina comprando otra.

| Lead de | Venta de | Ventas |
|---|---|---|
| GWM | Renew | 2 |

## Campañas con más ventas

| Campaña | Cuenta | Marca de la cuenta | Ventas | Gasto 90 días (USD) | Costo por venta (USD) |
|---|---|---|---|---|---|
| AON 2025 ASU | GWM Paraguay | GWM | 2 | 4.624 | 2.312 |
| JETOUR / Leads ASU / Dashing + T1/T2 + F700 + X50 + X70 / 20 | Jetour | Jetour | 2 | 4.858 | 2.429 |
| Nueva campaña de Clientes potenciales | — | GWM | 1 | — | — |
| JAC Camiones / LEADS / SET 26 | JORGE IBARROLA / Jac Paraguay | JAC | 1 | 197 | 197 |
| 2026_CLIENTES POTENCIALES | GABRIELA LEZCANO GWM | GWM | 1 | 472 | 472 |
| formulario/leads/L200 | Mitsubishi Paraguay | Mitsubishi | 1 | 158 | 158 |
| RENAULT / Koleos + Master / Leads / PY / 2026-10 | Renault Santa Rosa Paraguay | Renault | 1 | 2.201 | 2.201 |

## Cómo leerlo

- **Es un piso, no el total.** Solo cuenta leads de formulario (los chats de WhatsApp no se pueden leer por API), Meta guarda los leads 90 días y no todas las ventas del ERP traen teléfono o mail.
- **«Por nombre»** es una coincidencia probable: todas las palabras del nombre del lead están en el del cliente, ese nombre no se repite en otra venta y no aparece en más de 3 leads. Los nombres comunes quedan afuera.
- **Qué tan bien anda:** contra el cruce hecho a mano de Soueast (septiembre, 39 ventas, 03-10-2026) encontró 6 de las 13 ventas que habían venido de una campaña de Meta y marcó 3 que a mano no aparecían. Con teléfono o mail en el ERP la coincidencia es casi segura.
- **Costo por venta** = gasto de la campaña en los últimos 90 días ÷ ventas que salieron de sus leads. Sirve para comparar campañas entre sí, no como costo exacto.
- **Bitrix:** muchas de estas ventas figuran como «Prospecto del Asesor». En el cruce a mano de Soueast de septiembre, 12 de 15 ventas que vinieron de Meta estaban cargadas así. Si el origen se carga bien, este número sube.

Relacionado: [[📘 Manual Buyer Persona#4.6 Que el algoritmo aprenda de las ventas|Manual, 4.6]] · datos en `output/raw/ventas_meta_<fecha>.json`.
