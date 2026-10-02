---
type: campaña
created: 2026-09-23
updated: 2026-09-23
marca: Renew
estado: activa
tags: [campaña, renew, meta-ads, whatsapp, buyer-persona, marca/renew]
---

# 🚀 Pauta Renew IA — Clavos + Mantecas (23 al 30-09-2026)

> [!success] Activadas el 2026-09-23 por pedido de Carlos
> Las dos campañas, los 10 conjuntos y los 10 anuncios, en estado `ACTIVE`. Se activaron con las gráficas del Jetour X70 (año) y del Fiat Fastback (precio) tal como vinieron; ver «Revisar antes de activar».

> [!summary] En una línea
> Dos campañas aparte de la pauta vigente de Renew, con las 10 gráficas de marketing: **Clavos** (5 unidades difíciles de vender) y **Mantecas** (5 de las más vendibles). Objetivo **Ventas**, cada anuncio abre **WhatsApp** con un saludo que ya dice qué auto consulta. **USD 100 en total**, se cortan solas el **30-09 a las 23:59**. Creadas en pausa y **activadas el 23-09**.

## Estructura

| | Clavos | Mantecas |
|---|---|---|
| Campaña | `120250602052540465` | `120250602078240465` |
| Presupuesto | **USD 60** de por vida | **USD 40** de por vida |
| Reparto | **CBO desde el 23-09 ~18:15** con **piso de USD 8 por unidad** (antes ABO, USD 12 fijos por unidad: no entregaba, ver abajo) | **CBO:** Meta mueve la plata a la unidad con conversaciones más baratas |
| Por qué | el piso le asegura a cada clavo su parte; los USD 20 restantes van a la unidad que mejor responda | se venden solas: conviene que Meta persiga la conversación más barata |

Esquema copiado de la campaña que ya funciona en la cuenta, **LEADS 2026 - VENTAS WHATSAPP** (USD 0,32 a 1,54 por conversación en los últimos 30 días): objetivo `OUTCOME_SALES`, optimiza `CONVERSATIONS`, destino WhatsApp **0991 703 063**, Paraguay, Advantage+ audience. Encima va lo del Buyer Persona, igual que [[🚀 Pauta Renault IA — Koleos + Master 2026-09|Renault]] y [[🚀 Pauta Mitsubishi IA — L200 + Montero 2026-09|Mitsubishi]]: públicos propios como sugerencia y la edad de la persona de cada marca como rango sugerido.

> [!bug] Por qué Clavos no entregaba (resuelto: cambio el 23-09 ~18:15, primera impresión a las 18:22)
> A las 18:13, **1 h 40 min después de abrirlo igual que Mantecas**, Clavos seguía en **0 impresiones**. Ya no quedaban diferencias de públicos ni de creativos entre las dos campañas: la única era el presupuesto.
> - Meta pide como mínimo **USD 5 por día y por conjunto** cuando se optimiza por conversaciones de WhatsApp (en esta cuenta: USD 1 por impresiones, USD 5 para eventos frecuentes, USD 40 para eventos poco frecuentes).
> - Cada conjunto de Clavos tenía USD 12 para 7,5 días, o sea **USD 1,6 por día**. El API igual lo acepta y deja todo `ACTIVE`, pero Meta no lo entrega.
> - Mantecas funciona porque su presupuesto es de campaña: USD 40 son unos **USD 5,3 por día**.
>
> **Cambio:** Clavos pasó a presupuesto de campaña de **USD 60** (unos USD 8 por día), con un **piso de USD 8 por unidad** (`lifetime_min_spend_target`). El total y la fecha de fin no cambiaron. Antes de aplicarlo se validó por API sin ejecutar (`execution_options: validate_only`).

Presupuesto **de por vida con fecha de fin** en vez de diario: el total nunca pasa de USD 100 aunque se activen tarde. Meta reparte lo que queda entre los días que faltan.

## Las 10 unidades

### Clavos · USD 12 cada uno

