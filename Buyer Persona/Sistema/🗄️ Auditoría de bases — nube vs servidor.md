---
tipo: infraestructura
tags:
  - sistema
  - infraestructura
  - auditoria
  - supabase
actualizado: 2026-10-03
---

# Auditoría de bases — nube vs servidor (3 oct 2026)

Pedido de Croman: todas las bases en el servidor SRPY186, nada de Supabase de la nube. Verificado el 3/10 contra las
variables de los contenedores (solo el host), DNS, el código de cada repo y la base del servidor. Contexto general:
[[Infraestructura y Conexiones]].

## Dónde vive cada cosa

| Sistema | Base hoy | Estado |
|---|---|---|
| Tableros Meta Ads y Bitrix | Supabase propio `bitrix-supabase` | ✅ servidor (las variables de nube que quedan en Coolify se pisan al arrancar) |
| Bot Renew / Botika (botsrpy, wa-gateway, botika.lat) | `bot-supabase` (bot.santarosa.lat) | ✅ servidor desde el 26/9 |
| Sarpy CRM | `crm-supabase` (crm-db.santarosa.lat) | ✅ |
| PDI | `pdi-supabase` (pdi-db.santarosa.lat) | ✅ primaria · ⚠ réplica horaria a la nube + app Vercel de respaldo |
| Tasación Renew | `tasacion-supabase` | ✅ |
| Compras, Cotizador, Callbot, Monitoreo, Advisor Fernando, Directus | Postgres / SQLite propios | ✅ |
| Webs de marca y landings (GWM, Zeekr, Soueast, JAC, Jetour, JMEV, Santa Rosa, Mitsubishi, Expo, Showrooms) | sin base propia (APIs hacia Bitrix) | ✅ no aplica |
| Bloque "RENEW — Leads por WhatsApp" del tablero Meta | Supabase nube `yccall…` (la base vieja del bot) | ❌ roto desde el 25/9 |
| presentacion.santarosa.lat | Supabase nube `emsiaywtz…` | ❌ roto: ese proyecto ya no existe |
| Renew Subastas (renewsubastas.com.py, Netlify) | Firebase | ❌ copia de pruebas lista en el servidor (`renew-supabase`), corte sin decidir |
| renew.com.py (Netlify) | Firestore | ❌ |
| MASI, Novudent, Alba, Aura | nube (otro negocio) | ➖ fuera de Santa Rosa |
| Calidad NPS | Google Sheets / Apps Script | ➖ no revisado |

## Proyectos de nube de Supabase

| Proyecto | Para qué fue | Hoy |
|---|---|---|
| `yccall…` | Botika / botsrpy | vivo y restringido (402 desde el 25/9 19:28). 73 archivos de storage sin copia: no darlo de baja antes de resolverlo |
| `esowcfx…` | PDI | vivo; recibe la réplica horaria del servidor |
| `xpmay…` | MASI | vivo, otro negocio |
| `emsiaywtz…` | padrón de los tableros | no existe (DNS NXDOMAIN) |
| `cisayjv…` | Sarpy CRM | no existe |
| `lfghdok…` | Botika (primero) | no existe |

## Qué rompió y por qué

- Bloque RENEW del tablero: `BOTSRPY_SUPABASE_URL` nunca se repuntó cuando el bot se mudó el 26/9. Desde el 25/9 19:28 no
  hay datos. En el servidor hay 441 contactos de Renew desde esa hora (336 de anuncio, 129 calificados) que el tablero no
  puede mostrar. No se perdió nada: al repuntar vuelve todo el período.
- presentacion.santarosa.lat (repo `croman-coder/performance-santa-rosa`): el front y el servidor hacen login contra
  `emsiaywtz…`. Nadie entra.

## Riesgo principal: no hay copia fuera del servidor

`backup-supabase.sh` (03:15) deja los dumps de los seis Supabase en `~/backups/supabase`, el mismo disco, 14 días. pgbackweb
está instalado con 0 respaldos. La única copia externa era PDI → nube. Si el servidor se pierde, se pierde todo.

## Avance (3 oct 2026)

| Qué | Estado |
|---|---|
| Bloque RENEW del tablero | ✅ arreglado (v1.78): un script del servidor copia cada 10 min los contactos de Renew al Supabase del tablero, sin claves y sin datos personales. `BOTSRPY_SUPABASE_*` ya no se usan |
| presentacion.santarosa.lat | ✅ se puede entrar (login por el Supabase propio, desde el 3/10 22:51). 🟡 Falta cargar `SUPABASE_PROPIO_SERVICE_KEY` en Coolify solo para guardar el perfil y recuperar la contraseña |
| Respaldos de las bases que no son Supabase, Vaultwarden, Uptime Kuma y Coolify | ✅ activos (03:50 diario, 14 días) |
| Copia fuera del servidor (restic a un bucket cifrado) | 🟡 lista; falta el bucket y las claves (README en `SERVIDOR SRPY/respaldos`) |
| Archivos de Storage de los Supabase (el bot tiene 11 GB) | 🟡 no tenían ningún respaldo; entran en la copia externa |

## Pendiente

1. Cargar la variable de presentacion y la copia externa (pasos en el README de respaldos).
2. Corte de Renew Subastas y renew.com.py de Firebase al servidor (decisión de Croman; la copia de pruebas está lista).
3. Apagar la réplica de PDI a la nube cuando exista la copia externa.
4. Limpiar los restos inertes (variables de nube en Coolify, URLs de respaldo en `index.html`, `api/_auth.js` y
   `servidor/cabeceras.mjs`, `SUPABASE_URL_NUBE_ANTERIOR` del gateway) y recién entonces dar de baja `yccall…`, después de
   resolver los 73 archivos de storage sin copia.
5. Guardar la `APP_KEY` de Coolify fuera del servidor; `~/stack/CREDENCIALES.md` está en texto plano en el servidor.
