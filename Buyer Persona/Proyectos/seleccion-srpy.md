---
estado: activo
firma: 2c624814492a6996d274953410852454a95f07b6726c92d5160ec0d6ecaa138f
git_rama: main
git_remoto: git@github-croman:croman-coder/seleccion-srpy.git
git_sin_subir: 0
git_ultimo_commit: '2026-10-17 a666a0c feat(postular): store the consent version the
  web says it showed'
hijos: []
nombre: SELECCION SRPY
resumen: null
resumen_pendiente: true
ruta: /home/croman/Escritorio/SELECCION SRPY
slug: seleccion-srpy
stack:
- git
- node
tipo: proyecto
ultima_actividad: '2026-10-17'
---

<!-- hermes:inicio -->
## Estado

| Campo | Valor |
| --- | --- |
| Estado | activo |
| Última actividad | 2026-10-17 |
| Stack | git, node |
| Rama | main |
| Último commit | 2026-10-17 a666a0c feat(postular): store the consent version the web says it showed |
| Sin subir | 0 |
| Ruta | `/home/croman/Escritorio/SELECCION SRPY` |
<!-- hermes:fin -->

## Qué es

Base de talentos de Santa Rosa Paraguay. La página «Trabajá con nosotros» de santarosa.com.py manda cada postulación (datos + CV) a
esta app y Talento Humano la ve en un panel con login: la busca (también **dentro del texto del CV**), la filtra por área, puesto,
sucursal y estado, la exporta a Excel y queda asentado quién vio o bajó cada CV. Nació del pedido de Claudia Galeano (Gerente de TTHH)
del 16/10/2026; que sea una app propia y no Bitrix lo decidió Choco. El plan completo está en `PLAN.md` del proyecto: Fase 0 (reunión con
Claudia), **Fase 1 base de talentos (hecha)**, Fase 2 seguimiento del proceso de selección y Fase 3 reportes.

**Estado al 17/10/2026:** Fase 1 en producción y la web ya publica el formulario. 980 pruebas en 53 archivos, `tsc` y eslint limpios;
`smoke.mjs` 12/12 y recorrido real en Chrome contra producción (`qa-e2e.mjs`), y la web con 93 comprobaciones en navegador
(`qa-trabaja.mjs`, en la rama sin publicar).

**Estado al 20/10/2026 — rediseño y trazabilidad (MERGEADO a `main` el 20/10 por orden de Choco, `6de51f7`; publicado por el autodeploy):** Choco pidió «mejorar mucho más» y la trazabilidad del proceso, con el
diseño de la Agencia IA. Rama `diseno-agencia-ia` de `seleccion-srpy` (spec y plan en `docs/superpowers/{specs,plans}/2026-10-19-seleccion-diseno-agencia-ia*`).
Hecho: tokens y marco de la Agencia IA (barra lateral curva azul, cápsula de destinos, barra flotante en el celular, menú de cuenta), login, Candidatos con
tarjetas de resumen por estado y una tarjeta por fila, ficha con **Recorrido** (qué pasó con la persona, quién y cuándo, armado con lo que ya se registra),
usuarios, configuración y bitácora. 1057 pruebas, tipos, lint y `next build` en verde; revisión independiente hecha el 20/10 (arreglos en `b4cd397`). Sin migraciones ni variables nuevas. **Decidido por Choco:** quién abrió o bajó un CV se ve en el Recorrido para el administrador **y** para Talento Humano (la bitácora completa sigue siendo solo del administrador).
Procesos que faltan y vienen después, uno por uno: *antes* (aprobar el pedido de personal, publicar el aviso), *durante* (pruebas y referencias) y *después*
(oferta, examen médico, contrato, inducción), con Bandeja, Avisos y Reportería; las etapas reales se validan con Claudia en la reunión.

## URLs y despliegue

