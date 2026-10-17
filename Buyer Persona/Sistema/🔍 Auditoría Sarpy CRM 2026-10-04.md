---
tipo: auditoria
tags:
  - sistema
  - crm
  - sarpy
  - auditoria
actualizado: 2026-10-04
---

# Auditoría Sarpy CRM (4 oct 2026)

Pedido de Croman: analizar estructura y diseño de Sarpy CRM y recomendar mejoras para que sea muy funcional, simple de
usar y aguante más de 150 usuarios en el servidor. Uso interno; todavía no se comparte con gerencia (Sarpy es respaldo
de Bitrix hasta que el directorio decida). Plan que sale de acá: [[🧭 Plan Sarpy — plataforma única]].

**Cómo se hizo:** solo lectura. Cuatro revisiones en paralelo (servidor y base, capa de datos del navegador, uso para el
asesor, este vault) más mediciones directas en el servidor SRPY186 y en `crm.santarosa.lat`. Los hallazgos principales se
verificaron contra el código de `main` (`0b028c1`, 30/9). No se modificó nada.

## Veredicto

- **El hardware sobra:** 24 núcleos, 62 GB de RAM (36 GB disponibles), carga 3, disco al 39 %.
- **El diseño visual nuevo es bueno:** Hoy, Pipeline y Ficha están claros y son coherentes entre sí.
- **Hoy no está listo para 150 usuarios.** Nunca corrió con carga real (250 leads de demo, 1.315 mensajes, 2 usuarios,
  base de 21 MB). Los cuellos de botella son de código y de configuración, no de máquina.
- **Para el asesor:** en escritorio funciona bien; en celular es flojo, y quedan restos del producto original (bot de
  WhatsApp) a la vista.
- La prueba de carga del 25/9 ("aguanta 200 conexiones") no sirve como garantía: usó un solo usuario administrador, solo
  insertó mensajes, corrió sobre el esquema anterior al modelo persona / conversación / oportunidad y con 24 contactos.

## Mediciones del 4/10

| Qué | Valor | Lectura |
|---|---|---|
| Servidor | 24 núcleos · 62 GB · 133 contenedores | sobra |
| Swap | 8 de 8 GB usados, `swappiness` 60 | pendiente del 30/9 sin aplicar |
| Postgres del CRM | `max_connections` 100 · `shared_buffers` 160 MB · `work_mem` 4 MB · `random_page_cost` 4 | valores de fábrica, sin ajustar al hardware (disco NVMe) |
| PostgREST | conecta directo a la base (no usa el pooler), pool por defecto (10), `PGRST_DB_MAX_ROWS` 1000 | corto para 150 usuarios |
| Realtime | 13 tablas publicadas; su consulta de WAL es la más cara de la base (687 mil llamadas, 2.711 s acumulados) | con 2 usuarios |
| Contenedores | sin tope de memoria | un vecino puede ahogar al CRM |
| GPU | 10,9 de 12,2 GB usados; el modelo local atiende un pedido por vez | toda la IA del CRM hace fila ahí |
| Web en vivo | `/login` 87 ms; bundle principal 259 KB comprimido; caché inmutable por Cloudflare | bien |

## A. Qué se rompe primero con 150 usuarios

| # | Problema | Evidencia | Arreglo | Tamaño |
|---|---|---|---|---|
| 1 | Cada navegador carga todo el tenant (2 × 2.000 filas) y la base evalúa los permisos fila por fila con funciones anidadas | `frontend/src/lib/datosLead.js:72`, `supabase/migrations/0107_visibilidad_rls.sql` | Carga por asesor y paginada en el servidor; políticas con conjuntos precalculados; índice por `last_inbound_at` | medio |
| 2 | Corte silencioso a los 1.000 leads: producción devuelve como máximo 1.000 filas, el navegador pide 2.000 y solo avisa si llegan 2.000 | `PGRST_DB_MAX_ROWS=1000` (medido) contra `datosLead.js:14` | Sale con el punto 1 | chico |
| 3 | Realtime a todo el tenant: cada cambio llega a los 150 navegadores y cada uno relee 3 consultas; 7 a 12 canales por usuario | `frontend/src/hooks/useModeloB1.js:19` | Avisos por asesor o por marca; sacar `contacts` y `user_sessions` de la publicación; latido cada 5 min | medio-grande |
| 4 | El bot responde dentro del webhook, sin cola; el modelo local atiende de a uno y lo comparten bot, resumen, analista y asistente | `api/ycloud-webhook.js:2432` | Responder 200 al guardar; cola en una tabla; un trabajador con prioridad (el cliente primero) | grande |
| 5 | Postgres con valores de fábrica y PostgREST con pool de 10 | medido | `shared_buffers` ~4 GB, `work_mem` 16 MB, 200 conexiones, `random_page_cost` 1.1, pool ~30, tope de memoria por contenedor | chico (pide reiniciar la base) |
| 6 | Un solo proceso sin red de seguridad: no captura errores globales, `/healthz` no mira la base, cada push reinicia y corta los turnos del bot en vuelo | `server/index.js:164` | Capturas globales, `/readyz`, tope al cuerpo de los webhooks; trabajador aparte para el bot | chico-medio |
| 7 | Respaldo: un dump diario en el mismo disco; 11 GB de archivos sin respaldo | `DEPLOY.md`; [[🗄️ Auditoría de bases — nube vs servidor]] | Copia fuera del servidor, cada 4 a 6 h, simulacro de restauración mensual | chico |
| 8 | Navegador frágil: sin pantalla de error (un fallo deja la pantalla en blanco), Kanban sin virtualizar, un chat largo muestra los 500 mensajes más viejos, no se pone al día al volver del segundo plano | `datosLead.js:146` | Límite de error por pantalla, últimos mensajes + "cargar anteriores", recarga al reconectar | chico-medio |
| 9 | Reparto: una consulta de conteo por asesor por cada lead; el tablero en vivo recalcula cada 60 s con subconsultas por oportunidad | `api/_lib/assign.js:79`, `0122_b1c_front.sql:283` | Un solo conteo agrupado; `esperando_desde` guardado en la conversación | chico-medio |

