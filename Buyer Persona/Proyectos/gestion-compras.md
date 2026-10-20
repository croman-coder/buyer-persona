---
estado: activo
firma: 0db92d6e3b88c7b68e8ec36df3f1df0069f9bccc72b6db2e1f02ed62d3ad8b37
git_rama: feat/webapp-rediseno
git_remoto: https://github.com/croman-coder/gestion-compras.git
git_sin_subir: 0
git_ultimo_commit: '2026-10-09 5fa0302 feat: rediseño de toda la interfaz, app instalable
  y arreglos de producción'
hijos: []
nombre: GESTION COMPRAS
resumen: null
resumen_pendiente: true
ruta: /home/croman/Escritorio/GESTION COMPRAS
slug: gestion-compras
stack:
- git
- node
tipo: proyecto
ultima_actividad: '2026-10-13'
---

<!-- hermes:inicio -->
## Estado

| Campo | Valor |
| --- | --- |
| Estado | activo |
| Última actividad | 2026-10-13 |
| Stack | git, node |
| Rama | feat/webapp-rediseno |
| Último commit | 2026-10-09 5fa0302 feat: rediseño de toda la interfaz, app instalable y arreglos de producción |
| Sin subir | 0 |
| Ruta | `/home/croman/Escritorio/GESTION COMPRAS` |
<!-- hermes:fin -->

## Rediseño WebApp + app instalable (9 oct 2026)

