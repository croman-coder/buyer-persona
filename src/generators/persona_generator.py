"""
Generador de Buyer Persona.

Consolida los datos extraídos por los conectores (Google Ads, Meta Ads,
Histórico de Ventas) y los sintetiza en perfiles de Buyer Persona accionables.

Estrategia:
1. Cruza datos demográficos de las tres fuentes
2. Identifica patrones de comportamiento de compra
3. Detecta intereses predominantes
4. Construye narrativas de "dolores", "objetivos" y "motivaciones"
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime
from typing import Any

from src.catalog.models_py import category_for, detect_models_in_ads
from src.generators.ad_copy_analyzer import observed_interests, analyze_all_brands, analyze_brand

logger = logging.getLogger(__name__)


# Insights leídos a mano de los anuncios reales de Leapmotor y Renault
# (scripts/fetch_ad_creatives.py, 542 anuncios leídos el 2026-07-16).
# Se tratan como una curación de referencia con prioridad más alta que el
# análisis automático (ad_copy_analyzer), porque vienen de una lectura
# completa y humana del copy. El resto de las marcas usa el análisis
# automático (ver PersonaGenerator._dynamic_ad_insights) o, si tampoco hay
# anuncios suficientes, la heurística genérica.
AD_DERIVED_INSIGHTS: dict[str, dict[str, list[str]]] = {
    "leapmotor": {
        "pains": [
            "Ansiedad de autonomía: quiere confirmar los km reales antes de comprar un eléctrico",
            "Le preocupa dónde y cuánto cuesta cargar fuera de casa",
            "Compara la cuota mensual en guaraníes, no solo el precio de lista en USD",
        ],
        "goals": [
            "Reducir el gasto en combustible y mantenimiento a largo plazo",
            "Encontrar un eléctrico con autonomía suficiente para su rutina diaria",
        ],
        "motivations": [
            "Ahorro de combustible y mantenimiento a largo plazo",
            "Sentirse parte de la tecnología del futuro, no quedarse atrás",
            "Confianza en el respaldo y garantía de Santa Rosa en una categoría todavía nueva",
            "Trato cercano y personal con el vendedor, no una venta anónima",
        ],
    },
    "renault": {
        "pains": [
            "Necesita ubicar qué escalón de precio/equipamiento le corresponde (Kardian vs. Boreal vs. Koleos)",
            "Evalúa specs técnicos concretos (asistencias de manejo, seguridad, conectividad) antes de decidir",
            "En uso comercial (Master/Oroch) necesita justificar el vehículo como herramienta de trabajo, no solo transporte",
        ],
        "goals": [
            "Encontrar el modelo Renault que calce con su presupuesto y etapa (primera SUV, familiar, premium o comercial)",
            "Conseguir financiación propia con una cuota accesible",
        ],
        "motivations": [
            "Seguridad y tecnología verificable (visión 360°, asistencias a la conducción, Google integrado)",
            "Status y diseño en el segmento premium (Koleos)",
            "Rentabilidad y confiabilidad del vehículo como herramienta de trabajo (Master, Oroch)",
            "Aprovechar promociones y precio por tiempo limitado (Duster, Clio)",
        ],
    },
}


# Marcas que solo venden eléctricos: su comprador de marca sí tiene el miedo a
# quedarse sin batería. En las marcas mixtas (GWM, JAC) eso es de cada modelo.
MARCAS_ELECTRICAS = {"Zeekr", "Leapmotor", "JMEV", "XPeng"}
# El dolor y el objetivo que solo tienen sentido en un auto que se enchufa.
DOLOR_DE_CARGA = re.compile(r"ansiedad de autonom|cargar fuera de casa|el[eé]ctrico con autonom", re.I)


def es_electrico(segment: dict[str, Any]) -> bool:
    """¿La persona es de un modelo, marca o segmento 100 % eléctrico (según el catálogo)?"""
    tipo, nombre = segment.get("type"), segment.get("name", "")
    if tipo == "model":
        return category_for(nombre) == "Eléctrico"
    if tipo == "brand":
        return nombre in MARCAS_ELECTRICAS
    return nombre == "Eléctrico"


def sin_dolor_de_carga(segment: dict[str, Any], textos: list[str]) -> list[str]:
    """Saca la ansiedad de autonomía/carga de lo que no es 100 % eléctrico.

    El copy de un híbrido, de una pickup («capacidad de carga») o de un auto con
    «asientos eléctricos» la disparaba: el 03-10-2026 la tenían 10 fichas que no
    se enchufan (Duster, Poer, Sunray…).
    """
    return list(textos) if es_electrico(segment) else [t for t in textos if not DOLOR_DE_CARGA.search(t)]


class PersonaGenerator:
    """Sintetiza datos de múltiples fuentes en Buyer Personas estructuradas."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.num_personas = int(config.get("num_personas", 3))
        self.name_prefix = config.get("name_prefix", "Persona")
        # Desglose a nivel modelo (además de marca y tipo de vehículo)
        models_cfg = config.get("models", {}) or {}
        self.models_enabled = bool(models_cfg.get("enabled", True))
        # Un modelo necesita un mínimo de anuncios reales para tener persona
        # propia: con 1-2 anuncios no hay evidencia suficiente del mensaje.
        self.model_min_ads = int(models_cfg.get("min_ads", 5))
        self.model_min_orders = int(models_cfg.get("min_orders", 10))
        # Tope de personas de modelo. 0 = sin tope (default desde el 2026-09-22):
        # con 60 fijos, qué modelos entraban dependía del orden en que llegaban
        # los anuncios, así que Arkana, Boreal, Clio o Kangoo aparecían un día y
        # desaparecían al siguiente, y sus notas viejas quedaban en el vault.
        self.model_max_personas = int(models_cfg.get("max_personas", 0) or 0)
        self._ads_by_brand: dict[str, list[dict]] = {}
        self._dynamic_ad_insights: dict[str, dict[str, list[str]]] = {}
        self._model_ad_insights: dict[str, dict[str, list[str]]] = {}
        self._placement_by_brand: dict[str, dict[str, Any]] = {}
        self._meta_demo_by_brand: dict[str, dict[str, Any]] = {}
        self._meta_demo_by_model: dict[str, dict[str, Any]] = {}
        self._device_by_brand: dict[str, dict[str, Any]] = {}
        self._audience_mix_by_brand: dict[str, dict[str, Any]] = {}
        self._spend_by_brand: dict[str, dict[str, Any]] = {}
        self._periods: dict[str, Any] = {}
        self._leads_by_brand: dict[str, dict[str, Any]] = {}
        self._crm_by_brand: dict[str, dict[str, Any]] = {}
        self._competitors_by_model: dict[str, dict[str, Any]] = {}
        self._extras: dict[str, Any] = {}
        self.audiences: list[dict[str, Any]] = []

    def generate(self, data_sources: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Genera Buyer Personas a partir de los datos consolidados.

        Args:
            data_sources: Dict con claves ``google_ads``, ``meta_ads``, ``sales``.

        Returns:
            Lista de diccionarios, cada uno representando una Buyer Persona.
        """
        logger.info("Generando hasta %d Buyer Personas...", self.num_personas)

        sales_data = data_sources.get("sales", {})
        google_data = data_sources.get("google_ads", {})
        meta_data = data_sources.get("meta_ads", {})

        # Aprendizaje automático: re-leer el copy real de los anuncios vigentes
        # y derivar pains/goals/motivations por marca en cada corrida. No
        # requiere curación manual — si mañana cambia la campaña, cambia esto.
        ad_creatives = meta_data.get("ad_creatives", [])
        self._dynamic_ad_insights = analyze_all_brands(ad_creatives)
        if self._dynamic_ad_insights:
            logger.info(
                "Análisis automático de copy: %d marca(s) con insights derivados (%s)",
                len(self._dynamic_ad_insights),
                ", ".join(self._dynamic_ad_insights.keys()),
            )

        # Anuncios agrupados por marca (base del desglose por modelo)
        self._ads_by_brand = {}
        for ad in ad_creatives:
            brand = ad.get("account", "")
            if brand:
                self._ads_by_brand.setdefault(brand, []).append(ad)

        # Insights de copy específicos por modelo (solo anuncios que lo nombran)
        self._model_ad_insights = self._analyze_model_ads()
        if self._model_ad_insights:
            logger.info(
                "Análisis de copy por modelo: %d modelo(s) con anuncios propios",
                len(self._model_ad_insights),
            )

        # Edad/género reales de Meta por marca (el ERP no trae demografía)
        self._meta_demo_by_brand = self._summarize_meta_demographics(
            meta_data.get("demographics", {}).get("age_gender", [])
        )
        # ...y por MODELO: el desglose a nivel anuncio se atribuye al modelo
        # que nombra cada anuncio (copy + nombre), así L200 y Montero no
        # heredan el mismo perfil de "Mitsubishi".
        self._meta_demo_by_model = self._summarize_meta_demographics(
            self._attribute_rows_to_models(
                meta_data.get("demographics", {}).get("age_gender_ad", []), ad_creatives
            )
        )
        if self._meta_demo_by_model:
            logger.info(
                "Demografía Meta por modelo: %d modelo(s) con audiencia propia",
                len(self._meta_demo_by_model),
            )

        # iPhone vs Android por marca (proxy de NSE; PY promedio ~20% iOS)
        self._device_by_brand = self._summarize_devices(meta_data.get("demographics", {}).get("device", []))

        # Temperatura de los públicos que se pautan hoy (frío vs retargeting/lookalike)
        self._audience_mix_by_brand = self._summarize_audience_mix(meta_data.get("adset_targeting", []))

        # Gasto real por marca (90 días) para sugerir presupuesto por modelo
        self._spend_by_brand = self._summarize_spend(meta_data.get("campaigns", []), meta_data.get("leads_by_brand", {}))

        # Ventanas de tiempo de cada fuente (para que la nota diga qué período lee)
        self._periods = {
            "meta": meta_data.get("date_range", {}),
            "sales": data_sources.get("sales", {}).get("summary", {}).get("date_range", {}),
            "bitrix": {"days_back": data_sources.get("bitrix", {}).get("days_back")},
        }

        # Formato de creatividad real por marca (dónde cae hoy el gasto/impresiones)
        self._placement_by_brand = self._summarize_placements(meta_data.get("placements", []))

        # Leads reales agregados por marca (sin PII, ya vienen agregados del conector)
        self._leads_by_brand = meta_data.get("leads_by_brand", {})

        # Custom audiences existentes (para exportar como nota de referencia)
        self.audiences = meta_data.get("audiences", [])

        # Embudo CRM (Bitrix) agregado por marca: lead -> convertido -> deal ganado
        self._crm_by_brand = data_sources.get("bitrix", {}).get("by_brand", {})

        # Precios de lista y competencia directa por modelo (Datacar, uso interno)
        self._competitors_by_model = data_sources.get("datacar", {}).get("analysis", {}).get("by_model", {})

        # Stock, acciones comerciales, objetivos y negociación (Excel del negocio)
        self._extras = data_sources.get("extras", {}) or {}

        # Consolidar insights globales
        consolidated = self._consolidate(sales_data, google_data, meta_data)

        personas: list[dict[str, Any]] = []

        # Estrategia de segmentación
        # Si hay datos de ventas con productos, segmentar por categoría de producto
        # Si no, segmentar por canal o por datos demográficos de ads
        segments = self._segment(consolidated)

        for idx, segment in enumerate(segments[: self.num_personas], start=1):
            persona = self._build_persona(idx, segment, consolidated)
            personas.append(persona)

        # Si hay menos segmentos que num_personas, crear personas genéricas
        while len(personas) < self.num_personas:
            idx = len(personas) + 1
            persona = self._build_persona(idx, segment={}, consolidated=consolidated)
            personas.append(persona)

        # Desglose adicional a nivel modelo (no compite con el cupo de
        # num_personas: se agregan después de marcas y tipos de vehículo).
        model_segments = self._segment_models(consolidated)
        if model_segments:
            logger.info(
                "Desglose por modelo: %d modelo(s) reales de Paraguay (mín. %d anuncios)",
                len(model_segments),
                self.model_min_ads,
            )
        # Los nombres de nota ya no llevan número (son estables por marca/
        # modelo), así que el índice solo sirve para el id interno.
        for offset, segment in enumerate(model_segments, start=1):
            personas.append(self._build_persona(len(personas) + 1, segment, consolidated))

        return personas

    def _analyze_model_ads(self) -> dict[str, dict[str, list[str]]]:
        """
        Corre el análisis de copy sobre los anuncios de cada modelo por
        separado, para que la persona del modelo refleje el mensaje puntual
        de ese modelo y no el promedio de la marca.
        """
        insights: dict[str, dict[str, list[str]]] = {}
        for brand, brand_ads in self._ads_by_brand.items():
            for model, ads in detect_models_in_ads(brand_ads, brand).items():
                result = analyze_brand(ads)
                if result:
                    insights[model] = result
        return insights

    def _segment_models(self, consolidated: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Crea un segmento por modelo realmente disponible en Paraguay.

        La fuente de verdad es el catálogo validado contra los anuncios
        reales de Meta (``src/catalog/models_py.py``): un modelo genera
        persona solo si se está pautando de verdad. Si además aparece en el
        histórico de ventas, se le suman los stats de venta reales.
        """
        if not self.models_enabled:
            return []

        by_model_sales = consolidated["purchase"].get("by_model", {})
        segments: list[dict[str, Any]] = []
        seen: set[str] = set()

        # 1) Modelos con pauta real (catálogo x anuncios)
        logger.info("Cuentas con anuncios: %s", {b: len(a) for b, a in self._ads_by_brand.items()})
        for brand, brand_ads in self._ads_by_brand.items():
            detectados = detect_models_in_ads(brand_ads, brand)
            logger.info("Modelos detectados en anuncios de %s: %s", brand, {m: len(a) for m, a in detectados.items()} or "ninguno")
            for model, ads in detect_models_in_ads(brand_ads, brand).items():
                sales_stats = self._match_sales_stats(model, by_model_sales)
                orders = (sales_stats or {}).get("orders", 0)
                if len(ads) < self.model_min_ads and orders < self.model_min_orders:
                    logger.info("Modelo sin persona: %s (%d anuncios < %d y %d ventas < %d)",
                                model, len(ads), self.model_min_ads, orders, self.model_min_orders)
                    continue
                seen.add(model)
                segments.append({
                    "type": "model",
                    "name": model,
                    "brand": brand,
                    "category": category_for(model),
                    "ad_count": len(ads),
                    "active_ads": sum(1 for a in ads if a.get("status") == "ACTIVE"),
                    "revenue": (sales_stats or {}).get("revenue", 0),
                    "orders": orders,
                    "orders_last_90d": (sales_stats or {}).get("orders_last_90d", 0),
                    "orders_last_365d": (sales_stats or {}).get("orders_last_365d", 0),
                    "stats": sales_stats or {},
                })

        # 2) Modelos que se venden pero no tienen pauta (o no matchearon en anuncios)
        for model, stats in by_model_sales.items():
            if model in seen or stats.get("orders", 0) < self.model_min_orders:
                continue
            brand = stats.get("brand", "")
            if not brand:
                continue
            segments.append({
                "type": "model",
                "name": model,
                "brand": brand,
                "category": stats.get("category") or category_for(model),
                "ad_count": 0,
                "active_ads": 0,
                "revenue": stats.get("revenue", 0),
                "orders": stats.get("orders", 0),
                "orders_last_90d": stats.get("orders_last_90d", 0),
                "orders_last_365d": stats.get("orders_last_365d", 0),
                "stats": stats,
            })

        # 3) Brecha pauta/venta dentro de cada marca: share de anuncios vs share de
        #    unidades de los ÚLTIMOS 12 MESES (la base arranca en 2018: el histórico
        #    completo sobre-representaría modelos que ya no se venden).
        def _recent(seg: dict[str, Any]) -> int:
            return seg.get("orders_last_365d") or 0
        use_recent = any(_recent(s) for s in segments)
        by_brand_tot: dict[str, dict[str, int]] = {}
        for seg in segments:
            t = by_brand_tot.setdefault(seg["brand"], {"ads": 0, "orders": 0})
            t["ads"] += seg["ad_count"]
            t["orders"] += _recent(seg) if use_recent else seg["orders"]
        for seg in segments:
            t = by_brand_tot[seg["brand"]]
            ad_share = seg["ad_count"] / t["ads"] * 100 if t["ads"] else 0.0
            own = _recent(seg) if use_recent else seg["orders"]
            sales_share = own / t["orders"] * 100 if t["orders"] else 0.0
            seg["gap_window"] = "12 meses" if use_recent else "histórico"
            seg["ad_share"] = round(ad_share, 1)
            seg["sales_share"] = round(sales_share, 1)
            if t["orders"] and t["ads"]:
                if sales_share >= 5 and ad_share < sales_share / 2:
                    seg["gap"] = "sub-pautado"      # vende mucho, poca pauta → escalar
                elif ad_share >= 5 and sales_share < ad_share / 2:
                    seg["gap"] = "sobre-pautado"    # mucha pauta, poca venta → revisar
                else:
                    seg["gap"] = "equilibrado"
            else:
                seg["gap"] = "sin datos"

        # Hasta qué fecha llega el ERP (para leer bien la brecha: un modelo
        # lanzado después de esa fecha tiene pauta pero todavía 0 ventas)
        sales_until = consolidated["purchase"].get("summary", {}).get("date_range", {}).get("end", "")
        for seg in segments:
            seg["sales_until"] = sales_until
            if seg["gap"] == "sobre-pautado" and (seg.get("orders_last_365d") or seg["orders"]) == 0 and seg["orders"] == 0:
                seg["gap"] = "lanzamiento"  # pauta sin ventas en el ERP: probable modelo nuevo

        # Orden: unidades vendidas primero, pauta como desempate
        segments.sort(key=lambda s: (s.get("orders_last_365d") or 0, s["orders"], s["ad_count"]), reverse=True)
        # Orden estable y con sentido: primero lo que más vende en 12 meses,
        # después lo que más se pauta. Así, si algún día hay tope, corta por
        # relevancia y no por azar.
        segments.sort(key=lambda s: (s.get("orders_last_365d") or 0, s.get("ad_count") or 0, s.get("orders") or 0), reverse=True)
        if self.model_max_personas:
            return segments[: self.model_max_personas]
        return segments

    @staticmethod
    def _match_sales_stats(
        model: str, by_model_sales: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Busca el modelo en los stats de ventas.

        Match tolerante: el histórico puede nombrar al modelo distinto que
        el catálogo (ej. 'Kardian' vs 'Renault Kardian').
        """
        if not by_model_sales:
            return None
        if model in by_model_sales:
            return by_model_sales[model]

        model_norm = model.lower().strip()
        for sales_name, stats in by_model_sales.items():
            s = str(sales_name).lower().strip()
            if s == model_norm or s in model_norm or model_norm in s:
                return stats
        return None

    @staticmethod
    def _summarize_meta_demographics(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """
        Edad y género dominantes por marca a partir del desglose age+gender
        de Meta, ponderado por clics (quien interactúa, no solo quien ve).
        """
        gender_label = {"male": "Masculino", "female": "Femenino"}
        by_brand: dict[str, dict[str, Counter]] = {}
        for row in rows:
            brand = row.get("account", "")
            if not brand:
                continue
            weight = int(row.get("clicks", 0) or 0) or int(row.get("impressions", 0) or 0)
            if not weight:
                continue
            d = by_brand.setdefault(brand, {"age": Counter(), "gender": Counter()})
            if row.get("age") and str(row["age"]).lower() != "unknown":
                d["age"][str(row["age"])] += weight
            g = gender_label.get(str(row.get("gender", "")).lower())
            if g:
                d["gender"][g] += weight

        out: dict[str, dict[str, Any]] = {}
        for brand, d in by_brand.items():
            if not d["age"]:
                continue
            total_age = sum(d["age"].values())
            top_age, top_w = d["age"].most_common(1)[0]
            top_gender = d["gender"].most_common(1)[0][0] if d["gender"] else "mixto"
            gender_share = (
                round(d["gender"][top_gender] / sum(d["gender"].values()) * 100, 1)
                if d["gender"] else 0
            )
            out[brand] = {
                "age_range": top_age,
                "age_share": round(top_w / total_age * 100, 1),
                "age_distribution": {k: round(v / total_age * 100, 1) for k, v in d["age"].most_common()},
                "gender": top_gender,
                "gender_share": gender_share,
                "weight": int(total_age),   # clics (o impresiones) que sostienen el perfil
                "source": "meta",
            }
        return out

    @staticmethod
    def _attribute_rows_to_models(
        rows: list[dict[str, Any]], ad_creatives: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Reetiqueta cada fila de insights a nivel anuncio con el/los modelo(s)
        que ese anuncio nombra (según el catálogo real de PY), poniendo el
        modelo en ``account`` para reutilizar ``_summarize_meta_demographics``.
        Un anuncio multi-modelo (carrusel) cuenta para todos los que nombra.
        """
        creative_by_id = {
            str(ad.get("ad_id")): ad for ad in ad_creatives if ad.get("ad_id")
        }
        out: list[dict[str, Any]] = []
        cache: dict[tuple[str, str], list[str]] = {}
        for row in rows:
            brand = row.get("account", "")
            ad_id = str(row.get("ad_id", ""))
            if not brand:
                continue
            key = (brand, ad_id)
            if key not in cache:
                ad = creative_by_id.get(ad_id) or {"ad_name": row.get("ad_name", "")}
                cache[key] = list(detect_models_in_ads([ad], brand).keys())
            for model in cache[key]:
                out.append({**row, "account": model})
        return out

    @staticmethod
    def _summarize_devices(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        by: dict[str, Counter] = {}
        for r in rows:
            b = r.get("account", "")
            if b:
                by.setdefault(b, Counter())[str(r.get("impression_device", ""))] += int(r.get("clicks", 0) or 0)
        out = {}
        for b, c in by.items():
            tot = sum(c.values()) or 1
            ios = sum(v for k, v in c.items() if k.startswith(("iphone", "ipad", "ipod")))
            desk = sum(v for k, v in c.items() if "desktop" in k)
            out[b] = {"ios_pct": round(ios / tot * 100, 1), "desktop_pct": round(desk / tot * 100, 1), "clicks": tot}
        return out

    @staticmethod
    def _summarize_audience_mix(adset_targeting: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """
        Por marca: cuántos adsets activos apuntan a público frío (intereses /
        Advantage+ sin base propia) vs caliente (custom audience, lookalike).
        Sirve para responder "¿estamos tirando todo a público frío?".
        """
        by_brand: dict[str, dict[str, Any]] = {}
        for row in adset_targeting:
            brand = row.get("account", "")
            if not brand:
                continue
            d = by_brand.setdefault(brand, {"adsets": 0, "frio": 0, "caliente": 0, "lookalike": 0, "advantage": 0, "custom_audiences": Counter()})
            d["adsets"] += 1
            d[row.get("audience_type", "frio")] += 1
            if row.get("lookalike"):
                d["lookalike"] += 1
            if row.get("advantage_audience"):
                d["advantage"] += 1
            for name in row.get("custom_audiences", []) or []:
                if name:
                    d["custom_audiences"][name] += 1
        out: dict[str, dict[str, Any]] = {}
        for brand, d in by_brand.items():
            n = d["adsets"] or 1
            out[brand] = {
                "adsets": d["adsets"],
                "frio": d["frio"],
                "caliente": d["caliente"],
                "lookalike": d["lookalike"],
                "advantage": d["advantage"],
                "frio_pct": round(d["frio"] / n * 100, 1),
                "custom_audiences": [k for k, _ in d["custom_audiences"].most_common(5)],
            }
        return out

    @staticmethod
    def _summarize_spend(campaigns: list[dict[str, Any]], leads_by_brand: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Gasto real (USD, ventana Meta) y CPL por marca a partir de las campañas."""
        spend: Counter = Counter()
        convos: Counter = Counter()   # conversaciones de WhatsApp/Messenger iniciadas (Renew pautea click-to-WhatsApp)
        for c in campaigns:
            brand = c.get("account", "")
            if brand:
                try:
                    spend[brand] += float(c.get("spend", 0) or 0)
                except (TypeError, ValueError):
                    pass
                for a in c.get("actions", []) or []:
                    if a.get("action_type") == "onsite_conversion.messaging_conversation_started_7d":
                        convos[brand] += float(a.get("value", 0) or 0)
        out: dict[str, dict[str, Any]] = {}
        for brand, total in spend.items():
            leads = int((leads_by_brand.get(brand) or {}).get("total_leads", 0) or 0)
            conv = int(convos.get(brand, 0))
            # Si la marca genera mucho más conversaciones que formularios, su
            # "lead" es la conversación (costo por conversación), como en el
            # informe Radiografía del dashboard.
            basis = "conversacion" if conv > leads * 3 else "formulario"
            n = conv if basis == "conversacion" else leads
            out[brand] = {
                "spend_90d": round(total, 2),
                "spend_month": round(total / 3, 2),
                "leads_90d": n,
                "form_leads_90d": leads,
                "conversations_90d": conv,
                "lead_basis": basis,
                "cpl": round(total / n, 2) if n else None,
            }
        return out

    @staticmethod
    def _summarize_placements(placements: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """
        Agrupa impresiones por marca en 3 baldes (Reels/Stories, Feed, Otros)
        y devuelve el formato dominante — para recomendar dónde poner el
        esfuerzo creativo de remarketing.
        """
        by_brand: dict[str, Counter] = {}
        for row in placements:
            brand = row.get("account", "")
            if not brand:
                continue
            position = str(row.get("platform_position", "")).lower()
            impressions = int(row.get("impressions", 0) or 0)
            if not impressions:
                continue

            if "reel" in position or "stor" in position:
                bucket = "Reels/Stories (video vertical corto)"
            elif "feed" in position:
                bucket = "Feed (imagen/carrusel estático)"
            else:
                bucket = "Otros (marketplace, search, audience network...)"

            by_brand.setdefault(brand, Counter())[bucket] += impressions

        summary: dict[str, dict[str, Any]] = {}
        for brand, counter in by_brand.items():
            total = sum(counter.values())
            if not total:
                continue
            top_bucket, top_impressions = counter.most_common(1)[0]
            summary[brand] = {
                "top_format": top_bucket,
                "top_format_share": round(top_impressions / total * 100, 1),
                "breakdown": dict(counter),
            }
        return summary

    # ------------------------------------------------------------------
    # Consolidación
    # ------------------------------------------------------------------

    def _consolidate(
        self,
        sales: dict[str, Any],
        google: dict[str, Any],
        meta: dict[str, Any],
    ) -> dict[str, Any]:
        """Consolida los datos de todas las fuentes en un único perfil."""

        # --- Demografía ---
        demo = {"age_ranges": [], "genders": [], "age_stats": {}, "locations": []}

        # Google Ads - demografía
        g_demo = google.get("demographics", {})
        if g_demo.get("age"):
            demo["age_ranges"] = g_demo["age"]
        if g_demo.get("gender"):
            demo["genders"] = g_demo["gender"]

        # Meta Ads - demografía
        m_demo = meta.get("demographics", {})
        if m_demo.get("age_gender"):
            demo["meta_age_gender"] = m_demo["age_gender"]
        if m_demo.get("country"):
            demo["meta_countries"] = m_demo["country"]
        if m_demo.get("region"):
            demo["meta_regions"] = m_demo["region"]

        # Google Ads - ubicaciones
        if google.get("locations"):
            demo["locations"] = google["locations"]

        # Sales - demografía
        s_demo = sales.get("demographics", {})
        if s_demo.get("age"):
            demo["age_stats"] = s_demo["age"]
        if s_demo.get("gender"):
            demo["sales_gender"] = s_demo["gender"]

        # --- Intereses ---
        interests: list[dict] = []
        if google.get("interests"):
            interests.extend(google["interests"])
        if meta.get("interests"):
            interests.extend(meta["interests"])

        # --- Comportamiento de compra ---
        purchase = {
            "top_products": sales.get("top_products", []),
            "top_brands": sales.get("top_brands", []),
            "top_categories": sales.get("top_categories", []),
            "channels": sales.get("channels", []),
            "cities": sales.get("cities", []),
            "summary": sales.get("summary", {}),
            "by_brand": sales.get("by_brand", {}),
            "by_category": sales.get("by_category", {}),
            "by_model": sales.get("by_model", {}),
        }

        # --- Rendimiento de campañas ---
        campaigns = {
            "google": google.get("campaigns", []),
            "meta": meta.get("campaigns", []),
        }

        return {
            "demographics": demo,
            "interests": interests,
            "purchase": purchase,
            "campaigns": campaigns,
            "date_range": {
                "google": google.get("date_range", {}),
                "meta": meta.get("date_range", {}),
                "sales": sales.get("summary", {}).get("date_range", {}),
            },
            "sources": [k for k, v in data_sources_check(sales, google, meta) if v]
                       + (["bitrix"] if self._crm_by_brand else [])
                       + (["datacar"] if self._competitors_by_model else []),
        }

    # ------------------------------------------------------------------
    # Segmentación
    # ------------------------------------------------------------------

    def _segment(self, consolidated: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Segmenta los datos consolidados en grupos para crear personas.

        Estrategia: prioriza categorías de producto (si hay), luego canales,
        luego grupos demográficos.
        """
        segments: list[dict[str, Any]] = []

        # Segmentar por marca (una persona por marca, con stats propios)
        by_brand = consolidated["purchase"].get("by_brand", {})
        for name, stats in sorted(
            by_brand.items(), key=lambda x: x[1].get("revenue", 0), reverse=True
        )[: self.num_personas]:
            segments.append({
                "type": "brand",
                "name": name,
                "revenue": stats.get("revenue", 0),
                "orders": stats.get("orders", 0),
                "stats": stats,
            })

        # Segmentar por categoría/tipo de producto (con stats propios)
        by_category = consolidated["purchase"].get("by_category", {})
        for name, stats in sorted(
            by_category.items(), key=lambda x: x[1].get("revenue", 0), reverse=True
        ):
            if len(segments) >= self.num_personas:
                break
            segments.append({
                "type": "product_category",
                "name": name,
                "revenue": stats.get("revenue", 0),
                "orders": stats.get("orders", 0),
                "stats": stats,
            })

        # Compatibilidad: si no hay stats por marca/categoría, usar top_categories
        if not segments:
            categories = consolidated["purchase"].get("top_categories", [])
            for cat in categories[: self.num_personas]:
                segments.append({
                    "type": "product_category",
                    "name": cat.get("category", ""),
                    "revenue": cat.get("revenue", 0),
                    "orders": cat.get("orders", 0),
                })

        # Si no hay suficientes segmentos, usar canales
        if len(segments) < self.num_personas:
            channels = consolidated["purchase"].get("channels", [])
            existing = {s["name"] for s in segments}
            for ch in channels[: self.num_personas - len(segments)]:
                ch_name = ch.get("channel", "")
                if ch_name and ch_name not in existing:
                    segments.append({
                        "type": "channel",
                        "name": ch_name,
                        "revenue": ch.get("revenue", 0),
                        "orders": ch.get("orders", 0),
                    })

        # Si todavía no hay suficientes, usar intereses principales
        if len(segments) < self.num_personas:
            interests = consolidated.get("interests", [])
            interest_names = [i.get("name", "") for i in interests if i.get("name")]
            top_interests = Counter(interest_names).most_common(self.num_personas - len(segments))
            for name, count in top_interests:
                segments.append({
                    "type": "interest",
                    "name": name,
                    "count": count,
                })

        return segments

    # ------------------------------------------------------------------
    # Construcción de Persona
    # ------------------------------------------------------------------

    def _build_persona(
        self,
        idx: int,
        segment: dict[str, Any],
        consolidated: dict[str, Any],
    ) -> dict[str, Any]:
        """Construye una persona individual a partir de un segmento."""

        # Datos demográficos consolidados
        demo = consolidated["demographics"]

        # Stats propios del segmento (marca/categoría); si no hay, usar globales
        seg_stats = segment.get("stats") or {}
        # Un modelo sin ventas propias hereda el perfil de compra de su marca
        if not seg_stats and segment.get("type") == "model":
            seg_stats = consolidated["purchase"].get("by_brand", {}).get(
                segment.get("brand", ""), {}
            )
        seg_age = seg_stats.get("age", {})

        # Demografía real de Meta: primero la del MODELO (anuncios que lo
        # nombran, mínimo de clics para que sea estadísticamente útil) y, si
        # no alcanza, la de su marca (se deja constancia del nivel usado).
        demo_brand = segment.get("brand") if segment.get("type") == "model" else segment.get("name", "")
        meta_demo = self._meta_demo_by_brand.get(demo_brand or "", {})
        meta_level = "marca" if meta_demo else ""
        if segment.get("type") == "model":
            model_demo = self._meta_demo_by_model.get(segment.get("name", ""), {})
            if model_demo and model_demo.get("weight", 0) >= self.MODEL_DEMO_MIN_CLICKS:
                meta_demo = model_demo
                meta_level = "modelo"
            elif model_demo:
                meta_demo = {**meta_demo, "model_sample": model_demo}
        demo_source = "ventas"

        # --- Edad predominante ---
        if seg_age.get("range"):
            age_range = seg_age["range"]
            age_stats = seg_age
        elif meta_demo.get("age_range"):
            age_range = meta_demo["age_range"]
            age_stats = {}
            demo_source = "meta"
        else:
            age_range = self._top_age_range(demo)
            age_stats = demo.get("age_stats", {})

        # --- Género predominante ---
        if seg_stats.get("gender"):
            gender = max(seg_stats["gender"].items(), key=lambda x: x[1])[0]
        elif meta_demo.get("gender"):
            gender = meta_demo["gender"]
            demo_source = "meta"
        else:
            gender = self._top_gender(demo)

        # --- Ubicación ---
        location = seg_stats.get("cities") or self._top_location(demo, consolidated["purchase"])

        # --- Intereses top ---
        top_interests = self._top_interests(consolidated["interests"], limit=10)

        # --- Productos y categorías ---
        purchase = consolidated["purchase"]

        # --- Dolores y objetivos (heurística) ---
        pains = self._infer_pains(segment, consolidated)
        goals = self._infer_goals(segment, consolidated)
        motivations = self._infer_motivations(top_interests, segment)
        pains, goals = sin_dolor_de_carga(segment, pains), sin_dolor_de_carga(segment, goals)

        # Productos/canales del segmento; si no hay, usar globales
        top_products = seg_stats.get("top_products") or [
            p.get("product", "") for p in purchase.get("top_products", [])[:5]
        ]
        if segment.get("type") == "model":
            # Solo canales del propio modelo: el global del portfolio no dice nada de él.
            preferred_channels = list(seg_stats.get("channels") or [])
        else:
            preferred_channels = seg_stats.get("channels") or [
                c.get("channel", "") for c in purchase.get("channels", [])[:3]
            ]
        avg_order_value = seg_stats.get("avg_order_value") or purchase.get(
            "summary", {}
        ).get("avg_order_value", 0)
        total_revenue = seg_stats.get("revenue") or purchase.get(
            "summary", {}
        ).get("total_revenue", 0)

        seg_name = segment.get("name", "")
        # Meta entrega demografía/placement/leads a nivel cuenta (= marca).
        # Una persona de modelo hereda esos datos de su marca.
        lookup_name = segment.get("brand", "") if segment.get("type") == "model" else seg_name

        # En una persona de modelo, el "producto" es el modelo mismo
        if segment.get("type") == "model":
            top_products = [seg_name]

        persona = {
            "id": f"{self.name_prefix}-{idx:02d}",
            "name": self._generate_name(idx, gender, segment),
            "segment": {k: v for k, v in segment.items() if k != "stats"},
            "demographics": {
                "age_range": age_range,
                "age_mean": age_stats.get("mean"),
                "age_median": age_stats.get("median"),
                "gender": gender,
                "location": location,
                "source": demo_source,
                "meta": meta_demo or None,
                "meta_level": meta_level if demo_source == "meta" else "",
            },
            "interests": top_interests,
            "top_products": top_products,
            "top_brands": [b.get("brand", "") for b in purchase.get("top_brands", [])[:5]],
            # Un modelo es de UNA categoría; las globales del portfolio se quedan en las personas de marca/segmento.
            "top_categories": (
                [segment["category"]] if segment.get("type") == "model" and segment.get("category")
                else [] if segment.get("type") == "model"
                else [c.get("category", "") for c in purchase.get("top_categories", [])[:5]]
            ),
            "preferred_channels": preferred_channels,
            "pains": pains,
            "goals": goals,
            "motivations": motivations,
            "spending": {
                "avg_order_value": avg_order_value,
                "total_revenue": total_revenue,
            },
            "creative_format": self._placement_by_brand.get(lookup_name),
            "audience_mix": self._audience_mix_by_brand.get(lookup_name),
            "nse": self._estimate_nse(segment, seg_stats, lookup_name, location),
            "observed_interests": self._observed_interests_for(segment, lookup_name),
            "budget": self._suggest_budget(segment, lookup_name),
            "periods": self._periods,
            "real_leads": self._leads_del_modelo(self._leads_by_brand.get(lookup_name), segment, lookup_name),
            "insight_basis": self._insight_basis(segment),
            "crm": self._crm_by_brand.get(lookup_name),
            "competitors": self._competitors_by_model.get(seg_name) if segment.get("type") == "model" else None,
            "extras": self._extras_for(segment, lookup_name),
            "erp": {
                k: seg_stats[k]
                for k in ("top_versions", "tradein_brands", "tradein_rate", "branches", "top_sellers", "price", "orders_last_90d")
                if k in seg_stats
            } or None,
            "data_sources": consolidated.get("sources", []),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }

        return persona

    # ------------------------------------------------------------------
    # Métodos auxiliares de análisis
    # ------------------------------------------------------------------

    MODEL_DEMO_MIN_CLICKS = 100

    def _observed_interests_for(self, segment: dict[str, Any], brand: str) -> dict[str, Any] | None:
        """Intereses observados: temas de los anuncios que ve el público + modelos que pide en el formulario."""
        ads = self._ads_by_brand.get(brand, [])
        if segment.get("type") == "model":
            ads = detect_models_in_ads(ads, brand).get(segment.get("name", ""), []) or ads
        temas = observed_interests(ads)
        leads = self._leads_by_brand.get(brand) or {}
        pedidos = self._normalizar_pedidos(leads.get("model_interest") or {}, brand)
        out = {"temas": temas, "modelos_pedidos": dict(list(pedidos.items())[:5]), "base_anuncios": len(ads)}
        return out if (temas or pedidos) else None

    @staticmethod
    def _normalizar_pedidos(pedidos: dict[str, int], brand: str) -> dict[str, int]:
        """
        Une las variantes con que el formulario guarda el mismo modelo
        ("koleos_", "koleos", "renault_koleos" → "Koleos") y suma sus conteos.
        Antes se pisaban y el modelo más pedido aparecía con el conteo de la
        última variante. Devuelve ordenado de mayor a menor.
        """
        import re as _re
        marca = (brand or "").strip().lower()
        suma: dict[str, int] = {}
        for k, v in (pedidos or {}).items():
            if not k or str(k).lower().startswith(("más", "mas", "no_", "otro", "otra")):
                continue
            s = _re.sub(r"[_\-]+", " ", str(k)).strip().lower()
            if marca and s.startswith(marca + " "):
                s = s[len(marca) + 1:]
            s = _re.sub(r"\s+", " ", s).strip()
            if not s:
                continue
            suma[s.title()] = suma.get(s.title(), 0) + int(v or 0)
        return dict(sorted(suma.items(), key=lambda kv: kv[1], reverse=True))

    @staticmethod
    def _pedido_es_del_modelo(pedido: str, modelo: str) -> bool:
        """
        ¿La respuesta del formulario se refiere a este modelo? Se comparan sin
        espacios ni signos, en los dos sentidos: la gente escribe "Montero"
        (modelo "Montero Sport"), "Js 4" (JS4) o "E30 X Eléctrico" (E30X).
        Antes solo se buscaba el modelo dentro de la respuesta y esos tres
        daban 0 pedidos. El sentido inverso exige al menos 4 caracteres para
        que una respuesta corta no se lleve modelos ajenos.
        """
        import re as _re
        a = _re.sub(r"[^a-z0-9]", "", str(pedido).lower())
        b = _re.sub(r"[^a-z0-9]", "", str(modelo).lower())
        if not a or not b:
            return False
        # También sufijo de 3+ caracteres: "Js 1" es el E-JS1 ("ejs1" termina en "js1").
        return b in a or (len(a) >= 4 and a in b) or (len(a) >= 3 and b.endswith(a))

    def _leads_del_modelo(self, real_leads: dict[str, Any] | None, segment: dict[str, Any], brand: str) -> dict[str, Any] | None:
        """
        Para una persona de modelo: cuántos de los leads del formulario de la
        marca pidieron ESTE modelo. Los formularios de Meta son por cuenta
        (= marca), así que sin esto la nota de un modelo mostraba los pedidos
        de toda la marca como si fueran suyos.
        """
        if not real_leads:
            return real_leads
        norm = self._normalizar_pedidos(real_leads.get("model_interest") or {}, brand)
        if segment.get("type") != "model":
            return dict(real_leads, model_interest_norm=norm)
        total = int(real_leads.get("total_leads") or 0)
        nombre = str(segment.get("name", "")).strip().lower()
        corto = nombre[len(brand) + 1:] if brand and nombre.startswith(brand.lower() + " ") else nombre
        propios = sum(v for k, v in norm.items() if self._pedido_es_del_modelo(k, corto))
        out = dict(real_leads)
        out["model_interest_norm"] = norm
        out["this_model"] = {"count": propios, "pct": round(propios / total * 100, 1) if total else 0.0}
        return out

    def _estimate_nse(self, segment: dict[str, Any], seg_stats: dict[str, Any], brand: str, location: list[str]) -> dict[str, Any] | None:
        """
        Nivel socioeconómico ESTIMADO (Meta no lo da en PY). Señales: precio
        del vehículo, financiación vs contado en los formularios, iPhone vs
        Android en los clics y ciudad. Se muestra la base del cálculo.
        """
        senales: list[str] = []
        score = 0.0; n = 0
        price = (seg_stats.get("price") or {}).get("avg")
        if price:
            n += 1
            if price >= 45000: score += 3; senales.append(f"ticket promedio USD {price:,.0f} (gama alta)")
            elif price >= 28000: score += 2; senales.append(f"ticket promedio USD {price:,.0f} (gama media-alta)")
            elif price >= 16000: score += 1; senales.append(f"ticket promedio USD {price:,.0f} (gama media)")
            else: senales.append(f"ticket promedio USD {price:,.0f} (entrada)")
        leads = self._leads_by_brand.get(brand) or {}
        pm = leads.get("payment_method") or {}
        if pm:
            tot = sum(pm.values()) or 1
            fin = sum(v for k, v in pm.items() if "financ" in k.lower() or "cuota" in k.lower())
            fin_pct = fin / tot * 100; n += 1
            if fin_pct < 40: score += 2
            elif fin_pct < 70: score += 1
            senales.append(f"{fin_pct:.0f}% pide financiación en el formulario ({tot} respuestas)")
        dev = self._device_by_brand.get(brand)
        if dev and dev.get("clicks", 0) > 500:
            n += 1
            if dev["ios_pct"] >= 30: score += 2
            elif dev["ios_pct"] >= 20: score += 1
            senales.append(f"{dev['ios_pct']}% de los clics desde iPhone (promedio del portfolio ~21%)")
        if location:
            senales.append("zona: " + ", ".join(location[:3]))
        if not n:
            return None
        avg = score / n
        nivel = "AB (alto)" if avg >= 2.3 else "C+ (medio-alto)" if avg >= 1.5 else "C (medio)" if avg >= 0.5 else "C- / D (medio-bajo)"
        return {"nivel": nivel, "senales": senales, "score": round(avg, 2)}

    def _extras_for(self, segment: dict[str, Any], brand: str) -> dict[str, Any] | None:
        """Stock / acciones / negociaciones del modelo + objetivos y negociación de su marca."""
        ex = self._extras
        if not ex:
            return None
        out: dict[str, Any] = {}
        name = segment.get("name", "")
        if segment.get("type") == "model":
            st = (ex.get("stock") or {}).get("by_model", {}).get(name)
            ac = (ex.get("acciones") or {}).get("by_model", {}).get(name)
            ng = (ex.get("negociacion") or {}).get("by_model", {}).get(name)
            if st:
                out["stock"] = st
            if ac:
                out["acciones"] = {**ac, "periodo": (ex.get("acciones") or {}).get("periodo", "")}
            if ng:
                out["negociaciones_modelo"] = ng
        ob = (ex.get("objetivos") or {}).get("by_brand", {}).get(brand)
        if ob:
            out["objetivos"] = {**ob, "month": (ex.get("objetivos") or {}).get("month"), "year": (ex.get("objetivos") or {}).get("year"),
                                "sales_until": (ex.get("objetivos") or {}).get("sales_until")}
        ng_b = (ex.get("negociacion") or {}).get("by_brand", {}).get(brand)
        if ng_b:
            out["negociacion_marca"] = ng_b
        st_b = (ex.get("stock") or {}).get("by_brand", {}).get(brand)
        if st_b and segment.get("type") != "model":
            out["stock"] = st_b
        return out or None

    def _suggest_budget(self, segment: dict[str, Any], brand: str) -> dict[str, Any] | None:
        """
        Presupuesto mensual sugerido a partir del gasto real de la marca:
        la pauta de cada modelo debería acompañar su peso real en ventas
        (sales_share), no el peso que hoy tiene en anuncios (ad_share).
        Para una persona de marca devuelve el gasto y CPL actuales.
        """
        sp = self._spend_by_brand.get(brand)
        if not sp:
            return None
        out: dict[str, Any] = dict(sp)
        if segment.get("type") == "model":
            sales_share = float(segment.get("sales_share") or 0)
            ad_share = float(segment.get("ad_share") or 0)
            out["current_month_est"] = round(sp["spend_month"] * ad_share / 100, 2)
            if segment.get("gap") == "lanzamiento":
                out["suggested_month"] = None
                out["basis"] = "lanzamiento: sin ventas en el ERP todavía; definir presupuesto de lanzamiento aparte"
            elif sales_share > 0:
                out["suggested_month"] = round(sp["spend_month"] * sales_share / 100, 2)
                out["basis"] = f"{sales_share}% de las ventas de la marca sobre USD {sp['spend_month']:,.0f}/mes que gasta la marca"
            else:
                out["suggested_month"] = None
                out["basis"] = "sin ventas en el ERP para este modelo"
            if sp.get("cpl") and out.get("suggested_month"):
                out["expected_leads_month"] = int(out["suggested_month"] / sp["cpl"])
        return out

    def _top_age_range(self, demo: dict[str, Any]) -> str:
        """Identifica el rango de edad con más impresiones."""
        ages = demo.get("age_ranges", [])
        if not ages:
            return "25-34"

        sorted_ages = sorted(ages, key=lambda x: x.get("impressions", 0), reverse=True)
        top = sorted_ages[0] if sorted_ages else {}
        return top.get("age_range", "25-34")

    def _top_gender(self, demo: dict[str, Any]) -> str:
        """Identifica el género predominante."""
        genders = demo.get("genders", [])
        if not genders:
            # Intentar con datos de ventas
            sales_gender = demo.get("sales_gender", {})
            if sales_gender:
                top = max(sales_gender.items(), key=lambda x: x[1])
                return top[0]
            return "mixto"

        sorted_genders = sorted(genders, key=lambda x: x.get("impressions", 0), reverse=True)
        top = sorted_genders[0] if sorted_genders else {}
        return top.get("gender", "mixto")

    def _top_location(self, demo: dict[str, Any], purchase: dict[str, Any]) -> list[str]:
        """Identifica las ubicaciones principales."""
        locations: list[str] = []

        # Priorizar ciudades de ventas
        cities = purchase.get("cities", [])
        for city in cities[:5]:
            name = city.get("customer_city", "")
            if name:
                locations.append(name)

        if not locations:
            # Usar ubicaciones de Google Ads
            g_locations = demo.get("locations", [])
            for loc in g_locations[:5]:
                cid = loc.get("country_id", "")
                if cid:
                    locations.append(str(cid))

        if not locations:
            # Usar países de Meta
            meta_countries = demo.get("meta_countries", [])
            for c in meta_countries[:5]:
                country = c.get("country", "")
                if country:
                    locations.append(country)

        return locations

    def _top_interests(self, interests: list[dict], limit: int = 10) -> list[str]:
        """Extrae los intereses más frecuentes."""
        if not interests:
            return []

        counter: Counter = Counter()
        for item in interests:
            name = item.get("name") or item.get("category", "")
            if name:
                # Ponderar por impresiones si están disponibles
                weight = item.get("impressions", 1)
                if isinstance(weight, (int, float)) and weight > 0:
                    counter[name] += int(weight)
                else:
                    counter[name] += 1

        return [name for name, _ in counter.most_common(limit)]

    def _insight_basis(self, segment: dict[str, Any]) -> dict[str, Any] | None:
        """De dónde salen los dolores/objetivos/motivaciones de la ficha: cuántos
        anuncios se leyeron y si eran del modelo o de la marca."""
        ins = self._ad_insights_for(segment)
        if not ins:
            return None
        if not ins.get("sample_size"):
            # Curación manual del equipo (AD_DERIVED_INSIGHTS), no análisis automático.
            return {"sample": None, "level": "manual"}
        nivel = "modelo"
        if segment.get("type") == "model" and not self._model_ad_insights.get(str(segment.get("name", "")).strip()):
            nivel = "marca"
        elif segment.get("type") != "model":
            nivel = "marca"
        return {"sample": ins.get("sample_size"), "level": nivel}

    def _ad_insights_for(self, segment: dict[str, Any]) -> dict[str, list[str]] | None:
        """
        Devuelve los insights de anuncios reales para la marca del segmento.

        Prioridad: curación manual (AD_DERIVED_INSIGHTS) > análisis
        automático de esta misma corrida (_dynamic_ad_insights) > None
        (cae a la heurística genérica en el caller).
        """
        seg_type = segment.get("type")

        # Persona de modelo: si hay anuncios que nombran ese modelo, usar el
        # análisis específico del modelo; si no, heredar el de su marca.
        if seg_type == "model":
            model_insight = self._model_ad_insights.get(str(segment.get("name", "")).strip())
            if model_insight:
                return model_insight
            brand = str(segment.get("brand", "")).strip()
            if not brand:
                return None
            return AD_DERIVED_INSIGHTS.get(brand.lower()) or self._dynamic_ad_insights.get(brand)

        if seg_type != "brand":
            return None
        name = str(segment.get("name", "")).strip()

        manual = AD_DERIVED_INSIGHTS.get(name.lower())
        if manual:
            return manual

        return self._dynamic_ad_insights.get(name)

    def _infer_pains(self, segment: dict[str, Any], consolidated: dict[str, Any]) -> list[str]:
        """Infiere puntos de dolor basados en el comportamiento de compra."""
        # Si la marca tiene anuncios reales analizados, usar esos dolores
        # en vez de la heurística genérica.
        ad_insights = self._ad_insights_for(segment)
        if ad_insights and ad_insights.get("pains"):
            return list(ad_insights["pains"])

        pains: list[str] = []
        purchase = consolidated.get("purchase", {})

        # Analizar ticket promedio
        summary = purchase.get("summary", {})
        aov = summary.get("avg_order_value", 0)

        if aov > 0 and aov < 50:
            pains.append("Sensibilidad al precio; busca ofertas y promociones")
        elif aov > 200:
            pains.append("Requiere justificación de valor; necesita ver ROI antes de comprar")

        # Canales
        channels = purchase.get("channels", [])
        if len(channels) == 1:
            pains.append(f"Depende exclusivamente del canal '{channels[0].get('channel', '')}'")

        # Categorías
        categories = purchase.get("top_categories", [])
        if len(categories) == 1:
            pains.append("Concentración en una sola categoría de producto")

        # Pains genéricos basados en el tipo de segmento
        seg_type = segment.get("type", "")
        if seg_type == "model":
            pains.append(
                f"Compara el '{segment.get('name', '')}' contra otros modelos "
                f"del mismo segmento antes de decidir"
            )
        elif seg_type == "brand":
            pains.append(f"Evalúa respaldo, garantía y posventa de la marca '{segment.get('name', '')}'")
        elif seg_type == "product_category":
            pains.append(f"Necesita soluciones específicas dentro de '{segment.get('name', '')}'")
        elif seg_type == "channel":
            pains.append(f"Prefiere interactuar únicamente vía '{segment.get('name', '')}'")

        if not pains:
            pains = [
                "Necesita más información antes de tomar decisiones de compra",
                "Compara opciones antes de comprometerse",
            ]

        return pains

    def _infer_goals(self, segment: dict[str, Any], consolidated: dict[str, Any]) -> list[str]:
        """Infiere objetivos del cliente."""
        # Si la marca tiene anuncios reales analizados, anteponer esos
        # objetivos (más específicos) a los genéricos por producto/segmento.
        ad_insights = self._ad_insights_for(segment)
        if ad_insights and ad_insights.get("goals"):
            return list(ad_insights["goals"])

        goals: list[str] = []
        purchase = consolidated.get("purchase", {})
        seg_stats = segment.get("stats") or {}

        # En una persona de modelo el objetivo es ese modelo puntual
        if segment.get("type") == "model":
            model = segment.get("name", "")
            return [
                f"Adquirir un '{model}' en la versión que se ajuste a su presupuesto",
                f"Confirmar que el '{model}' cubre su uso real (ciudad, ruta, trabajo o familia)",
                "Conseguir financiación con una cuota accesible",
            ]

        # Priorizar el producto top del propio segmento
        seg_products = seg_stats.get("top_products", [])
        if seg_products:
            goals.append(f"Adquirir '{seg_products[0]}' o modelos relacionados")
        else:
            top_products = purchase.get("top_products", [])
            if top_products:
                top_product = top_products[0].get("product", "")
                if top_product:
                    goals.append(f"Adquirir '{top_product}' o productos relacionados")

        seg_name = segment.get("name", "")
        if seg_name:
            goals.append(f"Encontrar las mejores opciones en '{seg_name}'")
        else:
            top_cats = purchase.get("top_categories", [])
            if top_cats:
                top_cat = top_cats[0].get("category", "")
                if top_cat:
                    goals.append(f"Encontrar las mejores opciones en '{top_cat}'")

        # Objetivos genéricos
        goals.extend([
            "Optimizar su presupuesto de compra",
            "Recibir productos/servicios de calidad",
            "Tener una experiencia de compra sin fricción",
        ])

        return goals

    def _infer_motivations(
        self, interests: list[str], segment: dict[str, Any] | None = None
    ) -> list[str]:
        """Infiere motivaciones de compra basadas en intereses."""
        # Si la marca tiene anuncios reales analizados, usar esas motivaciones
        # en vez de la heurística genérica por palabras clave.
        ad_insights = self._ad_insights_for(segment or {})
        if ad_insights and ad_insights.get("motivations"):
            return list(ad_insights["motivations"])

        motivations: list[str] = []

        if not interests:
            return [
                "Calidad del producto/servicio",
                "Buen servicio al cliente",
                "Precio competitivo",
            ]

        # Mapear intereses a motivaciones
        interest_text = " ".join(interests).lower()

        if any(w in interest_text for w in ["tech", "tecnolog", "gadget", "digital", "software"]):
            motivations.append("Innovación tecnológica y novedades")
        if any(w in interest_text for w in ["salud", "fitness", "deporte", "wellness", "health"]):
            motivations.append("Bienestar y estilo de vida saludable")
        if any(w in interest_text for w in ["moda", "belleza", "fashion", "style", "beauty"]):
            motivations.append("Estética y cuidado personal")
        if any(w in interest_text for w in ["negocio", "business", "emprend", "finance", "invers"]):
            motivations.append("Crecimiento profesional y financiero")
        if any(w in interest_text for w in ["family", "familia", "hogar", "home", "kids", "niños"]):
            motivations.append("Bienestar familiar y del hogar")
        if any(w in interest_text for w in ["travel", "viaje", "tour", "vacation"]):
            motivations.append("Experiencias y viajes")

        # Motivaciones base
        motivations.append("Relación calidad-precio")
        motivations.append("Confianza en la marca")

        return motivations

    def _generate_name(self, idx: int, gender: str, segment: dict[str, Any] | None = None) -> str:
        """Genera un nombre descriptivo para la persona."""
        segment = segment or {}
        seg_name = segment.get("name", "")
        seg_type = segment.get("type", "")

        # Nombres estables (sin número): el nombre de la nota es la marca, el
        # modelo o el segmento, así los wikilinks no se rompen entre corridas
        # y el vault se agrupa por marca.
        if seg_name:
            if seg_type == "model":
                return seg_name                      # "Mitsubishi L200"
            type_prefix = {
                "brand": "Comprador",
                "product_category": "Segmento",
                "channel": "Canal",
                "interest": "Interés",
            }.get(seg_type, "")
            return f"{type_prefix} {seg_name}".strip()   # "Comprador Mitsubishi"

        descriptors = [
            "El Explorador", "El Decidido", "El Práctico",
            "La Analítica", "El Innovador", "La Social",
            "El Profesional", "La Ahorradora",
        ]
        descriptor = descriptors[(idx - 1) % len(descriptors)]
        return f"{self.name_prefix} {idx:02d} - {descriptor}"


def data_sources_check(
    sales: dict[str, Any], google: dict[str, Any], meta: dict[str, Any]
) -> list[tuple[str, bool]]:
    """Devuelve qué fuentes tienen datos reales."""
    return [
        ("sales", bool(sales)),
        ("google_ads", bool(google)),
        ("meta_ads", bool(meta)),
    ]