---
tipo: plan
tags:
  - sistema
  - crm
  - sarpy
  - plan
actualizado: 2026-10-04
estado: borrador v0 — faltan decisiones de Croman
---

# Plan Sarpy — plataforma única (borrador v0, 4 oct 2026)

Sale de la [[🔍 Auditoría Sarpy CRM 2026-10-04]] y del pedido de Croman del mismo día.

> **Revisión del 4/10 (tarde), después de conversarlo:**
> - **Copia en sombra desde Bitrix: SÍ** (Croman). Reemplaza al "sin migrar nada" del 26/9 solo en esto: se copia en
>   modo lectura, nadie se muda y ninguna fuente cambia. Tiene que quedar inerte (sin bot, sin reparto, sin avisos).
> - **Alcance en revisión:** Croman duda de integrar PDI, Cotizador, Gestión de Compras y los tableros, porque son cosas
>   distintas. Recomendación: **no embeberlos**. Sarpy queda como el sistema comercial (lead → venta → facturación →
>   escrituración, con tasación, stock y calidad adentro). Criterio: entra lo que usa la misma persona dentro del mismo
>   flujo de venta. Para lo demás alcanza una lista de enlaces en el menú de usuario, filtrada por persona. Si se confirma,
>   salen del plan las fases 2 (Portal) y 6 (Ingreso único) y vuelve la simplificación de la navegación como arreglo chico.
> - **Cotizador: afuera** (Croman, 4/10). Es de Repuestos, otra área de la empresa; no es del asesor de ventas. Con eso
>   también se aclara "el sistema de repuestos": es el Cotizador (`quote.santarosa.lat`).
>
> **Alcance vigente:** Sarpy es el sistema comercial. PDI, Gestión de Compras, Cotizador de repuestos y los tableros
> quedan afuera. Las fases 2 (Portal) y 6 (Ingreso único) de la tabla de abajo **no se hacen**; en su lugar va una lista
> de enlaces en el menú de usuario y la simplificación de la navegación del asesor (Hoy · Leads · Conversaciones + "Más").
> Las secciones "Lectura del plan", "Niveles de integración" y "Quién ve qué" quedan como registro de lo que se evaluó.

## Qué pidió Croman

1. Sarpy sigue siendo **respaldo de Bitrix**: afinado y completo antes de que falle Bitrix o el directorio decida cambiar.
   Todavía no se comparte con gerencia.
2. Sumar los procesos que faltan: **facturación, escrituración** y lo que sigue.
3. **Todo bajo Sarpy:** los sistemas que ya existen (compras, repuestos, talleres, PDI…) embebidos con sus enlaces, cada
   uno con su base, sin tocarlos porque están en producción. Bien acomodado visualmente.
4. Cada usuario ve lo que le corresponde según el perfil que ya tiene en cada sistema.
5. Conexión con **SAP**.
6. Más sólido: las ventanas no se cierran con un clic afuera, nada se traba.
7. **Registro de todo** y que el administrador pueda resolver cualquier inconveniente.
8. Todo **documentado**.

## Lectura del plan

**La dirección es correcta.** Un solo ingreso, un solo menú y cada sistema con su base es el primer paso más barato y
reversible. Con eso Sarpy deja de ser "un CRM" y pasa a ser **el portal interno de Santa Rosa**, con el CRM como un
módulo más. Eso cambia la navegación: hace falta un lanzador de módulos, no más pestañas arriba.

Cuatro puntos donde el pedido choca con la realidad medida:

1. **"Sin tocar nada" no alcanza para todos.** Medido el 4/10 (cabeceras de cada sitio):

   | Sistema | Dirección | ¿Se puede embeber hoy? |
   |---|---|---|
   | PDI | `preentrega.santarosa.lat` | Sí |
   | Tasación | `tasacion.santarosa.lat` | Sí (ya embebida) |
   | Callbot | `callbot.santarosa.lat` | Sí (ya embebido, con ingreso único) |
   | Cotizador | `quote.santarosa.lat` | Sí |
   | Prospectos | `prospectos.santarosa.lat` | Sí |
   | Advisor (mercado) | `advisor.santarosa.lat` | Sí |
   | Presentación semanal | `presentacion.santarosa.lat` | Sí |
   | **Compras** | `compras.santarosa.lat` | **No**: prohíbe ser embebido |
   | **Dashboard Comercial** | `bitrix.santarosa.lat` | **No**: prohíbe ser embebido |
   | **Dashboard Meta Ads** | `dashboardmeta.santarosa.lat` | **No**: solo se deja embeber por sí mismo |

   Los tres "No" piden cambiar **una línea de cabeceras** en cada uno (lo mismo que ya se hizo en Tasación el 27/9). No
   toca lógica ni datos.

2. **Segundo ingreso.** Cada sistema tiene su propio login. Embebido tal cual, el usuario se loguea una vez por sistema
   y por dispositivo dentro del marco. Sacar ese segundo ingreso pide un punto de entrada chico en cada sistema (el
   mismo boleto de un solo uso que ya usa Callbot).

3. **Repuestos y talleres no aparecen.** `~/Escritorio/REPUESTOS` tiene solo un PRD de indicadores y no hay nada de
   talleres en el escritorio ni en el [[🖥️ Inventario del servidor]]. Falta saber dónde viven.

4. **Un respaldo sin datos ni usuarios no respalda.** Si Bitrix cayera mañana, Sarpy tiene 250 leads de demo y 2
   usuarios. Para que sea respaldo de verdad hacen falta tres cosas que no migran a nadie ni cambian ninguna fuente:
   usuarios precargados (inactivos), una copia en sombra de los leads de Bitrix (solo lectura, todas las noches) y un
   simulacro de "Bitrix se cayó". Choca con la decisión del 26/9 ("sin migrar nada aún"): la decide Croman.

## Niveles de integración (por sistema)

| Nivel | Qué es | Qué toca en el sistema | Cuándo |
|---|---|---|---|
| 1. Embebido | Abre dentro de Sarpy con el menú de Sarpy; login propio dentro del marco | Nada (o una línea de cabeceras) | Ya |
| 2. Ingreso único | Entra solo con la sesión de Sarpy (boleto de un solo uso) | Un punto de entrada chico | Después, uno por uno |
| 3. Datos cruzados | Sarpy muestra datos del sistema en la ficha (ej. estado del PDI por VIN) | Una lectura acordada | Solo donde ahorre trabajo |

Cada sistema mantiene su base y sus roles. Sarpy guarda solo **quién ve qué módulo**.

## Quién ve qué

- **Ahora:** matriz usuario × módulo en Administración de Sarpy (la matriz de permisos ya existe para marcas).
- **Después:** un trabajo que lee los usuarios de cada sistema (solo lectura) y **sugiere** los módulos por correo
  coincidente. El administrador confirma. Los roles dentro de cada sistema los sigue mandando ese sistema.

## Orden propuesto

