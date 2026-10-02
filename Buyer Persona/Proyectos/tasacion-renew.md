---
estado: activo
firma: d21503c6118b404f2bbd9f6b814faff3ff417be7b1d8e4f640c97bb2dec0e21b
git_rama: main
git_remoto: https://github.com/croman-coder/tasacion-renew.git
git_sin_subir: 1
git_ultimo_commit: '2026-09-30 61fdc69 Auditoría: fecha de la cita sin corrimiento,
  el correo sin "al asesor" y sin baja de cuenta'
hijos: []
nombre: Tasacion RENEW
resumen: Web app que reemplaza la planilla Excel de tasación de usados y el peritaje
  en papel. Fases 1-3, la Fase 4 (salvo el seguimiento) y el circuito en dos manos
  (el asesor carga y entrega, el tasador tasa, gerencia aprueba, el asesor recibe
  el aviso) en producción en tasacion.santarosa.lat (Coolify + Supabase self-hosted
  en SRPY186). Nació del incidente del margen 27% que la planilla no detectó.
resumen_pendiente: true
ruta: /home/croman/Escritorio/Tasacion RENEW
slug: tasacion-renew
stack:
- git
- node
tipo: proyecto
ultima_actividad: '2026-09-30'
---

<!-- hermes:inicio -->
## Estado

| Campo | Valor |
| --- | --- |
| Estado | activo |
| Última actividad | 2026-09-30 |
| Stack | git, node |
| Rama | main |
| Último commit | 2026-09-30 61fdc69 Auditoría: fecha de la cita sin corrimiento, el correo sin "al asesor" y sin baja de cuenta |
| Sin subir | 1 |
| Ruta | `/home/croman/Escritorio/Tasacion RENEW` |
<!-- hermes:fin -->

## Qué es

Web app que reemplaza la planilla Excel de tasación de usados certificados
(Renew). Nació de un incidente real: un tasador cargó 27% de margen bruto
donde la banda es 12–15%, la oferta de toma salió bajísima, el cliente se fue
y escaló al gerente general. Dos defectos del Excel lo causaron: la fórmula
del margen no restaba los gastos de puesta a punto, y el control decía "Mark
Up" pero todos lo leían como margen. La app existe para que eso no pueda
volver a pasar: la fórmula correcta vive en el servidor, la banda por marca
se valida en la base, y salirse de banda exige aprobación del Gerente General
con registro de quién y por qué.

**Estado al 6 de septiembre de 2026: las tres fases del SPEC, los bloques
A, C y B de la Fase 4, y el circuito en dos manos, en producción.** La app
cubre el circuito entero del PR-CU-01: el asesor carga el auto, el cliente,
las declaraciones y las fotos y **entrega**; el tasador hace el peritaje,
busca referencias y fija el precio y **manda a revisión**; gerencia aprueba;
después se decide si el auto entra al stock o va a reventa, se pide la
documentación que le toca a ese cliente, se lo recibe con su chequeo de
entrega y se crea el vehículo en el stock sin recargar nada. Queda el bloque
D (seguimiento por responsable), que espera cuatro decisiones.

731 tests en 76 archivos, tsc limpio, 47 migraciones aplicadas en local y en
el servidor. Probada por Croman el 3/9 ("probé todo y funciona"); el circuito
en dos manos recorrido de punta a punta en el navegador el 6/9 (`docs/manual/circuito.py`).

## URLs y despliegue

| Qué | Dónde |
| --- | --- |
| App | https://tasacion.santarosa.lat |
| Supabase (navegador) | https://tasacion-db.santarosa.lat — solo la API; la raíz responde 404 a propósito |
| Supabase Studio | Fuera del túnel. Solo por SSH: `ssh -L 8103:127.0.0.1:8103 srpy-servidor` y abrir http://localhost:8103 |
| Servidor | SRPY186 (192.168.221.87, alias SSH `srpy-servidor`), Coolify |
| App en Coolify | `waiymmkvernk7ho90bsepogd` (proyecto SRPY, production) |
| Rama desplegada | `main` (desde el 4/9/2026; `fase-1-tasacion` se mergeó por fast-forward y se borró) |
| Auto-deploy | Cron cada 3 min en el servidor (`~/tasacion-autodeploy/check.sh`, `BRANCH="main"`): detecta el push y encola el deploy; un push está en producción en ~2 min |
| Harvester de Clasipar | Cron 4 AM (`scripts/harvester-clasipar.sh`), log en `~/stack/logs/harvester.log` |
| Credenciales | `/home/santarosa/stack/CREDENCIALES.md` en el servidor (chmod 600) |
| Respaldos | `~/stack/backups/` en el servidor (los datos de prueba borrados, chmod 600) |
| SMTP | Gmail. Para la recuperación de contraseña (GoTrue) y, desde el 6/9, para los avisos al asesor: las mismas credenciales, en el entorno de la app en Coolify (`SMTP_*`, `APP_URL`) |

Detalle completo de infraestructura y de cada cierre: `DEPLOY.md` del repo.
Regla de oro que ya costó un incidente: **cada migración se aplica en local Y
en el servidor**. Migraciones aplicadas en los dos lados hasta la **047**.

## Qué tiene hoy

