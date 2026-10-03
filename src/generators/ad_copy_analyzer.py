"""
Analizador de Copy de Anuncios.

Lee el texto real de los anuncios que ya están corriendo (título + body,
extraídos por MetaAdsConnector) y deriva automáticamente dolores, objetivos
y motivaciones por marca, usando un diccionario de señales de marketing
automotriz en español.

Esto reemplaza la curación manual: cada vez que se corre el pipeline con
cuentas de Meta Ads conectadas, se vuelve a leer el copy vigente y se
recalculan los insights. Si mañana cambia la campaña, cambia el buyer
persona — no hace falta tocar código para que una marca nueva quede
cubierta, solo que tenga anuncios activos con texto.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

# Cada regla: palabras/frases gatillo (regex, minúsculas) → un insight de
# cada tipo. Una regla dispara si aparece en al menos MIN_HITS anuncios
# distintos de la marca, para no reaccionar a un único copy aislado.
# Etiqueta de "interés observado" de cada regla (mismo orden que RULES):
# lo que el público de esa marca/modelo ve y clickea en los anuncios.
INTEREST_LABELS = [
    "Autos eléctricos y ahorro de combustible",
    "Financiación en cuotas",
    "Garantía y respaldo posventa",
    "Familia y espacio",
    "Probar antes de comprar (test drive)",
    "Seguridad y asistencias a la conducción",
    "Diseño y estatus",
    "Ofertas y promociones",
    "Trabajo, negocio y carga",
    "Primer auto / primera SUV",
    "Tecnología y conectividad",
]

RULES: list[dict[str, Any]] = [
    {
        # Que el AUTO sea eléctrico. «Asientos/espejos/dirección eléctricos» es
        # equipamiento de cualquier auto, «capacidad de carga» es de una pickup
        # y «autonomía» la anuncia también un diésel: ninguno cuenta solo.
        "keywords": [
            r"(?:auto|autos|veh[ií]culo|veh[ií]culos|suv|sed[aá]n|camioneta|pickup|utilitario|motor|motorizaci[oó]n|propulsi[oó]n|movilidad|tecnolog[ií]a)\s+(?:100\s?%\s+)?el[eé]ctric",
            r"100\s?%\s+el[eé]ctric", r"cero emisiones", r"sin combustible", r"\bkwh\b",
            r"carga r[aá]pida", r"tiempo de carga", r"cargador", r"wallbox", r"enchuf",
        ],
        "pain": "Ansiedad de autonomía/carga: evalúa km reales y tiempo de carga antes de decidir",
        # Un híbrido también dice "eléctrico" en el copy, pero no se enchufa a
        # esperar: el dolor de autonomía/carga solo cuenta en anuncios que no
        # hablen de híbrido. La motivación de ahorro aplica a los dos.
        "pain_exclude": r"h[ií]brid|hybrid|e-tech|\bphev\b|\bhev\b",
        "motivation": "Ahorro de combustible y mantenimiento a largo plazo",
    },
    {
        "keywords": [r"cuota", r"financia", r"entrega inicial", r"refuerzos", r"gs\.\s?\d", r"mensual"],
        "pain": "Compara el valor de la cuota mensual, no solo el precio de lista",
        "goal": "Conseguir financiación accesible con cuotas manejables",
    },
    {
        "keywords": [r"garant[ií]a", r"respaldo", r"posventa", r"santa rosa"],
        "motivation": "Confianza en la garantía y el respaldo de posventa de la marca/concesionaria",
    },
    {
        "keywords": [r"familia", r"asientos", r"espacio para", r"7 asientos"],
        "pain": "Necesita espacio y capacidad suficiente para uso familiar",
        "goal": "Encontrar un vehículo con espacio adecuado para la familia",
    },
    {
        "keywords": [r"test drive", r"prueba de manejo", r"agend[aá]", r"reserv[aá]"],
        "goal": "Probar el vehículo antes de decidir (test drive)",
    },
    {
        "keywords": [r"seguridad", r"asistencias", r"visi[oó]n 360", r"airbags", r"frenado"],
        "motivation": "Seguridad y tecnología de asistencia a la conducción verificable",
    },
    {
        "keywords": [r"premium", r"insignia", r"elegante", r"sofisticad", r"dise[nñ]o"],
        "motivation": "Status y diseño en el segmento premium",
    },
    {
        "keywords": [r"oferta", r"descuento", r"[uú]ltimos d[ií]as", r"tiempo limitado", r"precio mejorado", r"promoci[oó]n"],
        "pain": "Sensible a promociones y precio por tiempo limitado",
    },
    {
        "keywords": [r"negocio", r"carga [uú]til", r"flota", r"pyme", r"trabajo diario"],
        "pain": "Necesita justificar el vehículo como inversión productiva, no solo transporte",
        "goal": "Usar el vehículo como herramienta confiable de trabajo/negocio",
    },
    {
        "keywords": [r"primera suv", r"primer auto", r"tu primer"],
        "pain": "Comprador primerizo en la categoría; necesita orientación básica antes de decidir",
    },
    {
        "keywords": [r"tecnolog[ií]a", r"conectividad", r"google integrado", r"pantalla", r"inteligente"],
        "motivation": "Tecnología y conectividad de última generación",
    },
]

MIN_HITS = 2  # una señal necesita aparecer en al menos 2 anuncios distintos


def analyze_brand(ads: list[dict[str, Any]]) -> dict[str, list[str]] | None:
    """
    Deriva pains/goals/motivations a partir del copy real de una marca.

    Args:
        ads: lista de anuncios ``{"title": ..., "body": ..., "status": ...}``
             (formato que produce ``MetaAdsConnector._extract_ad_copy``).

    Returns:
        ``{"pains": [...], "goals": [...], "motivations": [...]}`` o ``None``
        si no hay suficiente copy para sacar conclusiones confiables.
    """
    texts = [
        f"{ad.get('title', '')} {ad.get('body', '')}".lower()
        for ad in ads
        if ad.get("title") or ad.get("body")
    ]
    if len(texts) < 3:
        return None

    hits: Counter = Counter()
    pain_hits: Counter = Counter()
    rule_by_index: dict[int, dict] = {}
    for idx, rule in enumerate(RULES):
        rule_by_index[idx] = rule
        pattern = "|".join(rule["keywords"])
        matched = [t for t in texts if re.search(pattern, t)]
        count = len(matched)
        if count >= MIN_HITS:
            hits[idx] = count
        # El dolor puede tener una exclusión propia (ver pain_exclude en RULES).
        excl = rule.get("pain_exclude")
        pain_count = sum(1 for t in matched if not (excl and re.search(excl, t))) if excl else count
        if pain_count >= MIN_HITS:
            pain_hits[idx] = pain_count

    if not hits:
        return None

    pains: list[str] = []
    goals: list[str] = []
    motivations: list[str] = []

    for idx, _count in hits.most_common():
        rule = rule_by_index[idx]
        if rule.get("pain") and idx in pain_hits and rule["pain"] not in pains:
            pains.append(rule["pain"])
        if rule.get("goal") and rule["goal"] not in goals:
            goals.append(rule["goal"])
        if rule.get("motivation") and rule["motivation"] not in motivations:
            motivations.append(rule["motivation"])

    if not (pains or goals or motivations):
        return None

    return {
        "pains": pains[:5],
        "goals": goals[:5],
        "motivations": motivations[:5],
        "sample_size": len(texts),
    }


def analyze_all_brands(ad_creatives: list[dict[str, Any]]) -> dict[str, dict[str, list[str]]]:
    """Agrupa por marca (campo ``account``) y analiza cada grupo."""
    by_brand: dict[str, list[dict]] = {}
    for ad in ad_creatives:
        brand = ad.get("account", "")
        if brand:
            by_brand.setdefault(brand, []).append(ad)

    results: dict[str, dict[str, list[str]]] = {}
    for brand, ads in by_brand.items():
        insight = analyze_brand(ads)
        if insight:
            results[brand] = insight

    return results


def observed_interests(ads: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    """
    Temas de interés observados en los anuncios de una marca/modelo: cuántos
    anuncios tocan cada tema. No es "interés declarado" (Meta ya no lo
    expone): es lo que el público ve y con lo que interactúa.
    """
    texts = [f"{ad.get('title', '')} {ad.get('body', '')}".lower() for ad in ads if ad.get("title") or ad.get("body")]
    if not texts:
        return []
    out = []
    for idx, rule in enumerate(RULES):
        pattern = "|".join(rule["keywords"])
        n = sum(1 for t in texts if re.search(pattern, t))
        if n:
            out.append({"tema": INTEREST_LABELS[idx] if idx < len(INTEREST_LABELS) else rule["keywords"][0], "anuncios": n, "pct": round(n / len(texts) * 100, 1)})
    out.sort(key=lambda x: -x["anuncios"])
    return out[:limit]
