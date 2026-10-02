"""
Catálogo de modelos realmente disponibles en Paraguay.

Los modelos NO se toman del CSV de ventas de ejemplo (que tiene nombres
ficticios), sino de la línea real que Santa Rosa pauta en Meta Ads. Cada
entrada se valida contra los anuncios reales: si un modelo no aparece en
ningún anuncio del período, no genera persona.

Fuente: análisis de los 3.933 anuncios reales de las 73 cuentas de Meta
(agosto 2026). Para regenerar/validar el catálogo:

    venv/bin/python3 scripts/validate_model_catalog.py
"""

from __future__ import annotations

import re
from typing import Any

# marca -> { nombre comercial del modelo: patrón regex para detectarlo }
# El patrón se aplica sobre nombre del anuncio + título + copy, en minúsculas.
MODEL_CATALOG: dict[str, dict[str, str]] = {
    "Renault": {
        "Renault Kardian": r"\bkardian\b",
        "Renault Kwid": r"\bkwid\b",
        "Renault Duster": r"\bduster\b",
        "Renault Oroch": r"\boroch\b",
        "Renault Koleos": r"\bkoleos\b",
        "Renault Master": r"\bmaster\b",
        "Renault Arkana": r"\barkana\b",
        "Renault Clio": r"\bclio\b",
        "Renault Boreal": r"\bboreal\b",
        "Renault Kangoo": r"\bkangoo\b",
    },
    "Jetour": {
        "Jetour X50": r"\bx-?50\b",
        "Jetour X70": r"\bx-?70\b",
        "Jetour X90": r"\bx-?90\b",
        "Jetour T1": r"\bt1\b",
        "Jetour T2": r"\bt2\b",
        "Jetour Dashing": r"\bdashing\b",
        "Jetour G700": r"\bg-?700\b",
    },
    "GWM": {
        "GWM Haval H6": r"\bh6\b|haval\s*h6",
        "GWM Haval H7": r"\bh7\b|haval\s*h7",
        "GWM Haval H9": r"\bh9\b|haval\s*h9",
        "GWM Haval Jolion": r"\bjolion\b",
        "GWM Tank 300": r"tank\s*300",
        "GWM Tank 400": r"tank\s*400",
        "GWM Tank 500": r"tank\s*500",
        "GWM Poer": r"\bpoer\b",
        "GWM Ora": r"\bora\s*0?3?\b",
        "GWM Wingle": r"\bwingle\b",
    },
    "JAC": {
        "JAC JS4": r"\bjs-?4\b",
        "JAC T8": r"\bt8\b",
        "JAC T9": r"\bt9\b",
        "JAC X200": r"\bx-?200\b",
        "JAC RF8": r"\brf-?8\b",
        "JAC E30X": r"\be-?30x\b",
        "JAC E-JS1": r"\be-?js-?1\b",
        "JAC Sunray": r"\bsunray\b",
        "JAC LD250": r"\bld-?250\b",
        "JAC LD123": r"\bld-?123\b",
        "JAC LE420": r"\ble-?420\b",
    },
    "Mitsubishi": {
        "Mitsubishi L200": r"\bl-?200\b",
        "Mitsubishi Montero Sport": r"montero",
        "Mitsubishi Eclipse Cross": r"eclipse",
        "Mitsubishi Outlander": r"outlander",
        "Mitsubishi Mirage": r"\bmirage\b",
        "Mitsubishi Destinator": r"destinator",
    },
    "Zeekr": {
        "Zeekr 001": r"\b001\b|zeekr\s*001",
        "Zeekr 7X": r"\b7x\b",
        "Zeekr X": r"zeekr\s*x\b",
    },
    "Leapmotor": {
        "Leapmotor T03": r"\bt-?03\b",
        "Leapmotor C10": r"\bc-?10\b",
        "Leapmotor C11": r"\bc-?11\b",
        "Leapmotor C16": r"\bc-?16\b",
    },
    "Soueast": {
        "Soueast S06": r"\bs-?06\b",
        "Soueast S07": r"\bs-?07\b",
        "Soueast S08": r"\bs-?08\b",
        "Soueast S09": r"\bs-?09\b",
    },
    "JMEV": {
        "JMEV EV2": r"\bev-?2\b",
        "JMEV EV3": r"\bev-?3\b",
    },
    # Renew (usados certificados): la unidad de análisis es la MARCA del usado,
    # porque el ERP carga "USADOS" o la marca en la columna Modelo y la pauta
    # nombra al vehículo (KIA SPORTAGE, NISSAN KICKS...).
    "Renew": {
        "Renew Jetour": r"\bjetour\b|\bx70\b|\bx90\b|\bt2\b|dashing",
        "Renew Renault": r"\brenault\b|\bkwid\b|\bduster\b|\boroch\b|\bkoleos\b|\bsandero\b|\bcaptur\b|\blogan\b",
        "Renew GWM": r"\bgwm\b|great ?wall|\bhaval\b|\bjolion\b|\btank\b|\bpoer\b|\bwingle\b",
        "Renew JAC": r"\bjac\b",
        "Renew Kia": r"\bkia\b|sportage|cerato|sorento|seltos|\brio\b|soluto|carnival",
        "Renew Toyota": r"toyota|hilux|corolla|rav ?4|yaris|fortuner|\bsw4\b|etios",
        "Renew Nissan": r"nissan|kicks|x-?trail|frontier|sentra|versa|qashqai",
        "Renew Chevrolet": r"chevrolet|tracker|\bonix\b|\bs10\b|montana|spin|equinox|trailblazer",
        "Renew Volkswagen": r"volkswagen|\bvw\b|amarok|\bpolo\b|t-?cross|\btaos\b|virtus|tiguan|nivus|saveiro",
        "Renew Hyundai": r"hyundai|tucson|creta|santa ?fe|\bhb20\b|kona",
        "Renew Ford": r"\bford\b|ranger|explorer|ecosport|territory|bronco|maverick",
        "Renew Mitsubishi": r"mitsubishi|\bl200\b|montero|outlander|eclipse|\basx\b",
        "Renew SsangYong": r"ssangyong|rexton|korando|musso|tivoli",
        "Renew Jeep": r"\bjeep\b|renegade|compass|wrangler|cherokee",
        "Renew BYD": r"\bbyd\b|song|yuan|dolphin|\bseal\b|\batto\b",
        "Renew Fiat": r"\bfiat\b|\btoro\b|\bstrada\b|\bcronos\b|\bargo\b|\bpulse\b|\bfastback\b",
        "Renew Honda": r"\bhonda\b|\bhr-?v\b|\bcr-?v\b|\bcivic\b|\bfit\b|\bwr-?v\b",
        "Renew Peugeot": r"peugeot|\b2008\b|\b3008\b|\b208\b|\b308\b",
        "Renew Mini": r"\bmini\b|cooper|countryman",
        "Renew Usados": r"\busados?\b",
    },
    "XPeng": {
        "XPeng G9": r"\bg9\b",
    },
}