- **La tasación en dos manos** (desde el 6/9/2026). El **asesor** carga
  cuatro pasos —vehículo y cliente, declaraciones del cliente, diez fotos,
  entrega— y **entrega**; no ve valoración, referencias, gastos, margen ni
  peritaje, y el precio de toma le aparece recién aprobado. El **tasador**
  (rol nuevo; gerentes y admin también tasan) abre la misma tasación y hace
  sus seis pasos —peritaje con el estado general 1–5, referencias de
  mercado, valoración, gastos, margen con banda por marca, resumen— con
  cálculo en vivo, y **manda a revisión**. Quien tasa de cero ve los diez
  pasos seguidos. Estados: borrador → **para tasar** → en revisión →
  aprobada/rechazada → vencida / compra concretada. **La máquina de estados
  vive en la base**: en borrador edita el dueño, en para tasar quien tasa;
  la entrega exige chapa, cliente, declaraciones y diez fotos; a revisión
  llega solo una ficha completa; el rol asesor no puede saltar al tasador;
  fuera de banda solo aprueba el Gerente General; una vencida no se
  concreta; ningún cambio de estado se confirma sin su fila de auditoría —
  todo en triggers y RLS, no solo en la app. Lo que se corrige vuelve al
  tasador; al asesor solo con motivo escrito. Quien tasa ve "N esperan al
  tasador" y quien aprueba "N esperan tu decisión" arriba del listado.
- **Avisos al asesor** (6/9/2026): cuando su tasación cambia de mano le
  aparece la novedad en el listado (cartel y chapita, se apagan al abrir la
  ficha) y le llega un correo — tasada (sin precio), aprobada (con el
  **precio de toma**, hasta cuándo vale y el link de CarDoc si está),
  rechazada o devuelta (con el motivo). Nunca margen, gastos, valoración,
  referencias ni peritaje. Cada envío queda registrado y se ve en el
  historial de la ficha.
- **Buscador por chapa** en el listado ("la chapa no hay dos"), que también
  encuentra por modelo, versión y número. Las chapas se guardan normalizadas
  (mayúsculas, sin espacios ni guiones), así que "aad 5150" encuentra
  "AAD5150" — hay un trigger que lo garantiza venga de donde venga el dato.
- **Peritaje del vehículo** (el formulario FO-CU-01, entregado el 4/9/2026):
  33 ítems en cinco bloques colapsables marcados ✓ / Rep / NA con
  observación solo al marcar Rep, prueba dinámica, responsable de taller y
  las cinco declaraciones del cliente. La chapa pasó a ser obligatoria para
  enviar, se cargan los dos años (modelo y fabricación) y transmisión,
  combustible y cilindrada del PY-RN-01. Cada "Rep" se ofrece como gasto de
  puesta a punto. **La ficha imprime el peritaje entero** con Rep en rojo,
  el aviso de indicio mecánico, la firma del cliente dibujada en el celular
  (PNG, hasta 200 KB) y el texto legal reescrito para Santa Rosa Paraguay.
  Sin chapa, sin responsable, con un ítem sin marcar o una declaración sin
  responder, la tasación no sale a revisión — ni por la app ni por un UPDATE
  directo (migración 033).
- **De la reunión del 4/9** (ver más abajo): cada número del estado general
  dice qué significa, las fotos se pueden sacar con la cámara **o elegir de la
  galería** (muchas las manda el cliente por WhatsApp), se agregó la foto del
  **tablero con el motor en marcha** —van diez obligatorias—, se registra
  **cómo tributa la operación** (IVA 10%, 3% o exento), hay un campo de
  **observaciones** que se imprime en la ficha, y "grúa" es un concepto fijo
  de gasto para los autos que vienen de Ciudad del Este.
- **Toma: del auto tasado al auto en el patio** (bloque C, 5/9/2026). Cuando
  la tasación queda aprobada, la ficha suma un bloque con el tramo que el
  PR-CU-01 describe después: si el vehículo **cumple los criterios de ingreso**
  (≤10 años, ≤100.000 km, sin indicio mecánico) y, si no cumple, la
  autorización del gerente con su motivo; la **documentación del cliente** del
  FO-GE-01, donde se elige quién es el cliente (física o jurídica, casado,
  contribuyente) y la lista de los trece documentos se arma sola; la
  **recepción** del FO-GS-01 con sus siete ítems de entrega, el VIN leído del
  auto y el **re-peritaje** ("¿llegó como se tasó?"), donde la diferencia que
  absorbe el cliente baja el precio de toma sin tocar la tasación; y el botón
  que **crea el vehículo en el stock** con los datos de la tasación. Una
  tasación ingresa una sola vez, y sin recepción cargada no ingresa —lo frena
  el RPC, no solo la pantalla.
- **Reventa** (bloque B, 5/9/2026): cuando el cliente no acepta o el auto no
  nos sirve, el gerente lo pasa a reventa con motivo escrito. El precio base
  sale de "la tasación + 3% o USD 300"; como el procedimiento no dice cuál,
  la app calcula los dos y quien publica elige. Un auto en reventa ya no entra
  al stock de Renew.
- **Express**: precio orientativo con marca, modelo, año y 0km, y un botón
  que lo convierte en tasación completa con los datos ya cargados.
