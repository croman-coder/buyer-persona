---
type: recurso
proyecto: agencia-ia
fecha: 2026-10-15
updated: 2026-10-15
tags: [sistema, agencia-ia, recurso, react, animaciones, video, mobile]
---
# React Bits: recurso para la Agencia IA

> Pedido de Croman el 15/10/2026: tener el GitHub de React Bits como recurso de la Agencia. Está descargado en `recursos/react-bits/` (fuera de git), listo para consultar y copiar componentes.

## Qué es

Una biblioteca de **más de 215 componentes animados para React** (efectos de texto, fondos, interacciones, tarjetas, menús), de código abierto y gratis.

| Dato | Valor |
|---|---|
| Repositorio | <https://github.com/DavidHDev/react-bits> (sitio: reactbits.dev) |
| Popularidad | ~49.000 estrellas, ~2.400 bifurcaciones, con cambios el mismo 15/10/2026 |
| Versión descargada | commit `382dc89` del 15/10/2026 |
| Dónde está | `recursos/react-bits/` (19 MB: solo `src/ts-tailwind`, `src/ts-default`, `src/constants` y `src/docs`; los 351 MB de demos de `public/` no se bajaron) |
| Variantes | 4 por componente: JavaScript o TypeScript, con CSS o con Tailwind. Se usa `src/ts-tailwind` (la de la Agencia es TypeScript) |
| Cómo se usa | **Se copia el archivo del componente** a la app (no hay un paquete que instalar). Los textos usan la biblioteca `motion`; los fondos de WebGL suelen usar `three`, `ogl` o `gsap`: se ve en el `import` de cada archivo |

## Licencia: MIT + Commons Clause

- **Se puede** usar, copiar y modificar, también en uso comercial, **dentro de una aplicación, sitio o producto propio**. La Agencia IA es una herramienta interna de Santa Rosa: entra sin problema.
- **No se puede** vender, sublicenciar ni redistribuir los componentes en sí, ni solos ni en un paquete ni portados a otra biblioteca.
- Hay que **conservar el aviso de copyright** de David Haz en lo que se copie.
- Tiene una versión **Pro de pago**. No hace falta: lo gratis alcanza para lo que sigue.

## Qué le sirve a la Agencia

| Categoría | Cantidad | Ejemplos | Para qué |
|---|---:|---|---|
| Text Animations | 33 | BlurText, SplitText, ShinyText, GradientText, CountUp, TextType, DecryptedText, RotatingText | Títulos y frases animadas de los **reels y las historias** |
| Backgrounds | 64 | Aurora, Silk, Particles, GradientWaves, LightRays, Iridescence, Grainient, Waves | **Fondos** de piezas de video y, en una captura fija, fondos de flyers (con la foto real del auto encima) |
| Animations | 38 | GlareHover, ClickSpark, Magnet, StarBorder, ImageTrail | Detalles del panel y de las presentaciones |
| Components | 48 | Dock, SpotlightCard, ProfileCard, Stack, Carousel, MagicBento | Pantallas del panel y portadas |
| Micro | 34 | HoldButton, SwipeToast, SpringCheck, StatusMark | Botones y avisos pequeños del panel |

**Dos usos concretos**

1. **Video como pieza (pedido el 14/10 y en la reunión del 15/10).** La Agencia ya arma flyers abriendo una página en Chromium y sacándole una captura. El mismo camino sirve para video: abrir la página con un efecto de texto o de fondo, **capturar cuadros** y unirlos con ffmpeg en un MP4 vertical de 1080×1920. Sale de las fotos buenas de la marca más texto y fondos animados, sin IA generativa de video. **Todavía no se probó**: es la prueba que sigue.
2. **El panel.** La entrada y las portadas pueden usar un fondo o un efecto de texto. Con las reglas de `design.md`: movimiento breve y con sentido, `prefers-reduced-motion` obligatorio y colores solo de los tokens.

## Qué no se hizo y qué cuidar

- **No se instaló ni se ejecutó nada** del repositorio (ni `npm install` ni sus scripts). Es código de terceros: antes de copiar un componente a la app, leerlo, y fijar de qué commit salió.
- Los fondos de WebGL pesan en equipos flojos y en celulares: probar antes de ponerlos en el panel.
- Las reglas de la Agencia siguen mandando: la IA no dibuja el auto, ningún texto nombra a la competencia, y los colores y tipografías son los de cada marca.
- Hay un servidor MCP de React Bits para que un agente consulte los componentes (reactbits.dev/get-started/mcp). **No está configurado.**

## Cómo ver un componente

```bash
ls recursos/react-bits/src/ts-tailwind/TextAnimations      # una carpeta por componente
sed -n 1,80p recursos/react-bits/src/ts-tailwind/TextAnimations/BlurText/BlurText.tsx
```

