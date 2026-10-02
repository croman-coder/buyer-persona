#!/usr/bin/env python3
"""
 ===========================================================================
  Generador de Buyer Persona - Pipeline Principal
 ===========================================================================

  Orquesta la extracción de datos desde múltiples fuentes:
    1. Google Ads    (demografía, intereses, ubicaciones, campañas)
    2. Meta Ads      (audiencia, targeting, rendimiento)
    3. Histórico de Ventas (productos, categorías, canales, clientes)

  Luego consolida todo y genera Buyer Personas que se exportan
  como notas de Obsidian (Markdown con frontmatter, tags y wikilinks).

  Uso:
    python main.py                         # Usa config/settings.yaml
    python main.py --config ruta.yaml      # Configuración personalizada
    python main.py --demo                  # Ejecuta con datos de ejemplo
 ===========================================================================
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Asegurar que el directorio actual esté en el path
sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import load_config
from src.connectors.google_ads_connector import GoogleAdsConnector
from src.connectors.meta_ads_connector import MetaAdsConnector
from src.connectors.sales_connector import SalesConnector
from src.connectors.funnel_connector import FunnelConnector
from src.connectors.bitrix_connector import BitrixConnector
from src.connectors.datacar_connector import DatacarConnector
from src.generators.competitor_analyzer import analyze as analyze_competitors, price_changes
from src.exporters import competitor_exporter
from src.generators.persona_generator import PersonaGenerator
from src.generators.marketing_generator import MarketingContentGenerator
from src.exporters.obsidian_exporter import ObsidianExporter
from src.exporters.funnel_exporter import FunnelExporter

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)-30s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("buyer-persona")


# ---------------------------------------------------------------------------
# Exportación de Marketing a Obsidian
# ---------------------------------------------------------------------------

def _linea_test_drive(item: dict) -> str | None:
    """Qué dice el stock del ERP sobre la unidad de prueba (solo modelos 0km)."""
    if item.get("tipo") != "model" or item.get("used"):
        return None
    td, n = item.get("test_drive"), item.get("test_drive_unidades")
    if td:
        return f"**Test drive:** hay {n} unidad{'es' if n != 1 else ''} de prueba en el stock de hoy (ERP)."
    if td is False:
        return "**Test drive:** no hay unidad de prueba en el stock de hoy (ERP): los textos invitan a verlo en el salón."
    return "**Test drive:** sin dato de stock. Confirmar que haya unidad antes de prometerlo."


def _bloque_oferta_y_stock(item: dict, canal: str) -> list[str]:
    """Oferta del mes (planilla de acciones) y stock (ERP), aparte: se confirman antes de usarlos."""
    oferta, disponible = item.get("offer"), item.get("stock_disponible")
    if not oferta and not disponible:
        return []
    lines = ["", "## 💲 Oferta del mes y stock: confirmar antes de usar",
             "> [!warning] Sale de la planilla de acciones comerciales y del stock del ERP",
             "> Vence con el mes y puede tener condiciones. No se usa sin confirmarla con la marca.", ""]
    if item.get("offer_text"):
        etiqueta = "Párrafo para sumar al mail" if canal == "email" else "Mensaje para sumar"
        lines.append(f"- {etiqueta}: `{item['offer_text']}`")
    if oferta:
        partes = []
        if oferta.get("pvp_min"):
            partes.append("precio de lista desde USD " + f"{oferta['pvp_min']:,.0f}".replace(",", "."))
        if oferta.get("descuento_max"):
            partes.append("descuento hasta USD " + f"{oferta['descuento_max']:,.0f}".replace(",", "."))
        lines.append(f"- Planilla ({oferta.get('periodo') or 'vigente'}): " + " · ".join(partes))
        for c in oferta.get("condiciones", []):
            lines.append(f"- Condición en la planilla: {c}")
    if disponible:
        lines.append(f"- Stock disponible hoy (ERP): {disponible} unidades. «Entrega inmediata» solo si la marca lo confirma.")
    return lines


RESPUESTAS_WHATSAPP = {"precio": "el precio", "test_drive": "el test drive", "financiacion": "la financiación",
                       "usado": "su usado como parte de pago"}


def _export_marketing_to_obsidian(
    content: dict,
    output_dir: Path,
    exporter: ObsidianExporter,
    subdir_by_persona: dict[str, str] | None = None,
) -> list[Path]:
    """
    Exporta el contenido de marketing como notas Markdown de Obsidian.
    Cada nota va a ``<carpeta de la marca>/Marketing/`` (``subdir_by_persona``
    mapea nombre de persona → carpeta); sin mapa, todo a ``output_dir``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    subdir_by_persona = subdir_by_persona or {}

    def _dir_for(persona_name: str) -> Path:
        sub = subdir_by_persona.get(persona_name)
        d = output_dir / sub / "Marketing" if sub else output_dir
        d.mkdir(parents=True, exist_ok=True)
        return d

    # --- Google Ads ---
    for ad in content.get("google_ads", []):
        safe = exporter._sanitize_filename(ad.get("persona", "persona"))
        path = _dir_for(ad.get("persona", "")) / f"Google Ads - {safe}.md"
        lines = [
            "---",
            f"type: google-ads",
            f"persona: {ad.get('persona', '')}",
            f"campaign: {ad.get('campaign_name', '')}",
            f"tags: [marketing, google-ads]",
            "---",
            f"# 🔵 Google Ads - {ad.get('persona', '')}",
            f"**Persona:** [[{ad.get('persona', '')}]] · **Campaña sugerida:** `{ad.get('campaign_name', '')}` · búsqueda, anuncio responsivo",
            *[x for x in [_linea_test_drive(ad)] if x],
            "",
            "> [!info] Borrador listo para cargar",
            "> Cada texto respeta los límites de Google (títulos de 30 caracteres, descripciones de 90) y no promete tasas, "
            "plazos ni garantías. Sale del modelo y de los temas que más se repiten en sus anuncios, no del análisis interno "
            "de la ficha. La oferta del mes va aparte, al final, y se confirma con la marca antes de publicar. Cómo arrancar "
            "y cuándo juzgar la campaña: [[📘 Manual Buyer Persona#4.5 Google Ads — qué falta y cómo vamos a arrancar|Manual, 4.5]].",
            "",
            "## Títulos (hasta 15 · máx. 30 caracteres)",
            "| # | Título | Caract. |",
            "|---|---|---|",
        ]
        for i, h in enumerate(ad.get("headlines", []), 1):
            lines.append(f"| {i} | {h} | {len(h)} |")
        lines += ["", "## Descripciones (hasta 4 · máx. 90 caracteres)", "| # | Descripción | Caract. |", "|---|---|---|"]
        for i, d in enumerate(ad.get("descriptions", []), 1):
            lines.append(f"| {i} | {d} | {len(d)} |")
        if ad.get("paths"):
            lines += ["", f"**URL visible:** `…/{'/'.join(ad['paths'])}` (cada tramo, máx. 15 caracteres)"]
        lines += ["", "## Palabras clave",
                  '_`"entre comillas"` = concordancia de frase · `[entre corchetes]` = concordancia exacta._', ""]
        grupos = ad.get("keyword_groups") or {"Palabras clave": ad.get("keywords", [])}
        for grupo, kws in grupos.items():
            if kws:
                lines.append(f"- **{grupo}:** " + " · ".join(f"`{k}`" for k in kws))
        if ad.get("negative_keywords"):
            lines.append("- **Negativas** (búsquedas que no son de compra): "
                         + " · ".join(f"`-{k}`" for k in ad["negative_keywords"]))
        lines += ["", "## Extensiones", "**Sitelinks** (texto máx. 25 · cada línea máx. 35)"]
        for s in ad.get("sitelinks", []):
            lines.append(f"- **{s['text']}** — {s['desc1']} / {s['desc2']}")
        if ad.get("callouts"):
            lines += ["", "**Textos destacados** (máx. 25): " + " · ".join(ad["callouts"])]
        oferta = ad.get("offer")
        if oferta:
            lines += ["", f"## 💲 Oferta del mes ({oferta.get('periodo') or 'vigente'}): confirmar antes de publicar",
                      "> [!warning] Sale de la planilla de acciones comerciales",
                      "> Vence con el mes y puede tener condiciones. No se sube sin confirmarla con la marca.", ""]
            for t in oferta.get("titulos", []):
                lines.append(f"- Título: `{t}` ({len(t)})")
            if oferta.get("descripcion"):
                lines.append(f"- Descripción: `{oferta['descripcion']}` ({len(oferta['descripcion'])})")
            for c in oferta.get("condiciones", []):
                lines.append(f"- Condición en la planilla: {c}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        files.append(path)

    # --- Meta Ads ---
    for ad in content.get("meta_ads", []):
        safe = exporter._sanitize_filename(ad.get("persona", "persona"))
        path = _dir_for(ad.get("persona", "")) / f"Meta Ads - {safe}.md"
        targeting = ad.get("targeting", {})
        lines = [
            "---",
            f"type: meta-ads",
            f"persona: {ad.get('persona', '')}",
            f"campaign: {ad.get('campaign_name', '')}",
            f"tags: [marketing, meta-ads]",
            "---",
            f"# 🟣 Meta Ads - {ad.get('persona', '')}",
            f"**Persona:** [[{ad.get('persona', '')}]]",
            f"**Campaña:** `{ad.get('campaign_name', '')}`",
            "## Targeting",
            f"- **Edad:** {targeting.get('age_range', 'N/D')}",
            f"- **Género:** {targeting.get('gender', 'N/D')}",
            f"- **Intereses:** {', '.join(targeting.get('interests', []))}",
            f"- **Ubicaciones:** {', '.join(targeting.get('locations', []))}",
            "## Primary Text",
            "```",
            ad.get("primary_text", ""),
            "```",
            f"## Headline\n> {ad.get('headline', '')}",
            f"## Description\n> {ad.get('description', '')}",
            f"## CTA\n**{ad.get('cta', '')}**",
        ]
        if ad.get("carousel_cards"):
            lines.append("## Carrusel")
            for card in ad["carousel_cards"]:
                lines.append(f"- **{card['headline']}** — {card['description']}")
        path.write_text("\n".join(lines), encoding="utf-8")
        files.append(path)

    # --- Emails ---
    for email in content.get("emails", []):
        safe = exporter._sanitize_filename(email.get("persona", "persona"))
        path = _dir_for(email.get("persona", "")) / f"Email - {safe}.md"
        lines = [
            "---",
            f"type: email-marketing",
            f"persona: {email.get('persona', '')}",
            f"tags: [marketing, email]",
            "---",
            f"# 📧 Email - {email.get('persona', '')}",
            f"**Persona:** [[{email.get('persona', '')}]]",
            *[x for x in [_linea_test_drive(email)] if x],
            "",
            "> [!info] Cómo usar este mail",
            "> Los campos entre llaves (`{nombre}`, `{link}`) los completa la herramienta de envío. No promete tasas, "
            "plazos, garantías ni urgencias: la oferta del mes y el stock van al final, para confirmar con la marca "
            "antes de sumarlos.",
            "",
            f"## Asunto\n> {email.get('subject', '')}",
        ]
        if email.get("subject_alternatives"):
            lines += ["", "Alternativas: " + " · ".join(f"`{a}`" for a in email["subject_alternatives"])]
        lines += [
            f"## Pre-header\n> {email.get('preheader', '')}",
            "## Cuerpo del email",
            "```",
            email.get("body", ""),
            "```",
            "## Seguimiento (3 días después, si no respondió)",
            "```",
            email.get("follow_up_3_days", ""),
            "```",
        ]
        lines += _bloque_oferta_y_stock(email, "email")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        files.append(path)

    # --- WhatsApp ---
    for wa in content.get("whatsapp", []):
        safe = exporter._sanitize_filename(wa.get("persona", "persona"))
        path = _dir_for(wa.get("persona", "")) / f"WhatsApp - {safe}.md"
        templates = wa.get("templates", {})
        auto_replies = wa.get("auto_replies", {})
        lines = [
            "---",
            f"type: whatsapp-template",
            f"persona: {wa.get('persona', '')}",
            f"tags: [marketing, whatsapp]",
            "---",
            f"# 💬 WhatsApp - {wa.get('persona', '')}",
            f"**Persona:** [[{wa.get('persona', '')}]]",
            *[x for x in [_linea_test_drive(wa)] if x],
            "",
            "> [!info] Cuándo usar cada mensaje",
            "> Bienvenida, seguimiento y respuestas van dentro de las **24 horas** desde el último mensaje del cliente. "
            "Fuera de esa ventana, WhatsApp solo deja escribir con una **plantilla aprobada por Meta** (categoría marketing) "
            "y a quien aceptó recibir mensajes: esa es la invitación. `{asesor}` y `{nombre}` se completan al enviar. "
            "Sin tasas, plazos, garantías ni urgencias: la oferta del mes y el stock van al final, para confirmar antes.",
            "",
            "## Bienvenida (cuando el cliente escribe)",
            "```",
            templates.get("welcome", ""),
            "```",
            "## Seguimiento (dentro de las 24 horas)",
            "```",
            templates.get("follow_up", ""),
            "```",
            "## Invitación (plantilla de marketing, fuera de las 24 horas)",
            "```",
            templates.get("promo", ""),
            "```",
            "## Respuestas rápidas",
        ]
        for key, reply in auto_replies.items():
            lines.append(f"### Si pregunta por {RESPUESTAS_WHATSAPP.get(key, key)}")
            lines.append("```")
            lines.append(reply)
            lines.append("```")
        lines += _bloque_oferta_y_stock(wa, "whatsapp")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        files.append(path)

    logger.info("Exportadas %d notas de marketing", len(files))
    return files


# ---------------------------------------------------------------------------
# Exportación de Audiencias (Meta) a Obsidian
# ---------------------------------------------------------------------------

def _export_audiences_to_obsidian(
    audiences: list[dict],
    personas: list[dict],
    output_dir: Path,
    exporter: ObsidianExporter,
) -> list[Path]:
    """
    Exporta las custom audiences/lookalikes ya guardadas en Meta Ads como
    una nota de referencia por marca — para reusarlas en remarketing sin
    duplicar públicos que ya existen. Queda linkeada (ida y vuelta) con
    las personas de esa marca.
    """
    if not audiences:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    by_brand: dict[str, list[dict]] = {}
    for a in audiences:
        by_brand.setdefault(a.get("account", "Sin marca"), []).append(a)

    personas_by_brand: dict[str, list[str]] = {}
    for p in personas:
        segment = p.get("segment", {})
        if segment.get("type") == "brand" and segment.get("name"):
            personas_by_brand.setdefault(segment["name"], []).append(p.get("name", ""))

    files: list[Path] = []
    subtype_labels = {
        "CUSTOM": "Personalizada",
        "WEBSITE": "Visitantes del sitio",
        "ENGAGEMENT": "Interacción (IG/FB/anuncios)",
        "LOOKALIKE": "Público similar (Lookalike)",
        "IG_BUSINESS": "Interacción Instagram",
    }

    for brand, accs in by_brand.items():
        safe = exporter._sanitize_filename(brand)
        # Marca con carpeta propia → su nota va ahí; si no, a Audiencias/
        brand_dir = output_dir.parent / safe
        target_dir = brand_dir if brand_dir.is_dir() else output_dir
        path = target_dir / f"Audiencias Meta - {safe}.md"

        # Deduplicar por nombre (varias cuentas del mismo vendedor repiten audiencias)
        seen = {}
        for a in accs:
            seen[a["name"]] = a

        lines = [
            "---",
            "type: meta-audiences",
            f"marca: {brand}",
            "tags: [marketing, meta-ads, audiencias, remarketing]",
            "---",
            f"# 🎯 Audiencias Meta ya guardadas — {brand}\n",
            f"_{len(seen)} públicos únicos encontrados en las cuentas de {brand}. "
            "Reusalos para remarketing en vez de crear uno nuevo._\n",
            "| Audiencia | Tipo | Tamaño aprox. |",
            "|---|---|---|",
        ]
        for a in sorted(seen.values(), key=lambda x: x.get("size", 0) or 0, reverse=True):
            label = subtype_labels.get(a.get("subtype", ""), a.get("subtype", ""))
            size = a.get("size", 0)
            size_str = f"{size:,}" if isinstance(size, (int, float)) and size > 0 else "N/D"
            lines.append(f"| {a['name']} | {label} | {size_str} |")

        related = personas_by_brand.get(brand, [])
        if related:
            lines.append("\n## 🔗 Personas de esta marca\n")
            for name in related:
                lines.append(f"- [[{name}]]")

        path.write_text("\n".join(lines), encoding="utf-8")
        files.append(path)

    logger.info("Exportadas %d notas de audiencias (%d marcas)", len(files), len(by_brand))
    return files


# ---------------------------------------------------------------------------
# Interconexión: cada persona linkea de vuelta a su contenido de marketing
# ---------------------------------------------------------------------------

def _link_persona_notes(
    personas: list[dict],
    output_dir: Path,
    vault_dir: Path | None,
    brands_with_audiences: set[str],
) -> int:
    """
    Agrega a cada nota de persona ya escrita una sección '🔗 Contenido
    Relacionado' con wikilinks a sus 4 notas de marketing (Google Ads,
    Meta Ads, Email, WhatsApp) y a la nota de Audiencias de su marca si
    existe. Sin esto, esas notas quedan sueltas en el graph de Obsidian.
    """
    from src.exporters.obsidian_exporter import ObsidianExporter

    count = 0
    for persona in personas:
        name = persona.get("name", "")
        if not name:
            continue
        safe = ObsidianExporter._sanitize_filename(name)

        lines = ["\n## 🔗 Contenido Relacionado\n"]
        lines.append(f"- [[Google Ads - {safe}]]")
        lines.append(f"- [[Meta Ads - {safe}]]")
        lines.append(f"- [[Email - {safe}]]")
        lines.append(f"- [[WhatsApp - {safe}]]")

        segment = persona.get("segment", {})
        brand = segment.get("name") if segment.get("type") == "brand" else segment.get("brand")
        if brand:
            brand_safe = ObsidianExporter._sanitize_filename(brand)
            lines.append(f"- [[{brand_safe}|Índice de {brand}]]")
            if brand in brands_with_audiences:
                lines.append(f"- [[Audiencias Meta - {brand_safe}]]")

        block = "\n".join(lines) + "\n"

        subdir = ObsidianExporter.persona_subdir(persona)
        for base_dir in filter(None, [output_dir, vault_dir]):
            path = base_dir / subdir / f"{safe}.md"
            if not path.exists():
                continue
            with open(path, "a", encoding="utf-8") as f:
                f.write(block)
        count += 1

    return count


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(config_path: str = "config/settings.yaml", demo: bool = False, from_json: str = "") -> None:
    """
    Ejecuta el pipeline completo de generación de Buyer Personas.

    ``from_json`` salta los conectores y carga un ``output/raw/data_sources_*.json``
    ya guardado: sirve para regenerar notas sin volver a pegarle a Meta/Bitrix.
    """

    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║          🧠  GENERADOR DE BUYER PERSONA  🧠                  ║
    ║   Google Ads  │  Meta Ads  │  Ventas  →  Obsidian           ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

    start_time = datetime.now()

    # --- 1. Cargar configuración ---
    logger.info("Cargando configuración desde %s", config_path)
    config = load_config(config_path)

    if demo:
        logger.info("🔧 Modo DEMO activado: usando datos de ejemplo")
        config.setdefault("google_ads", {})["enabled"] = False
        config.setdefault("meta_ads", {})["enabled"] = False
        config.setdefault("sales", {})["enabled"] = True
        config["sales"]["file_path"] = config["paths"].get(
            "sales_history", "data/sample_sales/ventas.csv"
        )

    # --- 2. Recolectar datos de cada fuente ---
    data_sources: dict = {}
    if from_json:
        logger.info("📂 Cargando fuentes desde %s (sin llamar a las APIs)", from_json)
        with open(from_json, encoding="utf-8") as f:
            data_sources = json.load(f)
        for k in ("google_ads", "meta_ads", "sales", "bitrix", "datacar"):
            data_sources.setdefault(k, {})

    # 2a. Google Ads
    google_cfg = config.get("google_ads", {})
    if from_json:
        pass
    elif google_cfg.get("enabled") and not demo:
        logger.info("📡 Conectando a Google Ads...")
        try:
            google_connector = GoogleAdsConnector(google_cfg)
            data_sources["google_ads"] = google_connector.fetch_all()
            logger.info("✅ Google Ads: datos obtenidos correctamente")
        except Exception as e:
            logger.error("❌ Error con Google Ads: %s", e)
            data_sources["google_ads"] = {}
    else:
        logger.info("⏭️  Google Ads: deshabilitado")
        data_sources["google_ads"] = {}

    # 2b. Meta Ads
    meta_cfg = config.get("meta_ads", {})
    if from_json:
        pass
    elif meta_cfg.get("enabled") and not demo:
        logger.info("📡 Conectando a Meta Ads...")
        try:
            meta_connector = MetaAdsConnector(meta_cfg)
            data_sources["meta_ads"] = meta_connector.fetch_all()
            logger.info("✅ Meta Ads: datos obtenidos correctamente")
        except Exception as e:
            logger.error("❌ Error con Meta Ads: %s", e)
            data_sources["meta_ads"] = {}
    else:
        logger.info("⏭️  Meta Ads: deshabilitado")
        data_sources["meta_ads"] = {}

    # 2c. Histórico de Ventas
    sales_cfg = config.get("sales", {})
    if sales_cfg.get("enabled", True):   # archivo local: se relee siempre, también con --from-json
        logger.info("📡 Leyendo histórico de ventas...")
        sales_path = config["paths"].get("sales_history", "")
        sales_cfg["file_path"] = sales_path

        try:
            sales_connector = SalesConnector(sales_cfg)
            data_sources["sales"] = sales_connector.fetch_all()
            total = data_sources["sales"].get("total_records", 0)
            logger.info("✅ Ventas: %d registros procesados", total)
        except Exception as e:
            logger.error("❌ Error con ventas: %s", e)
            data_sources["sales"] = {}
    else:
        logger.info("⏭️  Ventas: deshabilitado")
        data_sources["sales"] = {}

    # 2c-bis-0. Fuentes complementarias (stock, acciones comerciales, objetivos, negociación)
    extras_cfg = config.get("extras", {})
    if extras_cfg.get("enabled"):
        try:
            from src.connectors.extras_erp import fetch_extras
            data_sources["extras"] = fetch_extras(extras_cfg, config["paths"].get("sales_history", ""))
            logger.info("✅ Extras: %s", ", ".join(k for k in ("stock", "acciones", "objetivos", "negociacion") if k in data_sources["extras"]))
        except Exception as e:
            logger.error("❌ Error con extras: %s", e)
            data_sources["extras"] = {}
    else:
        data_sources["extras"] = {}

    # 2c-bis. CRM Bitrix24 (solo agregados por marca)
    bitrix_cfg = config.get("crm", {}).get("bitrix", {})
    if from_json:
        pass
    elif bitrix_cfg.get("enabled") and not demo:
        logger.info("📡 Conectando a Bitrix24 (agregados)...")
        try:
            data_sources["bitrix"] = BitrixConnector(bitrix_cfg).fetch_all()
            logger.info("✅ Bitrix: %d leads, %d deals agregados por marca",
                        data_sources["bitrix"].get("total_leads", 0),
                        data_sources["bitrix"].get("total_deals", 0))
        except Exception as e:
            logger.error("❌ Error con Bitrix: %s", e)
            data_sources["bitrix"] = {}
    else:
        logger.info("⏭️  Bitrix: deshabilitado")
        data_sources["bitrix"] = {}

    # 2c-ter. Datacar: precios de lista del mercado 0km (competencia, uso interno)
    dc_cfg = config.get("competitors", {}).get("datacar", {})
    if from_json:
        pass
    elif dc_cfg.get("enabled") and not demo:
        logger.info("📡 Leyendo precios de mercado (Datacar)...")
        try:
            dc_data = DatacarConnector(dc_cfg).fetch_all()
            raw_dc_dir = Path("output/raw"); raw_dc_dir.mkdir(parents=True, exist_ok=True)
            prev_snapshot = raw_dc_dir / "datacar_latest.json"
            dc_changes = price_changes(dc_data["versions"], prev_snapshot)
            dc_analysis = analyze_competitors(dc_data["versions"], float(dc_cfg.get("price_band", 0.25)))
            data_sources["datacar"] = {**dc_data, "analysis": dc_analysis, "changes": dc_changes}
            with open(prev_snapshot, "w", encoding="utf-8") as f:
                json.dump(dc_data, f, ensure_ascii=False)
            logger.info("✅ Datacar: %d versiones, %d modelos nuestros cruzados, %d cambios de precio",
                        dc_data["counts"]["versions"], len(dc_analysis["by_model"]), len(dc_changes))
        except Exception as e:
            logger.error("❌ Error con Datacar: %s", e)
            data_sources["datacar"] = {}
    else:
        logger.info("⏭️  Datacar: deshabilitado")
        data_sources["datacar"] = {}

    # 2d. Embudo Completo (Full Funnel)
    funnel_cfg = config.get("funnel", {})
    if funnel_cfg.get("enabled") or demo:
        logger.info("📡 Recopilando datos del embudo completo...")
        # En modo demo, activar sub-fuentes con CSV disponibles
        if demo:
            import os
            embudo_dir = Path("data/embudo")
            if embudo_dir.exists():
                for sub in ["web_forms", "test_drives", "whatsapp", "quotes", "showroom", "surveys"]:
                    csv_file = {
                        "web_forms": "formularios_web.csv",
                        "test_drives": "test_drives.csv",
                        "whatsapp": "whatsapp_conversaciones.csv",
                        "quotes": "cotizaciones.csv",
                        "showroom": "visitas_showroom.csv",
                        "surveys": "encuestas_satisfaccion.csv",
                    }[sub]
                    csv_path = embudo_dir / csv_file
                    if csv_path.exists():
                        funnel_cfg.setdefault(sub, {})["enabled"] = True
                        funnel_cfg[sub]["csv_path"] = str(csv_path)
                        logger.info("   → %s: activado", sub)

        try:
            funnel_connector = FunnelConnector(funnel_cfg)
            funnel_data = funnel_connector.fetch_all()
            data_sources["funnel"] = funnel_data

            # Exportar dashboard del embudo
            funnel_exporter = FunnelExporter(config["paths"].get("output_dir", "output/personas"))
            funnel_file = funnel_exporter.export(funnel_data)
            generated_files_extra = [funnel_file]

            # Copiar al vault
            vault_path = config["paths"].get("obsidian_vault", "")
            if vault_path:
                import shutil
                target = Path(vault_path) / "Buyer Personas"
                target.mkdir(parents=True, exist_ok=True)
                shutil.copy2(funnel_file, target / funnel_file.name)

            logger.info("✅ Embudo: dashboard generado")
        except Exception as e:
            logger.error("❌ Error con embudo: %s", e)
            data_sources["funnel"] = {}
    else:
        logger.info("⏭️  Embudo: deshabilitado")
        data_sources["funnel"] = {}

    # --- 3. Verificar que hay al menos una fuente con datos ---
    has_data = any(data_sources.values())
    if not has_data:
        logger.error("🛑 No hay datos de ninguna fuente. Abortando.")
        logger.info("💡 Ejecuta con --demo para probar con datos de ejemplo.")
        sys.exit(1)

    # --- 4. Guardar datos crudos (para debugging) ---
    raw_dir = Path("output/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"data_sources_{start_time.strftime('%Y%m%d_%H%M%S')}.json"

    def _json_default(obj):
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return str(obj)

    if from_json:
        logger.info("💾 Fuentes cargadas de %s: no se vuelve a guardar el JSON crudo", from_json)
    else:
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(data_sources, f, indent=2, ensure_ascii=False, default=_json_default)
        logger.info("💾 Datos crudos guardados en %s", raw_path)

    # --- 5. Generar Buyer Personas ---
    logger.info("🧠 Generando Buyer Personas...")
    persona_cfg = config.get("persona", {})
    generator = PersonaGenerator(persona_cfg)
    personas = generator.generate(data_sources)

    logger.info("✅ %d Buyer Personas generadas", len(personas))

    # Guardar personas en JSON
    personas_json_path = raw_dir / f"personas_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(personas_json_path, "w", encoding="utf-8") as f:
        json.dump(personas, f, indent=2, ensure_ascii=False, default=_json_default)
    logger.info("💾 Personas (JSON) guardadas en %s", personas_json_path)

    # --- 5b. Centro de compra: quién mira, quién da el paso, quién paga ---
    centro: dict = {}
    try:
        from src.generators.centro_de_compra import analizar as analizar_centro
        centro = analizar_centro(data_sources, str(raw_dir))
        centro_json_path = raw_dir / f"centro_de_compra_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(centro_json_path, "w", encoding="utf-8") as f:
            json.dump(centro, f, indent=1, ensure_ascii=False, default=_json_default)
        logger.info("👥 Centro de compra: %d marcas → %s", len(centro.get("marcas", {})), centro_json_path)
    except Exception as exc:  # no debe tumbar las fichas
        logger.warning("👥 Centro de compra: no se pudo calcular: %s", exc)

    # --- 6. Exportar a Obsidian ---
    logger.info("📝 Exportando a Obsidian...")

    # Preparar config del exportador
    sales_path = str(config["paths"].get("sales_history", ""))
    export_cfg = {
        "output_dir": config["paths"].get("output_dir", "output/personas"),
        "obsidian_vault": config["paths"].get("obsidian_vault", ""),
        # Marcar las notas si el histórico de ventas todavía es el de ejemplo
        "sales_is_sample": "sample" in sales_path.lower() or "ejemplo" in sales_path.lower(),
    }
    export_cfg.update(config.get("obsidian", {}))

    exporter = ObsidianExporter(export_cfg)
    exporter.centro = centro
    generated_files = exporter.export_all(personas)
    try:
        generated_files.extend(exporter.export_centro_de_compra(personas))
        hub = exporter.export_centro_hub(personas)
        if hub:
            logger.info("👥 Centro de compra: comparación entre marcas en %s", hub)
    except Exception as exc:
        logger.warning("👥 Centro de compra: no se pudieron escribir las notas: %s", exc)

    # --- 6b. Generar contenido de marketing ---
    logger.info("📣 Generando contenido de marketing (Google Ads, Meta Ads, Emails, WhatsApp)...")
    marketing_generator = MarketingContentGenerator()
    marketing_content = marketing_generator.generate_all(personas)

    # Guardar marketing en JSON
    marketing_json_path = raw_dir / f"marketing_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(marketing_json_path, "w", encoding="utf-8") as f:
        json.dump(marketing_content, f, indent=2, ensure_ascii=False, default=_json_default)
    logger.info("💾 Marketing (JSON) guardado en %s", marketing_json_path)

    # Exportar marketing a Obsidian
    personas_dir = Path(config["paths"].get("output_dir", "output/personas"))
    subdir_by_persona = {p.get("name", ""): ObsidianExporter.persona_subdir(p) for p in personas}
    marketing_files = _export_marketing_to_obsidian(
        marketing_content, personas_dir, exporter, subdir_by_persona
    )

    # Copiar marketing al vault si está configurado (misma subcarpeta de marca)
    vault_path = config["paths"].get("obsidian_vault", "")
    if vault_path:
        import shutil
        base = Path(vault_path) / "Buyer Personas"
        for f in marketing_files:
            dest = base / f.relative_to(personas_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
        logger.info("Copiados %d archivos de marketing al vault", len(marketing_files))

    # Sacar lo que esta corrida ya no produce (fichas y marketing de modelos
    # que salieron del portfolio): si quedan, se leen como datos actuales.
    vivas = {p.get("name", "") for p in personas}
    ObsidianExporter.cleanup_stale_notes(personas_dir, vivas)
    if vault_path:
        ObsidianExporter.cleanup_stale_notes(Path(vault_path) / "Buyer Personas", vivas)

    generated_files.extend(marketing_files)

    # --- 6c. Exportar audiencias de Meta ya guardadas ---
    audiences = getattr(generator, "audiences", [])
    audiences_output_dir = Path(config["paths"].get("output_dir", "output/personas")) / "Audiencias"
    audiences_files = _export_audiences_to_obsidian(audiences, personas, audiences_output_dir, exporter)

    if vault_path and audiences_files:
        import shutil
        base = Path(vault_path) / "Buyer Personas"
        for f in audiences_files:
            dest = base / f.relative_to(personas_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
        logger.info("Copiados %d archivos de audiencias al vault", len(audiences_files))

    generated_files.extend(audiences_files)

    # --- 6c-bis. Nota de precios de competencia (Datacar) ---
    if data_sources.get("datacar"):
        dc = data_sources["datacar"]
        comp_dir = Path(config["paths"].get("output_dir", "output/personas")).parent / "competencia"
        comp_note = competitor_exporter.export(dc["analysis"], dc, dc.get("changes", []), comp_dir)
        if vault_path:
            target = Path(vault_path) / "Competencia"
            target.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(comp_note, target / comp_note.name)
        generated_files.append(comp_note)

    # --- 6d. Interconectar: cada persona linkea de vuelta a su marketing/audiencias ---
    brands_with_audiences = {a.get("account", "") for a in audiences} if audiences else set()
    linked_files = _link_persona_notes(
        personas,
        Path(config["paths"].get("output_dir", "output/personas")),
        Path(vault_path) / "Buyer Personas" if vault_path else None,
        brands_with_audiences,
    )
    logger.info("Interconectadas %d notas de persona con su marketing/audiencias", linked_files)

    # --- 6d-bis. Memoria de audiencia: serie diaria + nota de aprendizajes ---
    if vault_path:
        try:
            from src.learning.audience_memory import update_memory
            mem_note = update_memory(personas, data_sources, Path(vault_path))
            generated_files.append(mem_note)
        except Exception as e:  # la memoria no debe tumbar la corrida
            logger.error("❌ Memoria de audiencia: %s", e, exc_info=True)

    # --- 6e. Linkear el MOC con Audiencias y Embudo (si existen) ---
    moc_path = Path(config["paths"].get("output_dir", "output/personas")) / config.get(
        "obsidian", {}
    ).get("index_filename", "Buyer Personas MOC.md")
    extra_links = []
    if data_sources.get("funnel"):
        extra_links.append("- [[📊 Embudo de Ventas]]")

    if extra_links:
        block = "\n## 📊 Otros Recursos\n\n" + "\n".join(extra_links) + "\n"
        for base_dir in filter(None, [moc_path.parent, Path(vault_path) / "Buyer Personas" if vault_path else None]):
            p = base_dir / moc_path.name
            if p.exists():
                with open(p, "a", encoding="utf-8") as f:
                    f.write(block)

    # --- 7. Resumen final ---
    elapsed = (datetime.now() - start_time).total_seconds()

    summary = f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    ✅  COMPLETADO                            ║
    ╠══════════════════════════════════════════════════════════════╣"""

    active_sources = []
    if data_sources.get("google_ads"):
        active_sources.append("Google Ads")
    if data_sources.get("meta_ads"):
        active_sources.append("Meta Ads")
    if data_sources.get("sales"):
        active_sources.append("Ventas")
    if data_sources.get("bitrix"):
        active_sources.append("Bitrix")
    if data_sources.get("datacar"):
        active_sources.append("Datacar")

    summary += f"""
    ║  Fuentes activas : {", ".join(active_sources):<44s} ║
    ║  Personas creadas: {len(personas):<44d} ║
    ║  Archivos .md    : {len(generated_files):<44d} ║
    ║  Tiempo total    : {elapsed:.1f}s{" " * (44 - len(f"{elapsed:.1f}s"))} ║"""

    output_dir = Path(config["paths"].get("output_dir", "output/personas"))
    summary += f"""
    ║  Salida          : {str(output_dir):<44s} ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(summary)

    # Listar archivos generados
    print("\n  📂 Archivos generados:")
    for f in generated_files:
        print(f"     • {f}")

    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generador de Buyer Persona desde Google Ads, Meta Ads y Ventas → Obsidian"
    )
    parser.add_argument(
        "--config", "-c",
        default="config/settings.yaml",
        help="Ruta al archivo de configuración YAML (default: config/settings.yaml)",
    )
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="Ejecuta en modo demo con datos de ejemplo (sin credenciales reales)",
    )
    parser.add_argument(
        "--from-json",
        default="",
        help="Regenera las notas desde un output/raw/data_sources_*.json guardado (no llama a las APIs)",
    )

    args = parser.parse_args()

    try:
        run_pipeline(config_path=args.config, demo=args.demo, from_json=args.from_json)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelado por el usuario.\n")
        sys.exit(130)
    except Exception as e:
        logger.error("Error fatal: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()