- **Stock** (95 vehículos importados de la planilla de Ángel): tablero de
  salud (banda, días en patio, a revisar, sobre el mercado), buscador libre,
  filtros, ficha por vehículo con QR para el parabrisas, impresión de QR en
  lote, movimientos con historial, gastos con foto de factura, galería de
  fotos del patio, alta y edición manual (admin, gerentes, producto). Los
  días en stock cuentan siempre: sin fecha de ingreso, desde el día de carga.
- **Mercado**: cada vehículo del stock se contrasta con los avisos de
  Clasipar del rastreo diario (mismo modelo, año ±1, últimos 30 días, vivos,
  con precio creíble, sin año absurdo ni duplicados del mismo vendedor): publicado a / mediana / rango / desvío / veredicto
  ±10%, y los avisos con link. El harvester busca en Clasipar cada
  marca+modelo del patio y de las tasaciones abiertas, además del listado
  general, y lee el año del título cuando la ficha no lo trae. Desde el
  6/9 (noche) además **busca el modelo solo** cuando "marca modelo" no trae
  nada, **le cree al título** cuando el vendedor eligió otra marca en el
  desplegable de Clasipar, y compara los modelos **sin puntuación** ("X-70"
  = "X70"). Al tasar, los comparables aparecen solos en el paso Referencias
  ("Comparables de X70 2023", con Usar), junto con las referencias usadas
  en tasaciones anteriores y el traído desde un link pegado.
- **Administración**: marcas y bandas de margen, precios 0km (con importador
  y plantilla CSV para Producto), cotización USD, ubicaciones (también
  logística), y **usuarios con roles** (solo admin).
- **Cuenta propia**: cambio de contraseña, idioma (solo español, honesto),
  baja de la propia cuenta (desactivación, el historial queda).
- **Diseño**: sistema propio en `docs/diseno-referencia.md` (stoic. para el
  wizard, Mercury para las pantallas de trabajo). Menú lateral oscuro,
  animaciones con `prefers-reduced-motion`, rojo reservado a la alarma de
  margen (en el stock, solo a la pérdida). Revisado con los siete roles en
  escritorio y celular; **manual visual por rol en PDF** con capturas reales
  (`docs/manual-tasacion-renew-por-rol.pdf`). **716 tests** en 76 archivos,
  tsc limpio.

## Seguridad — lo que hoy está garantizado

Dos pasadas (3/9 y 4/9), cada una con PoC contra la base con el JWT de cada
rol y verificación en producción. Once hallazgos, once cerrados; detalle y
tabla en `DEPLOY.md`.

- **La regla de negocio vive en la base**: gate del Gerente General,
  completitud para enviar, vigencia y auditoría obligatoria están en el
  trigger de `tasaciones`; un `UPDATE` o RPC directo por PostgREST ya no
  esquiva nada.
- **`anon` sin ningún permiso** sobre tablas ni funciones (la anon key es
  pública por diseño). `authenticated` y `service_role` por concesión
  explícita. Las funciones de trigger quedan como están porque GoTrue las
  dispara al crear usuarios — verificado.
- **RLS en todas las tablas**, todas las funciones DEFINER con `search_path`
  fijo y exigiendo perfil activo. Desde la 043 la RLS de `tasaciones` es
  por estado: el dueño escribe en borrador, quien tasa en para tasar, la
  gerencia aprueba lo ajeno; el trigger frena al rol asesor si intenta
  saltar a revisión por PostgREST (probado en la regresión SQL de 15 pasos).
- **Logística no ve costo, precio, margen ni mercado** y no edita fichas de
  vehículo (SPEC §7). Límite conocido: por PostgREST directo aún podría leer
  la tabla, porque mover un auto es un UPDATE sobre ella; cerrarlo requiere
  una vista y rompe las escrituras. Anotado en `DEPLOY.md`.
- Studio fuera del túnel; cabeceras (X-Frame-Options, frame-ancestors,
  HSTS, nosniff, Referrer-Policy, Permissions-Policy); bucket con tipos y
  tope de 15 MB; registro público apagado; `.env` con permisos 600; sin
  secretos en el historial de git; links a avisos validados al dibujarse.
- **Cloudflare tiene activada la ofuscación de emails** y rompía la
  hidratación de `/cuenta` y `/admin/usuarios` (error #418, solo en
  producción). Cerrado del lado de la app (`components/ui/Email.tsx`); no
  depende del panel de Cloudflare.
- Fuera a propósito: `npm audit` marca vitest, vite y postcss/next —
  herramientas de desarrollo y build, no corren en producción, y el fix
  exige saltos mayores. Tarea propia.

## Datos en producción (6/9/2026)

| Qué | Cuánto |
| --- | --- |
| Tasaciones | 1 — la **#1** real (Jetour X70, chapa AAD2525), cargada por Croman el 4/9, con su peritaje. Las 10 de prueba y el usuario `asesor.prueba` se borraron con respaldo |
| Vehículos en el patio | 95 (11 marcados para revisión, con el motivo escrito) |
| Usuarios | 7: Carlos Roman, Fernando Correa, Angel Mino (admin), Gerente Comercial, Gerente General, Prueba Asesor (asesor), Tasador (tasador, 6/9) |
| Avisos de mercado | 1.626 tras la cosecha del 6/9 (528 guardados esa corrida). **500 marcados no usables** con su motivo: compra/permuta, cuota disfrazada de precio, año absurdo (15 + 47) y duplicados del mismo vendedor (92). Nada borrado |
| Recepciones cargadas | 0 — el bloque de toma se estrena con la primera compra concretada |
| Storage | 0 objetos |
| Correos al asesor | 0 — se estrena con la primera tasación que cambie de mano (SMTP verificado desde el contenedor) |

