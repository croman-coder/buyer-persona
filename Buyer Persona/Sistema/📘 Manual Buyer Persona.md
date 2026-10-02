---
tipo: manual
actualizado: 2026-09-26
tags:
  - buyer-persona
  - manual
  - meta-ads
  - google-ads
  - curva-de-aprendizaje
  - remarketing
---

# 📘 Manual — Buyer Persona Santa Rosa

> Cómo está armado, cómo leerlo y cómo usarlo para pautar en Meta y, próximamente, en Google (sección 4). Para el estado técnico ver [[Infraestructura y Conexiones]]; para lo pendiente, [[🔍 Auditoría Buyer Persona 2026-09-16]].

## 1. Qué es

Un sistema que **todos los días a las 06:00** lee tres fuentes reales y regenera, sin intervención, ~75 buyer personas + 288 piezas de marketing + 12 notas de audiencias, y las deja en este vault:

| Fuente | Qué aporta | Ventana |
|---|---|---|
| **Meta Ads** (81 cuentas, 20 páginas) | demografía real (edad/género), copy de anuncios vigentes, placement, leads de formulario agregados, audiencias existentes | 90 días |
| **ERP** (`FacturacionUnidades.xlsx`) | ventas reales por marca/modelo/versión, precio facturado, sucursal, retoma | abr-2024 → última carga |
| **Bitrix24** | leads por canal, conversión, deals ganados/perdidos, ticket | 90 días |

Nada personal entra al vault: nombres, teléfonos, emails y VIN se descartan antes de agregar.

## 2. Dónde está cada cosa

```
Buyer Personas/
├── Buyer Personas MOC            ← empezar acá (índice general, agrupado por marca)
├── <Marca>/                      ← una carpeta por marca (Jetour, GWM, Renault, Mitsubishi, ...)
│   ├── <Marca>.md                   índice de la marca: tabla de modelos (edad, género, ventas, pauta, brecha, presupuesto)
│   ├── Comprador <Marca>.md         persona de la marca
│   ├── <Marca Modelo>.md            una nota por modelo (ej. "Renault Kwid", "Mitsubishi L200")
│   ├── Audiencias Meta - <Marca>.md públicos ya guardados en Meta
│   └── Marketing/                   Meta Ads | Google Ads | Email | WhatsApp - <nota>  (copy listo, legal)
├── Segmentos/                    Segmento SUV / Pickup / Hatchback / Furgoneta / Eléctrico / Camión (+ Marketing/)
├── Audiencias/                   Semillas Custom Audiences - Ventas Reales · 🔁 Base de Recompra (ERP)
└── Buyer Persona Real - Meta 90 dias       (perfil global sobre 17.800 leads)
```

> Desde el 18-sep-2026 las notas ya no llevan número ("Persona 22 - Modelo ..."): se llaman por marca/modelo, así los links no se rompen y el vault se lee Marca → modelos (pedido de marketing, ver [[🎧 Feedback Marketing 2026-09-17]]).

Tags para filtrar: `#marca/jetour` (marca + todos sus modelos) · `#modelo/jetour-x70` · `#segmento/pickup`.

> [!info] Notas de `Marketing/`: qué se puede usar tal cual (26-09-2026)
> **Google Ads, Email y WhatsApp** no prometen tasas, plazos, garantías ni urgencias: salen del modelo o la marca y de los temas que repiten sus anuncios. La **oferta del mes** (planilla de acciones, con sus condiciones) y el **stock** del ERP van en un bloque aparte, ya redactados, para sumarlos después de confirmarlos con la marca. Si el stock no tiene **unidad de test drive** del modelo (hoy, 12 modelos 0km), los textos invitan a verlo en el salón en vez de prometer la prueba. Cada corrida lo revisa sola.
> **Meta Ads** todavía trae «garantía de 5 años» y «financiación a 60 meses» fijos en todas las notas: no usar esas dos líneas sin confirmarlas.

> [!info] El mismo vault, en 3D
> Todo esto se ve también como globo en **https://cerebro.santarosa.lat** (login de los tableros). Instructivo para brands y equipo: [[🧠 Cómo usar el Cerebro Santa Rosa]].

