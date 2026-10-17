---
type: reunion-preparacion
proyecto: agencia-ia
fecha: 2026-10-14
updated: 2026-10-09
tags: [sistema, agencia-ia, costos, organigrama]
---
# 🤖 Agencia IA — Costos y organigrama para la reunión del miércoles 14/10, 11:00

> Lo que se pidió en la [[🤖 Agencia IA — Reunión 2026-10-09]]: el **mapa de costos** (servidor, plan, usuarios y total) y el **organigrama por actores**.
> Fuentes con enlace de cada precio: `~/Escritorio/AGENCIA IA/docs/investigacion/2026-10-09-costos-y-herramientas.md` (investigado el 9/10/2026).
> Especificación: [[🤖 Agencia IA — Especificación]].

## 1. Mapa de costos

### Una sola vez

| Ítem | Opción | USD | Estado del dato |
|---|---|---|---|
| Servidor de IA para marketing | **NVIDIA DGX Spark 128 GB** | **6.950** | Referencia de prensa del 2/10/2026. El precio de lista anterior era 4.699 y el de lanzamiento 3.999: **subió**. Confirmar en el Marketplace de NVIDIA, que no abrió |
| Traerlo a Paraguay | Compra en EE. UU. + casilla (flete, seguro e IVA 10 %) | ~750 a 1.350 | **Estimación propia**, sin cotización. Paraguay Courier no publica tarifa para computadoras |
| *Alternativa* | Mac Studio M5 Max 128 GB | ~4.799 | No verificado en Apple |
| *Alternativa barata* | Framework Desktop 128 GB (AMD Ryzen AI Max+ 395) | 3.449 | Agotado, en preventa |
| NAS para archivos | — | **a cotizar** | No se investigó todavía |
| Licencias de diseño y video | GIMP, Krita, Inkscape, Kdenlive, DaVinci Resolve gratis, Scribus | **0** | Libres |
| *Opcional* | DaVinci Resolve Studio | 295 por licencia | Solo si hace falta lo pago |

> [!note] Ojo con el DGX Spark
> En la reunión se habló de USD 5.000–5.500. Hoy está en **USD 6.950** (más importación). Por la mitad o menos hay equipos con la misma memoria (128 GB unificada) que alcanzan para correr modelos locales, aunque son más lentos en IA. Antes de comprar conviene decidir **qué va a correr ahí**: clonador de voz, video, MiroFish, modelos locales. Con eso se elige el equipo.

### Por mes

| Ítem | Opción | USD por mes | Estado del dato |
|---|---|---|---|
| Claude para el equipo | **Team**, 8 asientos estándar, pago anual | **160** | Verificado (USD 20 por asiento con pago anual, 25 con pago mensual; mínimo 2) |
| Claude para quien lo usa mucho | Asiento **premium** de Team, pago anual | 100 por asiento | Verificado |
| Claude para la app | API: planes, copies y propuestas de campaña | **se mide en el piloto** | Pocos pedidos por marca al mes. Lo registra la app para la prueba de costo |
| Jev (control de la ley) | Vercel AI Gateway | ~0 | Hoy entra en el crédito gratis de Vercel |
| Servidor y luz | En la red propia | — | Sin dato |

> [!warning] Corrección a lo que se dijo en la reunión
> - **Pro cuesta USD 20, no 100.**
> - USD 100 y 200 son los planes **Max** individuales, que se pagan solo mes a mes.
> - Los "USD 20 por usuario" corresponden al asiento **Team** estándar con pago anual. Team trae administración de usuarios. Max es por persona.
> - Claude Code viene en todos los planes pagos.

### Ejemplo de total para arrancar

| Escenario | Una sola vez | Por mes |
|---|---|---|
| **Con DGX Spark** | ~7.700 a 8.300 (equipo + traída) + NAS | 160 (Team, 8 asientos) + API de la app |
| **Con equipo alternativo** | ~3.500 a 4.800 + traída + NAS | 160 + API de la app |
| **Sin equipo nuevo** (la versión 1 corre en SRPY186) | 0 | 160 + API de la app |

