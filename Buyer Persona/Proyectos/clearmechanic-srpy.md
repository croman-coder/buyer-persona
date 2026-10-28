---
estado: activo
firma: cfae31196fcbc18918ac0337e9aef9e0b2ae287ab34bd4f51eb3f2639b841b3a
git_rama: main
git_remoto: git@github-croman:croman-coder/taller-srpy.git
git_sin_subir: 0
git_ultimo_commit: '2026-10-22 d5a6168 docs: solidez en producción (44d4f36), aviso
  de caída y health check de Coolify'
hijos: []
nombre: CLEARMECHANIC SRPY
resumen: Inspección digital de vehículos para la posventa (equivalente propio de ClearMechanic)
resumen_pendiente: true
ruta: /home/croman/Escritorio/CLEARMECHANIC SRPY
slug: clearmechanic-srpy
stack:
- git
- node
tipo: proyecto
ultima_actividad: '2026-10-22'
---

<!-- hermes:inicio -->
## Estado

| Campo | Valor |
| --- | --- |
| Estado | activo |
| Última actividad | 2026-10-22 |
| Stack | git, node |
| Rama | main |
| Último commit | 2026-10-22 d5a6168 docs: solidez en producción (44d4f36), aviso de caída y health check de Coolify |
| Sin subir | 0 |
| Ruta | `/home/croman/Escritorio/CLEARMECHANIC SRPY` |
<!-- hermes:fin -->

## Qué es

**Taller Santa Rosa**: app propia de posventa con las funciones de inspección digital de ClearMechanic. El técnico inspecciona el vehículo desde el celular (semáforo, mediciones con color sugerido, fotos y video), el asesor presupuesta cada punto amarillo o rojo, y el cliente recibe un link por WhatsApp para aprobar o rechazar ítem por ítem. Lo pidió Choco el 21/10/2026; en las pantallas del cliente la marca es Santa Rosa, no ClearMechanic.

> **Uso interno:** en los casos de éxito de ClearMechanic figura un grupo multimarca de Asunción (competencia) que ya lo usa. Detalle en `docs/investigacion-clearmechanic.md` del proyecto. No va en material público.

**Estado al 21/10/2026: EN PRODUCCIÓN en https://taller.santarosa.lat** (commit `5717f9e`, repo privado `croman-coder/taller-srpy`, rama `main`).
- Coolify: app `taller-srpy` (uuid `jxc7nfckjh1kf4ubxwakqbwv`), Nixpacks, **sin autodeploy** (redeploy a mano por la API). Base `taller` en `srpy-postgres` con las migraciones `0000` y `0001_paridad` (aplicadas a mano, con respaldo y ensayo). Túnel `compras-srpy186`. Detalle: `docs/deploy-coolify.md`.
- Administrador `marketing@santarosa.com.py` (Choco ya cambió la clave inicial). Respaldo diario 02:30 + alerta ntfy; restauración de ensayo hecha.
- **Paridad con ClearMechanic, plan 1, en producción:** agenda de citas (con atrasadas y «Llegó» → orden), planeador en vivo, cronómetro por trabajo, paquetes de precio fijo, opinión del cliente (NPS) y próxima visita con recordatorios. Revisión final hecha (0 críticos; los 3 importantes arreglados).
- **Pruebas:** 472 de lógica; humo 74/74 en producción; e2e en Chrome (local 23/23 los módulos nuevos; producción: la orden completa con video de 11 MB); seguridad dinámica (113 comprobaciones, sin críticos ni altos; el hallazgo medio, byte NUL → 500, arreglado); estrés (15 usuarios p95 111 ms; arreglados: dos pools → uno, topes de intentos atómicos, Seguimiento con tope). Resultados en `docs/qa-*-resultados.md`.
- **Datos de demostración en producción** (cliente Carlos Román, 0993 347 658): 6 órdenes en cada etapa marcadas `DEMO`, 3 citas «DEMO ·» y 3 paquetes. Se sacan con `npx tsx scripts/demo-taller.ts --borrar` dentro del contenedor. Queda también la orden de prueba OT-000001 «PRUEBA E2E».
- **Falta:** e2e de los módulos nuevos contra producción (lo corre Choco con su clave: `docs/deploy-coolify.md`), cargar talleres y usuarios reales, copia externa del respaldo, y la paridad plan 2 (YCloud, Pagopar, Bitrix, auto prospección, API y factura electrónica: necesitan credenciales) y plan 3 (escáner de chapa, sin conexión).
- Decidido: el asesor ve las órdenes de todos los talleres.