## 3. Cómo leer una nota de modelo

Ejemplo: `Renault/Renault Kwid`

Cada ficha arranca con un bloque plegado **«Cómo leer esta ficha»** que repite lo esencial de esta sección: qué es, de dónde sale cada dato y por qué dos números pueden no coincidir. Desde el 2026-09-22 cada bloque lleva además una línea en cursiva con *qué es / de dónde sale / cómo leerlo*.

### Por qué dos números no coinciden (lo que más se pregunta)

Cada fuente tiene su propio corte de fecha, y la ficha lo dice al lado de cada número:

| Fuente | Ventana | Qué mide |
|---|---|---|
| **Meta** | últimos 90 días | clics por edad/género, temas de los anuncios, respuestas de formulario, gasto y CPL |
| **ERP** | histórico hasta la última carga (la fecha aparece en la ficha) | ventas facturadas, versiones, precio real, retoma, sucursal |
| **Bitrix** | últimos 90 días | leads de todos los canales, convertidos, deals |
| **Planilla semanal de negociación** | una semana | promesa, venta del mes a esa semana, negociaciones abiertas |
| **Datacar** | vigente | precio de lista propio y de la competencia |

Casos típicos:
- **«Objetivo del mes 5 de 32» y «venta MTD 0»** → el objetivo sale del ERP (hasta la última carga) y el MTD de la planilla semanal (una semana puntual). Manda el ERP.
- **«Leads 1.057» en Leads reales y «Leads 1.601» en el CRM** → los primeros son solo formularios de Meta; los segundos, todo lo que entró a Bitrix por cualquier canal.
- **«Convertidos 6» y «Deals 0»** → convertido es el lead que pasó a negociación; deal es la negociación con monto cargada. 0 deals = Bitrix no tiene negociaciones cargadas en la ventana, no que no se vendió. La venta está en «Ventas reales (ERP)».
- **Precio facturado máximo mayor que el de lista** → el facturado incluye versiones anteriores, accesorios y otros períodos.
- **Edad y género** → son de quién hace **clic** en los anuncios, no de quién compró: el ERP no guarda ninguno de los dos.

| Bloque | Qué dice | De dónde sale |
|---|---|---|
| **Perfil Resumido** | edad/género **con %**, período leído, marca (link), ventas reales, pauta real, **brecha pauta/venta**, ticket | Meta + ERP |
| **Demografía** | rango de edad y género dominante con %, distribución por edad, y si el perfil es **propio del modelo** (anuncios que lo nombran, ≥100 clics) o **heredado de la marca** | Meta a nivel anuncio, ponderado por clics — quién hace clic, no quién compra |
| **Intereses y comportamientos** | temas que aparecen en los anuncios que ese público ve y clickea (% de anuncios por tema). No son intereses declarados | texto de los anuncios de Meta |
| **Nivel socioeconómico (estimado)** | AB / C+ / C / C-/D, con las señales usadas: precio facturado, financiación vs contado, iPhone vs Android, zona | cálculo propio; Meta no lo entrega en PY |
| **Comportamiento de compra** | versiones más vendidas, de qué marca vienen (retoma = entregó un usado), sucursal, precio real facturado. En una nota de modelo ya no aparecen categorías ni canales globales del portfolio | ERP |
| **Dolores / Objetivos / Motivaciones** | qué le preocupa, qué busca, qué lo mueve. La primera línea del bloque dice cuántos anuncios se leyeron y si eran del modelo o de la marca | copy real de los anuncios de **ese modelo** (o de su marca si tiene pocos). Un híbrido ya no recibe la «ansiedad de carga» de los 100 % eléctricos |
| **Estrategia Recomendada** | mensaje, **oferta vigente** (el descuento real de la planilla de acciones, no una regla genérica), **formato** (Reels/Stories vs Feed), **públicos hoy** (% de adsets a público frío), **presupuesto sugerido** por modelo y la línea *De dónde sale*. El CPL es el de toda la marca; si el modelo tiene campaña propia, el real es el de esa campaña | placement, targeting y gasto reales de Meta + peso del modelo en ventas del ERP + planilla de acciones |
| **Leads Reales** | leads de **toda la marca** (los formularios son por cuenta), cuántos pidieron **este modelo** y su %, modelos más pedidos con las variantes unificadas («koleos_», «renault_koleos» y «koleos» son uno solo), forma de pago, ciudad, interés | formularios Meta, agregado, sin datos personales |
| **Embudo CRM** | leads → convertidos → deals ganados, win rate, ticket, con la definición de cada término en la ficha | Bitrix, por marca |
| **Precio de mercado y competencia** | precio de lista, segmento, competidores a ±25 % de precio y solape con modelos propios. **Uso interno** | Datacar |
| **Stock, oferta y objetivos** | stock y días promedio, precio de lista y descuento vigente, presión de stock, objetivo del mes y acumulado **según el ERP**, y la línea del equipo comercial **según la planilla semanal** (corte distinto, la ficha lo aclara). **Uso interno** | ERP, planilla de acciones, budget, planilla de negociación |
| **Contenido Relacionado** | sus 4 piezas de marketing + audiencias de la marca | links |