El circuito completo del bloque C se probó de punta a punta **en local**, no
en producción: documentación de una persona física contribuyente (la lista
pasó sola de 4 a 9 documentos), recepción con sus siete ítems, compra
concretada y creación del vehículo en el stock con VIN, año, km, ubicación y
costo correctos. En producción no se cargan datos de prueba.

## Roles

asesor · **tasador** (desde el 6/9) · gerente_comercial · gerente_general ·
producto · logística · admin. La autorización real vive en RLS, en los
triggers y en las server actions; los botones se filtran por rol solo para
no chocar contra "sin permiso".

## 6/9/2026 — el asesor carga, el tasador tasa

Croman cerró la decisión B de la reunión: *"la vista de asesor solo debe
tener nueva tasación y express, nada de lo demás; para tasar no debe estar
peritaje, referencias, valoración ni gastos, solo lo básico más las fotos,
porque esto llega al área que tasa"*. Spec en
`docs/superpowers/specs/2026-09-06-asesor-y-tasador-design.md`.

| Qué | Cómo quedó |
| --- | --- |
| Rol nuevo | **Tasador** = "el encargado de tasación". Gerentes y admin también tasan |
| Estado nuevo | **Para tasar**, entre Borrador y En revisión. En borrador edita el asesor; en para tasar, el tasador |
| Asistente del asesor | Vehículo · Declaraciones del cliente · Fotos · Entrega (botón "Entregar", guarda y cambia el estado en un toque) |
| Asistente del tasador | Peritaje (con el estado general 1–5) · Referencias · Valoración · Gastos · Margen · Resumen |
| Quien tasa de cero | Ve los diez pasos y manda a revisión directo desde borrador |
| Lo que ve el asesor | Estado, lo que cargó y el precio de toma **recién aprobada**. Nada de valoración, referencias, gastos, margen ni peritaje. Menú: Tasaciones, Nueva, Express; el stock le rebota |
| Devoluciones | Lo que se corrige vuelve al tasador (para tasar). Al asesor solo vuelve con motivo, si el problema son las fotos o los datos del auto |
| Base | Migraciones 042 (enums) y 043: RLS por estado, trigger con la lista nueva y dos gates (entrega: chapa, cliente, declaraciones, 10 fotos; revisión: ficha completa), el rol asesor no puede saltar a revisión, fuera de banda no se juzga al entregar |
| Descubierto al probar | El asesor no podía guardar: la fila exigía el cálculo (`pve_usd > 0`, precio de toma…) que él nunca tiene. Las cinco columnas del cálculo admiten NULL mientras se carga; el trigger exige el PVE al enviar |

**Usuarios (6/9, tarde):** producción tiene 7 perfiles. A los 3 admin y los
2 gerentes se sumaron `asesor@santarosa.com.py` ("Prueba Asesor", lo cargó
Croman desde Usuarios) y `tasador@santarosa.com.py` ("Tasador", creado por
la Admin API en el servidor a pedido de Croman, con clave inicial entregada
por chat para cambiar al entrar). Login verificado por password grant contra
Kong local: 200.

## Fase 4 — A, C y B entregados; falta D

Los cinco documentos del sistema de gestión (abajo) son la fuente de esta
fase. El spec y el plan de cada bloque están versionados en
`docs/superpowers/`, y los documentos en `docs/procedimientos/`.

| Bloque | Estado | Qué quedó en la app |
| --- | --- | --- |
| **A — peritaje** | En producción 4/9 | Paso Peritaje con los 33 ítems, chapa obligatoria, firma del cliente y ficha impresa con el texto legal |
| **C — recepción e ingreso** | En producción 5/9 | Elegibilidad (tabla 1) con autorización, documentación del FO-GE-01, recepción del FO-GS-01 con re-peritaje, e ingreso a stock desde la tasación |
| **B — reventa** | En producción 5/9 | Decisión del gerente con motivo y precio base por los dos criterios; bloqueo del ingreso a stock |
| **D — seguimiento** | Spec escrito, sin código | Los trece pasos del anexo B con responsables y plazos |

### Por qué D no se construyó todavía

El anexo B nombra responsables que la app no tiene (Asesor de Post Venta,
Adm. de Ventas, Jefe de Taller, Marketing) y cinco de sus trece pasos ocurren
dentro de CARS, que la app no toca. Construirlo ahora sería inventar un
circuito que después nadie usa. El spec
(`docs/superpowers/specs/2026-09-05-fase4d-seguimiento.md`) deja las cuatro
decisiones que lo destraban:

1. **Los responsables**: ¿se agregan roles nuevos, o el seguimiento se asigna
   a personas concretas? (lo segundo sobrevive a los cambios de organigrama)
2. **CARS**: ¿los pasos administrativos se marcan a mano como hechos, o
   quedan fuera del seguimiento?
3. **Plazos vencidos**: ¿alcanza con verlos en rojo, o hay que avisar por
   WhatsApp o correo?
4. **Dónde vive**: recomendación — pasos 1 a 8 en la tasación, 9 a 13 en el
   vehículo de stock, sin crear una entidad nueva.