| Unidad | Contado | Cuota ref. | Edad de la persona | Persona usada | Conjunto |
|---|---|---|---|---|---|
| Mercedes-Benz GLC 200 4MATIC 2023 · negro | USD 52.000 | Gs. 7.800.000 | 35-54 | [[Comprador Renew]] (no hay persona Mercedes) | `120250602053440465` |
| Mercedes-Benz GLC 220d 2017 · blanco | USD 27.000 | Gs. 3.900.000 | 35-54 | [[Comprador Renew]] | `120250602060660465` |
| Peugeot 2008 Active 1.6 2020 · rojo | USD 7.000 | Gs. 1.100.000 | 25-44 | [[Renew Peugeot]] | `120250602066020465` |
| Ford Territory Titanium 2023 · blanco | USD 19.500 | Gs. 2.800.000 | 35-54 | [[Renew Ford]] | `120250602070660465` |
| Hyundai Tucson GL 2.0 2022 · azul | USD 22.000 | Gs. 3.200.000 | 35-54 | [[Renew Hyundai]] | `120250602074990465` |

### Mantecas · USD 40 entre las cinco

| Unidad | Contado | Cuota ref. | Edad de la persona | Persona usada | Conjunto |
|---|---|---|---|---|---|
| Changan Uni-K AWD 2023 · blanco | USD 26.000 | Gs. 3.800.000 | 35-54 | [[Comprador Renew]] (no hay persona Changan) | `120250602078650465` |
| Fiat Fastback Limited 2024 · gris | USD 18.000 | Gs. 2.600.000 | 35-64 | [[Renew Fiat]] | `120250602081700465` |
| GWM H6 PHEV 4WD 2024 · gris | USD 26.500 | Gs. 3.800.000 | 25-44 | [[Renew GWM]] | `120250602083930465` |
| Jetour X70 GLX 2023 · rojo | USD 17.500 | Gs. 2.500.000 | 25-44 | [[Renew Jetour]] | `120250602085670465` |
| Zeekr X Flagship 2025 · verde | USD 35.000 | Gs. 5.000.000 | 35-54 | [[Comprador Renew]] (no hay persona Zeekr en usados) | `120250602087980465` |

La clasificación cierra con el stock del ERP: **los cinco clavos están publicados por debajo de su precio de lista** (el GLC 220d, USD 9.000 abajo) y las mantecas van a lista.

> [!warning] Revisar antes de activar
> Cruzando las gráficas con el stock de usados (archivo del 11-09):
> - **Jetour X70 GLX:** la gráfica dice **2023**; en stock el X70 GLX rojo figura **2022** (lista USD 18.500). Probablemente es el mismo auto con el año mal.
> - **Fiat Fastback:** la gráfica dice **USD 18.000**; la lista del stock es **USD 17.000**. Es la única gráfica más cara que la lista.
> - **Peugeot 2008 a USD 7.000:** parece bajo, pero cierra: la lista es USD 8.990. Está bien.
> - El stock es del 11-09: confirmar que las 10 siguen disponibles.

## Públicos (ninguno usa datos personales)

| Público | ID | Qué es |
|---|---|---|
| Interacción Instagram 365d | `120250602045370465` | interactuó con el IG de Renew en el último año |
| Interacción Facebook 365d | `120250602046630465` | interactuó con la página de Renew |
| Web 180d | `120250602047980465` | visitó el sitio (píxel **Renew Paraguay**, el único que dispara). Reemplaza al viejo "RENEW \| Público Web", que Meta marca chico y desactualizado |
| Similar 1 % PY ← Instagram | `120250602048710465` | lookalike |
| Similar 1 % PY ← Facebook | `120250602050120465` | lookalike |
| Similar 1 % PY ← Web | `120250602051430465` | lookalike |

**Desde el 23-09 a las 16:35** las dos campañas van con **Advantage+ abierto**, igual que LEADS 2026 - VENTAS WHATSAPP. Mantecas se abrió a las 15:45 y entregó a los 30 minutos (349 impresiones y la primera conversación de WhatsApp a las 16:30). Clavos conservó los seis públicos sin la edad sugerida y siguió en cero 45 minutos, así que se abrió igual.

