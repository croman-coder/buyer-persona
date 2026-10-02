# CLAUDE.md — Pautas con el Buyer Persona 360 · Santa Rosa Automotores

> Lo lee Claude Code al abrir esta carpeta. Está pensado para quien se encarga de las **pautas** de las marcas de Santa Rosa (Meta Ads hoy, Google Ads próximamente) usando el Buyer Persona como base. El sistema (pipeline, servidor, Cerebro) lo mantiene Croman (Carlos Roman, Innovación); detalle técnico en `README.md`.

## De dónde sale esto

- `Buyer Persona/` es el **vault de Obsidian** (en Obsidian: *Abrir carpeta como vault*). En el servidor se regenera todos los días a las 06:00 con datos reales de Meta Ads (85 cuentas), el ERP de ventas y Bitrix (solo agregados).
- Esta carpeta es una **copia** y puede estar unos días atrasada. Para ponerla al día: `git pull` (con acceso al repo privado `croman-coder/buyer-persona`) o una copia nueva de Croman. **No editar las notas generadas:** la próxima corrida las pisa.
- En la web, con login: https://cerebro.santarosa.lat (mismo usuario que los tableros).

## Antes de armar una pauta, leer en este orden

1. `Buyer Persona/Sistema/📘 Manual Buyer Persona.md`, **sección 4**: qué plataforma para qué, el flujo con Meta, **cuándo juzgar** una campaña y cuándo cortarla.
2. La ficha del modelo, `Buyer Persona/Buyer Personas/<Marca>/<Marca Modelo>.md`: público (edad, género, zona), temas que atraen, brecha pauta/venta, presupuesto sugerido, **oferta vigente** y stock.
3. `Buyer Personas/<Marca>/👥 Quién mira y quién decide — <Marca>.md`: la pieza sugerida para quien acompaña la decisión.
4. Los textos listos en `Buyer Personas/<Marca>/Marketing/`: `Meta Ads -`, `Google Ads -`, `Email -` y `WhatsApp -`.
5. Lo que ya se probó, en `Buyer Persona/Campañas/`: pautas IA de Mitsubishi, Renault y Renew, y la prueba de GWM H6.
6. Referencias: `🤖 Meta Ads Lo Que Funciona`, `🎯 Playbook Meta Ads` y `💸 Pauta Meta Rendimiento` (en `Buyer Personas/`), `Sistema/🧠 Memoria de Audiencia.md`, `Investigación/📈 Curva de aprendizaje — Google Ads vs Meta (26 semanas).md` y `Cuentas Meta/` (cada anuncio de cada cuenta).

Marcas: GWM · JAC · Jetour · JMEV · Leapmotor · Mitsubishi · Renault · Renew (usados certificados) · Soueast · XPeng · Zeekr.

## Reglas que no se negocian

1. **Ley de Paraguay:** nunca nombrar marcas ni modelos de la competencia en un texto público; solo argumentos propios. `Competencia/`, las battle cards y el benchmark son de uso interno.
2. **Toda campaña se crea en PAUSA.** Se activa solo con el OK explícito de Croman o de la marca.
3. **Campañas de agencia:** no tocar presupuesto, segmentación ni anuncios sin coordinar con la agencia (Mitsubishi: Cecilia; Renault: Fabrizzio). No pautarle al mismo público que una campaña que ya corre en la misma cuenta: se encarecen entre ellas (pasó con la L200 en septiembre).
4. **Presupuesto:** un conjunto con optimización a conversaciones necesita **al menos USD 5 por día**; con menos, Meta no lo entrega. Para que aprenda hacen falta ~50 resultados por semana: presupuesto diario ≈ 7 × el costo por resultado de la marca. Mejor un conjunto con plata que tres chicos.
5. **Cuándo juzgar:** a las 3-4 semanas, con el promedio de 4 semanas. La primera semana suele salir más barata y engaña. Cortar antes solo si compite con otra campaña nuestra o si a las 2 semanas cuesta el doble o más que el promedio de la marca (casi nunca se recupera).
6. **Textos:** sin tasas, plazos, garantías ni urgencias inventadas. La oferta del mes sale de la planilla de acciones (bloque «Oferta del mes» de cada nota) y se confirma con la marca. Test drive solo si el stock tiene unidad de prueba (lo dice cada nota). ⚠️ Las notas `Meta Ads -` todavía traen «Garantía de 5 años» y «Financiación a 60 meses» fijos: no usar esas líneas sin confirmarlas.
7. **Datos de clientes:** ningún nombre, mail ni teléfono en archivos ni en el chat. Subir una lista de clientes a Meta o Google necesita el OK de Croman. La base de ventas de Mitsubishi no sirve para públicos (tiene los contactos de Nipon).
8. **Claves:** nunca en archivos versionados ni en el chat; solo en `.env`, que no viene en esta copia.

## Herramientas

- **Conector de Meta (`facebook-ads`)**: viene configurado en `.mcp.json` (el oficial de Meta, `https://mcp.facebook.com/ads`) y no lleva claves. La primera vez, Claude Code pregunta si usar el servidor de `.mcp.json`: aceptar. Después `/mcp` → `facebook-ads` → *Authenticate*, y entrar con **el usuario de Facebook de quien pauta**, con acceso a las cuentas en el Business Manager de Santa Rosa. Si deja de pautar, se le saca el acceso ahí.
- **Skill `meta-ads-santarosa`** (`.claude/skills/`): cuentas, páginas y formularios de cada marca, y cómo armar la campaña. Se carga sola al abrir Claude Code en esta carpeta.
- **Scripts de lectura** (necesitan `META_ADS_ACCESS_TOKEN` y `META_ADS_AD_ACCOUNT_IDS` en `.env`): `scripts/diagnostico_pauta.py` (14 días, todas las cuentas: conjuntos caros, chicos y con fatiga), `scripts/informe_pautas_ia.py` y `scripts/curva_aprendizaje.py`.
- **Entorno:** `python3 -m venv venv && venv/bin/pip install -r requirements.txt` y `cp .env.example .env`.

## Pendiente al 26-09-2026 (confirmar con Croman)

- **Mitsubishi y Renault:** plan de mejora sin tocar segmentación ni presupuesto, esperando OK. Está al final de cada nota de `Campañas/`.
- **GWM H6:** anuncio «Vengan a probarla juntos» creado en pausa, esperando OK.
- **Google Ads:** falta conectar la API con una cuenta de servicio (Manual, sección 4.5). Las notas `Google Ads -` ya son borradores listos para cargar.