| Fase | Qué | Tamaño | Depende de |
|---|---|---|---|
| **0. Afinado chico** (en curso, rama `afinado`) | Red del servidor, pantalla de error, chat con los últimos mensajes, ponerse al día al reconectar, un solo "Marcar vendido", confirmaciones, buscador en Leads, teléfono normalizado, restos del bot solo para administradores, "Hoy" sin falso "al día" | chico | — |
| 0b. Ventanas sólidas | Ningún diálogo se cierra con clic afuera; fuera los 15 diálogos nativos; "Deshacer" en descartar y mover | chico | fase 0 fusionada |
| 0c. Servidor | Ajuste de Postgres y PostgREST, tope de memoria por contenedor, respaldo fuera del servidor | chico | OK y ventana de Croman; destino del respaldo |
| **1. Solidez a escala** | Carga por asesor y paginada, permisos sin función por fila, Realtime por asesor, reparto con un solo conteo, prueba de carga real (150 sesiones, 50 mil oportunidades, en copia) | medio | 0c |
| **2. Portal** | Lanzador de módulos (reemplaza las 7 pestañas), embebidos de nivel 1, matriz usuario × módulo, mismo marco visual para todos | medio | lista de sistemas |
| **3. Registro y centro de control** | Bitácora (quién, qué, cuándo, antes y después) de etapas, asignaciones, apartados, permisos, configuración e ingresos; pantalla del administrador con errores, webhooks fallidos, colas, salud de integraciones y acciones (reintentar, reasignar, deshacer) | medio | — |
| **4. Facturación y escrituración** | Pedido de facturación desde la ficha (cédula o RUC, persona o empresa, unidad por VIN, forma de pago), tablero de Facturación, Escrituración, rol Administración, enlace con PDI por VIN | grande | decisión SAP / Cars |
| **5. Respaldo real** | Usuarios precargados, copia en sombra desde Bitrix, simulacro | medio | decisión de Croman |
| 6. Ingreso único por sistema | Nivel 2, uno por uno | medio | fase 2 |
| 7. SAP | Conector | grande, sin dimensionar | respuestas sobre SAP |
| 8. Pendientes grandes de la auditoría | Cola del bot, Leads en celular, plantillas de WhatsApp | grande | fase 1 |

Las fases 1, 2 y 3 no comparten archivos: pueden ir en paralelo.

**Documentación** (transversal): ayuda por rol dentro de la aplicación, guía del administrador con el centro de control y
un registro de cambios visible. Cada fase cierra con su parte escrita.

## Decisiones que faltan

1. **Repuestos y talleres:** dónde están (dirección, quién los hizo, con qué login).
2. **SAP:** ¿SAP Business One o Cars? Hoy la facturación y el stock salen de Cars; SAP no aparece en ninguna nota. Qué
   datos tienen que ir y venir, y quién administra SAP.
3. **Copia en sombra desde Bitrix:** sí o no.
4. **Ventana para la fase 0c** (reinicia la base del CRM unos segundos) y **destino del respaldo externo**.
5. **Usuarios por rol y sede:** de dónde sale el "150".

## Estado

