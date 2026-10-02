# 📊 Semillas Custom Audiences — Ventas Reales

> Generado automáticamente desde `ENCUESTA AGESTA/FacturacionUnidades-7343.xlsx` (hoja Datos, 10167 filas con datos).
>
> Pipeline: normalización → dedup → hash **SHA-256** → CSV en `output/audiencias_meta/<Marca>/`.
> Los CSV se suben a la **cuenta madre** de cada marca como Custom Audience (fuente: datos propios, sin PII visible) y de ahí salen los **lookalikes PY**.

| Marca | Emails únicos | Teléfonos únicos | Carpeta |
|---|---|---|---|
| Jetour | 955 | 638 | `output/audiencias_meta/Jetour/` |
| GWM | 657 | 366 | `output/audiencias_meta/GWM/` |
| Renault | 371 | 282 | `output/audiencias_meta/Renault/` |
| Soueast | 118 | 81 | `output/audiencias_meta/Soueast/` |
| JAC | 134 | 52 | `output/audiencias_meta/JAC/` |
| Leapmotor | 26 | 19 | `output/audiencias_meta/Leapmotor/` |
| JMEV | 26 | 19 | `output/audiencias_meta/JMEV/` |
| Zeekr | 16 | 10 | `output/audiencias_meta/Zeekr/` |
| Mitsubishi | 2 | 0 | `output/audiencias_meta/Mitsubishi/` |
| Zeekr + Leapmotor (EV combinada) | 42 | 29 | `output/audiencias_meta/ZEEKR_LEAPMOTOR_EV/` |
| Otros (JMC/Karry/sin marca) | 11 | 12 | — |

**Total semillas:** 2305 emails + 1467 teléfonos únicos con hash.

## Cómo subir cada lista a Meta
1. Ads Manager → *Audiences* → *Create a Custom Audience* → *Customer list*.
2. Elegir *Upload customers manually*, marcar que los identificadores ya vienen hasheados con SHA-256.
3. Subir `emails.csv` (columna `email_sha256`) y repetir con `phones.csv` (columna `phone_sha256`).
4. Nombrar la audiencia `VENTAS REALES <MARCA> — base`.
5. Una vez madurada (~500+ personas), crear Lookalike origen esa audiencia, país Paraguay, 1%.

## Notas
- Un mismo cliente aparece en varias marcas si compró más de una vez: correcto, cada cuenta usa su propia semilla.
- `GREATWALL` del ERP se mapea a **GWM**.
- Zeekr y Leapmotor van combinadas porque por separado quedan debajo del mínimo útil de Meta (~100 matching).
- ⚠️ Uso interno: los CSV tienen PII hasheada, no commitear a ningún repo público.

## ⚠️ Mitsubishi: data de contacto inservible
Las 525 ventas de Mitsubishi en el ERP están cargadas con el email y teléfono **corporativos de Nipon** (`impor@nipon.com.py` / `021505511`) — 524 de 525 filas. Es decir, quien cargó esas ventas puso el contacto del importador competidor, no del cliente real. **No subir esa lista a Meta**: contaminaría la semilla con datos del competidor y además no representa compradores propios. Pendiente de negocio: recuperar los contactos reales de los compradores Mitsubishi desde Bitrix u otra fuente.