### La brecha pauta/venta (lo más accionable)
Compara el % de ventas del modelo dentro de su marca contra el % de anuncios:

- 🟢 **sub-pautado** → vende mucho con poca pauta. Candidato a **escalar** presupuesto.
- 🔴 **sobre-pautado** → mucha pauta, poca venta. **Revisar** creatividad, oferta o audiencia.
- ⚖️ equilibrado.
- 🆕 **lanzamiento** → hay pauta pero el ERP todavía no registra ventas (modelo nuevo o ERP desactualizado).

> El ERP se carga a mano; la fecha hasta la que llega aparece en la misma línea. Si la pauta es más nueva que el ERP, la brecha de los lanzamientos no es real.

## 4. Pauta con el Buyer Persona — Meta Ads hoy, Google Ads próximamente

*Actualizado el 26-09-2026.* Meta está conectado y se usa todos los días. Google Ads tiene el conector escrito y espera credenciales (4.5). Todo lo que sigue se apoya en una idea: **cada plataforma tiene su curva de aprendizaje, y una campaña se juzga por su curva, no por una semana suelta.** El estudio de base y la comprobación con nuestras cuentas están en [[📈 Curva de aprendizaje — Google Ads vs Meta (26 semanas)]] (uso interno).

### 4.1 Qué le da el Buyer Persona a cada plataforma

| Del Buyer Persona | En Meta Ads (hoy) | En Google Ads (próximamente) |
|---|---|---|
| **Quién hace clic**: edad, género, zona | Edad y zona del conjunto. Con público Advantage+, como sugerencia y no como límite | Ajustes por edad, género y ubicación; señales de audiencia en PMax |
| **Temas que atraen** (intereses observados) | Ángulo del creativo e intereses sugeridos | Temas de búsqueda y grupos de recursos de PMax |
| **Dolores y motivaciones** | Texto principal y título (`Marketing/Meta Ads - <modelo>`) | Títulos y descripciones del anuncio de búsqueda (`Marketing/Google Ads - <modelo>`, hoy borradores: ver 4.5) |
| **👥 Quién mira y quién decide** | Pieza para quien acompaña, para ellas o para empresas | Grupos de anuncios por intención: «precio», «cuotas», «test drive», «empresa» |
| **Brecha pauta/venta** | Qué modelo escalar y cuál revisar | Qué modelo merece campaña de búsqueda propia |
| **Compradores reales (ERP)** | Público similar y exclusión de quien ya compró (preparado, §5) | Customer Match: la misma base, con el mismo OK |

### 4.2 Qué plataforma para qué

Lo que muestra la curva, en dos líneas:
- **Meta aprende rápido.** Su señal es inmediata: un formulario, un chat. En el estudio, el costo por lead baja hasta 80 % en 26 semanas. **En nuestras cuentas, no:** una campaña que anda bien se mantiene más o menos igual (mejora 13 % en su mejor tramo, los meses 3 y 4), y una que arranca cara casi nunca se arregla sola. Con Meta decide el arranque, no la paciencia (4.4).
- **Google acumula.** Search atrapa a quien ya está buscando el modelo. PMax es la que más mejora con el tiempo, pero las primeras 6 semanas casi no se mueve. Esto es lo que dice el estudio: nuestras cuentas de Google todavía no están conectadas para comprobarlo.

