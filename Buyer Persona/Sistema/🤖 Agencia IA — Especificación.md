---
type: especificacion
proyecto: agencia-ia
estado: versión 1 aprobada en diseño, pendiente de revisión del documento
updated: 2026-10-14
tags: [sistema, agencia-ia, posteos, flyers, campaña, meta, especificacion]
---
# 🤖 Agencia IA — Especificación de la versión 1 (piloto JAC y Soueast)

> Herramienta propia que reemplaza de a una a las **agencias externas** de las 11 marcas durante 2027. **No reemplaza al equipo**: diseñadores, contenido y pauta usan la IA de apoyo. La IA propone; las personas aprueban.
> Documento completo: `~/Escritorio/AGENCIA IA/docs/superpowers/specs/2026-10-09-agencia-ia-version-1-design.md` (repo local, commit `bdefc59`). Reemplaza a la especificación de posteos de esa misma mañana.
> Sale de la [[🤖 Agencia IA — Reunión 2026-10-09]].

> [!warning] Ley de Paraguay
> Ningún texto público nombra ni se compara con la competencia. El revisor lo controla con Jev y con el filtro del chat de marcas, incluso en las versiones que sube el diseñador.

## Decisiones

| Tema | Elegido |
|---|---|
| Qué se recorta | Las agencias externas, no el equipo interno |
| Líder | Andrea |
| Piloto | **JAC y Soueast**, cada una con su campaña desde el **1/1/2027**, trabajada en nov–dic. GWM sigue con su agencia; Mitsubishi y Renault quedan a decisión de Agustín |
| Versión 1 | Tablero de pedidos + Contenido + Diseño + propuesta de campaña. Pauta y video, después |
| Pedidos | Tablero propio en `agencia.santarosa.lat`, con bandeja por actor y avisos por correo |
| Recorrido | IA → diseñador o contenido → Andrea → brand. **El rechazo del brand vuelve al diseñador**, no a la IA |
| Corrección | El diseñador le pide el cambio a la IA **o** sube su versión retocada, que también pasa por el revisor |
| Imágenes | Solo fotos reales que el equipo marcó como buenas. La IA nunca dibuja el auto |
| Publicación | Lo aprobado se programa en Meta. Si el permiso no llega a tiempo, se descarga y se sube a mano |
| Éxito | Las 5 pruebas en 3 meses: costo, velocidad, resultados, calidad, coherencia |

## Calendario

| Período | Qué se hace |
|---|---|
| Hasta el 14/10 | Especificación, mapa de costos y organigrama para la reunión del **miércoles 14/10 a las 11:00** |
| 15/10 – 31/10 | Núcleo: marcas, fotos, flyers, revisor, planificador y propuesta de campaña. Se pide el permiso de Meta |
| 1/11 – 20/11 | Panel: tablero, aprobaciones, subir versión, campaña → pedidos, las 5 pruebas |
| 21/11 – 30/11 | Ensayo con pedidos reales, sin publicar. Capacitación |
| Diciembre | Producción en Coolify. Las campañas del Q1 se trabajan en la herramienta |
| 1/1/2027 | Salen JAC y Soueast |

## Avance (14/10/2026)

Adelantado respecto del calendario: el núcleo y el panel (previstos para el 15/10–20/11) ya están hechos y probados en local.

| Qué | Estado |
|---|---|
| Plan 1 — núcleo (marcas, fotos, flyers, revisor, planificador, propuesta de campaña) | ✅ hecho |
| Plan 2 — panel web (bandejas por rol, aprobación en tres pasos, campañas, tablero de las 5 pruebas, avisos) | ✅ mergeado a `main` |
| Diseño del panel: sistema visual propio, isologo **SR** de Santa Rosa, barra de avance por pieza y por pedido, «N de 5 pruebas con datos», movimiento con sentido | ✅ rama `feat/plan-3-panel`, sistema fijado en `design.md` del repo |
| Plan 3 — **Fotos en el panel** (pantalla para marcar fotos + selector y subida de la foto de entrega en el pedido nuevo) | ✅ hecho y desplegado (15/10) |
| **Panel en producción** | ✅ **https://agencia.santarosa.lat** (Coolify, app `agencia-ia`, rama `feat/panel-carpetas`, se redespliega sola con cada push). 429 fotos y sus miniaturas ya están en el servidor |
| Plan 3 — publicación en Meta, pantalla de precios, despliegue en Coolify | ⬜ |

**Cuello de botella hoy:** hay 416 fotos pendientes de marcar y solo Soueast (11) y Leapmotor (3) tienen fotos buenas. Hasta que se marquen,
JAC, Jetour, JMEV, XPeng, Zeekr y Mitsubishi no pueden pedir un flyer con foto elegida por la IA. La pantalla **Fotos** ya está en producción para destrabarlo,
pero **solo marcan diseño y el líder**: en producción hoy solo hay dos administradores, así que falta darle esos oficios a quien corresponda (pantalla Oficios).

Pruebas del repo: 107 archivos, 2.781 pruebas en verde; prueba de humo del panel 23/23.

## Reunión del 15/10/2026

El equipo pidió un pedido guiado (tipo → subtipo, modelos múltiples o toda la marca, campos por tipo, Brief con sugerencias, referencias), que la IA razone el pedido antes de producir, un perfil de marca cargado una vez, el flujo con todos los actores (BTL, audiovisual) y una presentación corta de 9–10 diapositivas. Detalle y puntos a confirmar: [[🤖 Agencia IA — Reunión 2026-10-15]].

## Recursos

- [[🤖 Agencia IA — Recursos — React Bits]]: biblioteca de más de 215 componentes animados para React (texto, fondos, tarjetas). Descargada en `~/Escritorio/AGENCIA IA/recursos/react-bits`. Sirve para los reels y para el panel; licencia MIT + Commons Clause.

## Temas abiertos

- **Permiso de Meta** para publicar: se pide en octubre y puede tardar semanas.
- **Fotos limpias:** las grandes de la web de JAC son banners con texto impreso. Hay que pedir el kit de prensa.
- **Manuales de marca:** solo está el de Jetour.
- **Servidor de marketing aparte:** DGX Spark o alternativa, más un NAS. El precio sale de la investigación del 9/10.
- **"MiroFish"**, la simulación de público: queda fuera de la versión 1 hasta confirmar qué es.

Relacionado: [[💬 Chat de marcas — Especificación]] (comparte el login y la guardia por marca).