Vale la pena tener presente lo que la app ya cubre sin ese bloque: el
historial de estados con fecha, usuario y motivo responde por los pasos 4 a 6,
y los días en stock por el 10.

### Decisiones abiertas de la fase

- **Vigencia**: 15 días en FO-CU-01 y en la app, 30 días o 1.000 km en
  PY-RN-01. Hoy manda la de 15 (`VIGENCIA_DIAS`, y el texto legal la lee de
  ahí).
- **El "2" de la escala 1–5**: en la reunión se definieron el 5, el 4, el 3 y
  el 1. El 2 quedó descrito como el escalón entre el 3 y el 1, a confirmar.

## Reunión del 4/9/2026 — qué se aplicó y qué falta decidir

Croman pasó la grabación completa (69 minutos, transcrita localmente en la
GPU de la notebook; la transcripción **no se versiona**: tiene comentarios
sobre personas). Cada decisión quedó documentada con su minuto en
`docs/reunion-2026-09-04-decisiones.md`.

**Aplicado el 5/9:** buscador por chapa · fotos desde cámara o galería ·
escala 1–5 escrita en pantalla · foto del tablero con el motor en marcha
(diez obligatorias) · tipo de IVA de la operación · observaciones libres ·
grúa como concepto de gasto. **Aplicado el 6/9:** el asesor sin valoración ni
referencias — el circuito en dos manos (sección arriba).

**Confirmado que la app ya lo hacía bien:** el markup mal calculado que
Fernando detectó era el del **Excel**, no el de la app. La app calcula el
margen sobre el precio de venta y deriva el markup como `margen / (1 −
margen)`, que nunca puede dar menor que el margen. Con 13% de margen muestra
14,9% de markup. La depreciación (20% el primer año, 10% sobre el saldo
después) también coincide.

**Esperando decisión de Croman:**

| Qué | Por qué está frenado |
| --- | --- |
| **El cálculo con IVA** | Fernando ofreció pasar "la planilla de cómo se debería calcular". El tipo de IVA ya se registra, pero sin esa planilla tocar el precio sería inventar cómo se reparte plata |
| **Estimada vs. definitiva** | Hoy Express no guarda nada. Para responder "cuántas nos piden por fotos y cuántas vinieron" —la pregunta que abrió la reunión— Express tiene que guardar como estimada, y entonces hace falta su filtro en el listado |

## 6/9/2026 (noche) — avisos al asesor

Croman: *"cuando el tasador hace la tasación se debe actualizar en el
perfil del asesor para que sepa que se hizo, y enviarle un correo con la
ficha, el monto, el link de CarDoc y todos los detalles menos márgenes y
gastos"*.

- **En la app:** cartel verde y chapita "Novedad: …" en el listado del dueño
  (tasada · aprobada · rechazada · devuelta), que se apaga al abrir la ficha
  (tabla `tasacion_lecturas`, migración 044).
- **Por correo** (nodemailer, `lib/correo/`): cuatro eventos; el **precio va
  solo en el de aprobada** — es el único número que el asesor puede
  prometerle al cliente, mismo criterio que la ficha. Nunca lleva margen,
  gastos, valoración, referencias ni peritaje (los tests lo fijan). Cada
  envío queda en `tasacion_correos` y se ve en el historial de la ficha.
- El envío corre con `after()` de Next, después de responder: un SMTP lento
  o caído nunca frena un cambio de estado.
- **SMTP:** las mismas credenciales que usa GoTrue para la recuperación,
  copiadas al contenedor de la app por la API de Coolify (`SMTP_HOST/PORT/
  USER/PASS/FROM` + `APP_URL`), sin pasar por la notebook.
- Probado de punta a punta en local con un SMTP de prueba (`aiosmtpd`):
  los dos correos llegaron con lo que corresponde (`docs/manual/correo.py`).
- **Desplegado** el 6/9 a las 19:33 (commit 4e6839e, contenedor con las seis
  variables SMTP/APP_URL). Desde adentro del contenedor, `nodemailer
  verify()` contra el servidor de correo real: OK (conexión y login). El
  primer correo real sale con la primera tasación que cambie de mano.

## 6/9/2026 (noche) — la búsqueda de referencias traía 0 avisos para X70

Croman: *"arreglá la búsqueda de referencias que trae 0 avisos para X70"*.
Se siguió el dato en vez de tocar código: producción no tenía ningún aviso
Jetour, el log del harvester decía `jetour x70: 0 avisos` todos los días, y
contra Clasipar a mano `@jetour_x70` daba 0 y `@x70` daba 15.

| Capa | Causa | Arreglo (commits b3aa294, 454a174; migración 045) |
| --- | --- | --- |
| Buscador de Clasipar | Los vendedores cargan el Jetour bajo otra marca del desplegable (el primer aviso decía `Marca: Jeep`); la consulta con la marca no los encuentra | Con 0 avisos, el harvester vuelve a buscar el **modelo solo** si es distintivo (con dígito, o de 4 letras o más) |
| Lectura del aviso | Los tres X70 guardados quedaron como Jeep con modelo vacío: el campo "Marca" mandaba sobre el título y un "Modelo:" en blanco capturaba el rótulo siguiente | El extractor recibe el catálogo de marcas y **le cree al título** si nombra una marca conocida que el campo no repite (con freno: "permuto por Toyota" no cambia una Ranger); el campo vacío cuenta como ausente; los avisos sin modelo se releen |
| Comparación | "X-70" y "X70❗❗❗" no eran "X70" | `modelo_comparable()` deja solo letras y números; `avisos_comparables` compara con ella |