| Si necesitás… | Usá | Por qué |
|---|---|---|
| Leads ya: promo con fecha, lanzamiento, evento | **Meta** (formulario o WhatsApp) | Aprende en semanas. Una promo de 2 o 3 semanas no le da tiempo a Google |
| Atrapar a quien ya busca el modelo («precio Koleos», «L200 Paraguay») | **Google Search** | Es la intención más alta. Meta genera la demanda y alguien la tiene que atajar |
| Un modelo siempre encendido, con presupuesto estable por 3 meses o más | **Meta + Google PMax** | Meta sostiene el volumen mientras PMax madura; desde el segundo mes PMax puede quedar más barata |
| Leads que compren, no solo más leads | **Devolverle al algoritmo qué leads compraron** (4.6) | Es la diferencia entre las dos campañas de Meta del estudio |

### 4.3 Flujo con Meta (hoy)

```
1. Elegir modelo   → abrir su ficha: brecha pauta/venta + ventas 90d
2. Público         → Audiencias Meta - <Marca>: reusar lo que ya existe
                     (+ semilla de compradores reales cuando se active, ver §5)
3. Mensaje         → Dolores/Motivaciones de la ficha → Marketing/Meta Ads - <modelo>
                     (+ la pieza de «👥 Quién mira y quién decide» de la marca)
4. Formato         → Estrategia: el placement que concentra las impresiones reales
5. Estructura      → pocos conjuntos, cada uno con plata para ~50 resultados por semana
6. Lanzar PAUSADA  → revisar en Ads Manager, activar a mano
7. Dejar aprender  → nada de cambios grandes las primeras 2 semanas (4.4)
8. Medir           → a las 3-4 semanas, con el promedio de 4 semanas; recién ahí volver al 1
```

**Cuánta plata necesita un conjunto para aprender.** Meta pide ~50 resultados por semana en cada conjunto para salir de la «fase de aprendizaje». La cuenta rápida: **presupuesto diario ≈ 7 × el costo por resultado de la marca.** Con resultados de USD 2, son unos USD 14 por día. Un conjunto de USD 4 por día con resultados de USD 3 junta 9 por semana y no sale nunca: Ads Manager lo marca como «Aprendizaje limitado». Con poca plata, **mejor 1 conjunto de USD 15 que 3 de USD 5.** En Ads Manager lo avisa la columna «Entrega»: «Aprendizaje limitado» quiere decir que al conjunto le falta plata o público.

Regla legal: los copies de `Marketing/` **no nombran competencia**. La inteligencia competitiva (`⚔️ Battle Cards`, `⚔️ Benchmark`) es solo interna.

### 4.4 Cuándo juzgar una campaña

| | Meta (formulario o WhatsApp) | Google Search | Google PMax |
|---|---|---|---|
| **Qué necesita para aprender** | ~50 resultados por semana **en cada conjunto** | Conversiones medidas en el sitio (referencia práctica: 30 o más por mes por campaña) | Lo mismo, más señales de audiencia y listas propias |
| **Primer vistazo** | A la semana, solo para ver que entregue | A las 2 semanas: términos de búsqueda y negativos | A las 3 semanas, sin tocar nada |
| **Juzgar** | **A las 3-4 semanas**, con el promedio de 4 semanas | A las 4-6 semanas | **No antes de 6 semanas** |
| **Qué reinicia el aprendizaje** | Cambiar segmentación, creativo, optimización o puja; sumar un anuncio; pausar 7 días o más; saltos grandes de presupuesto | Cambiar la estrategia de puja; saltos grandes de presupuesto | Lo mismo, y es la más sensible |

Lo que muestran nuestras cuentas (561 campañas de Meta lanzadas desde junio de 2025; detalle en [[📈 Curva de aprendizaje — Google Ads vs Meta (26 semanas)]]):

