---
type: especificacion
proyecto: chat-marcas
estado: EN PRODUCCIÓN, abierto al público en jac.com.py el 2026-10-13 (prospectos reales a Bitrix)
updated: 2026-10-13
tags: [sistema, chat-marcas, jac, embeddings, especificacion]
---
# 💬 Chat de marcas — Especificación (piloto JAC)

> Chat dentro de las webs de marca que contesta con las **fichas técnicas oficiales** y convierte el interés de compra en un **prospecto de Bitrix**. Se administra desde un panel central. Empieza con **JAC** (jac.com.py).
> Documento completo: `~/Escritorio/CHAT MARCAS/docs/superpowers/specs/2026-10-08-chat-marcas-design.md` (repo local `chat-marcas`, commit `d1158c3`).

> [!warning] Ley de Paraguay
> El chat no nombra marcas ni modelos de la competencia ni compara: lo impiden las reglas, un filtro de salida y un examen con preguntas trampa.

## Decisiones (Croman, 2026-10-08)

| Tema | Elegido |
|---|---|
| Modelo que redacta | `gemma4-hermes` del servidor, **el mismo que ya tiene cargado el bot** (no suma memoria a la placa) |
| Marca piloto | JAC |
| Panel | Central, `chat.santarosa.lat/admin`, con el **login de los dashboards** (rol por marca) |
| Precios | **No da precios**: pide nombre, teléfono y sucursal y crea el prospecto |
| Enfoque | Servicio nuevo en Coolify, independiente de Botika |

## Cómo funciona

- **Burbuja:** una línea de script en la web de la marca.
- **Conocimiento:** solo las fichas **aprobadas** en el panel (de [[🚗 Fichas técnicas]]), más las sucursales, los talleres y el contacto de la web. Se buscan con **EmbeddingGemma v1** en el servidor, que corre en el procesador.
- **Prospectos:** por el `jac.com.py/api/lead` que ya existe, con origen `WEB_SR_JAC`, el asesor por sucursal y la nota "Enviado desde: chat".
- **Seguridad:** el modelo no tiene herramientas, hay límites de mensajes, verificación anti-robots (Turnstile) y un interruptor para apagarlo desde el panel.
- **Carga:** el chat responde de a una consulta por vez y corta a los 25 s con salida a un asesor, para no frenar al bot de WhatsApp.

## Fases

0. Aprobar las 19 fichas de JAC. Seis tienen avisos: RF8, Sunray Bus y Cargo, LE760, LD123 y camiones.
1. Servicio andando en una página de prueba.
2. Panel.
3. Pegarlo en jac.com.py con un deploy de Netlify. Al principio aparece solo con `?chat=1`.
4. Dos semanas de medición antes de sumar otra marca.

## Estado del embedding (08/10)

- **Índice general del vault (v1):** notebook y servidor, se actualiza cada hora y ya incluye las fichas. Lo usa la skill de Hermes `buscar-en-el-vault`.
- **Índice de fichas con EmbeddingGemma 2:** solo en la notebook, a modo de comparación. En las pruebas, v1 empató o ganó en 7 de 8 preguntas y fue 4 veces más rápido.
- **Chat de marcas:** pendiente, es este proyecto.

## Avance (2026-10-09)

- **Plan 1 (núcleo):** chat, burbuja y examen. Resultado del examen: 40/40 preguntas reales y 19/19 trampas.
- **Plan 2 (panel `/admin`):** mergeado a `main` (`8565455`). Incluye:
  - entrada con la cuenta de los dashboards;
  - Inicio, con el interruptor del chat y los números del día;
  - Conocimiento: aprobar o quitar cada una de las 19 fichas de JAC y probar preguntas;
  - Asistente: nombre, saludo, color y preguntas sugeridas, con filtro de competencia y precios;
  - Conversaciones y Prospectos.

  Lo que lo verifica: 644 tests, 102 pruebas de navegador (compu y celular) y un ataque de inyección de código revisado con unos 90 casos.