## Mejoras v2: EN PRODUCCIÓN desde el 22/10/2026 (`80c81f6`)

Ya en `main` y desplegadas (migración `0002` aplicada a mano con respaldo `pre-0002.dump`; humo 75/75). **La IA y el aviso por ntfy están apagados** hasta cargar `ANTHROPIC_API_KEY` y `NTFY_TOPIC` en Coolify; faltan también los planes base y el enlace de reseñas de cada taller (Configuración). Elegidas de la investigación `docs/investigacion-funciones-2026-10-22.md` (puntos 3, 4, 5, 6, 7, 8 y 10). Detalle en `docs/producto.md` y `docs/deploy-coolify.md` de la rama.

| Mejora | Qué hace |
| --- | --- |
| Evidencia más clara | Foto marcada (círculo, flecha, trazo), nota de voz interna, sello de fecha y fotos del «después» que el cliente ve como «Así quedó» |
| Link como «taller en línea» | 6 etapas, «Tengo una duda» por WhatsApp, contador de vistas y alerta «no abrió» a los 45 min |
| Opinión → reseña | 9-10 ve «Dejá tu reseña en Google» (solo enlaces de Google, uno por taller); 0-6 avisa por ntfy y alerta «llamalo» 48 h |
| Reportes | Calidad por técnico, por marca, dónde se demora una orden y resumen de hoy para WhatsApp |
| Mejorar con IA | Claude (Haiku 5.5) reescribe la nota y la recomendación para el cliente; el asesor revisa y guarda; sin datos del cliente; 20 usos por hora y persona |
| Recepción y entrega formales | Inventario, firma del cliente, control de calidad obligatorio para «lista» y hoja imprimible/PDF |
| Plan de mantenimiento por marca | Qué toca por km o meses (±1.000 km de un múltiplo), se suma al presupuesto con el paquete; «La vez anterior» en las mediciones |

- **Verificación:** 609 pruebas, recorrido en Chrome real 62/62 (repetible, con micrófono falso y un Claude de mentira), semilla y demo probadas en una base nueva, y **dos revisores independientes** (correctitud/migración y seguridad): sin críticos; 1 alto, 5 medios y varios bajos, todos arreglados.
- **Cómo se desplegó (referencia):** migración `0002_mejoras.sql` a mano (respaldo `pre-0002.dump`, ensayo con ROLLBACK, COMMIT; solo agrega); variables opcionales `ANTHROPIC_API_KEY` (mejor una clave propia con límite de gasto) y `NTFY_TOPIC` (topic propio de 24+ caracteres); después, «Cargar los planes base» y el enlace de reseñas de cada taller en Configuración. Los planes base son genéricos: ajustarlos con el manual de cada marca.
- **Para tener en cuenta:** el control de calidad pasa a ser obligatorio (las órdenes que ya estén «en trabajo» tendrán que registrarlo); no volver a `main` una vez cargadas notas de voz; Google desaconseja pedir reseñas solo a quien puntúa alto (lo que se eligió: riesgo a vigilar). La versión de producción de hoy tiene un defecto que esta rama arregla (el planeador «en vivo» no se actualiza y la foto de recepción no aparece hasta recargar).

## Solidez: EN PRODUCCIÓN desde el 22/10/2026 (`44d4f36`)

Pedido de Choco: «que sea sólida y que funcione realmente bien». Sin migración.

