---
tipo: proyecto
tags:
  - sistema
  - croman-ads
  - logica
  - ads
actualizado: 2026-10-07
estado: fundación 4.0 publicada en producción (1ffb42d, 7-oct 06:14); sigue 4.1 (Resumen y Rendimiento) y la etapa 5a (MCP con el plan de Croman)
---

# Croman Ads — etapa de lógica, fundación 4.0 (6 y 7 de octubre de 2026)

**Producción:** https://ads.santarosa.lat (Coolify, rama `rediseno-ads` del repo privado `croman-coder/APP-DE-PAUTAS`). Commit publicado: `1ffb42d`. Antes: `783c8ed` (punto de vuelta).
**Guía para quien siga:** `~/Escritorio/croman-ads-dashboard/docs/design/logica.md` (módulos, la regla de oro de cada uno, cómo se agrega una moneda y una pantalla, el candado, cómo se vuelve atrás, lo pendiente).
**Spec y plan:** `docs/superpowers/specs/2026-10-06-etapa-logica-design.md` y `docs/superpowers/plans/2026-10-06-etapa-logica-4-0-fundacion.md`. Registro de cada decisión y reseña: `.superpowers/sdd/2026-10-06-etapa-logica-4-0-fundacion/progress.md` (git lo ignora).

## Qué cambió (casi nada se ve; todo se siente)

La etapa 1 cambió cómo se ve la plataforma; esta le pone **cimientos para que las cifras sean confiables**. 14 tareas (4.0.0 a 4.0.13):

| Pieza | Para qué |
|---|---|
| `dates.ts` | Todo día es `YYYY-MM-DD` en `America/Asuncion`; el rango se llama `{ since, until }`. |
| `money.ts` | Toda conversión de dinero (a Meta y de vuelta) pasa por `aMenor`/`deMenor`; una moneda solo se escribe si está verificada (hoy solo USD; el guaraní está bloqueado hasta correr `scripts/verificacion/moneda-meta.ts`). |
| `metrics.ts`, `format.ts` | Un cociente sin con qué dividir es `null` y se pinta «—»; `contactos = lead + chats` (`lead` y `lead_grouped` son el mismo conteo: no se suman). |
| `meta-http.ts` | Todo pedido a Meta con semáforo, plazo, uso y token redactado; nunca sale a otro origen. |
| `api-cliente.ts` + `use-api.ts` | Un pedido, una clave, un vuelo; lo de una persona o cuenta no pasa a otra. |
| `cuenta.tsx` | La cuenta elegida vive en una cookie (`ads_cuenta`): la primera respuesta ya la sabe, sin destello. |
| `MarcoApp` + grupo `(app)` | La barra y el riel se montan **una sola vez**; las 19 pantallas devuelven solo su `<main>`. Con el diagnóstico retrasado, cinco pantallas hacen **1** pedido (antes 9). |
| Tablas `app_settings`, `account_goals` | Tasa del guaraní y metas por cuenta (costo objetivo y tope diario). Migradas en el servidor el 7-oct con respaldo previo. |
| `scripts/ratchet-logica.mjs` | El candado: ninguna convención nueva vuelve a la forma vieja (7 patrones; solo se aprieta). |

## Cómo se trabajó

Subagent-driven: un implementador por tarea, reseña (spec + calidad) con rondas de arreglo, **puerta** (`scripts/gate.sh`: tsc, 4.474 pruebas, 4.543 con base de datos, build, galería fuera de producción, humo de la imagen) y una **revisión independiente de toda la rama** en tres partes (aislamiento, dinero/Meta/fechas, migración/scripts/pantallas): ningún crítico. Arregló, entre otras: el borrador de «Crear con IA» que pasaba de una persona a la siguiente en el mismo navegador, «Santa Rosa Automotores» en el prompt del asistente, y un rollback del plan que `publicar.sh` no podía hacer.

## Decisiones que conviene recordar

- **El plan de Claude de Croman no se puede enchufar al panel «Asistente» de la web** (hay que usar clave de API). Se eligió ambas: MCP de la plataforma (`/mcp`, token personal revocable) para su Claude, y el panel con una clave barata y con tope de gasto (la carga Croman en Coolify como `ANTHROPIC_API_KEY`; hay que confirmar que `CHAT_MODEL` sea un id válido).
- **Obsidian en las dos direcciones:** la plataforma lee el vault (etapa 5a) y escribe una nota de estado diaria en `Sistema/` con solo agregados (etapa 5e).
- Un evento de cambio de cuenta se valida; `/login` borra la cuenta elegida también de quien tiene sesión y es redirigido (costo visible, documentado).

## Pendiente conocido (cada uno con su etapa en la guía)

- 4.1: Resumen y Rendimiento con el marco único; apilado de avisos, `error.tsx` y `loading.tsx` del grupo `(app)`; los 11 `/ 100` de lectura de presupuestos; `usePlataformas`; segunda pestaña vieja que conserva lista y chip mientras otra persona ingresa; `hoy()` del navegador y las ventanas UTC de 3 rutas.
- 4.2: escrituras con tope y moneda; guaraní.
- Cloudflare (de Croman): apagar el Web Analytics automático (rompe `offline.html`) y el `Cache-Control` de `/sw.js` (`max-age=14400`): son los dos «MAL» que deja `verif-produccion.py` por fuera aunque el código esté bien.

## Cómo seguir

Primero verificar con una sesión real el recorrido de cinco pantallas. Después: plan de la etapa 5a (MCP + lectura del vault) y 4.1.
