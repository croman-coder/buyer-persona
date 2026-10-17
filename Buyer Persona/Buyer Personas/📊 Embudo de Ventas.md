---
type: embudo-ventas
created: '2026-10-12'
updated: '2026-10-12'
period_start: '2026-09-12'
period_end: '2026-10-12'
tags:
- embudo
- bitrix
- conversion
---

# 📊 Embudo de ventas — lo que dice el CRM

> [!info] **Armado por script el 2026-10-12** contra Bitrix24.
> Período: **2026-09-12 al 2026-10-12** (30 días).
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

## 1️⃣ Entran: 17.849 leads

De los cuales **15.325 (85,9%) vienen de Meta Ads**. El CRM guarda la cuenta de origen, así que la pauta y el CRM se pueden cruzar.

| Origen | Leads | % |
|---|---|---|
| JETOUR Meta Ads - Cuenta Madre | 2.497 | 14,0% |
| JETOUR Meta Ads - Cuenta Asesores | 2.468 | 13,8% |
| GWM Meta Ads - Cuenta Asesores | 2.049 | 11,5% |
| GWM Meta Ads - Cuenta Madre | 1.701 | 9,5% |
| JAC Meta Ads - Cuenta Madre | 1.108 | 6,2% |
| Prospecto Asesores Whatsapp | 899 | 5,0% |
| RENAULT Meta Ads - Cuenta Madre | 770 | 4,3% |
| SOUEAST Meta Ads - Cuenta Madre | 647 | 3,6% |
| MITSUBISHI Meta Ads - Cuenta Madre | 625 | 3,5% |
| Prospecto del asesor | 581 | 3,3% |
| ZEEKR Meta Ads - Cuenta Madre | 550 | 3,1% |
| RENEW Meta Ads - Cuenta Madre | 538 | 3,0% |

---

## 2️⃣ El cuello de botella: el contacto

> [!danger] **25 leads (0,1%) no fueron contactados.**
>
> A un CPL de **$2,17**, los leads de pauta que nadie llamó representan aproximadamente **$47** de inversión en Meta que no llegó a una conversación.
>
> No es plata tirada del todo — un lead sin contactar todavía se puede llamar — pero cada día que pasa vale menos.

| Estado del lead | Leads | % |
|---|---|---|
| Leads contactado | 9.073 | 50,8% |
| Demora en atencion | 4.915 | 27,5% |
| Lead en espera | 1.052 | 5,9% |
| Solo curiosidad | 1.028 | 5,8% |
| Incontactable | 567 | 3,2% |
| Convertido a Negociación | 503 | 2,8% |
| Datos falsos / Spam / Repetidos | 241 | 1,4% |
| Duplicado | 100 | 0,6% |
| No Califica para Credito | 95 | 0,5% |
| Busca otro producto | 64 | 0,4% |
| Cliente ya compro | 40 | 0,2% |
| Falta de Stock | 35 | 0,2% |

Descartados por calidad (duplicado, spam, datos falsos, no califica, incontactable): **1.067** (6,0%). Ese porcentaje es la mejor medida de la calidad del lead que entrega la pauta: si sube, el problema está antes del CRM.

---

## 3️⃣ Dónde se corta la medición

> [!warning] **El embudo NO se puede cerrar hasta la venta para la mayoría de las marcas, y no es un problema de este documento: es que los deals no están en el CRM.**

| Embudo | Deals (histórico) | Ganados | En este período |
|---|---|---|---|
| GWM Ventas | 405 | 13 | 401 |
| JAC Ventas | 122 | 21 | 33 |
| SOUEAST Ventas | 100 | 22 | 68 |
| JETOUR Ventas | 80 | 6 | 78 |
| RENEW Ventas | 67 | 42 | 21 |
| MITSUBISHI Ventas | 19 | 4 | 11 |
| JMEV Ventas | 15 | 0 | 10 |
| ZEEKR Ventas | 5 | 0 | 4 |
| LEAPMOTOR Ventas | 3 | 0 | 2 |
| XPENG Ventas | 0 | 0 | 0 |

> [!danger] **XPENG Ventas: cero deals registrados, nunca.** No significa que no vendan — CADAM los muestra matriculando autos todos los meses. Significa que **la venta no pasa por el CRM**, así que la conversión de lead a venta de esas marcas no se puede calcular con estos datos. Decir un porcentaje ahí sería inventarlo.

---

## 4️⃣ Lo que sí cerró en el CRM

**51 ventas** por **$1.145.389** en el período, concentradas en los embudos que sí se usan:

| Embudo | Ventas | Monto |
|---|---|---|
| RENEW Ventas | 14 | $217.159 |
| SOUEAST Ventas | 14 | $373.380 |
| GWM Ventas | 13 | $363.410 |
| JETOUR Ventas | 6 | $80.470 |
| JAC Ventas | 4 | $110.970 |

> Este número mide **lo que el CRM registra**, no lo que la empresa vendió. Para las unidades reales del grupo está CADAM, que es otra fuente y otro evento (matriculación, no cierre).


---

## 🎯 Las dos cosas que este embudo dice hacer

1. **Llamar a los 25 leads sin contactar.** Es el número más
   grande y el más barato de mover: no requiere pauta nueva ni creatividad
   nueva, sólo que alguien los llame. Todo lo demás del embudo está aguas
   abajo de esto.
2. **Decidir si el CRM es el sistema de cierre o no.** Hoy es una respuesta a
   medias: RENEW cierra ahí, GWM y JETOUR ni siquiera abren un deal. Mientras
   siga así, «conversión de lead a venta» es una métrica que no existe para la
   mayor parte del negocio — y ninguna herramienta la va a poder calcular.


---

*Armado el 2026-10-12 por `armar-embudo.py`. Volvé a correrlo en vez de editarlo a mano.*