- **La primera semana engaña: suele salir más barata.** En 6 de cada 10 de nuestras campañas costó menos que las semanas 3-4 (en la mediana, 11 % menos). Con ella no se decide nada: ni cortar ni festejar.
- **El arranque predice.** De las campañas que siguieron 8 semanas, las que empezaron más baratas que el promedio de su marca siguieron baratas (34 de 41). Las que empezaron al doble o más casi nunca se recuperaron (2 de 9).
- **Sostener a las que funcionan.** El 62 % de nuestras campañas deja de pautar antes de la semana 5, y una campaña nueva es una apuesta: el 43 % arranca más cara que el promedio de su marca. A la que anda bien conviene refrescarle las piezas, de a una, en vez de reemplazarla (sumar una pieza reinicia el aprendizaje unos días, pero en nuestras cuentas eso pesa poco).
- **El presupuesto se mueve de a poco:** subir o bajar de a 20 % por vez (regla práctica, ya en [[🤖 Meta Ads Lo Que Funciona]]).
- **Se mira la tendencia, no la semana:** promedio de 4 semanas, y se comparan campañas de la misma edad (semana 3 contra semana 3), no una nueva contra una que lleva seis meses.

> [!warning] Cuándo sí cortar antes
> Esperar solo sirve si la campaña arrancó bien. Pausarla o cambiarle la pieza o la oferta antes de las 3 semanas está bien si:
> 1. **compite con otra campaña nuestra por el mismo público**: se encarecen entre ellas en la subasta, o
> 2. **a las 2 semanas cuesta el doble o más que el promedio de la marca**: en nuestras cuentas, solo 2 de cada 9 se recuperaron.
>
> Si lo que falta es volumen (pocos resultados, pero baratos), no se corta: se le da más plata o se junta con otro conjunto.

### 4.5 Google Ads — qué falta y cómo vamos a arrancar

**Hoy:** el conector de Google Ads está escrito (`src/connectors/google_ads_connector.py`), pero apagado (`google_ads.enabled: false`). Cuando se prenda, trae edad, género, ubicación, intereses y rendimiento por campaña.

**Lo que ya está (24 y 25-09-2026):** Google Analytics 4 con los eventos `generate_lead` (formulario enviado) y `click_whatsapp`, y el píxel de Meta, en 8 sitios: Santa Rosa, Jetour, JAC, JMEV, Mitsubishi, XPeng, Zeekr y Leapmotor. Renew ya tenía GA4. Search Console está verificado. Con eso, **la conversión ya se mide en la web**. Falta marcar `generate_lead` como *evento clave* en cada propiedad de GA4 e importarlo como conversión cuando se vincule Google Ads.

> [!info] Google cambió el acceso a la API el 9-sep-2026
> Ya no hay token de desarrollador ni hace falta una cuenta administradora (MCC): el acceso lo da un **proyecto de Google Cloud**. Con una sola **cuenta de servicio de solo lectura** se leen Google Ads, GA4 y Search Console.

**Para conectarlo:**

| Paso | Dónde | Quién |
|---|---|---|
| 1. Crear el proyecto `santarosa-buyer-persona` | Google Cloud Console, con la cuenta de Google de la empresa | Croman inicia sesión; Claude lo completa y pide OK antes de crear |
| 2. Activar Google Ads API, Google Analytics Data API, Google Analytics Admin API y Search Console API | APIs y servicios | Claude, con OK |
| 3. Pedir el nivel **Explorer** | Google Ads API → *Overview* → *Upgrade access level* | Claude, con OK. Google suele aprobarlo solo. Lee cuentas reales, hasta 2.880 operaciones por día: alcanza de sobra para un informe diario |
| 4. Crear la cuenta de servicio `buyer-persona-lector` y su clave | IAM y administración → Cuentas de servicio | La clave (JSON) se descarga a la notebook y va al servidor sin abrirse; nunca por chat |
| 5. Darle acceso de **solo lectura** con su mail | Cada cuenta de Google Ads (Administrador → Acceso y seguridad), cada propiedad de GA4 (Gestión del acceso) y cada sitio de Search Console (Usuarios y permisos) | Quien administra cada una. Si una cuenta de Google Ads es de la agencia, la agencia |
| 6. Verificar | `venv/bin/python3 scripts/verificar_google.py` | Claude |

