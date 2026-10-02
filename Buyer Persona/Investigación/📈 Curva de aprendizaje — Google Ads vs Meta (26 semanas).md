---
type: investigación
fecha: 2026-09-26
fuente: "Análisis publicado por Felipe López Miranda (@flopezmiranda) · Efecto Podcast, compartido por Croman"
uso: interno
tags: [investigación, meta-ads, google-ads, curva-de-aprendizaje, pauta]
---
# 📈 Curva de aprendizaje: Google Ads vs Meta en 26 semanas

> [!info] Qué es esta nota
> Resume un análisis que Croman compartió el 26-09-2026 y lo compara con nuestras propias cuentas de Meta. Del post original quedan la idea, los números y qué hacemos con eso, no el texto completo. **Uso interno.** Las reglas para el equipo y los brands están en el [[📘 Manual Buyer Persona#4. Pauta con el Buyer Persona — Meta Ads hoy, Google Ads próximamente|Manual, sección 4]].

![[curva-26-semanas-google-vs-meta.png]]

## La pregunta del estudio

¿Cuánto cuesta un lead semana a semana cuando a la campaña **se la deja aprender** durante 26 semanas?

- **45+ campañas reales** de generación de leads en cuatro industrias: telecomunicaciones, retail, educación y bienes raíces. **No hay autos.**
- Mismo objetivo en todas: un lead que marketing le pasa a ventas. Mismo horizonte: 26 semanas.
- Cuatro tipos de campaña: **Google Search con AI Max**, **Google Performance Max (PMax)**, **Meta Advantage+ Leads** y **Meta Conversion Leads**.

## Lo que encontró

| Campaña | Semana 1 | Semana 26 | Cambio | Cómo es la curva |
|---|---|---|---|---|
| **Google Search / AI Max** | ≈ 7.200 | ≈ 6.100 | −15 % | Baja hasta la semana 12 (≈ −35 %) y **después vuelve a subir** |
| **Google PMax** | ≈ 6.500 | ≈ 2.200–2.500 | ≈ −65 % | **Casi plana las primeras 6 semanas**, cae fuerte entre la 7 y la 13, meseta, y otra baja al final. Es la que más mejora |
| **Meta Advantage+ Leads** | ≈ 4.100 | ≈ 760 | ≈ −80 % | **Cae rápido desde la semana 1** (≈ −40 % a la semana 6), meseta, y sigue bajando hasta el final |
| **Meta Conversion Leads** | ≈ 5.200 | ≈ 2.900 | ≈ −45 % | Arranca más cara y baja parejo, semana a semana |

Semana 1 y semana 26 salen del texto del post. Los tramos intermedios están leídos del gráfico y son aproximados. Los montos están **en la moneda del estudio, no en dólares**: lo que sirve es cuánto baja cada curva, no el monto.

## Lo que concluye el autor

- **Meta aprende rápido** porque su señal es inmediata: un formulario, un chat, un evento. Da volumen y velocidad desde la primera semana.
- **Google acumula.** Necesita volumen, señales propias y paciencia. PMax es la que más mejora, pero **si se la corta antes del mes no despega**.
- **No se trata de cuál es mejor.** En el corto plazo gana Meta. Si se mira la película completa, Google empata y a veces gana.
- **Los costos por lead no se juzgan semana a semana**, sino por la tendencia completa. Su pregunta de cierre: «¿En qué semana estás tomando decisiones?».

## Cuidado al usarlo

- **Otras industrias, otra moneda:** sirve la forma de las curvas, no los montos.
- **En 26 semanas cambian muchas cosas además del aprendizaje:** creativos, ofertas, temporada, presupuesto. No todo lo que baja es aprendizaje.
- **Es un análisis publicado en redes**, sin el detalle del método. Sirve como orientación, no como regla.
- **«Conversion Leads»** es la opción de Meta que optimiza hacia los leads que después **avanzan en el CRM**. Para usarla hay que devolverle a Meta qué leads se calificaron o compraron, y **hoy no lo hacemos** (ver el [[📘 Manual Buyer Persona#4.6 Que el algoritmo aprenda de las ventas|Manual, 4.6]]).

## ¿Se cumple en nuestras cuentas? Solo en parte

Se revisaron **561 campañas de contacto** (formulario o WhatsApp) que arrancaron entre junio de 2025 y septiembre de 2026 en las 85 cuentas de Meta, semana por semana de vida. Google no se pudo mirar porque todavía no está conectado. Corrida del 26-09-2026 con `scripts/curva_aprendizaje.py`; datos en `output/curva_aprendizaje_2026-09-26.json`.

### 1. Casi no las dejamos aprender

| Campañas lanzadas hace… | Dejaron de pautar antes de la semana 5 | Llegaron a 8 semanas | Llegaron a 26 semanas |
|---|---|---|---|
| 8 semanas o más (495) | 306 (62 %) | 114 (23 %) | — |
| 26 semanas o más (341) | 214 (63 %) | 69 (20 %) | 26 (8 %) |

La mayoría de nuestras campañas vive menos de un mes. La curva del estudio necesita meses.

### 2. Las que siguieron casi no bajaron

Costo por resultado de cada tramo, contra el de sus dos primeras semanas (mediana: 1,00 = igual, 0,80 = 20 % más barato):

| Tramo | Nuestras campañas que llegaron a 8 semanas (80) | Nuestras campañas que llegaron a 26 semanas (29) | Estudio: Meta Advantage+ Leads (≈, leído del gráfico) |
|---|---|---|---|
| Semanas 3-4 | 1,09 | 1,08 | ≈ 0,80 |
| Semanas 5-8 | 1,03 | 0,96 | ≈ 0,65 |
| Semanas 9-12 | — | 0,95 | ≈ 0,60 |
| Semanas 13-18 | — | **0,87** (su mejor tramo) | ≈ 0,50 |
| Semanas 19-26 | — | 0,97 | ≈ 0,30 |

- **No es por el presupuesto:** el gasto semanal se mantuvo parejo (+10 % en la mediana), así que no se encarecieron por escalar.
- **Mitad y mitad:** a las 8 semanas, el 49 % de las campañas estaba más barata que al arrancar y el 51 % más cara. Solo 5 de 80 bajaron su costo a la mitad.
- **Vale sobre todo para formularios:** solo 8 campañas de WhatsApp llegaron a 8 semanas, y ninguna a 26.

### 3. La primera semana engaña, pero al revés

En **6 de cada 10 campañas la semana 1 salió más barata** que las semanas 3-4 (en la mediana, 11 % menos; 274 campañas). En el estudio pasa lo contrario. Con la primera semana no se decide nada: ni cortar ni festejar.

### 4. El arranque predice cómo sigue

| Costo en las 2 primeras semanas, contra el promedio de su marca | Campañas que siguieron 8 semanas | Semanas 5-8 (mediana, contra el promedio de la marca) | Terminaron en 1,2× el promedio o menos |
|---|---|---|---|
| Por debajo del promedio | 41 | 0,70× | **34 de 41** |
| Entre 1 y 2 veces | 30 | 1,25× | 12 de 30 |
| El doble o más | 9 | 1,42× | **2 de 9** |

Una campaña nueva es una apuesta: el 43 % arranca más cara que el promedio de su marca, y el 13 % al doble o más. A la mayoría de estas últimas ya se las corta antes de la semana 5 (40 de 58). De las que se dejaron correr 8 semanas, solo 2 de 9 se recuperaron.

### Por qué puede ser distinto al estudio (hipótesis, no medido)

- **Mercado chico:** el público de un modelo en Paraguay se agota rápido. Lo que Meta gana aprendiendo se pierde porque la misma gente ya vio el aviso.
- **Cambios seguidos:** creativos, promos y estructura cambian cada pocas semanas, y cada cambio grande reinicia el aprendizaje.
- **Conjuntos chicos:** muchos no llegan a los ~50 resultados por semana que Meta necesita para aprender.
- **Otro tipo de campaña y otras industrias:** el estudio mide Advantage+ Leads en telecomunicaciones, retail, educación y bienes raíces.

## Qué hacemos con esto

1. **Juzgar a las 3-4 semanas.** La primera semana suele salir más barata de lo que va a costar después. El nivel se asienta en las semanas 3-4 y de ahí se mueve poco.
2. **No esperar que el tiempo arregle una campaña cara.** Si a las 2 semanas cuesta el doble o más que el promedio de su marca, hay que cambiar pieza u oferta, o pausarla: casi nunca se recupera sola.
3. **Sostener a las que funcionan.** La que arranca bien sigue bien y mejora un poco con los meses (−13 % en los meses 3 y 4). Conviene refrescarle las piezas de a una antes que reemplazarla por una campaña nueva. Sumar una pieza reinicia el aprendizaje unos días, pero en nuestras cuentas ese costo es chico (la curva es casi plana) y evita que el aviso se gaste.
4. **Google, cuando se conecte:** seguir la curva del estudio (Search se juzga a las 4-6 semanas; PMax, no antes de 6) y repetir este mismo control con nuestros datos de Google.

Todo esto quedó en el [[📘 Manual Buyer Persona#4.4 Cuándo juzgar una campaña|Manual, 4.4]].

Relacionado: [[📘 Manual Buyer Persona]] · [[🤖 Meta Ads Lo Que Funciona]] · [[🎯 Playbook Meta Ads]] · script `scripts/curva_aprendizaje.py`
