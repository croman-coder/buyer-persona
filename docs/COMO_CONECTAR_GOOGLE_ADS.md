# 🔵 Cómo conectar tus Buyer Personas a Google Ads

> **Actualizado el 02-10-2026.** La opción A (manual) sigue vigente. La opción B (API) cambió: ver más abajo.

Este proyecto ya incluye un conector (`src/connectors/google_ads_connector.py`)
que extrae automáticamente de la Google Ads API:

- **Demografía** por edad y género (`age_range_view`, `gender_view`)
- **Ubicaciones geográficas** con mejor rendimiento (`geographic_view`)
- **Intereses y audiencias** afines / in-market (`user_interest_view`)
- **Rendimiento de campañas** (impresiones, clics, CTR, costo, conversiones)

El conector cubre los últimos `days_back` (default 90) desde la fecha de hoy.

---

## OPCION A: Manual (Recomendado para empezar)

Es la forma más rápida de probar. Usás los copys, keywords y targeting que el
sistema ya generó y los cargás manualmente en Google Ads. Toma ~15 min/persona.

### Paso 1: Crear audiencias en Google Ads

1. Entrá a https://ads.google.com/
2. Vas a **Herramientas → Administrador de audiencias → Crear audiencia**

#### Audiencia de clientes (Customer Match):
```
1. Tipo: Datos del cliente (Customer Match)
2. Subí tu CSV de ventas (data/sample_sales/ventas.csv)
3. Nombre: "Clientes - [Marca]" (ej: "Clientes - Zeekr")
4. Membresía: 365 días
```

#### Audiencia Similar (Similar Audiences):
```
1. Tipo: Audiencias similares
2. Fuente: "Clientes - [Marca]"
3. Tamaño: 1% (más parecido a tus clientes)
4. Nombre: "Lookalike 1% - [Marca]"
```

### Paso 2: Crear la campaña

1. Vas a **Campañas → + Nueva campaña**
2. Objetivo: **Ventas** (o **Clientes potenciales** si buscás leads)
3. Tipo: **Búsqueda** (Search) o **Rendimiento Máximo** (Performance Max)
4. Nombre de campaña: usá el que generó el sistema
   (ej: `Google - SUV - Persona 01 - Comprador Zeekr`)

### Paso 3: Configurar el grupo de anuncios (Ad Group)

Abrí el archivo `Marketing/Google Ads - Persona 01.md` de tu Obsidian
y copiá estos datos:

```
En Google Ads → Ad Group → Configuración:

Demografía:
  - Edad: [copiar del archivo, ej: 25-34]
  - Género: [copiar del archivo, ej: Masculino]

Ubicaciones:
  - Buscar y agregar cada ciudad del archivo
  - Ej: Asunción, Ciudad del Este, Encarnación...

Audiencias (Audiencias detalladas / Detailed demographics):
  - Escribir cada interés del archivo
  - Ej: "SUV", "Vehículos eléctricos", "Compra de automóviles"
```

### Paso 4: Palabras clave (si es campaña de Búsqueda)

```
En Google Ads → Ad Group → Palabras clave:

Palabras clave principales:
  → Copiar la lista "keywords" del archivo .md
  → Ej: "zeekr precio", "zeekr 001", "suv eléctrico paraguay"

Palabras clave negativas (recomendado):
  → "usado", "segunda mano", "gratis", "barato"
```

### Paso 5: Crear los anuncios (Responsive Search Ads)

Usá el texto del archivo `Marketing/Google Ads - Persona 01.md`:

```
En Google Ads → Ad → Anuncio de búsqueda responsivo:

1. Titulares (Headlines - hasta 15):
   → Copiar la lista "headlines" del archivo .md
   → Ej: "Zeekr 001 | Test Drive Gratis"

2. Descripciones (hasta 4):
   → Copiar la lista "descriptions" del archivo .md

3. Sitelinks:
   → Copiar del archivo "sitelinks"

4. Ruta de visualización:
   → ej: zeekr.com/testdrive
```

### Paso 6: Presupuesto y Publicación

```
1. Budget: Diario $20-$50 por grupo de anuncios (recomendado)
2. Estrategia de oferta: Maximizar conversiones (o CPA objetivo)
3. Revisar y Publicar
```

---

## OPCION B: Automatizada (vía API)

> **Cambió el 9-sep-2026.** Google dio de baja el **token de desarrollador**: el acceso a la API de Google Ads
> lo da ahora el **proyecto de Google Cloud** dueño de la credencial y **ya no hace falta una cuenta
> administradora (MCC)**. Los pasos que traía esta guía (token de desarrollador, OAuth de escritorio y
> refresh token) ya no sirven. Fuente: documentación oficial de la API de Google Ads, leída el 26-09-2026.

Con **una cuenta de servicio de solo lectura** se leen Google Ads, Google Analytics 4 y Search Console.

| Paso | Dónde | Notas |
|---|---|---|
| 1. Crear el proyecto (ej. `santarosa-buyer-persona`) | console.cloud.google.com | Con la cuenta de Google de la empresa |
| 2. Activar Google Ads API, Google Analytics Data API, Google Analytics Admin API y Search Console API | APIs y servicios → Biblioteca | |
| 3. Pedir el nivel **Explorer** | Google Ads API → *Overview* → *Upgrade access level* | Lee cuentas reales, hasta 2.880 operaciones por día. Google suele aprobarlo solo. El planificador de palabras clave pide el nivel Basic (verificar la marca del proyecto) |
| 4. Crear la cuenta de servicio y su clave JSON | IAM y administración → Cuentas de servicio → Claves → Crear clave nueva (JSON) | Guardar la clave **fuera del repo**, con `chmod 600`. Nunca por chat |
| 5. Darle acceso de **solo lectura** al mail de la cuenta de servicio | Google Ads: Administrador → Acceso y seguridad → Usuarios · GA4: Administrar → Gestión del acceso · Search Console: Configuración → Usuarios y permisos | Lo hace quien administra cada cuenta |
| 6. Completar el `.env` | | `GOOGLE_SA_KEY_FILE=/ruta/a/la/clave.json` y `GOOGLE_ADS_CUSTOMER_IDS=1234567890:Marca,...` (sin guiones) |
| 7. Verificar | `venv/bin/python3 scripts/verificar_google.py` | Dice qué ve en cada servicio y qué falta |

**Falta del lado del código** (ver el Manual del vault, sección 4.5): actualizar la librería `google-ads` (la
fijada en `requirements.txt` es anterior al cambio), que el conector lea una cuenta por marca (hoy lee una sola,
`GOOGLE_ADS_CUSTOMER_ID`; `GOOGLE_ADS_CUSTOMER_IDS` todavía no se usa) y sumar los términos de búsqueda.
