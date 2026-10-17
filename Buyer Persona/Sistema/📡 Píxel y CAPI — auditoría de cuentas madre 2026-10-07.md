---
tipo: auditoria
tags:
  - sistema
  - croman-ads
  - pixel
  - capi
  - meta
actualizado: 2026-10-07
estado: auditoría de solo lectura hecha; falta decidir qué medir y armar el envío de CAPI desde Bitrix
---

# Píxel y CAPI — auditoría de las cuentas madre (7-oct-2026)

Pedido de Croman: que las cuentas madre tengan lo que muestra la pantalla **Pixel y CAPI** de Croman Ads (píxel activo con eventos y Conversions API configurada) «para poder medir». Auditoría de solo lectura con el Ads MCP de Meta (`ads_get_datasets`), 7-oct-2026 ~08:50 (-03). «Servidor» = `server_last_fired_time` del dataset (eventos de CAPI); «navegador» = `last_fired_time`.

| Cuenta madre | Cuenta | Dataset (píxel) | Navegador | CAPI (servidor) |
|---|---|---|---|---|
| Jetour | `494721666377008` | Jetour Paraguay — Web (creado 25-sep) | hoy | **nunca** |
| GWM Paraguay | `763951659027712` | VENTAS GWM (2024) | hoy | **nunca** |
| Renew Usados | `1006324631233144` | Renew Paraguay (+ «Ventas Renew 2025», «VENTAS_RENEW», «Renew»: 4 en total, solo el primero dispara) | hoy | **nunca** |
| Mitsubishi Paraguay | `506680188632635` | Píxel de Mitsubishi Paraguay (jun-2026) | hoy | **nunca** |
| Zeekr Paraguay | `1269532904152087` | Zeekr Paraguay | hoy | **nunca** |
| Leapmotor Paraguay | `1277218516594487` | Leapmotor Paraguay — Web (el de la captura de Croman: 830 PageView, 211 ViewContent, 5 Lead, 0 Purchase) | hoy | **nunca** |
| JMEV | `1254617639244434` | JMEV Paraguay — Web | hoy | **nunca** |
| JAC Paraguay | `2641166576069195` | Santa Rosa JAC \| Pixel (+ 3 datasets: «Santa Rosa \| JAC 2», «PIXEL RENEW DATA», «WhatsApp Marketing Message Event Sharing»; dos pertenecen a otro negocio, `697701823689352`) | hoy | **sí, hoy** (la única) |
| Renault Paraguay Oficial | `984754555983141` | Renault Paraguay (abr-2025) | **nunca disparó** | nunca |
| Renault Santa Rosa Paraguay | `956049245637827` | no visible: la cuenta no está habilitada en el Ads MCP | ? | ? |
| Soueast Paraguay | `1966396187518765` | no visible: la cuenta no está habilitada en el Ads MCP | ? | ? |
| Multimarcas | `1017217342783272` | **sin píxel** | — | — |
| Karry Utilitarios | `387460907784413` | **sin píxel** | — | — |

## Lectura

- Siete marcas ya tienen el píxel del sitio disparando (navegador), pero **ninguna manda eventos desde el servidor salvo JAC**: la pantalla dice «Conversions API: no configurado» y es verdad. Lo que no llega es el envío de **leads y ventas del CRM (Bitrix)** al endpoint `POST /api/capi/event` de Croman Ads (con `x-capi-key` = `CAPI_INGEST_KEY`; el servidor hashea email y teléfono con SHA-256 y no guarda el dato crudo).
- **Renault**, la marca más grande, tiene su dataset «Renault Paraguay» sin un solo evento: el píxel no está instalado o está en otro dataset.
- Multimarcas y Karry no tienen píxel.
- Renault Santa Rosa y Soueast no se pudieron auditar por el MCP (hay que usar el token de Graph).
- JAC tiene datasets duplicados y repartidos entre dos negocios: conviene dejar uno solo como fuente de verdad.

## Siguiente

1. Croman decide qué se mide (leads, ventas cerradas o ambos) y confirma la lista de cuentas madre.
2. Envío desde Bitrix al endpoint de CAPI por marca (mapa marca → dataset), con `event_id` para no duplicar con el píxel y con la prueba de eventos de Meta.
3. Instalar el píxel donde falta (Renault, Multimarcas, Karry) y auditar Renault Santa Rosa y Soueast con Graph.
4. Un tablero «todas las cuentas madre» en la pantalla Pixel y CAPI (hoy es por cuenta).

## Diseño (7-oct-2026)

Spec: `~/Escritorio/croman-ads-dashboard/docs/superpowers/specs/2026-10-07-medicion-pixel-capi-design.md` (sub-proyecto 7, etapas 7a a 7e). Decidido con Croman: **leads y ventas cerradas**, con un **cron en el servidor** (Python, junto a los de Buyer Persona) que lee Bitrix y manda a un endpoint de Croman Ads que hashea, evita duplicados (tabla `capi_eventos`) y habla con Meta. Hechos clave: Bitrix no guarda ningún ID de Meta (el cruce es por email y teléfono hasheados), Bitrix subestima las ventas (30 al mes contra ~400 del ERP; 10 % tienen lead de Meta) y el endpoint actual no puede funcionar (hallazgos L-30 y L-35).
