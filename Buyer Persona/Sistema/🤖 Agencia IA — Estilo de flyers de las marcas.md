---
type: referencia-diseno
proyecto: agencia-ia
created: 2026-10-11
tags: [sistema, agencia-ia, diseno, redes]
---
# 🤖 Agencia IA — Estilo de flyers de las marcas (redes de Paraguay)

> Armado el 11/10/2026 mirando las **16 páginas oficiales** de Facebook e Instagram que maneja Santa Rosa (50 publicaciones por red, las 10 estáticas con más interacción y las 4 más recientes de cada una). Las hojas de contacto y los datos están en `~/Escritorio/AGENCIA IA/data/referencias-redes/` (fuera de git). Especificación: [[🤖 Agencia IA — Especificación]].

## Lo que tienen todas en común

| Rasgo | Qué se ve |
|---|---|
| Formato | **Vertical 4:5**. El mismo flyer sale en Facebook e Instagram |
| Estructura | Logo chico arriba o abajo, **foto del auto ocupando 60–80 %**, titular de **menos de 8 palabras** y la marca de Santa Rosa al pie |
| Santa Rosa | Casi todas llevan el sello **«MARCA \| SANTA ROSA»** (Soueast y Leapmotor arriba; Jetour, Mitsubishi y JMEV abajo) |
| Foto | Auto en escenario real (ruta, ciudad, atardecer), con degradado oscuro abajo para que se lea el texto |
| Pocas palabras | Un dato fuerte («280 km de autonomía», «891 HP», «hasta 7.500 kg») o una frase corta |

## El estilo de cada marca

| Marca | Cómo lo hace |
|---|---|
| **GWM** | Plantillas globales: fondo oscuro, nombre del modelo enorme y fino («TANK 700»), frase en mayúsculas en dos pesos, acento verde o celeste. Teasers negros («PRONTO LO VAS A CONOCER») |
| **Jetour** | Fotografía de aventura con colores intensos (atardecer naranja), nombre del modelo arriba, recuadros con interior y detalles, número gigante detrás del auto («891HP») |
| **Zeekr** | Minimalista: letra fina blanca sobre cielo, personas reales, casi sin texto. Preguntas («¿Qué tiene el 001 que otros no?») y cuenta regresiva |
| **Leapmotor** | Gente en la ciudad, tono cercano y en vos: «Spoiler: no usa combustible», «POV: pintó escapada el finde». Datos como «¿Sabías qué?» |
| **JMEV** | Fondo blanco limpio o ciudad; ahorro y autonomía con tablas de costo por ciudad |
| **Soueast** | Escenas cinematográficas, **frases cortas en inglés** («PARK. STEP OUT. ENJOY.»), el modelo en una pastilla abajo a la derecha |
| **Mitsubishi** | Rojo y negro, campañas con identidad local (la selección, nostalgia de los 80) y promos con precio («USD 5.000 menos»), cinta «ENTREGA INMEDIATA» |
| **JAC** | Degradado azul, camiones con su uso real, eventos con fecha, lugar y hora; «Mito / Realidad» para explicar el eléctrico |
| **Renault** | Blanco limpio, línea de color que sigue al auto (campaña Alpine y F1) |
| **Multimarcas (Fer)** | Fotos reales de **entregas** con moño: prueba social, la que más seguidores tiene |

## Qué rindió más (tasa de interacción sobre seguidores)

Todas las tasas son bajas (0,0 a 0,3 %). Arriba aparecen: **sorteos** (camiseta de la selección de Mitsubishi), **lanzamientos y teasers**, **foto de aventura con atardecer** (Jetour F700) y **eventos** (CADAM, test drive). Los flyers de datos y de rutina quedan abajo.

## Errores a no repetir

- Un flyer de Mitsubishi salió con un **enlace de Google Maps escrito en la imagen** («AFU»).
- Hay flyers con mucho texto chico (Koleos F1) que no se leen en el celular.
- Algunos precios («USD 5.000 menos») no pasan por una revisión: en la Agencia IA el revisor los compara contra los precios autorizados.

## Qué hacer para hacerlo mejor (plantillas por agregar a la Agencia IA)

1. **Sello de marca + Santa Rosa** en la franja de arriba, igual que ya hacen Soueast y Leapmotor.
2. **Titular de 6 palabras o menos** y el nombre del modelo en grande. El resto del texto, más chico.
3. Plantillas nuevas que hoy no tenemos: **evento** (fecha, lugar y hora con íconos), **teaser / cuenta regresiva**, **«¿Sabías qué?»**, **«Mito / Realidad»**, **sorteo** y **entrega** (foto real del cliente, con su permiso).
4. Un solo estilo fijo por marca, que ya es el de la tabla de arriba.
5. Comprobar siempre que la imagen no lleve enlaces ni texto accidental.

## Plantillas implementadas (11/10/2026)

Las seis plantillas del punto 3 ya existen en la Agencia IA (rama `feat/plantillas`): **evento**, **teaser / cuenta regresiva**, **«¿Sabías qué?»**, **«Mito / Realidad»**, **sorteo** y **entrega**. Se piden con `--plantilla` en `npm run pedido` (guía en `docs/uso-terminal.md` del proyecto). Los hechos reales (fechas, lugares, premios, clientes) los da el equipo y van tal cual a la lámina; la IA solo escribe titular, bajada y botón (y los datos de la ficha en «sabías» y «mito»). Un sorteo no sale sin bases y condiciones, ni una entrega sin el permiso del cliente. Probadas con Soueast S07 (rojo/naranja y Montserrat) y con una foto de JAC (rojo y Lato).

## Marcas configuradas (11/10/2026)

La Agencia IA ya tiene la ficha de las diez marcas con sello oficial: JAC, Soueast, GWM, Jetour, JMEV, Leapmotor, Mitsubishi, Renault, XPeng y Zeekr (Renew queda afuera: no tiene sello). Falta, para producir flyers de Mitsubishi, GWM y Renault, bajar fotos por modelo del Drive; los colores de GWM, JMEV, XPeng, Jetour, Leapmotor y Renault hay que confirmarlos con el manual de marca. Detalle en `docs/2026-10-11-marcas-configuradas.md` del proyecto `~/Escritorio/AGENCIA IA`.

