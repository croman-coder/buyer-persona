---
type: fuente-ventas
marca: Jetour
fuente: Tecnom (jetourpy.tecnomcrm.com) — reporte "Estado de consultas comerciales", casos en estado Vendido
periodo: 2022-08-05 → 2026-09-20
registros: 1158
created: 2026-09-20
tags:
  - marca/jetour
  - ventas
  - tecnom
  - buyer-persona
---

# 🧾 Ventas Tecnom — Jetour (leads que compraron)

> Dataset extraído el **20/09/2026** al migrar Tecnom → Bitrix. 1.158 casos "Vendido" (1.104 *en preventa* + 54 *entregados*).
> Archivo sin datos personales: `data/fuentes/tecnom_jetour_vendidos_2022-2026.csv` (una fila por venta: canal, fechas, modelo, origen, campaña, anuncio, localidad, asesor, días lead→compra).
> Complementa al ERP ([[Comprador Jetour]] usa `ventas_bi`): el ERP dice **qué** se vendió; Tecnom dice **de dónde vino el lead y cuánto tardó**.

## ⚠️ Lo primero: qué mide y qué no

| Dato | Cobertura | Implicación |
|---|---|---|
| Ventas registradas en Tecnom (sep-25 → ago-26) | **501** vs ~1.243 del ERP en 12 meses | Tecnom captura ~40 % de las ventas reales → los ratios de abajo son **piso**, no verdad absoluta |
| Canal del caso vendido | **83 % cargado a mano por el asesor** (965), 16 % lead digital webconnector (181), 1 % showroom/importador | Los asesores no convierten el lead digital: abren un caso manual al cerrar. La atribución digital en Tecnom está subestimada |
| Modelo | conocido en solo **165** ventas (14 %) | Tecnom no obliga a cargar producto. Para modelo, usar ERP |
| Localidad | 106 ventas (9 %) | Solo la que el lead escribió en el formulario |
| Edad / género | 14 / 10 ventas | No sirve. Seguir con Meta + ERP para demografía |

## 📈 Lo que sí aporta (y no está en el ERP)

### 1. Velocidad de compra — ventana de 30 días
Sobre 593 ventas con fecha de lead y de compra:

| Métrica | Valor |
|---|---|
| Mediana lead → compra | **7 días** |
| p25 / p75 | 1 día / 18 días |
| Compran en ≤ 7 días | **51 %** |
| Compran en ≤ 30 días | **87 %** |
| Compran después de 90 días | 3 % |

→ El comprador Jetour **decide rápido**: la mitad cierra en la primera semana. Un lead de más de 30 días vale poco; más de 90, casi nada. Justifica: (a) presión de contacto en las primeras 72 h, (b) retargeting/WhatsApp de 7-30 días, (c) no gastar seguimiento en leads viejos (mejor difusión masiva).

### 2. Tiempo de atención de los que compraron
88 % de las ventas fueron leads atendidos en **≤ 2 h**; 96 % en ≤ 24 h (mediana: minutos). Sesgo de selección (los rápidos venden), pero refuerza el KPI "En 2h" del [[📊 Embudo de Ventas|dashboard Bitrix]].

### 3. Origen digital de las 181 ventas con lead trazable

| Origen | Ventas | Leads no eliminados | Conversión Tecnom |
|---|---|---|---|
| Facebook | 83 | 46.204 | 0,18 % |
| Instagram | 67 | 25.048 | 0,27 % |
| Web orgánico | 7 | 585 | **1,20 %** |
| Web (formulario) | 9 | 1.193 | 0,75 % |
| WhatsApp (Tecnom + web) | 10 | 1.880 | 0,5 % |
| No identificado (Meta) | 5 | 2.075 | 0,24 % |

- Instagram convierte 1,5× más que Facebook por lead.
- Web orgánico convierte **5-6× más** que Meta por lead: poco volumen, mucha intención → cuidar SEO/landing de jetour.com.py.
- De las ventas Meta con cuenta identificada: **101 vinieron de cuentas personales de asesores vs 57 de la cuenta madre (AON)**. Los asesores registran la venta de *sus* leads; la pauta de marca queda sin atribución. Para medir la cuenta madre hay que mirar Bitrix, no Tecnom.

### 4. Modelo (solo 165 ventas con modelo)
X70 **51 %** · Dashing 23 % · T2 14 % · X50 6 % · X90 4 % · T1 2 %. Sub-representa X50/T1 (lanzamientos recientes que el ERP sí muestra: X50 291 y T1 162 en 12 m). Días lead→compra por familia: X70 mediana 8 d, Dashing 6 d, T2 7 d.

### 5. Estacionalidad de cierres (fecha de compra)
Noviembre es el pico todos los años: **2025-11: 106**, 2024-11: 46, 2023-11: 40. Octubre 85 y septiembre 55 (2025). Segundo empuje enero-febrero (46 / 36). → Presupuesto y stock cargados a sep-nov.

### 6. Asesores que más cierran (Tecnom, todo el período)
Katherine Vera 168 · Zenon González 139 (Jetour + Soueast) · Diego Carrapateira 134 · Guido Riquelme (CDE) 105 · Jeremías Lopez 83 · Hector Martinez 65 · Fernando Gonzalez 64 · Juan Silvero 57 · Rodrigo Duarte 55.
Casa Central concentra el 79 % de las ventas con localidad conocida (Gran Asunción 84, Interior 14, CDE 8).

## 🎯 Ajustes sugeridos a [[Comprador Jetour]] y a las personas por modelo

1. **Decisor rápido (≤ 7 días)** → pauta con CTA de agenda/test-drive inmediata, no "conocé más". Secuencia WhatsApp: día 0, día 2, día 7, día 21 y cerrar.
2. **Instagram y web orgánico como canales de alta intención**: mover parte del presupuesto Facebook → Instagram/Reels; mantener landing por modelo indexable.
3. **Pauta de asesores convierte mejor en Tecnom**: mantener el esquema "cuenta asesores" ([[Audiencias Meta - Jetour]]) y medir la cuenta madre en Bitrix desde ahora (todos los leads Jetour entran a Bitrix desde el 20/09/2026 — ver `[[Sistema/📈 Inteligencia de Mercado — Avances]]`).
4. **Q4 es la temporada**: campañas de conversión sep-nov; ene-feb para stock remanente.
5. Datos demográficos: seguir usando Meta/ERP; Tecnom no aporta edad/género.

## 🔁 Cómo actualizar
Fuente ya migrada: Tecnom Jetour deja de usarse; desde ahora la trazabilidad lead → venta vive en Bitrix (prospecto → negociación). Próxima versión de esta nota debería salir del `bitrix_connector` del pipeline, no de Tecnom.
Script y datos crudos: `~/Escritorio/BITRIX/BITRIX TECNOM/BASE TECNOM/JETOUR/` (`vendidos_jetour_tecnom.xlsx`, `tecnom_jetour_casos_reporte.json`).

← [[Jetour]] · [[Comprador Jetour]] · [[ Buyer Personas MOC|Mapa general]]