| Fecha | Qué |
|---|---|
| 4/10 | Auditoría terminada. Rama `afinado` abierta con la fase 0 en cuatro tandas en paralelo. Nada publicado. |
| 4/10 12:32 | Fase 0 terminada en la rama `afinado` (commits `10f3373`, `6546689`, `7a1002c`; sin subir ni publicar): red del proceso, `/readyz`, tope de 1 MiB a los webhooks, un solo "Marcar vendido", confirmaciones, buscador en Leads, teléfono local, restos del bot ocultos, "Hoy" sin falso "al día", pantalla de error, chat con los últimos mensajes, ponerse al día al reconectar. 2.804 tests en verde y build compilado. Visto en la vista previa: Hoy (escritorio y celular) y el buscador. Fase 0b (ventanas sólidas) en curso. Publicar espera el OK de Croman. |
| 4/10 13:00 | Croman: alcance confirmado (PDI, Compras y tableros afuera); **SAP y Cars siguen emitiendo la factura**; dentro de Sarpy hace falta el proceso de Bitrix: al pasar a Facturación se crea una tarea para Administración y sale un correo de aviso, que hoy va solo a `croman@santarosa.com.py`. Diseño v1 en el repo (`docs/superpowers/specs/2026-10-04-facturacion-design.md`, rama `facturacion`) y cuatro tandas en paralelo (base, correo, asesor, bandeja de Administración). Publicar `afinado` quedó bloqueado por el control de permisos: lo empuja Croman. |
| 4/10 20:06 | **PUBLICADO en producción** (`main` = `d9639e8`): arreglos chicos, ventanas sólidas, Facturación, escala y copia en sombra. Respaldo previo `crm_db_20261004_2000_fase1.dump`; migraciones 0127–0130 aplicadas una por una; app nueva sana (`/readyz` ok, 0 errores). Sin verificar todavía con gente real: el tiempo real por canales. Faltan pasos tuyos: webhook propio en Bitrix, variables `SMTP_*` y tareas `correos` y `bitrix-sombra` en Coolify, invitar a Administración, ventana para el ajuste de Postgres. |
| 4/10 noche | **Fase 1 (escala) y copia en sombra de Bitrix terminadas en la rama `fase1`** (26 commits sobre `main`: afinado + facturación + escala + sombra; sin subir ni publicar). Medido con 60.000 leads y 150 usuarios inventados en una copia: abrir el CRM le tomaba a un asesor 8,4 s + 16,8 s (más que el corte de 8 s: no cargaba) y ahora 19 + 32 ms; mismas reglas de permisos, probadas usuario por usuario. Tiempo real por canales (asesor / marca / empresa) en vez de avisar a los 150 navegadores, verificado contra un Realtime real. Reparto en una consulta (4.000 → 1), rol guardado 60 s, carga paginada y honesta (producción corta en 1.000 filas), Leads por trozos, Excel a pedido. Copia en sombra: solo lectura e inerte, probada contra el Bitrix real (46.306 leads, 112.874 contactos, 727 negocios). 3.465 tests, build y ensayo de las migraciones 0127–0130 en una copia, todo en verde. Falta: publicar (pasos en `DEPLOY.md`), webhook propio en Bitrix, ventana para ajustar Postgres. |
| 4/10 tarde | **Facturación v1 terminada en la rama `facturacion`** (8 commits sobre `afinado`, sin subir ni publicar): pedido desde el lead (cédula o RUC, persona o empresa, nombre o razón social), tarea para Administración, bandeja propia con rol "Administración", Facturada → Vendido, Devuelta → Negociación, aviso por correo a la lista (arranca con `croman@santarosa.com.py`). Revisión de seguridad independiente: sin críticos; arreglados los topes contra abuso de correos (3 pedidos por lead al día, 60 correos por hora) y los menores. Ensayo en copia: `VERIFICACION FACTURACION OK`. 3.065 tests y build en verde. Vista en navegador con datos de muestra. Para publicar: migración 0127 → código → variables SMTP y tarea `correos` en Coolify (`DEPLOY.md`, "Facturación"). |
| 4/10 12:45 | Fase 0b terminada en la rama `afinado` (commit `114525b`, sin subir ni publicar): ningún diálogo se cierra con un clic afuera, 14 `confirm()` y 1 `prompt()` nativos reemplazados, confirmación al liberar desde la ficha, guardia de tests. 2.812 tests en verde y build compilado. El clic afuera no se pudo probar de punta a punta en la vista previa (sus ventanas no tienen cierre real); queda cubierto por tests. |


## Actualización 4/10 noche — importador, propuesta de Cars y correo de Administración (PUBLICADO 23:19, `main` = b24bbd7)
- **Facturación**: el N.º de propuesta de Cars es obligatorio al pasar el lead a Facturación; el correo a Administración ahora es HTML con cabecera de Santa Rosa (propuesta y monto destacados, detalle, observaciones, botón «Abrir en Sarpy»). Migración 0131.
- **Importador de Bitrix → Sarpy** (migración 0132): por olas de marca, con simulacro antes (informe de lo que entraría, lo que no tiene traducción, asesores sin cuenta), reversible y sin avisos ni reparto. Probado con datos sintéticos de forma real y con 50.000 leads. Falta correrlo con datos reales: depende de la copia en sombra (webhook propio de Bitrix).
- Decisiones por defecto a revisar: Facturación/Escrituración de Bitrix entran como Negociación; «Lead en espera» → Contactado; leads sin teléfono no se importan.
