---
type: guia
created: 2026-10-12
tags: [buyer-persona, directorio, guia]
---
# 📖 Guía para explicar las láminas del directorio (12/10)

> Cómo se calcula y de dónde sale cada número de las tres láminas, y las preguntas que suelen venir. La arma `scripts/laminas_directorio.py` junto con las láminas, con los mismos datos.

## Lámina 1 · Las pruebas con el Buyer Persona (Meta hasta el 11/10)

**Qué es una prueba.** Una campaña de Meta armada con la ficha del Buyer Persona (a quién hablarle, qué formato y qué texto). Innovación la crea en pausa y se activa con el OK de la marca. Renault empezó el 18/09, Mitsubishi el 21/09 y Renew corrió del 23 al 30/09 con USD 100.

**Cómo se calcula el costo por lead.** Lo pagado a Meta dividido por los leads que dejó. Un lead es un formulario completado. En Renew es una conversación de WhatsApp iniciada desde el anuncio, porque esa campaña pide mensajes y no formulario. No incluye honorarios de agencia ni costos internos.

**Renew: USD 0,45 contra USD 0,66.** Prueba (campañas Clavos y Mantecas): USD 99,98 y 223 conversaciones. Campaña habitual de ventas por WhatsApp de la misma cuenta, en los mismos días: USD 248,24 y 375 conversaciones. La diferencia es de 32 %. Ojo: son 8 días y USD 100, sirve como señal y no como promedio. Los 10 autos se eligieron con la ficha: 5 difíciles de vender (campaña Clavos) y 5 de los más buscados (Mantecas).

**Renault: +47 % de leads por día.** Compara toda la cuenta, con las campañas de la agencia incluidas. Antes: 04/09 al 17/09 (14 días), 14,0 leads por día a USD 3,70 cada uno. Con la prueba corregida: 22/09 al 11/10 (20 días), 20,6 leads por día a USD 3,56. La primera versión de la prueba (18/09 al 21/09) se reemplazó por la corregida y no entra en la comparación. Es un antes y después de la cuenta, no un experimento aislado: en ese tiempo la agencia también hizo cambios.

**Renault: Master.** Casi no se pautaba: 0,4 leads por día en la cuenta. Pasó a 6,8: 1,8 de la campaña de prueba y 5,0 de la agencia, que sumó un conjunto propio en Ciudad del Este. Por eso se dice que la prueba «abrió» el modelo, no que lo hizo sola.

**Prueba contra agencia: Renault USD 6,60 contra USD 3,12; Mitsubishi USD 11,68 contra USD 3,10.** Renault: USD 442 y 67 leads la prueba; USD 1.277 y 409 las demás campañas de la cuenta. Mitsubishi: USD 421 y 36 la prueba; USD 1.192 y 385 las demás. Las campañas de la agencia llevan meses optimizándose y la de prueba recién aprende (Meta necesita unas 3 o 4 semanas y unos 50 resultados por semana). En Mitsubishi la prueba fue sobre todo L200, un modelo que la agencia ya pautaba bien: ahí no mejoró el costo.

**Qué contestan los leads.** Del formulario solo se cuentan las respuestas (cuándo piensa comprar, cómo pagaría, para qué lo usa). No se guardan nombres, mails ni teléfonos.

**Lo invertido.** USD 963 en Meta: Renew USD 100, Renault USD 442 y Mitsubishi USD 421, sin honorarios.

**Estado de las campañas de prueba al 11/10.** Renault: Master en pausa, Koleos activo (USD 9 por día). Mitsubishi: Montero en pausa, L200 activo (USD 20 por día). Las campañas de prueba las activa y las pausa cada marca.

**Por qué se recomienda como guía y no como campañas nuevas.** Donde la prueba repitió un modelo que la agencia ya pautaba bien (Koleos, L200) el costo por lead no mejoró. Donde abrió algo nuevo (los usados de Renew, Master) sí funcionó. Por eso: primero se usa para ajustar los anuncios que ya corren, y una campaña aparte solo se justifica donde hay algo nuevo que abrir.

## Lámina 2 · ¿Esos leads convirtieron?

**Qué se mide.** «Contactado» es que un asesor trabajó el lead: lo movió de etapa o lo convirtió en negocio. El pase automático de Bitrix a «Leads contactado» a las 2 horas no cuenta. Es el primer paso del embudo: lead, contactado, test drive, venta. Los datos salen de ROI Pauta del Dashboard Meta (tabla roi_embudo, que se recalcula cada noche), y solo se leyeron conteos.

**Renault: ¿se contactan?** Mismas fechas (22/09 al 11/10) y misma cuenta. Campaña de prueba: 53 leads, 30 contactados (56,6 %). Resto de la cuenta: 360 leads, 202 contactados (56,1 %). Test drive y venta: 0 y 0 en total. Con los leads de 7 días o más (hasta el 04/10, para que hayan tenido tiempo de ser trabajados): 50,0 % (19 de 38) contra 38,5 % (87 de 226). Antes de la prueba (04/09 al 17/09) la cuenta tenía 197 leads con 70,6 % contactados, y con la prueba 413 con 56,2 %. La baja se ve igual en los leads de la prueba que en el resto, así que no viene de la prueba; qué la causa no se midió.

