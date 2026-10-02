---
type: embudo-ventas
created: '2026-09-21'
updated: '2026-09-21'
period_start: '2026-08-22'
period_end: '2026-09-21'
tags:
- embudo
- bitrix
- conversion
---

# 📊 Embudo de ventas — lo que dice el CRM

> [!info] **Armado por script el 2026-09-21** contra Bitrix24.
> Período: **2026-08-22 al 2026-09-21** (30 días).
>
> [!danger] **La versión anterior de este documento tenía los números
> inventados.** Mostraba un embudo de 5.000 personas → 400 leads → 150
> cotizaciones y una «conversión global del 3,0%», mientras cada sección de
> abajo decía «Sin datos de esta etapa» y «Total de leads: 0». Un diagrama
> prolijo con cifras que no salieron de ningún lado es peor que una página
> vacía: la página vacía se nota.
>
> Acá cada etapa se dibuja **sólo si hay dato**. Donde la medición se corta, se
> dice dónde y por qué.

---

## 1️⃣ Entran: 14.274 leads

De los cuales **12.850 (90,0%) vienen de Meta Ads**. El CRM guarda la cuenta de origen, así que la pauta y el CRM se pueden cruzar.

| Origen | Leads | % |
|---|---|---|
| JETOUR Meta Ads - Cuenta Madre | 2.722 | 19,1% |
| JAC Meta Ads - Cuenta Madre | 1.473 | 10,3% |
| GWM Meta Ads - Cuenta Asesores | 1.433 | 10,0% |
| GWM Meta Ads - Cuenta Madre | 1.221 | 8,6% |
| JETOUR Meta Ads - Cuenta Asesores | 1.064 | 7,5% |
| MITSUBISHI Meta Ads - Cuenta Madre | 936 | 6,6% |
| SOUEAST Meta Ads - Cuenta Madre | 743 | 5,2% |
| Prospecto del asesor | 637 | 4,5% |
| RENAULT Meta Ads - Cuenta Madre | 556 | 3,9% |
| ZEEKR Meta Ads - Cuenta Madre | 556 | 3,9% |
| LEAPMOTOR Meta Ads - Cuenta Madre | 445 | 3,1% |
| XPENG Meta Ads - Cuenta Madre | 413 | 2,9% |

---

## 2️⃣ El cuello de botella: el contacto

> [!danger] **3.515 leads (24,6%) no fueron contactados.**
>
> A un CPL de **$2,23**, los leads de pauta que nadie llamó representan aproximadamente **$7.052** de inversión en Meta que no llegó a una conversación.
>
> No es plata tirada del todo — un lead sin contactar todavía se puede llamar — pero cada día que pasa vale menos.

| Estado del lead | Leads | % |
|---|---|---|
| Leads contactado | 7.395 | 51,8% |
| Leads sin contacto | 2.994 | 21,0% |
| Lead en espera | 1.326 | 9,3% |
| Solo curiosidad | 1.040 | 7,3% |
| Leads sin contactar | 521 | 3,6% |
| Duplicado | 291 | 2,0% |
| Datos falsos / Spam / Repetidos | 255 | 1,8% |
| Incontactable | 199 | 1,4% |
| Convertido a Negociación | 115 | 0,8% |
| No Califica para Credito | 59 | 0,4% |
| Busca otro producto | 47 | 0,3% |
| Competencia | 16 | 0,1% |

Descartados por calidad (duplicado, spam, datos falsos, no califica, incontactable): **851** (6,0%). Ese porcentaje es la mejor medida de la calidad del lead que entrega la pauta: si sube, el problema está antes del CRM.

---

## 3️⃣ Dónde se corta la medición

> [!warning] **El embudo NO se puede cerrar hasta la venta para la mayoría de las marcas, y no es un problema de este documento: es que los deals no están en el CRM.**

| Embudo | Deals (histórico) | Ganados | En este período |
|---|---|---|---|
| JAC Ventas | 106 | 17 | 41 |
| RENEW Ventas | 50 | 27 | 39 |
| SOUEAST Ventas | 46 | 10 | 26 |
| JETOUR Ventas | 16 | 0 | 16 |
| MITSUBISHI Ventas | 14 | 4 | 12 |
| JMEV Ventas | 10 | 0 | 9 |
| GWM Ventas | 10 | 0 | 10 |
| ZEEKR Ventas | 3 | 0 | 3 |
| LEAPMOTOR Ventas | 2 | 0 | 2 |
| XPENG Ventas | 0 | 0 | 0 |

> [!danger] **XPENG Ventas: cero deals registrados, nunca.** No significa que no vendan — CADAM los muestra matriculando autos todos los meses. Significa que **la venta no pasa por el CRM**, así que la conversión de lead a venta de esas marcas no se puede calcular con estos datos. Decir un porcentaje ahí sería inventarlo.

---

## 4️⃣ Lo que sí cerró en el CRM

**40 ventas** por **$830.508** en el período, concentradas en los embudos que sí se usan:

| Embudo | Ventas | Monto |
|---|---|---|
| RENEW Ventas | 26 | $408.118 |
| SOUEAST Ventas | 8 | $181.950 |
| JAC Ventas | 3 | $111.470 |
| MITSUBISHI Ventas | 3 | $128.970 |

> Este número mide **lo que el CRM registra**, no lo que la empresa vendió. Para las unidades reales del grupo está CADAM, que es otra fuente y otro evento (matriculación, no cierre).


---

## 🎯 Las dos cosas que este embudo dice hacer

1. **Llamar a los 3.515 leads sin contactar.** Es el número más
   grande y el más barato de mover: no requiere pauta nueva ni creatividad
   nueva, sólo que alguien los llame. Todo lo demás del embudo está aguas
   abajo de esto.
2. **Decidir si el CRM es el sistema de cierre o no.** Hoy es una respuesta a
   medias: RENEW cierra ahí, GWM y JETOUR ni siquiera abren un deal. Mientras
   siga así, «conversión de lead a venta» es una métrica que no existe para la
   mayor parte del negocio — y ninguna herramienta la va a poder calcular.


---

*Armado el 2026-09-21 por `armar-embudo.py`. Volvé a correrlo en vez de editarlo a mano.*