Para actualizarlo: `git -C recursos/react-bits pull --depth 1`.

## Evaluación para el panel y el celular (15/10/2026)

**Cómo está hoy.** El panel ya tiene un sistema de movimiento propio: entrada escalonada de las listas, barras de avance que se llenan, un barrido mientras la IA trabaja, esqueletos de carga y un pulso en el paso que toca. Todo respeta «reducir movimiento». Medido en producción, en la entrada, con un Chrome de celular simulado (4G rápida y procesador 4 veces más lento): **LCP de 0,6 segundos y CLS 0**; carga 12 archivos (una tipografía, cinco de JavaScript) y unos 148 kB de JavaScript en total.

**Qué costaría traer React Bits tal cual.** Sus componentes dependen de `motion` (~34 kB), `gsap` (~27 kB), `ogl` (~14 kB) y, en varios fondos, `three` (~170 kB): el panel pasaría de unos 148 kB a entre 180 y 320 kB, y los fondos de WebGL gastan batería y procesador justo en los celulares de quienes aprueban piezas. **Decisión: no se instalan esas librerías en el panel.**

**Lo que sí se hace.**
- Se toma la *idea* de un efecto y se escribe propio, liviano y sin dependencias. Hecho: `Contador` (el CountUp de React Bits) en las tarjetas de resumen de Pedidos: 30 líneas, respeta «reducir movimiento» y el lector de pantalla lee el valor final.
- Los efectos pesados (fondos de WebGL, texto animado) se usan **en el servidor, para las piezas de video**, donde no cargan el celular de nadie.

**Lo que se vio a 360 px y falta decidir** (no se tocó: la portada y los textos de «muestras» están en manos de otra sesión):
1. El aviso de «muestras de diseño» ocupa unos 170 px arriba en cada pantalla: en celular conviene una versión de una línea con «ver más».
2. En la pieza, «Qué podés hacer» queda a una pantalla y media del principio: una barra fija «Decidir» abajo lo acercaría al pulgar.
3. Cada tarjeta lleva 3 o 4 etiquetas que se parten en dos renglones («JAC · Flyer · Muestra · JS4»): se puede dejar la marca y el modelo, y mover el resto a una segunda línea más tenue.

## Prueba de video (15/10/2026): sí se puede

Un MP4 vertical de 9,5 segundos armado con componentes de React Bits y una foto buena del Soueast S07: `recursos/prueba-video/reel-soueast-s07-muestra.mp4` (1080×1920, 2,5 MB). Es una **muestra técnica**, no una pieza final.

| Qué | Con qué |
|---|---|
| Fondo | Aurora (WebGL2), con colores de ejemplo |
| Titular | BlurText, con el texto del flyer real: «Inteligencia urbana, con carácter.» |
| Pie | ShinyText y el logo de Santa Rosa |
| Auto | `car-PGray.jpg` de la biblioteca de fotos buenas, con un zoom lento |
| Captura | Chromium sin pantalla (Playwright) y ffmpeg a H.264, 25 cuadros por segundo |
| Dependencias | Solo React, Vite y `motion`. Corre **en el servidor**, nunca en el celular de nadie |

**Medición** (sin tarjeta gráfica, WebGL por software): a 1080×1920 el fondo corría a 13–17 cuadros por segundo; dibujándolo a media resolución (es un degradado suave) subió a **31**. La grabación de Playwright es de 25 cuadros por segundo.

**Lo que falta para que sea una pieza de verdad**
1. **Dibujar cuadro a cuadro** (avanzar el tiempo a mano) para sacar 30 o 60 cuadros sin depender de qué tan rápido es el equipo.
2. **Un guion de varias escenas**: hoy hay unos 3 segundos de movimiento y después casi nada. Faltan transiciones y subtítulos.
3. **Música libre** (hoy no tiene audio) y ritmo.
4. **Plantillas por marca**: colores y tipografía de cada una, y tres formatos (reel, cuadrado y horizontal).
5. **Reglas de siempre**: el titular lo escribe la IA y pasa por el mismo revisor (nada de competencia); las tres aprobaciones como cualquier pieza.
6. **Un tipo de pedido «Video»** en el panel, con el trabajo corriendo en el servidor como el de los flyers.

**Para repetirlo:** `recursos/prueba-video/proyecto/` (React + Vite). `npm install --ignore-scripts`, levantar con `npx vite`, y `node capturar.mjs` graba el `.webm`; ffmpeg lo pasa a MP4 recortando el arranque.

## Próximo paso sugerido

Dibujar cuadro a cuadro, escribir un guion de 3 o 4 escenas con música libre, y probarlo con JAC y Soueast. Con eso se decide si «Video» entra como tipo de pedido.

Relacionado: [[🤖 Agencia IA — Especificación]] · [[🤖 Agencia IA — Reunión 2026-10-15]]