- **Falta el Plan 3 (producción):** Docker, Coolify, DNS, deploy de Netlify y las compuertas 🔒. La lista de pendientes que dejó la revisión final está escrita en el plan 3 del repo.

## Medición en el servidor (2026-10-12)

Chat en `https://chat.santarosa.lat` (Coolify, SRPY186), modelo `gemma4-hermes:latest` (el mismo del bot de WhatsApp). Croman aprobó las 19 fichas (7 con aviso): el índice tiene 19 fichas y 221 trozos. El examen y la carga se corrieron con las claves de prueba de Turnstile durante 9 minutos (23:19 a 23:28); después se restauraron las reales y se comprobó que el token de prueba da 403.

| Medida | Resultado |
|---|---|
| Examen (65 casos) | 46/46 preguntas de datos y 0/19 fallas en trampas; 0 cortes del filtro |
| Primer texto, una persona | mediana 1,4 s, máximo 2,9 s; el 100 % en menos de 3 s |
| Carga: 10 conversaciones a la vez, 2 preguntas cada una | 20/20 respondidas, 0 salidas a contacto, 0 errores |
| Carga: primer texto | mediana 23,5 s y p95 24,8 s: es la cola (una respuesta por vez, unos 2,6 s cada una) |
| Bot en reposo (línea de base) | mediana 0,37 s, p95 0,41 s |
| Bot durante el examen (respuestas una tras otra, sin pausa) | mediana 1,8 s, p95 4,2 s, máximo 4,5 s |
| Bot durante la carga | mediana 0,40 s, p95 2,4 s, máximo 2,7 s |
| Modelo del bot | siguió cargado, mismo ID, sin recarga |

**Lectura:** con una persona el chat responde en menos de 3 s. Con uso sostenido, un pedido del bot puede esperar a que termine una respuesta del chat: entre 2 y 4 s más en el peor caso, porque el chat responde de a una por vez. El examen es un uso mucho más intenso que el real (el bot recibe unos 20 pedidos por hora); el efecto real se mide en las dos semanas posteriores a la apertura. Las respuestas más largas y cálidas (de unas 25 a unas 70 palabras) ocupan la placa más tiempo que las secas.

**Riesgo abierto:** las fichas con aviso que se aprobaron dan datos mal en el chat. RF8 mezcla valores del motor (habla de 745 nm de torque combinado), Sunray Bus dice «aire acondicionado crema», LD123 repite el alternador «12 Volt/0 A» y Sunray Cargo da 1.600 kg cuando el Drive dice 1.300. Recomendado: quitar la aprobación de RF8 y Sunray Bus hasta tener la ficha corregida.

## Apertura al público (2026-10-13)

El chat de marcas quedó **abierto al público** en `jac.com.py` el 13/10/2026 (~15:59, hora de Paraguay), a pedido de Croman.

- **Antes de abrir:** examen en el servidor con el modelo del bot: 46/46 preguntas de datos más los casos de gama, y 0/19 en trampas; respuestas generales de unas 70 palabras (por tipos: SUV, pickups, utilitarios y camiones, eléctricos).
- **Fichas aprobadas: 17 de 19.** RF8 y Sunray Bus quedaron afuera: sus PDF tienen los valores corridos y el chat los contestaba mal. Para sumarlas hay que corregir las fichas de origen.
- **Prospectos:** reales. Entran a Bitrix por el mismo camino que el formulario de la web (origen de JAC, marca JAC, asesor de la sucursal, nota «Enviado desde: chat»).
- **Panel:** `https://chat.santarosa.lat/admin` (mismo usuario que los dashboards). Desde ahí se apaga el chat al instante (Inicio → «Apagado») o se vuelve a «Solo pruebas».
- **Monitor:** «Chat de marcas» en el tablero de estado, con aviso por Telegram.
- **Pendiente:** revisar y cerrar como prueba el prospecto #118417 en Bitrix, y la **medición de dos semanas** (hacia el 27/10/2026): conversaciones, % que termina en prospecto, preguntas sin respuesta, tiempos y efecto sobre el bot de WhatsApp. Con eso se decide la segunda marca.
