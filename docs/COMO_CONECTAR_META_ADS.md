# 🟣 Cómo conectar tus Buyer Personas a Meta Ads

## Hay 2 formas de hacerlo:

---

## OPCION A: Manual (Recomendado para empezar)

Es la forma más rápida. Usás los copys y targeting que el sistema ya generó
y los cargás manualmente en Meta Ads Manager. Toma ~15 minutos por persona.

### Paso 1: Crear Audiencias en Meta Business Suite

1. Entrá a https://business.facebook.com/
2. Ve a **Audiences** → **Create Audience** → **Custom Audience**

#### Audiencia de Clientes (Custom Audience):
```
1. Tipo: Customer File (subir archivo)
2. Subí tu CSV de ventas (data/sample_sales/ventas.csv)
3. Nombre: "Clientes - [Marca]" (ej: "Clientes - Zeekr")
4. Retención: 365 días
```

#### Audiencia Similar (Lookalike):
```
1. Tipo: Lookalike Audience
2. Fuente: "Clientes - [Marca]" (la que creaste arriba)
3. País: Paraguay
4. Tamaño: 1% (más parecido a tus clientes)
5. Nombre: "Lookalike 1% - [Marca]"
```

### Paso 2: Crear la Campaña

1. Ve a **Ads Manager** → **Create** → **Campaign**
2. Objetivo: **Sales** (o **Leads** si buscás contactos)
3. Nombre de campaña: usá el que generó el sistema
   (ej: `Meta - SUV - Persona 01 - Comprador Zeekr`)

### Paso 3: Configurar el Conjunto de Anuncios (Ad Set)

Abrí el archivo `Marketing/Meta Ads - Persona 01.md` de tu Obsidian
y copiá estos datos:

```
Ubicación en Meta Ads: Ad Set → Detailed Targeting

Demografía:
  - Age: [copiar del archivo, ej: 25-34]
  - Gender: [copiar del archivo, ej: Men]

Ubicación geográfica:
  - Buscar y agregar cada ciudad del archivo
  - Ej: Asunción, Ciudad del Este, Encarnación...

Intereses detallados (Detailed Targeting):
  - Escribir cada interés del archivo en la barra de búsqueda
  - Ej: "SUV", "Zeekr", "Electric vehicle"

Comportamientos (Behaviors):
  - "Engaged Shoppers"
  - "Vehicle buyers"
```

### Paso 4: Crear el Anuncio (Ad)

Usá el texto del archivo `Marketing/Meta Ads - Persona 01.md`:

```
En Meta Ads → Ad → crear nuevo anuncio:

1. Primary Text:
   → Copiar y pegar el "primary_text" del archivo
   (el texto con emojis, beneficios y CTA)

2. Headline:
   → Copiar del archivo (ej: "Zeekr Mix | Test Drive Gratis")

3. Description:
   → Copiar del archivo (ej: "Reservá hoy tu prueba")

4. Call to Action (CTA):
   → Usar el CTA del archivo (ej: "Enviar mensaje de WhatsApp")

5. Creative (imagen/video):
   → Subir foto del vehículo
   → O crear carrusel con los modelos del archivo
```

### Paso 5: Presupuesto y Publicación

```
1. Budget: Daily budget $20-$50 (recomendado por conjunto)
2. Optimization: Conversions (Formularios o WhatsApp)
3. Schedule: Revisar y publicar
```

---

## OPCION B: Automatizada (Vía API)

El sistema puede conectarse directamente con la API de Meta
para crear audiencias y campañas automáticamente.

### Paso 1: Configurar credenciales

```bash
# En tu archivo .env:
META_ADS_ACCESS_TOKEN=EAAGxxxxxxxxx     # Token de acceso
META_ADS_AD_ACCOUNT_ID=act_1234567890   # ID de tu cuenta publicitaria
META_ADS_APP_ID=1234567890              # App ID
META_ADS_APP_SECRET=xxxxxxxxx           # App Secret
```

### Paso 2: Dónde obtener cada credencial