| Qué | Resultado |
| --- | --- |
| Esperas en la base | Topes por conexión (bloqueo 5 s, consulta 20 s) y «probá de nuevo» en vez de un 500. Con una orden bloqueada 8 s y 30 subidas: 30/30 bien (antes 1/30) |
| Subidas | Tope de 240 MB en vuelo; el celular reintenta solo ante «ocupado» o corte de señal, sin duplicar la foto. El estrés G4 (10 videos de 50 MB a una orden), abierto desde la paridad, ahora pasa |
| Datos | Una chapa = un vehículo (no se parte el historial). Puntos manuales sin posición repetida |
| Velocidad | Fotos y videos en caché del navegador (304 verificado en producción) |
| Agenda y galerías | Se actualizan siempre después de guardar (se encontró y sacó un `router.refresh()` que a veces dejaba la cita sin mostrar) |
| Vigilancia | Aviso de caída por ntfy cada 5 min (`~/bin/taller-salud-alerta.sh`) y health check de Coolify en `/api/salud` (`healthy`) |

- **Verificación:** 630 pruebas; recorridos en Chrome 52/52 (2 en paralelo), 23/23 y 68/68 (con la subida resistente); seguridad 127 sin fallas; estrés sin ✗.
- **Pendiente (de Choco):** la copia externa del respaldo (`respaldo-externo.sh` del servidor espera las credenciales del bucket R2/B2) y el cambio de dueño de un vehículo (hoy, si la chapa es de otro cliente, se pide buscarlo).

## Fase 1 (hecha)

| Pieza | Qué hace |
| --- | --- |
| Órdenes | Tarjetas por estado y búsqueda por chapa, teléfono, cliente u `OT-000123` |
| Recepción | La chapa trae el vehículo y el cliente si ya vinieron; km, combustible, motivo y fotos de ingreso |
| Inspección | Plantilla multipunto de 7 secciones y 37 puntos, con umbrales (cubierta 3 y 1,6 mm; pastillas 4 y 2 mm; batería 12,4 y 12,0 V; humedad del líquido de frenos 2 y 3%) y comentarios precargados. No se termina con puntos sin revisar ni con amarillos o rojos sin foto |
| Presupuesto | Repuestos y mano de obra en guaraníes, IVA incluido. Un amarillo sin precio queda «a observar» |
| Link del cliente | Link corto `taller.santarosa.lat/i/<12 letras y números>` (desde el 22/10/2026; los largos de antes siguen valiendo hasta que vencen) con vista previa de Santa Rosa en WhatsApp; vence a los 30 días. Se manda por `wa.me` desde el WhatsApp del asesor, sin API. La apertura se registra desde el navegador, así la vista previa de WhatsApp no cuenta |
| Seguimiento | Links sin respuesta y trabajos rechazados, con WhatsApp para volver a ofrecer |
| Reportes | Ofrecido contra aprobado, tasa de aprobación, venta adicional por orden y mediana de respuesta, por asesor, técnico y taller; exportación a Excel |
| Roles | admin, jefe de taller, asesor y técnico (el técnico solo toca sus órdenes) |

## Después (fase 2 y siguientes)

1. Envío por la API de YCloud y aviso al asesor cuando el cliente responde.
2. Citas y planeador del taller.
3. Cronómetro por trabajo.
4. Encuesta al entregar (conectar con [[Calidad NPS]]) y recordatorio automático de lo rechazado.
5. Integración con Bitrix (cliente y oportunidad de posventa).
6. Trabajo sin conexión en la inspección.

## Técnico

Stack y base de Selección SRPY: Next.js 15, Drizzle, PostgreSQL y el diseño de la Agencia IA. Las fotos y los videos van en la base (bytea), comprimidos en el celular y servidos con Range. Para desarrollo: base local en el puerto 5435 (`taller_dev` / `taller_test`), dev server en el 3020 y `npm run muestra` para cargar 12 órdenes de muestra. Guías: `README.md`, `docs/producto.md` y `docs/deploy-coolify.md`.
