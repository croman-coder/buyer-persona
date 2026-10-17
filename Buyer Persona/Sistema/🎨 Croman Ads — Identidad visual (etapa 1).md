---
tipo: proyecto
tags:
  - sistema
  - croman-ads
  - diseno
  - ads
actualizado: 2026-10-06
estado: etapa 1 publicada en producción (H1 a H3); sigue el sub-proyecto 4 (lógica por sección)
---

# Croman Ads — identidad visual, etapa 1 (5 y 6 de octubre de 2026)

**Producción:** https://ads.santarosa.lat (Coolify, rama `rediseno-ads` del repo privado `croman-coder/APP-DE-PAUTAS`; cada push redespliega en 2 a 4 minutos). Commit publicado: `6b6e33b`.
**Guía para quien siga:** `~/Escritorio/croman-ads-dashboard/docs/design/identidad.md` (13 secciones: marca, tokens, reglas, voz y glosario, el híbrido, plataformas, atajos, componentes, decisiones, cómo verificar, limitaciones, pendientes).
**Plan y registro:** `docs/superpowers/plans/2026-10-05-identidad-visual-etapa-1.md` y `.superpowers/sdd/2026-10-05-identidad-visual-etapa-1/progress.md` (un reporte por tarea y la revisión final independiente).

## Qué se hizo

Croman pidió «mejorar por completo la identidad visual» tomando como referencia el CRM Sarpy y saleads.ai. Dirección elegida por él: **híbrido CRM + SaleADS, oscuro por defecto**, con modo sobrio (`?fx=pro`) que deja el CRM tal cual.

| Hito | Publicado | Qué se ve |
|---|---|---|
| H1a | 5-oct 19:51 | tokens, fuentes, tema, marca, shell (barra con cápsula, selector de plataforma Meta · Google · TikTok, selector de cuenta, riel, cápsula del celular) y las 20 pantallas con la piel nueva |
| H1b | 5-oct 21:08 | login a una columna, 404, 500 y mantenimiento; **app instalable** (service worker que nunca guarda HTML ni `/api`, página sin conexión, instalación guiada en Chromium e iOS) y pulido para celular |
| H2 | 6-oct 01:28 | componentes base (`<dialog>` nativo), galería `/design` (solo desarrollo), **asistente nuevo** (panel, orbe, burbuja con avisos reales), **paleta Ctrl+K**, **atajos de teclado** |
| H3 | 6-oct 05:18 | títulos a 28 px, botones en pastilla, Resumen como pantalla de referencia, glosario en español, accesibilidad (interruptores, orden de Tab, títulos de pestaña), guía de identidad, prueba de contraste y los arreglos de la revisión final |

Además, un **hotfix el 5-oct 20:59**: el selector de cuenta no se podía recorrer con las ~91 cuentas (lo vio Croman en producción). Lección guardada: toda lista o menú se prueba con el volumen real y con toque real.

## Cómo se trabajó

Subagent-driven: un implementador por tarea (con pruebas en rojo primero, mutaciones y capturas), verificación propia del controlador en un Chromium real con 91 cuentas simuladas, una **puerta por hito** en una copia limpia (`tsc`, 3.409 pruebas, 3.434 con base de datos, `next build`, humo de la imagen Docker con 54 rutas y roles) y una **revisión final independiente** (0 críticos, 3 importantes arreglados antes de publicar; el más relevante: el asistente conservaba la conversación entre sesiones en la misma pestaña).

## Decisiones que conviene recordar

- Se borraron «Insights» y «Top performer» de Resumen: no están en la composición que aprobó Croman el 3-oct. Se recuperan del historial (`git show 1594cac:src/components/TopPerformer.tsx`).
- Resumen **no tiene serie diaria ni proyección**: el pedido de datos actual solo trae el total por campaña. Es del sub-proyecto 4 (lógica por sección), igual que el estado real de entrega y el objetivo de la cuenta.
- «Estrategia» solo dentro del flujo de IA; «campaña» en todo lo demás (decisión de producto para Croman).
- Tres pares de contraste de la spec no llegan a 4,5:1 y quedan documentados (texto de éxito y de aviso sobre el lienzo claro, que ninguna pantalla usa).

## Pendiente de Croman

1. **Probar en el teléfono:** instalar la app (Android: menú «Más → Instalar la app»; iPhone: Compartir → Añadir a pantalla de inicio), el selector de cuentas, la paleta, el asistente y el teclado de iOS.
2. **Decidir:** (a) el beacon de Cloudflare Web Analytics bloqueado por nuestra política de seguridad: apagar la inyección automática en Cloudflare (recomendado) o permitirlo; (b) el resplandor violeta del orbe; (c) si quiere un activador de `/mantenimiento`; (d) embeber la fuente en la página sin conexión; (e) si quiere «Top performer» e «Insights» de vuelta, rediseñados.
3. **Pedir ya la app de TikTok** (tarda semanas en aprobarse) y crear la cuenta de servicio de Google de solo lectura: ver `docs/superpowers/specs/2026-10-05-plataformas-google-tiktok-design.md` (sub-proyecto 6).

## Lo que sigue

Sub-proyecto 4: la lógica y las funciones por sección (`useApi`, moneda y fechas en `America/Asuncion`, estado en la URL, «Por marca» y «Por vendedor», serie diaria y proyección reales), más los nueve diálogos propios que siguen sin foco atrapado y la campaña dentro de la paleta. Después el sub-proyecto 6 (datos reales de Google Ads y TikTok Ads).