Probado contra cuatro fichas reales de X70 y con el harvester corriendo en
el servidor con el código nuevo: 528 avisos guardados, entre ellos 14 X70
y 21 Dashing. Resultado: **la Jetour X70 2023 tiene 6 comparables** (USD
15.780 a 20.764) llamando al RPC como el usuario tasador. 725 tests.

Quedó a la vista un ruido menor y se cerró la misma noche: un concesionario
publica el mismo aviso "año 2027, 0 km" muchas veces con años absurdos
(1965, 1983, 1995…) en el campo Año, para aparecer en todos los filtros del
sitio. Desde entonces `motivosNoUsable()` marca **año en el futuro** y **año
de la ficha distinto del título en dos o más** (un año de diferencia es
normal: año modelo vs. fabricación), el harvester lo aplica a cada aviso y
la migración 046 lo aplicó a lo guardado: 15 + 47 avisos marcados en
producción, sin borrar nada. Y después los **duplicados del mismo vendedor**
(047): mismo título y mismo precio es el mismo aviso; se conserva el más
nuevo y los demás se marcan (92 en producción; un "Dashing GL 2026,
recibimos vehículo y financiamos" estaba siete veces). El harvester corre
`marcar_duplicados_avisos()` al final de cada cosecha.

**Estado final del mercado al cierre del 6/9:** 1.626 avisos, 1.126 usables;
la Jetour X70 2023 con 6 comparables (USD 15.780 a 20.764).

## 19/9/2026 — Ofertas de reventas (en producción)

De la reunión del 18/9 con Fernando: en vez de mandar el auto a Subastas para
que los reventas compitan, la competencia pasa **adentro de Tasación**. Al
entregar una tasación con las diez fotos se abre sola una ronda de 48 h y a
cada reventa activo le llega un WhatsApp con su link personal
(`tasacion.santarosa.lat/oferta/<token>`, sin cuenta): ve el auto y las fotos
sin chapa ni VIN y pone su precio a sobre cerrado (base 0, nadie ve a los
otros). Quien ve números ve el ranking en la ficha, "Valor reventa" en
Valoración y la chapita en el listado; el asesor solo que hay una ronda y
hasta cuándo. Al concretar la compra se elige el destino (reventa o stock) y
al elegido le llega "Renew te confirma…". Una sola ronda por tasación.

- Desplegado el 19/9 (migración 069 + código, `feat/ofertas-de-reventas`
  mergeado a `main`). Admin › Reventas para cargar los reventas. Cron cada
  15 min cierra las rondas vencidas. E2E 13 con un YCloud falso; 58 E2E y
  1178 tests unitarios verdes.
- **Falta de Croman para que salgan los WhatsApp**: `YCLOUD_API_KEY` y
  `YCLOUD_WHATSAPP_FROM` en Coolify, y las plantillas `oferta_renew` y
  `oferta_renew_elegida` aprobadas en YCloud/Meta (idioma `es`). Mientras
  tanto la ronda se abre igual y la ficha ofrece **Copiar mensajes**.
- Falta cargar los ~30 reventas con sus teléfonos.
- Lo de Subastas (CARBID, rama `feat/loop-ofertas-subastas-plan-a`) quedó
  congelado, sin mergear: la spec de Tasación lo reemplaza.

## 29/9/2026 — Sin comparables y estimadas por fotos

Dos pedidos de Rodrigo Sánchez (admin, hace de tasador):

- **Sin comparables directos.** "Tengo que tasar una Renault Kardian y no hay
  ninguna a la venta para comparar." Casilla **"No hay este modelo a la venta"**
  en el paso Referencias, con la explicación obligatoria (≥ 20 caracteres) y el
  precio 0 km cargado: el precio sale del valor contable. Gerencia ve la
  chapita **Sin comparables de mercado** y lo que explicó el tasador. Migración
  071 (aplicada en producción antes del push). Banda, tope 60 %, quién aprueba,
  Bitrix y correo no cambian.
- **Estimadas por fotos, el camino a la vista.** Rodrigo devolvía con "Devolver
  al asesor" las estimadas y el asesor (Rodrigo Retamozo, GWM) no veía el
  resultado: devolver **no muestra el precio**; el asesor ve el precio solo con
  la tasación aprobada. Ahora: botón "Tasar por fotos" en la ficha, "Enviar a
  revisión" como botón principal cuando está lista (y solo para quien puede
  editar), aviso al devolver una ya valorada, y para el asesor la tarjeta "El
  tasador te la devolvió" y la chapita "Devuelta". El 29/9 se destrabaron a mano
  la #52 y la #51 (aprobadas); la #49 y la #54 quedaron pendientes de Rodrigo.
- Tests: E2E 15 (14 tests) y suite completa 72/72. Manual actualizado.
- **Falta / no incluido:** catálogo de precios 0 km de Renault y del grupo (hoy
  solo Jetour: el 0 km se tipea a mano); "Consultar a los reventas ahora";
  sugerir como referencia lo que Renew ya tiene en stock; "Entregar al tasador"
  se ofrece a quien tasa en borradores ajenos.