**Mitsubishi: ¿se contactan?** Mismas fechas (24/09 al 11/10) y misma cuenta. Campaña de prueba: 30 leads, 24 contactados (80,0 %). Resto de la cuenta: 328 leads, 195 contactados (59,5 %). Test drive y venta: 0 y 0 en total. Con los leads de 7 días o más (hasta el 04/10, para que hayan tenido tiempo de ser trabajados): 79,2 % (19 de 24) contra 53,0 % (122 de 230). Son pocos leads de la prueba: leerlo como señal, no como promedio.

**Por qué no se compara con el período anterior.** Se compara la campaña de prueba contra el resto de la misma cuenta en las mismas fechas, no antes contra después: el porcentaje de leads trabajados cambia de un período a otro para toda la cuenta (en Renault bajó parejo en la prueba y en el resto).

**Qué todavía no se mide.** La venta: el reporte de ventas del ERP se exporta a mano y llega al 11/09, las pruebas empezaron después y del lead a la venta pasan 13 días (mediana). El ERP casi no trae teléfono ni mail desde agosto, así que el cruce va por nombre y es un mínimo (43 de 422 ventas). Test drive: de 13.123 leads desde septiembre, 4 pasaron por «Test Drive realizado» y 12 tienen venta registrada. Renew: sus campañas son de WhatsApp, Meta no entrega el teléfono y no se pueden seguir hasta Bitrix.

**Qué haría falta para medir la venta.** 1) cargar con regularidad un reporte de ventas del ERP posterior; 2) que el reporte traiga teléfono y mail; 3) que los asesores marquen la etapa «Test Drive realizado» en Bitrix; 4) en ROI Pauta, sumar el total por marca (cuentas madre y de asesores juntas) y el comparativo con el período anterior, como ya se hace con los leads.

## Lámina 3 · Cómo seguir con las demás marcas

**Falta pauta.** Modelo con 10 ventas o más al año cuya pauta «que le corresponde» supera en USD 100 al mes o más a la que tiene. Corresponde = gasto mensual de la marca × % de las ventas de la marca que es ese modelo (ERP, 12 meses). Tiene = gasto mensual de la marca × % de los anuncios de la marca que son de ese modelo.

**Modelos de la lista.** Con unidades disponibles: Jetour X50 (291 ventas al año; 88 disponibles + 47 en viaje al 18/09). Esperar stock: GWM Wingle (44 ventas al año; 0 disponibles + 11 en viaje al 18/09). Confirmar stock antes de pautar: JAC LD250 (17 ventas al año; sin dato de stock). El stock sale de Cars (disponible + en viaje), con la fecha de la última lectura.

**Retargeting y público nuevo.** Retargeting es volver a mostrarle anuncios a quien ya miró la web o abrió el formulario. Público nuevo (frío) es gente que todavía no conoce la marca: conjuntos con intereses o Advantage+ y sin base propia. Se cuentan conjuntos de anuncios, no gasto. En GWM, Jetour, JAC, Renew y JMEV el 95 % o más de los conjuntos es público nuevo.

**Quien acompaña la decisión.** En GWM, Leapmotor y Zeekr la lectura del centro de compra es «ella investiga y él da el paso». Sale de comparar quién hace clic con quién deja sus datos. Detalle en la nota «Centro de compra — todas las marcas».

**Qué falta para la etapa «Después».** Mandarle a Meta qué leads terminaron comprando necesita el OK de Innovación (usa datos de clientes). Google Ads necesita la cuenta de servicio de solo lectura de Google Cloud, que todavía no está creada.

**Dashboards.** El costo por lead y las ventas ya se siguen en el dashboard de Meta Ads (dashboardmeta.santarosa.lat) y en el Comercial de Bitrix (bitrix.santarosa.lat). El Buyer Persona no los reemplaza: suma quién es el comprador y qué anuncio poner.

## Lámina 4 · Lo que hay detrás

**Pauta de Meta.** 1.972 anuncios de los últimos 6 meses de las 85 cuentas: costo por lead, formato, ubicación y duración del video. API de Meta en solo lectura, todos los días a las 06:00. Se compara solo dentro del mismo tipo de cuenta (de la marca o de un asesor) y del mismo objetivo, para no mezclar cosas distintas. Nota «Materiales que funcionan» de cada marca.

**Segmentación.** 772 conjuntos de anuncios activos clasificados por público: nuevo (frío), base propia, similares o Advantage+. Se ve en cada nota de marca, en «Públicos hoy».

