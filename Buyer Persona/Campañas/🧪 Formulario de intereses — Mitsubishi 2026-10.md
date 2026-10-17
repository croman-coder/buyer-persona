---
type: campaña
marca: Mitsubishi
created: 2026-10-16
estado: formulario activo; campaña, conjunto y anuncio creados EN PAUSA (esperando OK para activar)
tags: [mitsubishi, meta-ads, formulario, intereses, eventos, buyer-persona]
---
# 🧪 Formulario de intereses — Mitsubishi (octubre 2026)

> [!info] Para qué
> El brand de Mitsubishi pidió saber **qué les gusta a quienes se interesan por la marca** (deporte, música, comunidad) para **mapear la presencia de marca y elegir eventos** ([[🎧 Feedback Marketing 2026-10-16]]). Meta ya no entrega los intereses declarados de una audiencia y ningún formulario de Mitsubishi los preguntaba: este formulario los pregunta.

## Estado (16-10-2026)

| | |
|---|---|
| Formulario | **SRPY - MITSUBISHI - Buyer Persona - 2026-10 - Intereses y comunidad** · ID `4742535782699414` · página Mitsubishi Motors Paraguay (`103344941701936`) |
| Estado del formulario | **Activo**, pero sin ningún anuncio activo: no recoge nada. Leads: 0 |
| Campaña | `120253009938340663` · «MITSUBISHI \| Buyer Persona \| Intereses y comunidad \| Leads \| 2026-10» · **en pausa** |
| Conjunto | `120253009938750663` · **en pausa** · **USD 15 por día** (propuesta) · Paraguay, 25 a 55 años |
| Anuncio | `120253009939380663` · «Pickup 9:16» · **en pausa** · Meta lo revisó sin observaciones |
| Cuenta | Mitsubishi Paraguay (`act_506680188632635`). **No se tocó ninguna campaña ni anuncio de la agencia** |

### Cómo está armado el anuncio

- **Segmentación por vehículo, no por pasatiempos:** camioneta, vehículo utilitario deportivo y Mitsubishi Montero. Si se apuntara a «fans del fútbol», las respuestas dirían «fútbol» por cómo se segmentó. Sin ampliación automática del público.
- **Excluye a quienes ya dejaron sus datos:** los mismos públicos que excluye la campaña de L200 del Buyer Persona (leads de L200 enviados, formularios de Montero abiertos y no enviados, y leads del sitio web).
- **Lugares:** Stories y Reels de Facebook e Instagram, porque la imagen es vertical.
- **Imagen:** una L200 en un camino de tierra, de las que ya están en la cuenta, sin precio, con el mensaje «Contanos qué te gusta» escrito encima. En Stories no se ve el texto del anuncio, solo la imagen y el botón, y sin el mensaje en la imagen nadie sabría de qué se trata.
- **Texto:** «Contanos qué te gusta y conocé más de Mitsubishi. Respondé unas preguntas cortas y un asesor de Santa Rosa te contacta.» Título «Comunidad Mitsubishi», botón «Más información». Sin precios, ofertas ni plazos.

## Qué pregunta

| Pregunta | Opciones |
|---|---|
| ¿Qué te gusta hacer en tu tiempo libre? | Fútbol y otros deportes · Automovilismo y motos · Aventura, 4x4 y camping · Pesca y naturaleza · Música y shows · Familia y paseos · Gastronomía y salidas · Otro |
| ¿Participás de algún club o comunidad? | Club de autos, motos o 4x4 · Club deportivo · Comunidad o grupo social · Ninguno por ahora |
| ¿Cuándo pensás comprar? | Este mes · En los próximos 3 meses · Solo estoy cotizando |
| Contacto | Nombre completo, teléfono, email y ciudad |

- **Solo gustos y clubes.** Nada sensible (religión, salud, política, ingresos): Meta no lo permite en formularios y la ley de datos personales tampoco.
- **«¿Cuándo pensás comprar?»** va para que el asesor sepa a quién llamar primero; sale igual que en los formularios de siempre de Mitsubishi.
- **Sin precios ni promesas** en la tarjeta de contexto ni en la pantalla de gracias. La política de privacidad es la de `mitsubishi-motors.com.py`, como en los otros formularios.
- Sigue la misma estructura que los formularios «SRPY … Buyer Persona 2026-10» de la página: idioma es_LA y modo «mayor intención» (agrega un paso de revisión antes de enviar, para que lleguen menos leads pero más serios).

## Antes de activarlo (decisiones que faltan)

1. **El OK de Croman y de la brand manager (Cecilia).** Para activar: en Ads Manager, cuenta de Mitsubishi, encender la campaña, el conjunto y el anuncio de arriba.
2. **Superposición con la agencia.** La cuenta ya tiene campañas con intereses de vehículo parecidos (Montero general, USD 66 por día) y la prueba de L200. Con USD 15 por día el efecto sería chico, pero compiten en la misma subasta: conviene avisarle a la agencia (Merco) antes de encender.
3. **El presupuesto.** USD 15 por día es una propuesta. Para llegar a unas 100 respuestas en 4 semanas alcanza si el costo por respuesta queda cerca de USD 4 a 5; el formulario es más largo que los de siempre y en modo «mayor intención», así que puede salir más caro.
4. **La imagen.** Es provisoria. Una pickup en el campo puede inclinar las respuestas hacia «aventura y 4x4». Si marketing tiene una pieza propia de la marca, se cambia en el anuncio sin tocar nada más.
5. **Leer a las 3 o 4 semanas**, o con al menos 100 respuestas, lo que llegue después. Antes, los porcentajes engañan.

## Cómo se leen las respuestas (sin datos personales)

- Cada respuesta llega al lead de Bitrix como cualquier otro. Para el Buyer Persona solo hace falta **contar**: cuántos eligieron cada opción, por ciudad y por modelo de interés.
- Eso alimenta el bloque **«🎪 Para eventos y presencia de marca»** de la ficha de Mitsubishi: dónde están y **qué les gusta**, que hoy dice «no se mide».
- Nombres, teléfonos y mails no se copian a ningún archivo del vault.

## Qué falta

- [ ] **OK de Croman y de la brand** para encender la campaña (el formulario y el anuncio ya están armados).
- [ ] **Agenda de eventos** del brand (ciudades y fechas), para cruzarla con las ciudades de los leads.
- [ ] Armar el conteo de respuestas en el pipeline cuando lleguen las primeras.

Código: `scripts/crear_formulario_intereses_mmc.py` (formulario) y `scripts/pauta_mmc_intereses_2026_10.py` (campaña, conjunto, imagen y anuncio, todo en pausa) · pruebas: `tests/test_formulario_intereses.py` y `tests/test_pauta_intereses.py`.