- El nivel Explorer no incluye el planificador de palabras clave (volumen de búsqueda). Para eso hace falta el nivel **Basic**, que pide verificar la marca del proyecto.
- **Del lado del código**, cuando estén los accesos: actualizar la librería `google-ads` (la instalada es anterior al cambio), leer una cuenta por marca como ya funciona Meta y sumar los **términos de búsqueda**. Es lo que más le suma al Buyer Persona: los dolores y motivaciones de cada ficha pasan a tener palabras reales. GA4 y Search Console entran como fuentes nuevas.

**Cómo vamos a arrancar, en orden:**
1. **Search Console y GA4 primero**, porque ya están instalados: qué busca la gente para llegar a cada sitio, qué modelo mira, de dónde viene y cuántos leads deja. No esperan a Google Ads.
2. **Search de marca y modelo** en las marcas con más búsquedas. Se revisa a las 2 semanas (términos de búsqueda, negativos) y se juzga a las 4-6.
3. **PMax**, cuando la conversión esté medida y haya volumen, con las señales del Buyer Persona (edad, zona, temas) y, si se aprueba, la base de compradores. **Seis semanas sin juzgar.**
4. **El mismo presupuesto, repartido según la curva:** Meta sostiene el volumen mientras Google madura. No hay que sacarle plata a Google en el primer mes porque «está caro»: es la parte plana de su curva.

> [!success] Las notas `Google Ads - <modelo>`, corregidas el 26-09-2026
> Antes eran plantillas: 174 de 291 descripciones pasaban los 90 caracteres que acepta Google, 21 notas metían texto del análisis interno y las 97 prometían «financiación sin interés», «hasta 60 meses» o «garantía de 5 años» sin importar la marca. Ahora cada nota:
> - trae entre 8 y 14 títulos y 3 o 4 descripciones dentro de los límites de Google, con los caracteres contados;
> - sale del modelo o la marca y de los temas que repiten sus anuncios, sin copiar el análisis interno ni prometer tasas, plazos o garantías;
> - agrupa las palabras clave por intención (modelo, precio y cuotas, prueba, marca), con su concordancia, y suma negativas de posventa;
> - trae sitelinks y textos destacados;
> - deja la **oferta del mes** (precio de lista y descuento de la planilla de acciones, con sus condiciones) en una sección aparte, que se confirma con la marca antes de publicar. Hoy la tienen 46 de las 97.
>
> Cada corrida lo revisa sola (`validar_google_ads`). Siguen siendo **borradores**: quien carga la campaña revisa el tono y la página de destino.

### 4.6 Que el algoritmo aprenda de las ventas

Hoy le pedimos a Meta «conseguime formularios o chats», y eso optimiza: el lead más barato, no el que compra. En el estudio, la campaña de Meta que aprende de lo que pasa **después** en el CRM («Conversion Leads») arranca más cara y baja más lento, pero busca leads que avanzan.

Con Bitrix se le puede devolver a cada plataforma **qué leads se calificaron o compraron**, y el algoritmo aprende a buscar a esa gente:
- **Meta:** API de conversiones para CRM. Viaja el ID del lead de Meta con su etapa en Bitrix. Falta confirmar si la integración actual guarda ese ID.
- **Google:** conversiones offline. El sitio tiene que guardar el identificador del clic (`gclid`) junto con el lead.
- Si además se mandan mail o teléfono (cifrados), viajan datos de clientes: **necesita el OK de Croman**, igual que los públicos similares (§5).

Es la continuación natural de lo que pidió Valentina (👥): medir quién avanza, no solo quién hace clic.

## 👥 Quién mira y quién decide

*Desde el 24-09-2026, a pedido de Valentina.* El Buyer Persona describía a un solo actor: el que compra. Pero en la compra de un auto hay más papeles: quien **investiga o influye**, quien **da el paso** (deja el contacto), quien **decide** y quien **paga**. Cada marca tiene ahora una nota **«👥 Quién mira y quién decide — <Marca>»** en su carpeta, y cada ficha de modelo un bloque corto arriba, debajo del resumen.

**De dónde sale cada cosa** (sin preguntar nada nuevo al cliente):