La versión 1 de la app **no necesita el equipo nuevo**: Claude y Jev son servicios externos, y Chromium y la base son livianos. El equipo hace falta para lo pesado (voz, video, simulación y modelos locales).

### Contra qué se compara

**Falta el dato principal: cuánto se paga hoy a las agencias.** Sale del relevamiento.
- La cifra de "más de 40 millones" que se mencionó no está confirmada.
- Para cerrar el mapa hace falta el **fee mensual de las agencias de JAC y Soueast** y, si se suma, el de Mitsubishi.
- Con ese dato se calcula en cuántos meses se paga el equipo.

## 2. Organigrama por actores

No es un organigrama de jerarquía sino de **quién interviene según el tipo de pedido**.

| Pedido | 1 | 2 | 3 | 4 | Si el brand rechaza |
|---|---|---|---|---|---|
| **Flyer** | IA arma con fotos reales | **Diseñador** (Santi o Marcos): aprueba, pide cambio o sube su versión | **Andrea**: control final | **Brand manager**: OK | Vuelve al diseñador |
| **Plan de posteos / copies** | IA arma el mes | **Contenido**: aprueba o corrige | **Andrea** | **Brand manager** → se programa en Meta | Vuelve a contenido |
| **Campaña** | IA arma la propuesta 360 | **Andrea** con el equipo la trabaja | **Brand manager** la conoce y aprueba | Las piezas pasan a ser pedidos de flyer y de posteos | Vuelve a Andrea |
| **Pauta** (después de la versión 1) | IA propone campañas pausadas | **Evelyn**: ajusta y activa | **Andrea** | Brand | Vuelve a Evelyn |

- **Coordinación de marketing:** ve todo en el panel, pero **no reparte pedidos** ni revisa pieza por pieza.
- **Croman:** administra la herramienta (marcas, precios autorizados, quién tiene qué oficio) y la infraestructura.
- **Filmación** (vendedores, ferias, eventos): la sigue haciendo el equipo; la IA ayuda a editar después de la versión 1.

## 3. Herramientas abiertas para el equipo

| Reemplaza a | Opción libre | Diferencias honestas |
|---|---|---|
| Photoshop | GIMP 3.2, Krita 5.3 | Abren PSD con limitaciones. GIMP no trabaja bien en CMYK para imprenta |
| Illustrator | Inkscape | Bien para vectores; menos plugins |
| Premiere | Kdenlive o DaVinci Resolve (gratis) | Resolve es de nivel profesional; Kdenlive es más liviano |
| After Effects | DaVinci Resolve (Fusion) | Otra forma de trabajar; lleva aprendizaje |
| InDesign | Scribus | Para folletos y catálogos; más tosco |

Hay editores "con IA" de 2025–2026 que se anuncian como clones de Photoshop o Premiere. Todavía son muy nuevos para el trabajo diario: **no se recomiendan para el piloto**.

## 4. MiroFish (la simulación de público)

- **Existe:** `github.com/666ghj/MiroFish`, código abierto con licencia AGPL-3.0 y muy popular (unas 77 mil estrellas).
- **La versión oficial necesita servicios externos** (Zep Cloud y una API de IA). No corre 100 % local.
- **Hay una copia local** que usa Ollama: `MiroFish-Offline`. Es menos mantenida (sin cambios desde marzo) y pide una placa de 10 a 24 GB.
- **Alternativa de Microsoft:** TinyTroupe (licencia MIT).
- **Recomendación:** probarlo como experimento aparte con una campaña real ya hecha, para ver si "predice" lo que pasó. Recién ahí decidir si entra en Estrategia.

## 5. Para decidir el miércoles

1. Si se compra el equipo para marketing y cuál: el DGX Spark subió a USD 6.950, y hay alternativas por la mitad.
2. Plan de Claude: **Team** con 8 asientos (USD 160 por mes) o algunos premium.
3. Quién pasa el **fee de las agencias** de JAC y Soueast para cerrar el mapa de costos.
4. Confirmar el organigrama: ¿coordinación aprueba algo, o solo mira?
5. Kit de prensa con fotos limpias de JAC y Soueast.