```
Access Token:
  1. Ir a https://developers.facebook.com/tools/explorer/
  2. Seleccionar tu app
  3. Generar token con permisos:
     - ads_management
     - ads_read
     - business_management

Ad Account ID:
  1. Ir a https://business.facebook.com/adsmanager
  2. Copiar el ID de la cuenta (formato: act_XXXXXXXXXX)

App ID y Secret:
  1. Ir a https://developers.facebook.com/apps/
  2. Seleccionar tu app
  3. Settings → Basic
```

### Paso 3: Activar en settings.yaml

```yaml
meta_ads:
  enabled: true      # ← Cambiar a true
  days_back: 90
```

### Paso 4: Ejecutar

```bash
python main.py
# El sistema automáticamente:
# 1. Lee tus campañas existentes de Meta
# 2. Extrae datos de audiencia
# 3. Genera Buyer Personas enriquecidas con datos reales
# 4. Crea copys personalizados
```

---

## 📋 Checklist completo para Meta Ads

- [ ] **Copiar** credenciales de Meta a `.env`
- [ ] **Activar** `meta_ads.enabled: true` en `config/settings.yaml`
- [ ] **Ejecutar** `python main.py` para generar personas con datos reales
- [ ] **Crear** audiencias personalizadas en Meta Business Suite
- [ ] **Crear** audiencias similares (Lookalike 1%)
- [ ] **Configurar** campaña por cada Buyer Persona
- [ ] **Copiar** el targeting del archivo `Meta Ads - [Persona].md`
- [ ] **Copiar** el primary text, headline y CTA del archivo
- [ ] **Publicar** y monitorear resultados
- [ ] **Semana 2**: Volver a ejecutar `python main.py` con datos actualizados

---

## 🔁 Flujo mensual recomendado

```
          ┌──────────────────────────┐
          │  1. python main.py       │  → Actualiza Buyer Personas
          │     (con datos nuevos)   │
          └───────────┬──────────────┘
                      │
                      ▼
          ┌──────────────────────────┐
          │  2. Revisar copys nuevos │  → En Obsidian
          │     en Marketing/        │
          └───────────┬──────────────┘
                      │
                      ▼
          ┌──────────────────────────┐
          │  3. Actualizar Meta Ads  │  → Copiar nuevos copys
          │     con el nuevo copy    │
          └───────────┬──────────────┘
                      │
                      ▼
          ┌──────────────────────────┐
          │  4. Crear variantes A/B  │  → Probar 2 copys
          │     por cada persona     │
          └───────────┬──────────────┘
                      │
                      ▼
          ┌──────────────────────────┐
          │  5. Medir resultados     │  → ¿Qué persona convierte más?
          │     y ajustar            │
          └──────────────────────────┘
                      │
                 (repetir mes siguiente)
```

---

## 💡 Ejemplo práctico: Lanzar campaña para Zeekr

### Archivo a usar: `Marketing/Meta Ads - Persona 01.md`

```
1. Meta Business Suite → Audiences → Create

   Custom Audience:
   ✅ Subir CSV de clientes
   ✅ Nombre: "Clientes Zeekr"

   Lookalike:
   ✅ Fuente: Clientes Zeekr
   ✅ 1% - Paraguay

2. Ads Manager → Create Campaign
   ✅ Objetivo: Sales
   ✅ Nombre: "Meta - SUV - Comprador Zeekr"

3. Ad Set:
   ✅ Age: 25-34
   ✅ Gender: Men
   ✅ Location: Asunción, Ciudad del Este, Encarnación
   ✅ Interests: Zeekr, SUV, Electric vehicle
   ✅ Audience: Lookalike 1% Zeekr
   ✅ Budget: $30/day

4. Ad:
   ✅ Primary Text: (copiar del archivo .md)
   ✅ Headline: "Zeekr Mix | Test Drive Gratis"
   ✅ CTA: "Enviar mensaje de WhatsApp"
   ✅ Imagen: Foto del Zeekr Mix

5. Publish ✅
```

¡Y listo! Tu campaña está segmentada exactamente según tu Buyer Persona.