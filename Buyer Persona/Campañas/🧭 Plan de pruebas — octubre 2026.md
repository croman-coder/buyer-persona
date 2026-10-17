---
type: plan
created: 2026-10-13
estado: propuesta (esperando OK de Croman)
tags: [meta-ads, prueba, plan, jetour, gwm]
---
# 🧭 Plan de pruebas — octubre 2026

> [!info] De dónde sale
> Datos de la corrida del servidor del **13-10-2026 06:01** (fichas, materiales y centro de compra), con la misma regla de «falta pauta» que el directorio del 12-10. Solo agregados, sin datos de clientes.

## Lo que aprendimos de septiembre

- **Abrir algo nuevo funcionó:** Renew salió 32 % más barato que su campaña habitual (USD 0,45 contra 0,66 por conversación, misma cuenta y mismos días) y Renault Master pasó de 0,4 a 7 leads por día en la cuenta.
- **Repetir lo que ya se pautaba bien no mejoró:** Koleos y L200 salieron más caros que las campañas de la agencia.
- **La calidad no empeoró:** leads trabajados por un asesor, Renault 56,6 % contra 56,1 % del resto de la cuenta; Mitsubishi 80 % contra 59,5 % (pocos leads).
- **Casi no dejamos aprender a las campañas:** de 561 campañas, el 62 % dejó de pautar antes de la semana 5 ([[📈 Curva de aprendizaje — Google Ads vs Meta (26 semanas)]]).

Por eso las pruebas de octubre van **donde falta pauta**, con presupuesto suficiente y **4 semanas sin tocar**.

## Prueba 1 — Jetour X50 (falta pauta)

| | |
|---|---|
| Por qué | **291 ventas al año, el 24,2 % de las ventas de Jetour**, pero solo el 9,2 % de sus anuncios |
| Pauta sugerida | **USD 978 al mes** contra unos **USD 372** de hoy (24,2 % de los USD 4.042/mes que gasta la marca) |
| Costo de referencia | **USD 1,70 por lead** de formulario (Jetour, 90 días) |
| Stock | 88 disponibles + 47 en viaje, **1 unidad de test drive**. ⚠️ El dato es del **18-09**: confirmar antes de pautar |
| Público | Hombres 68 %; 35–44 años (28,5 %) y 25–34 (26,4 %); Asunción |
| Qué les atrae | Financiación en cuotas (55 % de los anuncios), diseño y estatus (47 %), tecnología (40 %), garantía (30 %) |
| Oferta | ⚠️ La planilla es de **septiembre** («Bono 500 o transferencia de regalo USD 600»): **vencida**. Pedir la de octubre a la marca antes de escribir el texto |
| Pieza | **Imagen (gráfica)**, que trajo el lead más barato 4 de 5 meses; Feed primero (USD 1,33). Sumar un carrusel en el mismo conjunto para seguir comparando ([[🎬 Materiales que funcionan — Jetour]]) |
| Presupuesto | **USD 12 por día** (≈ 7 × USD 1,70), unos **USD 340 en 4 semanas**: entra en los USD ~600/mes que faltan |
| Armado | Campaña aparte en la cuenta de Jetour, formulario de siempre, **creada en PAUSA**. Confirmar quién pauta Jetour antes de crearla |

**Cómo se juzga** (reglas del [[📘 Manual Buyer Persona]], sección 4):

1. **A las 2 semanas:** cortar solo si el lead cuesta **USD 3,40 o más** (el doble del promedio de Jetour).
2. **A las 4 semanas, con el promedio de las 4:**
   - costo por lead contra Jetour en las mismas fechas;
   - leads de X50 por día en la cuenta, antes y durante la prueba;
   - % de leads trabajados contra el resto de la cuenta en las mismas fechas (tablero de Meta → ROI Pauta → «Por campaña», con «Comparar con período»).
3. **Ventas, a los ~2 meses:** solo si se actualiza el export de ventas del BI (hoy llega al 10-09).

**Éxito (propuesta):** más leads de X50 en la cuenta, con un costo por lead dentro de ±30 % del promedio de Jetour y un % de leads trabajados igual o mejor que el resto.

## Prueba 2 — GWM H6 «Vengan a probarla juntos» (ya creada)

Está **creada y en pausa desde el 24-09**, esperando el OK: [[🧪 Prueba GWM H6 — Vengan a probarla juntos 2026-09]]. Mide si un texto para **quien acompaña la decisión** hace que ellas dejen su contacto tanto como ellos (hoy 0,72×), sin subir el costo por lead. Se lee a los **7 días con al menos 30 resultados**. Al activarla, el conjunto reinicia su aprendizaje unos días.

## Prueba 3 (opcional, necesita OK) — primer público tibio en Jetour

En Jetour, **los 263 conjuntos de anuncios van a gente nueva** (100 % frío) y ninguno a quien ya interactuó. Propuesta: un conjunto chico para **quienes interactuaron con la página o abrieron el formulario en los últimos 60 días**. **No sube ninguna lista de clientes.** Se mide igual que la prueba 1.

## Prueba 4 — público similar de compradores de Jetour (creado el 14-10)

Con el OK de Croman se subió a la cuenta de Jetour la lista de **1.012 compradores reales** (ERP, abril 2024 a agosto 2026) y se creó su **similar al 1 % en Paraguay**. La lista se limpió: sin ventas a concesionarios, sin mails de Santa Rosa, sin relleno y sin contactos repetidos en 3 ventas o más. Detalle e IDs en [[🎯 Públicos de compradores (listas de clientes)]].

- **Cómo usarlo:** un conjunto aparte en la prueba 1 (X50), con el similar y su propio presupuesto, para compararlo con el público frío en las mismas fechas.
- **Excluir la lista de compradores** de los conjuntos de captación: ya compraron.
- **Ojo:** Meta tarda unas horas en calcular el similar; hasta entonces dice «demasiado pequeña».

## Qué hace falta para arrancar

- [ ] **OK de Croman** para crear la prueba 1 en pausa, y saber **quién pauta Jetour**.
- [ ] **Oferta de octubre** de Jetour X50 y **stock** actualizado (el último es del 18-09).
- [ ] **OK para activar** la prueba 2 (GWM H6).
- [ ] **OK para la prueba 3** (público tibio).
- [ ] **Export de ventas del BI** al día, para poder ver la venta.
- [ ] Para crearlas desde Claude Code: autenticar el conector de Meta (`/mcp` → `facebook-ads` → *Authenticate*).

## Estado

- 13-10-2026: propuesta armada, esperando OK.
