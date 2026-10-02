---
type: feedback
fecha: 2026-09-17
fuente: audio WhatsApp (44 min) — Valentina + brands de marketing + Croman
tags: [buyer-persona, sistema, feedback, marketing]
---
# 🎧 Feedback de marketing sobre Buyer Persona (17-sep-2026)

> Reunión de revisión del sistema con Valentina y los brand managers. Transcripto con Whisper y convertido en cambios el 18-sep-2026. Lo de la segunda mitad (WhatsApp API, precalificación de leads, política del 1 de octubre) no es de Buyer Persona y queda para otra nota.

## Lo que pidieron y qué se hizo

| # | Pedido (quién) | Qué se cambió | Estado |
|---|---|---|---|
| 1 | **La demografía de L200 y Montero era idéntica a la de Mitsubishi** ("86% masculino, 12% de 55-64, no puede ser") — Valentina | Meta ahora se consulta edad/género **a nivel anuncio** y se atribuye al modelo que nombra cada anuncio. Cada nota dice si el perfil es *propio del modelo* o *heredado de la marca* (cuando el modelo tiene <100 clics) | ✅ hecho · se ve desde la corrida del 19-sep |
| 2 | **"Predominante masculino, pero ¿cuánto?"** — pedir el porcentaje | Edad y género van con % (ej. *Femenino 69.7%*, *18-24: 45.7% de los clics*) y la distribución completa | ✅ |
| 3 | **Agrupar por marca**, no lista plana de 74 notas ("yo agruparía por marca; GWM tiene 100.000 versiones") — Valentina | Vault reorganizado: `Buyer Personas/<Marca>/` con el comprador de la marca, una nota por modelo, `Marketing/` y sus audiencias. Cada marca tiene su índice (`Mitsubishi.md`) con tabla de modelos; el MOC general queda agrupado por marca | ✅ |
| 4 | **"¿De dónde lo saca?"** — la estrategia recomendada y el mensaje clave sin explicación | Cada Estrategia Recomendada cierra con **De dónde sale**: origen de mensaje, canales, targeting, públicos y presupuesto | ✅ |
| 5 | **"¿Qué período está tomando?"** | Cada nota dice el período leído: *Meta 2026-06-20 → 2026-09-18 · ERP 2024-04-02 → 2026-04-30* | ✅ |
| 6 | **Base de recompra / fidelización**: "al que compró Duster o Arkana hace 3-4 años, mostrale Boreal; son ~300 personas" — Valentina | Script `generar_audiencia_recompra.py` arma cohortes por meses desde la compra (≥24m, 18-24m, 12-18m) por marca y modelo, con la escalera de a qué modelo invitar, y exporta CSV hasheados listos para Custom Audience. Nota: [[🔁 Base de Recompra (ERP)]] | ✅ · ⚠️ el ERP cargado arranca en abril 2024: la cohorte de 3-4 años aún no existe; Renault ≥24m = 300 unidades, 88 contactables |
| 7 | **"Estamos tirando todo a público frío"** — Croman | Se lee el targeting real de cada adset activo. Renault: **93,5 %** de 107 adsets a público frío (7 con base propia, 5 lookalike). Mitsubishi: 48 % frío (la agencia usa RMK web). Cada nota lo muestra en *Públicos hoy* | ✅ |
| 8 | **"¿Cuánto presupuesto necesita?"** — que el sistema diga un ideal | *Presupuesto sugerido* por modelo: gasto real de la marca repartido según el peso del modelo en ventas del ERP, con leads esperados al CPL actual. Ej. Kwid: hoy ~USD 547/mes por su peso en anuncios → sugerido ~USD 1.251/mes (42 % de las ventas de Renault) | ✅ |
| 9 | Dos campañas separadas: generación de leads + **fidelización** con la base propia, presupuesto aparte, sin pisar la creatividad de la agencia | Instrucciones en la nota de recompra (campaña separada, excluir la lista de las frías, medir en Bitrix con `RECOMPRA <MARCA>`) | ✅ documentado · ⏳ lanzar piloto |
| 10 | Ranking de asesores por rendimiento en Bitrix | Ya existe ([[Scorecard Asesores - ultimos 90 dias]] / tableros semanales) | ✅ ya estaba |
| 11 | Google Ads: seguir píxel por marca/modelo/segmento | Conector escrito, faltan credenciales | ⏳ pendiente |
| 12 | Humanizar la marca (Reels, historias) — Valentina | Las notas ya muestran que Reels/Stories concentran ~55 % de las impresiones; el copy lo decide marketing | ℹ️ |

## Hallazgos que salieron al aplicar los cambios (datos reales, ventana 20-jun → 18-sep)

- **Renault Kwid: 69,7 % mujeres, 18-24 años** (antes decía "masculino 76,8 %, 35-44", heredado de Renault). Kardian 18-24 · Koleos 25-34 · Master/Oroch 35-44 masculino.
- **Mitsubishi**: L200 83 % masc. 35-44 · Montero 81 % · Eclipse Cross 64 % (la más mixta) · Destinator 89 % masc. 35-44 (25,7 % de 45-54).
- Renault tiene 107 adsets activos: **100 a público frío**. Mitsubishi 27 adsets, 14 con base propia.
- Solo el **42 %** de las filas del ERP trae email/teléfono: la base contactable es menos de la mitad de las unidades vendidas. Mitsubishi tiene cargado el contacto de Nipon: no se genera su lista.

## Aprendizaje continuo (agregado el 18-sep)

Pedido de Croman: que se actualice todos los días y que Hermes aprenda de la audiencia real. Hecho: [[🧠 Memoria de Audiencia]] (serie diaria + público confirmado + tendencias + reglas) y cron semanal de Hermes `aprendizaje-audiencia` (lunes 08:45) que escribe lecciones y guarda en su memoria. Detalle en [[📘 Manual Buyer Persona]] §5b.

## Próximos pasos

1. Corrida del servidor del 19-sep 06:00 → todas las marcas con demografía por modelo (hoy se validó con Mitsubishi y Renault).
2. Elegir con Valentina el **piloto**: Mitsubishi (Destinator/L200) o Renault (Kwid con creatividad femenina 18-24 + recompra Duster/Arkana → Boreal).
3. Subir la primera lista de recompra (Renault ≥24m, 88 contactos; Jetour ≥24m, 166) como Custom Audience — lo hace marketing, el sistema no crea audiencias en Meta todavía.
4. Cargar el histórico de ventas anterior a abril 2024 en el ERP para que exista la cohorte de 3-4 años.

Relacionado: [[📘 Manual Buyer Persona]] · [[🔍 Auditoría Buyer Persona 2026-09-16]] · [[ Buyer Personas MOC]]
