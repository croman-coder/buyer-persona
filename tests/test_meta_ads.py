"""Notas de Meta Ads: sin promesas fijas, sin texto interno, límites de Meta y test drive según el stock.

Corre con pytest o directo: venv/bin/python3 tests/test_meta_ads.py
"""
import glob
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.generators.marketing_generator import MarketingContentGenerator, validar_meta_ads  # noqa: E402

GEN = MarketingContentGenerator({"hoy": date(2026, 9, 26)})
GEN_OCTUBRE = MarketingContentGenerator({"hoy": date(2026, 10, 3)})
KOLEOS = {
    "name": "Renault Koleos",
    "segment": {"type": "model", "name": "Renault Koleos", "brand": "Renault", "category": "SUV"},
    "pains": ["Necesita ubicar qué escalón de precio/equipamiento le corresponde (Kardian vs. Boreal vs. Koleos)"],
    "motivations": ["Seguridad y tecnología de asistencia a la conducción verificable (visión 360°, asistencias a la conducción)"],
    "demographics": {"age_range": "35-54", "gender": "Masculino", "location": ["Asunción", "Central"]},
    "observed_interests": {"temas": [{"tema": "Financiación en cuotas"}, {"tema": "Diseño y estatus"}]},
    "extras": {"stock": {"total": 49, "disponible": 43, "test_drive": 2, "fecha": "2026-09-18"},
               "acciones": {"pvp_min": 36990.0, "descuento_max": 2000.0, "periodo": "2026-09", "acciones": []}},
}


def _ultimas_personas():
    rutas = sorted(glob.glob(os.path.join(ROOT, "output", "raw", "personas_*.json")))
    if not rutas:
        return []
    with open(rutas[-1], encoding="utf-8") as fh:
        return json.load(fh)


def test_personas_reales_sin_problemas():
    for p in _ultimas_personas():
        ad = GEN._gen_meta_ads(p)
        assert validar_meta_ads(ad) == [], (p.get("name"), validar_meta_ads(ad))


def test_sin_promesas_fijas_ni_analisis_interno():
    ad = GEN._gen_meta_ads(KOLEOS)
    fijo = json.dumps({k: ad[k] for k in ("primary_texts", "headlines", "description", "carousel_cards")}, ensure_ascii=False)
    for frase in ("5 años", "60 meses", "GRATIS", "Necesita", "verificable", "Kardian"):
        assert frase not in fijo, frase
    assert all(len(t) <= 40 for t in ad["headlines"]) and len(ad["description"]) <= 30


def test_sin_unidad_de_prueba_no_promete_test_drive():
    p = dict(KOLEOS, name="GWM Tank 300", segment={"type": "model", "name": "GWM Tank 300", "brand": "GWM", "category": "SUV"},
             extras={"stock": {"total": 6, "disponible": 6, "test_drive": 0, "fecha": "2026-09-18"}})
    ad = GEN._gen_meta_ads(p)
    assert "test drive" not in json.dumps(ad["primary_texts"] + ad["headlines"], ensure_ascii=False).lower()
    assert "Conocelo en el Salón" in ad["headlines"] and validar_meta_ads(ad) == []


def test_oferta_vigente_y_vencida():
    assert "USD 2.000" in GEN._gen_meta_ads(KOLEOS)["offer_text"]
    vencida = GEN_OCTUBRE._gen_meta_ads(KOLEOS)
    assert vencida["offer"]["vencida"] and vencida["offer_text"] is None


def test_validador_detecta_la_plantilla_vieja():
    viejo = {"primary_texts": ["🚗 El Kwid llega con todo:\n✅ Garantía de 5 años\n✅ Financiación a 60 meses\n✅ Test drive GRATIS"],
             "headlines": ["Renault Kwid | Test Drive Gratis"], "description": "Reservá hoy tu prueba"}
    problemas = " | ".join(validar_meta_ads(viejo))
    assert "promesa sin respaldo" in problemas and "resto de la plantilla vieja" in problemas


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in pruebas:
        t()
        print("ok ", t.__name__)
    print(f"{len(pruebas)} pruebas OK · personas reales leídas: {len(_ultimas_personas())}")