| Pregunta | Fuente | Cómo se mide |
|---|---|---|
| ¿Quién mira y quién da el paso? | Meta, 90 días, anuncio × edad × género | Dentro de cada conjunto de anuncios (mismo aviso, mismo botón) se compara qué tanto contactan las mujeres que hicieron clic contra los hombres, y los mayores de 55 contra el resto. Se suman todos los conjuntos (razón de Mantel-Haenszel). Se descartan los conjuntos apuntados a un solo género. |
| ¿Qué le interesa a cada uno? | Meta, texto de cada anuncio | El anuncio se clasifica por tema (prueba de manejo, seguridad, cuotas…) con las mismas reglas de las fichas, y se compara su parte de clics de mujeres o de 55+ con el **promedio del mismo modelo**. Solo temas con 3+ anuncios y sin uno que se lleve más de la mitad de los clics. |
| ¿Quién paga? | ERP, 12 meses | Parte de las ventas a **cliente final** facturadas a una empresa (se detecta la razón social; el nombre no se guarda). Fuera: subconcesionarios y concesionarias que revenden, como Nipon en Mitsubishi. |
| ¿Quién más aparece? | Chats de Messenger e Instagram de las páginas de marca y de asesores (lectura semanal) | En cuántos el cliente nombra a otra persona: pareja, hijos, padres, familia, empresa o socio, o dice que lo tiene que consultar. Solo conteos. WhatsApp no deja leer su historial por API. |

**Cómo leer los números:**
- **Ellas vs. ellos, mismo anuncio: 0,87×** → las mujeres que hacen clic contactan 13 % menos que los hombres viendo lo mismo. 1,00× = igual; 1,20× = 20 % más.
- **«Ellas menos en 29 de 44 conjuntos»** → la señal se repite en casi todos: no es casualidad.
- **Tema +10** → ese tema suma 10 puntos de mujeres (o de 55+) sobre lo normal del modelo.
- Las **lecturas** posibles: *Ellas miran y el contacto lo deja él* · *Misma tendencia, con pocos conjuntos* · *Sin diferencia* · *Las que miran, contactan más que ellos*.

**Cómo usarlo en Meta Ads.** Cada nota de marca trae en la sección 5 la pieza sugerida con texto base, dónde ponerla y cómo medirla:
1. **Pieza para quien acompaña la decisión**, donde ella mira y él contacta: el tema que más la atrae a ella (en GWM, «Vengan a probarla juntos»).
2. **Pieza que les hable a ellas**, donde las que miran son las que avanzan (Mitsubishi).
3. **Pieza para empresas**, donde una parte grande de las compras la factura una empresa.
4. **Algo para compartir** en el chat, cuando el cliente nombra a otra persona.

Siempre como un anuncio más dentro del conjunto que ya funciona, **sin cortar por género ni edad**: Meta se la muestra a quien responde. Se mide en Ads Manager → Desglose → Por entrega → Edad y Sexo. **Tasa de contacto = resultados ÷ clics en el enlace.**

**Qué NO dice:** Meta no sabe quién decidió la compra. Es una **señal** que se refuerza cuando Meta, el ERP y los chats apuntan al mismo lado. La comparación entre todas las marcas está en [[👥 Centro de compra — todas las marcas]] (uso interno).

## 5. Públicos similares con ventas reales (preparado, no activado)

Ya existe todo lo necesario, a la espera de decisión de negocio:

- Semillas: `output/audiencias_meta/<Marca>/emails.csv` + `phones.csv`, **hash SHA-256**, 2.305 emails + 1.467 teléfonos (detalle en [[📊 Semillas Custom Audiences - Ventas Reales]]).
- Token con `ads_management`: se puede crear la Custom Audience y el Lookalike **por API**, sin subir CSV a mano.
- Receta cuando se active: Custom Audience `VENTAS REALES <MARCA> — base` en la cuenta madre → Lookalike Paraguay 1% → usar como prospecting → excluir la misma semilla (no gastar en quien ya compró).
- ⚠️ **Mitsubishi no**: sus 525 ventas tienen el contacto de Nipon, no del cliente.

## 5b. Cómo aprende (memoria de audiencia)

Cada corrida guarda una fila por modelo en `Sistema/Memoria/historial_audiencia.jsonl` y reescribe [[🧠 Memoria de Audiencia]]:

- **Público confirmado**: un modelo entra cuando repite el mismo género y edad 3 corridas seguidas (🟡) y pasa a 🟢 con 7.
- **Qué cambió**: género o edad que se movió más de 8 puntos frente a hace 7 días, brechas que cambiaron, modelos nuevos.
- **Tendencias por marca**: CPL, leads, gasto y % de público frío hoy vs 7 y 30 días.
- **Reglas aprendidas**: recomendaciones que se sostienen 3+ corridas (ej. "Kwid: presupuesto sugerido ≥1,5× el actual → escalar").
- **Intereses y NSE**: Meta no expone intereses declarados ni NSE en PY. Cada ficha trae *intereses observados* (temas de los anuncios reales que ve y clickea el público + modelos pedidos en el formulario) y un *NSE estimado* por señales: ticket, % que pide financiación, % de clics desde iPhone (`impression_device`), zona. Siempre con la base del cálculo a la vista.
- **Lecciones de Hermes**: los lunes 08:45 el cron `aprendizaje-audiencia` (GLM 5.3 por OpenRouter) lee la memoria y la competencia, escribe su bloque semanal en `Sistema/Memoria/lecciones_hermes.md` (el pipeline lo incrusta en la nota) y guarda los aprendizajes durables en su propia memoria.

Antes de tocar una campaña: público confirmado del modelo → qué cambió → reglas. Cuanto más días corre, más afinado.

## 6. Mantenimiento

> [!info] Desde el 2026-09-22
> - **No hay tope de modelos.** `persona.models.max_personas: 0` en `config/settings.yaml`. Con el tope de 60 que había, qué modelos entraban dependía del orden en que llegaban los anuncios: Arkana, Boreal, Clio o Kangoo aparecían un día y desaparecían al siguiente. Hoy entra todo modelo con ≥5 anuncios o ≥10 ventas (82 modelos, 97 fichas).
> - **Las notas de personas que la corrida ya no produce se borran solas** (ficha + sus 4 notas de marketing), en `output/personas/` y en el vault. Antes quedaban con datos y formato de otra fecha y se leían como actuales. Solo se toca lo generado (`type: buyer-persona` y `<Canal> - <Persona>.md`); las notas a mano no.
> - El log de cada corrida dice qué modelos detectó por marca y cuáles descartó y por qué (`Modelo sin persona: …`).


| Tarea | Cada cuánto | Cómo |
|---|---|---|
| Pipeline completo | diario 06:00, automático | timer `buyer-persona-pipeline.timer` en el servidor SRPY186 |
| Ver que corrió | cuando quieras | `logs/last_status.txt` → `OK <fecha>` |
| Actualizar ventas | cuando Contabilidad exporte | reemplazar `ENCUESTA AGESTA/FacturacionUnidades-*.xlsx` en el servidor y ajustar `paths.sales_history` si cambia el nombre |
| Modelo nuevo | al lanzar | agregarlo en `src/catalog/models_py.py` (nombre + regex) y correr `scripts/validate_model_catalog.py` |
| Cuenta Meta nueva | al crearla | agregarla a `META_ADS_AD_ACCOUNT_IDS` en `.env` con su etiqueta de marca |
| Revalidar catálogo | mensual | `venv/bin/python3 scripts/validate_model_catalog.py` |

Forzar una corrida ahora (servidor): `systemctl --user start buyer-persona-pipeline.service`. Tarda ~25 min. El vault se publica solo por git en la hora siguiente.

## 7. Qué NO hace todavía

- Google Ads, GA4 y Search Console: el conector de Google Ads está escrito y GA4 y Search Console ya están instalados en los sitios, pero ninguno está conectado al Buyer Persona todavía. Qué falta y cómo arrancar: 4.5.
- Devolverle a Meta y a Google qué leads compraron, para que aprendan de las ventas y no de los formularios: 4.6.
- Contado vs financiado: el ERP lo carga todo como "Salon"; no se puede leer.
- Edad/género del **comprador**: el ERP no lo registra; se usa la audiencia de Meta de la marca.
- Lookalikes de ventas reales: preparado, ver §5.
