---
type: reunion
proyecto: agencia-ia
fecha: 2026-10-09
updated: 2026-10-09
tags: [sistema, agencia-ia, reunion]
---
# 🤖 Agencia IA — Reunión del 9/10/2026

> Resumen de la grabación de 52 minutos, transcrita en la notebook (Whisper large-v3 local; el audio no salió a ningún servicio). La transcripción tiene tramos rotos por el ruido: lo marcado con **(?)** hay que confirmarlo.
> Transcripción: `~/Escritorio/AGENCIA IA/reuniones/2026-10-09-transcripcion.txt` (fuera de git).
> Especificación anterior: [[🤖 Agencia IA — Especificación]], que **cambia** según lo de abajo.

## Lo que quedó claro

1. **Se recortan las agencias externas, no el equipo.** El equipo interno usa la IA como apoyo:
   - los diseñadores (Santi y Marcos) para gráfica y video;
   - Evelyn para la pauta;
   - quien hace contenido, para planes de posteos, copies y guiones.

   Es una mesa de trabajo de tres personas, no una idea cerrada.
2. **Andrea lidera el proyecto de la agencia.**
3. **Recorrido de una pieza de diseño:**
   1. el brand pide;
   2. la IA propone y diseña;
   3. se avisa al diseñador, que aprueba o corrige;
   4. Andrea da el control final;
   5. va al brand manager.

   **Si el brand no aprueba, vuelve al diseñador, no a la IA**: el diseñador le da las nuevas indicaciones a la IA. En estrategia, el recorrido es IA → Andrea. Quien coordina marketing no quiere hacer de "tráfico" pedido por pedido.
4. **Áreas de la agencia:**
   - **Estrategia:** campañas 360 y tácticas.
   - **Contenido:** planes de posteos, copies y guiones.
   - **Diseño:** gráfica y video.
   - **Pauta:** Evelyn, que también usa la herramienta.

   La filmación (vendedores, ferias) sigue siendo humana.
5. **Pedidos:** hace falta un **tablero de necesidades** donde el brand cargue lo que necesita, en lugar de escribirle directo al diseñador. No se definió dónde: Bitrix, una plataforma propia, correo o WhatsApp.
6. **Marcas del piloto: JAC y Soueast** (fijas), para salir con todo en el Q1.
   - Cada una necesita una **campaña** desde el 1/1. Se trabaja **en noviembre y diciembre**; octubre queda para terminar de definir todo.
   - "Solo posteos y flyers de una marca" no alcanza ("está feo").
   - **GWM sigue con su agencia.**
   - **Mitsubishi** podría sumarse: la agencia funciona, pero la marca no vende y es cara. **Renault** depende de lo que diga **Agustín**.
7. **Capacitación:** todo el equipo de la agencia tiene que saber usar la herramienta.
8. **Herramientas locales y abiertas:**
   - clones gratuitos del ecosistema Adobe (Photoshop, Premiere) instalados en la red;
   - **MiroFish** (?) para simular cómo reacciona el público a una campaña antes de lanzarla, que va en Estrategia;
   - clonadores de voz y editores de video.
9. **Servidor de marketing aparte.** SRPY186 está al tope: 64 GB de RAM, 12 GB de VRAM y 1 TB, con IAs locales y crons.
   - Propuesta: un **NVIDIA DGX Spark** (128 GB de memoria unificada, unos USD 5.000–5.500). Hay que **investigar el precio exacto**.
   - Sumar un **NAS** para guardar archivos.
10. **Plan de Claude:** se habló de USD 100 (Pro) o USD 200 (Max), más unos USD 20 por usuario (?). Hay que verificar los planes reales.
11. **Benchmark de costos:** lo que cuesta la agencia propia (servidor, plan, usuarios) contra lo que se paga hoy a las agencias. Se mencionó un ahorro de "más de 40 millones" (?). Con dos marcas ya se paga. Se pidió dejarlo **mapeado**.
12. **El cerebro tiene que leer todos los dashboards** (ventas, mercado y los demás).
13. **Organigrama por actores:** quién interviene en cada tipo de pedido.

## Dudoso o sin cerrar

- La web de cada marca la manejan importadores con un *toolkit* estricto. Hay que consultarlo con **Fabri** antes de tocar algo (?).
- "Saúl" aparece varias veces. A veces parece ser Soueast ("la campaña de JAC y de Saúl"), otras una persona ("la conferencia de Saúl… el presupuesto 2027") (?).
- El presupuesto 2027 se está definiendo ahora, junto con el plan.

## Próximo paso

- **Próxima reunión: miércoles 14/10 a las 11:00.**
- Para llevar: la especificación ajustada, el organigrama por actores, el mapa de costos (servidor, plan y usuarios) y el precio exacto del DGX Spark.