# Categoría (tipo de vehículo) de cada modelo, para cruzar con las personas
# de segmento. Solo los que no son obvios por el nombre.
MODEL_CATEGORY: dict[str, str] = {
    # Pickups / utilitarios
    "Renault Oroch": "Pickup",
    "Renault Master": "Furgoneta",
    "Renault Kangoo": "Furgoneta",
    "GWM Poer": "Pickup",
    "GWM Wingle": "Pickup",
    "JAC T8": "Pickup",
    "JAC T9": "Pickup",
    "JAC X200": "Furgoneta",
    "JAC Sunray": "Furgoneta",
    "JAC LD250": "Camión",
    "JAC LD123": "Camión",
    "JAC LE420": "Camión",
    "Mitsubishi L200": "Pickup",
    # Hatchback / sedán
    "Renault Kwid": "Hatchback",
    "Renault Clio": "Hatchback",
    "Mitsubishi Mirage": "Hatchback",
    "Leapmotor T03": "Hatchback",
    # Eléctricos
    "GWM Ora": "Eléctrico",
    "JAC E30X": "Eléctrico",
    "JAC E-JS1": "Eléctrico",
    "Leapmotor C10": "Eléctrico",
    "Leapmotor C11": "Eléctrico",
    "Leapmotor C16": "Eléctrico",
    "JMEV EV2": "Eléctrico",
    "JMEV EV3": "Eléctrico",
    "Zeekr 001": "Eléctrico",
    "Zeekr 7X": "Eléctrico",
    "Zeekr X": "Eléctrico",
    "XPeng G9": "Eléctrico",
}


def _ad_text(ad: dict[str, Any]) -> str:
    """Texto completo de un anuncio para buscar menciones de modelo."""
    return " ".join(
        str(ad.get(k, "") or "") for k in ("ad_name", "title", "body")
    ).lower()


def detect_models_in_ads(ads: list[dict[str, Any]], brand: str) -> dict[str, list[dict]]:
    """
    Agrupa los anuncios de una marca por el modelo que mencionan.

    Un anuncio puede mencionar más de un modelo (carruseles multi-modelo);
    en ese caso cuenta para todos.

    Returns:
        ``{"Renault Kardian": [anuncio, ...], ...}`` solo con modelos que
        tienen al menos un anuncio real.
    """
    patterns = MODEL_CATALOG.get(brand, {})
    if not patterns:
        return {}

    by_model: dict[str, list[dict]] = {}
    compiled = {model: re.compile(pat, re.I) for model, pat in patterns.items()}

    for ad in ads:
        text = _ad_text(ad)
        if not text.strip():
            continue
        for model, rx in compiled.items():
            if rx.search(text):
                by_model.setdefault(model, []).append(ad)

    return by_model


def category_for(model: str) -> str:
    """Devuelve la categoría/tipo de vehículo de un modelo (por defecto SUV)."""
    if str(model).startswith("Renew "):
        return "Usado"
    return MODEL_CATEGORY.get(model, "SUV")


def brand_for(model: str) -> str:
    """Devuelve la marca a la que pertenece un modelo del catálogo."""
    for brand, models in MODEL_CATALOG.items():
        if model in models:
            return brand
    return ""
