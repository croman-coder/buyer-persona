---
type: dashboard-meta
updated: 2026-10-06
tags: [meta-ads, bitrix, embudo, roi, interno]
---
# 💹 ROI Pauta — embudo por campaña

> [!info] Qué es
> Menú nuevo del Dashboard Meta (v1.82, 6/10/2026), primero de **Pauta Meta**:
> [dashboardmeta.santarosa.lat/#roi](https://dashboardmeta.santarosa.lat/#roi). Para cada campaña y cada cuenta:
> cuántos leads de formulario entraron en el período, cuántos llegaron a Bitrix, cuántos trabajó un asesor, cuántos
> hicieron test drive y cuántos compraron, con la inversión de Meta, el costo por lead y el costo por venta. Un cuadro
> compara **cuentas madre contra cuentas de asesores**. Uso interno.

## Reglas (Croman, 6/10/2026)

| Etapa | Qué cuenta |
|---|---|
| Lead | Formulario de Meta guardado en el historial del tablero (desde el 27/06/2026) |
| Contactado | Un asesor movió el lead de etapa o lo convirtió en negocio. El pase automático a "Leads contactado" a las 2 h **no** cuenta (misma regla que el Dashboard Comercial) |
| Test drive | Algún negocio del lead pasó por "Test Drive realizado". "Agendado" no alcanza |
| Venta | La venta concretada de Bitrix que Conversiones atribuye a ese lead, o la del ERP que encuentra el cruce de [[💰 Ventas que vinieron de Meta]] por teléfono, mail o nombre (desde el 6/10; las por nombre se marcan como probables) |
| Período | Los leads que **entraron** en las fechas elegidas y lo que pasó con ellos hasta hoy; la inversión es la de esas fechas |

Las campañas de WhatsApp y Messenger no se pueden seguir hasta Bitrix (Meta no entrega el teléfono): aparecen al
final con su inversión, sus conversaciones y el costo por conversación.

## Cómo se calcula

Todas las noches a las 04:00 (Hermes, `dashboard-roi-pauta.sh`) el servidor recorre los leads de los últimos 180 días
y busca su lead de Bitrix: primero lo que decidió la carga automática de leads; si no, por teléfono o email (el primero
de 1 h antes a 7 días después del formulario, o el último de los 14 días anteriores si el cliente ya estaba). Después
pregunta a Bitrix si un asesor lo trabajó y qué negocios pasaron por "Test Drive realizado". Solo lee de Bitrix, por
lotes. Detalle técnico: `CRONS.md` §4.e y la spec `docs/superpowers/specs/2026-10-06-roi-pauta-design.md` del repo
`dashboard-meta-ads`.

## Primer cálculo (6/10/2026, 15:06)

| | Leads | En Bitrix | Contactados | Test drives | Ventas | Inversión Meta | Costo por lead |
|---|---|---|---|---|---|---|---|
| **1 al 6 de octubre** | 1.932 | 99,9 % | 937 (48,5 %) | 1 | 0 | US$ 4.742,70 | US$ 1,92 |
| · Cuentas madre | 1.155 | 99,9 % | 535 (46,3 %) | 1 | 0 | US$ 2.921,18 | US$ 2,32 |
| · Cuentas de asesores | 777 | 100 % | 402 (51,7 %) | 0 | 0 | US$ 1.821,52 | US$ 1,33 |
| **27/6 al 6/10 (todo el historial)** | 27.177 | 55 % | 9.213 | 7 | 12 | — | — |

- En octubre los asesores contactan más (51,7 % contra 46,3 %) y su lead sale casi a la mitad (US$ 1,33 contra 2,32).
- El 55 % "en Bitrix" del historial completo es real, no un error del cruce (verificado con muestras contra Bitrix):
  GWM y Jetour iban a Tecnom hasta septiembre (1-3 % en Bitrix en julio y agosto), y en las demás marcas cerca de la
  mitad de los formularios de julio y agosto nunca llegó a Bitrix, o el cliente quedó cargado con otra marca. Desde
  septiembre, con la carga automática de leads, la cobertura es ~100 %.
- Costo por lead y por venta usan solo la inversión de campañas de formulario (US$ 3.711,62 de los 4.742,70 en
  octubre); el resto es WhatsApp/Messenger y alcance.

## Ventas del ERP (desde el 6/10/2026)

El cruce ERP × Meta del pipeline (06:00) ahora también le pasa al tablero **qué lead** terminó en cada venta (solo el ID
de Meta del lead, la fecha, la marca y el modelo; ningún nombre, teléfono ni mail). Primera carga: 49 ventas del 7/8 al
11/9, **48 por nombre** (probables) y 1 por teléfono. Con eso ROI Pauta pasó de 12 a **59 ventas**: 12 de Bitrix y 47
del ERP, 22 de ellas de otra marca que la de la campaña. Caen sobre todo en los leads de julio (17) y agosto (26).

> [!warning] El reporte del ERP se exporta a mano y hoy llega al **11/09**
> Las ventas posteriores no cuentan hasta que se cargue un reporte nuevo en el servidor; la pantalla lo avisa arriba.

> [!warning] Test drive y venta van a dar números chicos
> - En 90 días solo **51** negocios de todas las marcas pasaron por "Test Drive realizado": los asesores casi no usan la
>   etapa.
> - Bitrix tiene **100** ventas en "Ventas Concretadas" en un año y solo **14** con el lead exacto de Meta, mientras el
>   ERP registró **491** ventas a clientes finales del 7/8 al 11/9 ([[💰 Ventas que vinieron de Meta]]). Por eso, desde el
>   6/10, la columna Venta suma las del ERP (sección de arriba).

Relacionado: [[💰 Ventas que vinieron de Meta]] · [[Infraestructura y Conexiones]]