Rama `feat/webapp-rediseno`, commit `5fa0302` (328 archivos). **En producción desde el 13 oct 2026** (PR #3, ver abajo). Pedido: que ande, que sea más simple de usar, que sea WebApp.

**Qué cambió**
- Interfaz entera rehecha para escritorio, tablet y celular: menú lateral con grupos y paleta "Ir a…" (`/` o Ctrl+K, salta por número), barra de abajo con 4 destinos por rol + "Más", Inicio con "Te toca a vos", detalle de solicitud con "Qué te toca ahora", listas como tarjetas en el celular. A 390px las 33 pantallas desbordaban a lo ancho; ahora 0.
- App instalable (PWA): manifiesto, íconos, service worker (nunca guarda HTML ni datos: la tablet del depósito se comparte), página sin conexión y aviso de red.
- Docs: `ARCHITECTURE.md` §4.1 y §9, `DESIGN.md`, `PRODUCT.md`, spec en `docs/superpowers/specs/2026-10-08-webapp-rediseno.md`.

**Defectos que ya estaban en producción y se encontraron probando de verdad**
1. **Pantallas que se congelaban después de guardar** ("Enviando…" para siempre, o el contador sin cambiar hasta recargar). Es un defecto de React (el canary que trae Next 15.5): pierde un aviso cuando la respuesta del Server Action llega en varios pedazos pegados. Arreglo: `src/components/acciones-en-una-pieza.tsx`. Medido con `npm run qa:acciones-en-rafaga`: 5–7 de 12 corridas congeladas sin el arreglo, 0 de 30 con él. Sacarlo cuando una versión nueva de Next lo traiga arreglado (la prueba dice cómo).
2. **La cámara del escáner de códigos nunca abría**: `Permissions-Policy: camera=()` la bloqueaba sin avisar. Ahora `camera=(self)` y el escáner explica por qué si falla.
3. **El historial de una solicitud le mostraba proveedor y monto de los presupuestos a quien la pidió** aunque no sea de compras (el detalle los esconde).
4. **Filtros y gráfico por día cortaban en UTC**: lo de las 23:30 locales caía en el día siguiente. Ahora días de Asunción (`src/lib/fechas-py.ts`); las facturas (columna de sólo fecha) siguen en UTC a propósito.
5. Valuación de stock con `int × int`: un producto de 3.000 u × Gs. 1.000.000 tiraba "integer out of range". Reporte de stock "bajo mínimo" listaba productos dados de baja. "Por recibir" de depósito listaba órdenes sin producto en el catálogo.

**Verificado (contra un build de producción local, base de simulación)**: circuito completo con un usuario por rol y firma digital (solicitud → presupuestos → aprobación → orden → recepción → factura → retiro) en una tablet táctil, también detrás de un proxy de ráfagas; 164 archivos / 1.844 pruebas; tsc y eslint limpios; axe 0 violaciones en 34 pantallas × 3 tamaños; service worker sin HTML en caché. Herramientas: `scripts/qa/{circuito,capturas,acciones-en-rafaga}.cjs`.

**Pendiente / decisiones**
- ~~Decidir commit, push y redeploy en Coolify~~ Hecho el 13 oct 2026: mergeado a `master` y desplegado junto con licitaciones (sección siguiente).
- Recomendado, no hecho (tocan la base): índice en `log (entidad, entidad_id)` y único parcial para la aprobación vigente de cada solicitud.
- Producción: confirmar que el Node de Coolify trae husos horarios 2025+ (Paraguay quedó en UTC-3 fijo); `tests/lib/fechas-py.test.ts` lo vigila en desarrollo.
- Aviso de "sin conexión" sólo detecta el corte total del dispositivo, no un wifi sin salida a internet.
- Los manuales con capturas en `docs/manual` y `docs/instructivo` quedaron viejos.

## Licitaciones con sobre cerrado (13 oct 2026)

Pedido del comité para Compras (Mario), llegado por audio de WhatsApp: hoy los presupuestos se abren en días distintos (margen para que un precio se filtre) y cada proveedor cotiza lo que entiende (chapa vs MDF, un solo número total). Pedido, transcripción y preguntas: `~/Escritorio/LICITACION SRPY/PEDIDO.md`. Página para la reunión con Mario: https://claude.ai/artifact/2vZKX33De8HCmn3MagtA8J (privada: compartirla desde su menú).

**Cómo funciona**
1. Desde una solicitud **en compras**: «Licitar con sobre cerrado». Congela las líneas, deja agregar una especificación por línea y condiciones para todos, elige proveedores (mínimo 3) y fija el cierre.
2. Cada proveedor recibe un **link personal** `/oferta/<token>` (sin cuenta; botones para copiar el link o mandarlo por WhatsApp con el mensaje armado). Carga precio por línea, plazo y observaciones; corrige hasta el cierre.
3. Antes de abrir, compras ve **quién mandó y cuándo, nada más**. La bitácora guarda cuántas líneas cotizó cada uno, nunca precios. El link se guarda como sha256 y se muestra una sola vez («Link nuevo» invalida el anterior).
4. Desde el cierre se **abren los sobres**, todos juntos y una sola vez (queda quién y cuándo). Sale el **cuadro comparativo** ítem × proveedor: mejor precio por línea, mejor lote completo y compra por línea con su diferencia.

**Dónde se genera el link:** menú Compras → **Licitaciones** (desde el 13 oct ~19:40, PR #5). Arriba, **«Para licitar»**: las solicitudes que están en compras y no tienen licitación en curso, cada una con un botón **Licitar**; al tocarlo se abre el formulario y, al publicar, salen los links. Abajo, «Licitaciones publicadas». También sigue el botón en el detalle de la solicitud. Una solicitud en borrador no aparece: hay que enviarla a compras. (Antes había una pantalla aparte «Nueva licitación»; `/licitaciones/nueva` ahora redirige.) Los links se muestran una sola vez («Link nuevo» en cada proveedor genera otro).

**Código:** `src/lib/licitaciones.ts` (20 tests), `src/app/(app)/licitaciones/`, `src/app/(app)/peticiones/[id]/licitar/`, `src/app/oferta/[token]/`. Diseño, decisiones y preguntas abiertas: `docs/superpowers/specs/2026-10-13-licitaciones-design.md`. Demo local: `scripts/seed-licitaciones-demo.ts` (sólo corre contra localhost).

**Supuestos del prototipo, a confirmar con Mario:** mínimo 3 proveedores; se permite cotizar sólo algunas líneas; gana el precio (el plazo sólo se muestra); por invitación con link; guaraníes, IVA incluido.

**Límite conocido:** el sobre cerrado lo garantiza la aplicación, no la base: con acceso directo a Postgres de producción se podrían leer los precios. Se cierra cifrando las ofertas (está en el spec).

**Pendiente**
- Reunión con Mario y quien tiene experiencia en licitaciones (¿la jefa de compras?): responder las 10 preguntas.
- Pasar la oferta ganadora al circuito actual (presupuesto recomendado → aprobación → orden). Hoy `presupuestos` exige un PDF por proveedor.
- Límite de intentos en `/oferta/` (ojo: detrás del túnel la IP real llega en `CF-Connecting-IP`, ver [[Infraestructura y Conexiones]]).

## Deploy a producción del 13 oct 2026

PR #3 (rediseño, contra `master`) y PR #2 (licitaciones, apilado sobre el rediseño y después cambiado a `master`) mergeados con merge commit. `master` = `a6d6744`, desplegado a las 15:36 en compras.santarosa.lat (imagen `c3alcmmxxaciv6w6xk67m9m3:a6d6744`). Rollback: la imagen anterior `f768866` sigue en el servidor.

**Base de datos:** las 4 tablas nuevas (`licitaciones`, `licitacion_items`, `licitacion_invitaciones`, `licitacion_precios`) se crearon a mano, sólo `CREATE`, en una transacción. Además se agregaron `departamentos_ubicacion_id_idx` y `usuarios_ubicacion_id_idx`, que faltaban desde antes. Backup previo: `~/backup-compras/compras-pre-licitaciones-2026-10-13-1533.sql` en srpy186.

⚠️ **No usar `drizzle-kit push` contra producción.** Las restricciones de prod tienen nombres de Postgres (`_key`, `_fkey`) y el código los de Drizzle (`_unique`, `_..._fk`): mismas columnas, nombres distintos, y el push las borraría y recrearía. Antes de cada cambio de esquema: comparar columnas, índices y restricciones de prod contra la base de test y aplicar sólo lo nuevo.

**Verificado en producción:** `/login` 200 con la interfaz nueva; `/licitaciones` sin sesión → login; `/oferta/<link inventado>` 200 «Este link no es válido» (llega a la base sin cuenta); `/ofertas` pide sesión; manifiesto de la PWA 200; logs del container sin errores. Falta probarlo con un usuario real (Croman).

**Gotchas del deploy**
- `custom_labels` de la app en Coolify estaba en base64, idéntico a las labels generadas y a las del container: el redeploy ruteó bien. Comprobarlo igual antes de cada redeploy (comando en `docs/deploy-coolify-cloudflare.md`).
- `gh pr edit --base` falla por la baja de Projects classic: cambiar la base con `gh api -X PATCH repos/croman-coder/gestion-compras/pulls/N -f base=master`.
- El repo no tiene CI: los checks del PR vienen vacíos.