> [!info] Los públicos quedan listos para la próxima
> Los seis públicos se llenaron (Instagram 23-27 mil, Facebook 14-17 mil, web 3,1-3,6 mil y cada similar 34-43 mil). Con USD 12 por unidad no alcanzaron para que Meta entregue; Renault IA los usa con USD 9-11 **por día** por conjunto y sí entrega. Usarlos en la próxima campaña de Renew con más presupuesto por conjunto.

Historia: **desde las 15:45** los seis públicos iban solo en **Clavos**, como sugerencia de Advantage+ (Meta arranca por ahí y se abre si encuentra gente mejor). **Mantecas** quedó con Advantage+ abierto, igual que LEADS 2026 - VENTAS WHATSAPP.

> [!bug] Por qué se cambió la segmentación
> Una hora después de aprobados, los 10 anuncios seguían en **0 impresiones**, con la cuenta entregando normal. Lo único que tenían y no tenían las configuraciones que sí entregan (la campaña de referencia y Renault IA) era la **edad de la persona como sugerencia** (`age_range`). Se sacó de los diez conjuntos. Clavos conserva los públicos y Mantecas se abrió del todo, así el cambio también dice cuál era la traba. Detalle técnico: para editar un conjunto con Advantage+ y públicos propios, Meta exige mandar `targeting_relaxation_types` encendido; sin eso rechaza cualquier edición.

> [!info] La base de compradores no se pudo armar
> Solo **32 de las 501 ventas** de Renew en el ERP tienen teléfono o mail, y Meta pide al menos 100 personas para un público de clientes. Para tenerla hace falta exportar de Bitrix los negocios ganados de Renew con su teléfono. Además, subirla es mandar datos personales de clientes a Meta (van cifrados, pero salen de la empresa): **necesita el OK explícito de Carlos** antes de hacerse.

## Los anuncios

Una imagen por anuncio, la **4:5** armada desde cada gráfica sin recortar nada (la gráfica es vertical y así queda casi entera). Mismo formato que los anuncios de WhatsApp que ya andan en la cuenta (el JETOUR X90). Fuente: `data/fuentes/creatividades/renew_2026-09/`.

> [!bug] Lo que falló el 23-09 y cómo se arregló
> La primera versión usaba una pieza por ubicación (9:16, 4:5 y 1:1, con `asset_feed_spec`). El API la aceptó y los anuncios quedaron `ACTIVE`, pero el editor de Ads Manager los mostraba rotos — *Selecciona una imagen* (#1487212), *falta el título para destino Messenger* (#2016052), *no se pudo analizar la llamada a la acción* (#1373054) — y no entregaban. La señal por API: el creativo no tenía `call_to_action_type`. Se cambió el creativo de los 10 anuncios al formato `link_data` de una imagen (conservan su ID). Quedan con `object_type: SHARE` y botón `WHATSAPP_MESSAGE`, igual que la referencia, y las vistas previas de feed, Instagram e historias renderizan. **Para anuncios de WhatsApp en esta cuenta: una imagen por anuncio, no pieza por ubicación.**

Botón **Enviar mensaje por WhatsApp**. El chat abre con un saludo precargado que dice la unidad y el precio, por ejemplo *"¡Hola! Quiero más información del Mercedes-Benz GLC 200 4MATIC 2023 (USD 52.000)."* Así el asesor sabe desde el primer mensaje qué auto consulta, y se puede medir qué unidad genera más consultas.

Texto con el formato de los anuncios que ya corren: ficha, precio contado y cuota referencial, respaldo Santa Rosa, retoma, financiación, la leyenda de la cuota y la dirección de Mariscal López. Solo datos de la gráfica y del stock; nada de kilometraje ni equipamiento que no esté confirmado.

## Qué mirar

- **Costo por conversación** por unidad. Referencia de la cuenta: USD 0,32 (contado) a 1,54.
- **Qué clavo no genera consultas** con su piso de USD 8: es la señal de que el problema no es la pauta sino el precio o la unidad.
- **Cuántas conversaciones terminan en venta**: eso lo sabe el equipo de Renew por WhatsApp; no llega solo a Meta.

---
Script: `scripts/pauta_renew_ia_2026_09.py` (idempotente) · estado: `output/pauta_renew_ia_2026-09.json` · relacionado: [[Comprador Renew]] · [[Renew]]