**Clasificación con IA (Jev).** Una IA de TypeSafe lee el texto de 1.320 anuncios activos y los clasifica: oferta, argumento, si pone precio o cuotas, si llama a actuar y si apura. También marca el riesgo de publicidad comparativa (hoy 0 avisos para revisar). Lee solo el texto, no la imagen ni el video, y es una ayuda para revisar, no un dictamen. La corrida del 12/10 quedó incompleta (1.000 de 1.121 textos) por un límite de crédito del proveedor.

**Competencia.** 9 casas (Nissan, Nipon, Garden, Chery, Geely, Diesa, DLS, Automaq y Toyotoshi): su web se revisa a las 08:00 y cada cambio queda en la Bitácora (203 desde agosto). Sus anuncios activos en la Biblioteca de Anuncios de Meta se leen a pedido con una sesión de Claude y un navegador real, no corren solos: la API oficial de Meta no entrega anuncios comerciales de Paraguay y la página pública no se entrega a navegadores automatizados (y no se esquiva). La lectura del 12/10 trae 67 anuncios de 10 marcas o casas competidoras (los más vistos de cada uno, solo de sus páginas oficiales) y queda en la nota «Anuncios de la Competencia»: qué ofrecen, cómo arman el texto, hace cuánto corren y qué se puede responder con argumentos propios. Lee el texto, no la imagen ni el video. Es solo de uso interno: la ley de Paraguay no permite nombrar marcas ni modelos de la competencia en publicidad.

**Benchmark y precios.** 662 versiones con precio de lista de 48 marcas (datacarpy.com), contra nuestras 125 versiones (Cars, nuestro sistema). Competencia directa = mismo segmento y precio dentro del ±25 %. Los duelos modelo contra modelo usan solo precios verificados de los dos lados.

**Mercado.** 6,6 % = 4.137 de 62.314 matriculaciones de enero a julio de 2026 entre 80 marcas (CADAM/DNRA). Es matriculación, no facturación.

**Ventas y stock.** 3.662 unidades netas facturadas de abril de 2024 a abril de 2026 (ERP). 43 de 422 ventas recientes tenían antes un lead de Meta: el cruce compara nombre, teléfono y mail cifrados solo en memoria y se guardan solo totales. Es un mínimo: desde agosto el ERP casi no trae teléfono ni mail y el cruce depende del nombre.

**Píxel y analítica web.** 8 sitios (Santa Rosa, Jetour, JAC, JMEV, Mitsubishi, XPeng, Zeekr y Leapmotor) con Google Analytics (formulario enviado y clic a WhatsApp) y píxel de Meta desde el 24 y 25 de septiembre. Falta que el CRM le mande a Meta las conversiones (Conversions API): es el siguiente paso.

**Google Ads.** 97 anuncios de búsqueda ya redactados, uno por ficha, listos para cargar. Todavía no hay resultados: Google dio de baja el token de desarrollador el 9 de septiembre de 2026 y el acceso ahora va por una cuenta de servicio de solo lectura.

**Memoria que aprende.** 55 públicos confirmados (el mismo público se repitió en 25 corridas diarias seguidas), reglas aprendidas y tendencias. La búsqueda por significado usa EmbeddingGemma, un modelo que corre en la propia computadora: indexa 2.148 notas y el texto no sale de ahí.

## Preguntas que puede hacer Valentina

**¿Esto reemplaza a la agencia?** No. Es información: a quién hablarle, qué formato y qué texto. La pauta de cada marca la siguen manejando la marca y su agencia.

**¿Por qué Renew salió mejor que Mitsubishi?** Renew abrió 10 autos usados que no tenían campaña propia. En Mitsubishi se probó sobre todo L200, que la agencia ya pautaba bien.

**¿Los leads de la prueba convirtieron?** En el primer paso, sí: los de la prueba los trabaja un asesor igual o más que los demás de la misma cuenta (lámina 2). La venta todavía no se puede medir: el ERP llega al 11/09 y las pruebas empezaron el 18/09 y el 21/09.

**¿Entonces el Buyer Persona vende más?** Todavía no se puede afirmar. Se midió el costo por lead y que el lead se trabaje; falta la venta. Cuando se cargue un reporte de ventas posterior, ROI Pauta la va a mostrar por campaña y se podrá comparar la campaña de prueba con las demás.

**¿Cuánto costó probarlo?** USD 963 en Meta en las tres pruebas, sin honorarios.

**¿Qué parte de la mejora de Renault es del Buyer Persona?** No se puede separar del todo. Es un antes y después de toda la cuenta, y la agencia también sumó anuncios. Lo que sí se ve: Master pasó de casi no pautarse a 6,8 leads por día, y 1,8 de esos son de la prueba.

**¿Cómo sabemos qué venta vino de Meta?** Se cruza cada venta del ERP con los leads de Meta por teléfono, mail o nombre, cifrados solo en memoria. Es un mínimo, no el total.

**¿Se puede nombrar a la competencia en un anuncio?** No. Por ley de Paraguay solo se usan argumentos propios. La competencia se mira para decidir precio, pauta y argumentos de venta.