Lo que ya está sólido: la entrada de mensajes es idempotente y no pierde ni duplica; una excepción de un handler no tumba
el proceso; los assets viajan con caché inmutable; los índices del modelo nuevo existen; los reportes autorizan una sola
vez; todas las secciones del navegador se cargan a demanda.

## B. Simplicidad para el asesor

| # | Problema | Arreglo | Tamaño |
|---|---|---|---|
| 1 | "Cerré venta" del chat no registra la venta (solo cierra el hilo). Hay cuatro botones de "cierre" distintos | Un solo "Marcar vendido" | chico |
| 2 | Lead de formulario fuera de las 24 h: WhatsApp devuelve error y no hay plantillas. Los formularios son ~84 % de los leads y la mitad entra fuera de horario | Plantillas aprobadas, desde la ficha | grande |
| 3 | Leads no sirve en el celular: Kanban de 7 columnas sin arrastre táctil y una lista de 1.240 px de ancho | Pestañas por etapa + "Mover a…" | medio |
| 4 | Restos del bot a la vista del asesor: "Bot ON" global, "Reset bot", tarjetas "Conectá YCloud", engranaje que no lleva a nada | Solo dueño y administrador | chico |
| 5 | Navegación: 7 pestañas arriba + riel de 5 íconos + 3 controles | Se resuelve con el lanzador de módulos del plan | medio |
| 6 | Buscar: Leads no tiene buscador; "0981…" no encuentra nada (compara contra +595) | Campo visible + teléfono normalizado | chico |
| 7 | Anotar una llamada y agendar el seguimiento son ~9 pasos; el alta manual tiene 13 campos | Botones "Mañana / En 3 días"; alta con 4 campos + "más datos" | medio / chico |
| 8 | Sin red: arrastrar a Vendido no confirma, descartar es un toque, 15 diálogos nativos del navegador, no hay "Deshacer" | Confirmación única + deshacer | chico |
| 9 | Dos fichas: el chat abre el panel viejo; Conversaciones y Configuración siguen con la piel anterior | "Abrir ficha" desde el chat y borrar el panel viejo (~1.200 líneas) | medio |
| 10 | "Hoy" dice "Todo al día" mientras todavía está cargando | Esqueleto hasta que cargue | chico |

## C. Lo que sabe el vault y el CRM todavía no usa

- **La venta no queda registrada.** Bitrix: 10 ganados contra 115 vehículos facturados (12/9); 83 % de las ventas de Tecnom
  se cargaron a mano al cerrar; 12 de 15 ventas de Soueast que venían de Meta figuran como "Prospecto del asesor"
  ([[💰 Ventas que vinieron de Meta]]). El punto B1 es el mismo mal dentro de Sarpy. Al marcar vendido conviene pedir
  ahí cédula o RUC y persona o empresa, y buscar solo el lead previo por teléfono.
- **Conciliar con Cars por VIN o factura, no por teléfono:** desde agosto solo 9 de 518 ventas del ERP traen teléfono o
  correo ([[📘 Manual Buyer Persona]]).
- **35 % de las ventas con lead previo cerraron en otra marca:** el modelo de una oportunidad por marca fue un acierto.
- **SLA real: 2 horas hábiles, 21 % de cumplimiento en agosto.** "Hoy" debería ordenar por reloj hábil y el primer
  contacto salir solo por plantilla.
- **388 notas de WhatsApp por marca y las battle cards ya están escritas:** se pueden cargar como respuestas rápidas por
  marca, sin tipeo. La competencia es dato interno: nunca en textos al cliente.
- **Usuarios:** ninguna nota da el número 150. La planilla de septiembre trae 68 asesores únicos (no 89: hay asesores en
  más de una marca).

## Límites de esta auditoría

- El costo de los permisos a escala se leyó en el código; no se midió (la base tiene 250 filas).
- El uso se revisó con el código y las capturas del repo, sin entrar a la aplicación en vivo.
- No hay cifra de usuarios por rol y sede.

## Qué se hizo después

El mismo 4/10 se abrió la rama `afinado` del repo `crm-santarosa` con los arreglos chicos (A6, A8, B1, B4, B6, B8, B10).
Estado y orden completo en [[🧭 Plan Sarpy — plataforma única]].