- **Auditoría (rol de solo lectura para José Amado y Hernán Goydy):** base
  (070, con el barrido de funciones `security definer`), código y cortes de las
  acciones hechos y revisados; la 070 **sigue sin aplicar en producción**; faltan
  las pantallas (Tareas 4–8 del plan: ficha y listado sin botones, stock y
  catálogos en lectura, E2E 14, capítulo del manual y despliegue) y crear los dos
  usuarios.
- Un `git push` desde el repo despliega todo lo commiteado en `main`, aunque
  sea de otra sesión (el 27/9 arrastró a producción los commits de la
  auditoría).

## Documento para el manual de procedimientos

Fernando pidió por WhatsApp "el .md de la app de RENEW" para cargarlo en un
chat mientras redacta los procedimientos de RENEW. Se le entregó
`docs/RENEW-app-tasacion.md`: qué reemplaza, roles, los ocho pasos, el
circuito de estados con quién puede cada transición, qué exige el sistema
para enviar a revisión, el peritaje, el cálculo del precio, el bloque de toma
y el stock. Lo que se decidió pero todavía no existe va en una sección
aparte, para que el manual no describa como vigente algo que no está.
Actualizado el 6/9 con el circuito en dos manos.

**Manual visual por rol (PDF):** `docs/manual-tasacion-renew-por-rol.pdf`,
pedido por Croman el 6/9 ("a prueba de tontos"). Capturas reales de la app
por rol; se regenera con `docs/manual/circuito.py` + `capturar.py` +
`correo.py` + `render.py` (README en la carpeta). Versión final del 6/9
(23 páginas): circuito en dos manos, avisos al asesor, comparables como
aparecen de verdad (captura con seis X70 reales) y Express explicado
(0 km automático, rango desde el contable, "Convertir en tasación
completa").

## Insumos de la fase (recibidos el 4/9/2026)

Croman subió cinco documentos del
sistema de gestión, heredados de Car One (Uruguay) y adaptados a Santa Rosa.
Son el proceso completo de toma de usados. Al 5/9 la app cubre casi todo lo
que describen; esta tabla queda como mapa de qué salió de dónde:

| Documento | Qué es | Contra la app hoy |
| --- | --- | --- |
| **PR-CU-01** Toma de vehículos usados (procedimiento, ed. 08, 16/11/2023) | El proceso entero: criterios de ingreso a stock (≤10 años, ≤100.000 km, sin indicio mecánico grave), ramal a **reventa** (publicación a revendedores con precio base = tasación + 3% o USD 300; solo Jefe/Supervisor de Usados), autorizaciones con motivo registrado "en Tasapp", negociación de precio registrada, **re-peritaje al recibir** el vehículo (mantiene tasación sí/no, nuevo monto, el cliente absorbe la diferencia), legajo en CARS (VO, estados "Pre-ingresado Renew/Reventa" → "Ingresado"), zona de tránsito, y un paso a paso de 13 pasos con tiempos y responsables (vendedor, Adm Ventas/IT, asesor post venta, Jefe Renew, Gte Com Renew, Adm y Contabilidad, taller, Marketing) | La app **es** el "Tasapp" que el procedimiento nombra. Cubre tasación, aprobación y stock. **No tiene**: criterios de elegibilidad con autorización, ramal reventa, negociación registrada, re-peritaje en la entrega, paso a paso por responsable con plazos, ni enlace con CARS |
| **FO-CU-01** Tasación de vehículos usados (formulario PDF, PYFO-CU-01 ed. 01) | Peritaje de ~30 ítems en 5 bloques (exterior, interior, equipamiento incl. scanner y km real, mecánica, accesorios) marcados ✓ / Rep / NA, prueba dinámica, 5 preguntas declaradas (dueños, servicio oficial, vendido por el representante, uso comercial, siniestros), texto legal (validez **15 días**, 1.000 km de diferencia anula), bloque de entrega con firmas de APV y cliente | Hoy: estado general 1–5, daños libres y 9 fotos. El checklist estructurado, las preguntas declaradas, la firma del cliente y el re-peritaje no existen |
| **PY-RN-01** Valorización de toma de usados (formulario, ed. 01) | Es casi la ficha de tasación: datos del vehículo (transmisión, motor cc, combustible, año fabricación vs modelo, OT post venta), precio sugerido de venta, margen neto y margen sobre venta, costo total, partes y MOD post venta, precio de toma, **3 referencias** (marca/modelo/versión, precio, link, transmisión, motor, combustible, origen Rep/Imp directo), firmas en cadena Jefe Ventas Renew → Gte Comercial → Gte General, vigencia **30 días o 1.000 km** | Coincide con el wizard en lo esencial. Faltan campos (transmisión, cilindrada, combustible, año de fabricación, origen de cada referencia) y la firma en tres niveles |
| **FO-GE-01** Documentación a pedir | Checklist por tipo de cliente (siempre / contribuyente / persona física según estado civil / persona jurídica) con "Aplica"; factura a Santa Rosa (RUC 80101704-1) | No existe. Encaja como checklist al concretar la compra |
| **FO-GS-01** Ingreso de usado (ed. 02) | Chequeo de entrega física: título o contrato, cédula verde, manual, dos llaves, formulario de peritaje, factura; responsables de entrega y recepción, conformidad firmada | No existe. Encaja como recepción del vehículo al entrar al stock |
| Captura de **CARS** (en el procedimiento) | Los campos que Adm Ventas carga al dar de alta: VIN, motor, matrícula, odómetro, fecha de llegada, costo y precio en M/E, local, estado PRE-INGRESO, cantidad de dueños, IVA | Hoy el stock nace de la planilla o del alta manual; no hay puente con CARS |

**Inconsistencias entre los documentos, para resolver con Croman antes de
diseñar:** la vigencia es de 15 días en FO-CU-01 (y en la app) pero de 30
días o 1.000 km en PY-RN-01; el texto legal de FO-CU-01 todavía dice "CAR
ONE" y habla de telepeaje (Uruguay); y hay dos "márgenes" (neto de venta y
sobre venta) que hay que definir contra la fórmula única que la app impone.