| Qué | Dónde |
| --- | --- |
| App (panel y API) | https://talento.santarosa.lat — `GET /api/salud` da `{ok, version: 0.1.0+<commit>, db}` |
| Formulario público | https://santarosa.com.py/trabaja-con-nosotros (repo de la web, Netlify; el envío va a `POST /api/postular`) |
| Repo | `croman-coder/seleccion-srpy` (privado), rama `main`; pushes por el alias `github-croman` |
| Servidor | SRPY186 (`ssh srpy-servidor`), Coolify: app `seleccion-srpy` (`mmxf31pyp7eplofkkwotqd2t`), Nixpacks, Node 22, puerto 3000 |
| Base | Postgres 17 en `srpy-postgres`, base y rol `seleccion`. Migraciones **a mano** (nunca `drizzle-kit push`) |
| Túnel | regla `talento.santarosa.lat` en `~/cloudflared-compras/config.yml` + CNAME en Cloudflare |
| **Autodeploy** | cron cada 3 min: `~/seleccion-autodeploy/check.sh` (copia en `scripts/autodeploy-check.sh`). Un push a `main` sale a producción en ~4 min **sin tests y sin migraciones: la migración va primero, a mano**. No reintenta un build fallido ni ve cambios de variables |
| Respaldo | `seleccion-respaldo.sh`, 02:30 diario, `pg_dump` verificado, 14 días, en `/home/santarosa/backups` (mismo servidor: falta activar la copia externa). **Alerta por ntfy** si el último tiene más de 26 h (`seleccion-respaldo-alerta.sh`, cada hora, desde el 18/10/2026) |
| Secretos | `~/.seleccion-srpy-produccion.env` en la notebook (modo 600): pasarlos al gestor de claves |
| Guías | `docs/deploy-coolify.md`, `docs/respaldo.md`, `docs/postular-api.md`, `docs/consentimiento-borrador.md` |

## Usuarios y roles

El ingreso es email + clave (10 caracteres o más). Dos roles: **`admin`** (todo, y además «Usuarios» y «Bitácora») y **`tthh`** (candidatos y
configuración de áreas/puestos). Un admin no puede cambiarse el rol ni desactivarse; desactivar cierra las sesiones. Hoy hay dos:
«Administrador» (`marketing@santarosa.com.py`, de la siembra) y **Carlos Román** (`croman@santarosa.com.py`, admin, 16/10/2026). Las personas
de Talento Humano se crean desde «Usuarios» con el rol `tthh`.

## Lo que tiene hoy

- **Postulación:** anti-robots (señuelo + tiempo), cupo de 5 por hora por conexión y 3 por día por correo, CV validado por su contenido
  (PDF, DOC o DOCX, hasta 5 MB) y texto extraído para buscar adentro. Una persona que vuelve a postular se suma a su misma ficha (por
  documento, correo o teléfono con parecido de nombre).
- **Panel:** lista con filtros, ficha (contacto, CV, estado, notas, etiquetas), exportación a Excel, Bitácora, Configuración y Usuarios.
- **Seguridad:** argon2id, sesiones que se cierran al cambiar la clave, bloqueo de ingreso por intentos, CSP y HSTS, CV con tipo fijo y
  `nosniff`, secretos solo en variables de Coolify.

## Pendiente (17/10/2026)

| Qué | Quién |
| --- | --- |
| Reunión con Claudia (semana del 19/10): etapas reales y perfiles → Fase 2 | Choco |
| Texto de consentimiento (hoy `borrador-2026-10`, la web ya está en vivo), casilla de derechos y retención de datos | Legal |
| Casilla de TTHH con contraseña de aplicación: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` (`SMTP_PORT`, `MAIL_FROM` opcionales) en Coolify | TI / Choco |
| Activar la copia externa: `respaldo-externo.sh` del servidor (restic cifrado a R2/B2) ya copia todo `~/backups`, incluidos estos volcados; falta el bucket y `~/.config/restic/env` | Choco / TI |
| ¿Mismo teléfono con otro nombre es la misma persona? (hoy se exige parecido) | Claudia |
| Cambiar la clave de `croman@` y resetear o desactivar «Administrador»; pasar los secretos al gestor de claves | Choco |
| Publicar los arreglos de la web (rama `fix/deudas-trabaja`, un deploy de Netlify = 15 créditos): manda la versión del consentimiento y guarda el último catálogo | Choco |

## 17/10/2026 — deudas menores cerradas

Un lote de arreglos chicos tras la revisión, ya en producción por el autodeploy: la tabla `intentos` se poda sola (cada 200 intentos, los de
más de 2 días); un id más grande que la base (`/candidatos/2147483648`, filtros, bitácora) da «no encontrado» y no la pantalla de error, y la
página de la bitácora tiene tope; el correo de confirmación saluda solo con el primer nombre y solo si es una palabra de letras (antes
metía hasta 80 caracteres libres en un correo con el remitente de la empresa); la app guarda la versión del consentimiento que manda la web
(`consentimiento_version`). **No se aplicó** `CSP: sandbox` al visor de CV ni `isEvalSupported`: Chrome sigue dibujando el PDF, pero no se pudo
probar en otros navegadores y el beneficio es marginal; y el pdf.js que trae `unpdf` ya no tiene la opción ni ningún camino que evalúe código
(una prueba avisa el día que una versión nueva lo traiga).