Los cinco archivos están versionados en `docs/procedimientos/` con su
README; el spec y el plan del bloque A, en `docs/superpowers/`.

## Límites conocidos (no son fallas)

- **Marketplace** no se puede leer: el robots.txt de Facebook lo prohíbe.
  Clasipar cumple el criterio de la Fase 3 (pegar un link precarga precio,
  año y km).
- **Modelos sin mercado**: lo que de verdad no se publica en Clasipar no
  tiene comparables, por más que el rastreo lo busque todos los días.
  Cuidado con la lista de "sin mercado": hasta el 6/9 acá decía Jetour, y
  era falso — Clasipar tenía 15 avisos de X70; el buscador del sitio
  devolvía 0 para "jetour x70" porque los vendedores cargan el Jetour bajo
  otra marca del desplegable (Jeep). Arreglado: el harvester busca el modelo
  solo cuando "marca modelo" trae 0, y le cree al título cuando el campo de
  marca no aparece en él; y los modelos se comparan sin puntuación ni
  decoración ("X-70", "X70❗❗❗" y "X70" son lo mismo, migración 045).
  Resultado la misma noche: la Jetour X70 2023 tiene 6 comparables (USD
  15.780 a 20.764) y aparecieron 21 Dashing. Antes de declarar un modelo
  "sin mercado", probar a mano `clasipar.paraguay.com/motor/autos/@<modelo>`.
- **Tabla 0km incompleta**: ~29 marcas esperan el CSV de Producto (la
  plantilla ya se les mandó). Mientras, el asesor carga el 0km a mano.

### Ofertas de reventas — límites conocidos (19/9/2026)

- El destino elegido después desde la ficha (cuando concretó el asesor) no
  deja fila en el historial: queda en la ronda y en la tarjeta Reventas.
- Si el cambio de estado falla justo después de guardar el destino (dos
  personas a la vez), la ronda queda con destino y sin aviso al reventa; la
  tarjeta lo muestra y se le avisa a mano.
- `/oferta/<token>` inválido responde 200 con la pantalla de "no existe"
  (como `/verificacion`): el shell se streamea antes del `notFound()`.
- "Abrieron" cuenta también la vista previa que hace WhatsApp del link.
- El ranking no desempata dos ofertas iguales por hora.

## Pendientes

- **Bitrix (Fase 5, segunda parte):** el conector responde 403 a todo; el
  spec está escrito y la tasación ya guarda `bitrix_deal_id`. Faltan cuatro
  datos del lado de Bitrix (pipeline de usados, campos `UF_CRM_*`, cómo se
  adjuntan archivos, un webhook con escritura).
- Las dos decisiones de la reunión que siguen abiertas (IVA con la planilla
  de Fernando, Express como estimada) y las cuatro del bloque D.
- **Usuarios reales.** Hoy hay un asesor y un tasador genéricos; cuando
  entre el equipo, un usuario por persona (Catálogos → Usuarios), así el
  aviso por correo le llega a quien cargó.
- La alarma falsa del harvester ("Clasipar cambió su marcado") se resolvió
  el 6/9: los avisos sin bloque de campos se leen del título y la alarma
  salta solo con más del 80 % fallado.
- ~~Avisos con año absurdo~~ — **hecho el 6/9 (noche)**, commit 2be69aa: dos motivos nuevos en `motivosNoUsable()` (año en el futuro; año
  de la ficha y del título con dos o más de diferencia) y la 046 de
  respaldo sobre lo guardado: 15 futuros y 47 contradictorios marcados en
  producción, la X70 2023 conserva sus 6 comparables. Y los **duplicados
  del mismo vendedor** también, la misma noche (047): mismo título y mismo
  precio = el mismo aviso; se conserva el más nuevo y los demás quedan
  marcados. 92 en producción (el "Dashing GL 2026, recibimos vehículo y
  financiamos" estaba siete veces). El harvester lo corre al final de cada
  cosecha.
- Precios 0km de las otras ~29 marcas (CSV de Producto).
- Corregir los 11 vehículos marcados para revisión (los números reales los
  tiene Producto; la pantalla ya existe).
- Actualizar vitest/vite/next en una tarea propia, con sus tests.
- Idioma inglés si algún día hace falta: hoy el selector guarda la
  preferencia pero la interfaz es solo español.

## Relacionado

- [[renew]] · [[asset-web-srpy-renew-usados]] · CARBID (renewsubastas.com.py)
- Los usados tasados acá alimentan el stock que se publica en CARBID.

*Última actualización de esta sección: 29 de septiembre de 2026 (Claude).*
