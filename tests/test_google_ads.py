"""Borradores de Google Ads: límites de Google y nada de promesas sin respaldo.

Corre con pytest o directo: venv/bin/python3 tests/test_google_ads.py
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.generators.marketing_generator import MarketingContentGenerator, validar_google_ads  # noqa: E402

GEN = MarketingContentGenerator()
KOLEOS = {
    "name": "Renault Koleos",
    "segment": {"type": "model", "name": "Renault Koleos", "brand": "Renault", "category": "SUV"},
    "pains": ["Necesita ubicar qué escalón de precio/equipamiento le corresponde (Kardian vs. Boreal vs. Koleos)"],
    "motivations": ["Seguridad y tecnología de asistencia a la conducción verificable (visión 360°, asistencias a la conducción)"],
    "observed_interests": {"temas": [{"tema": "Diseño y estatus", "pct": 56.2}, {"tema": "Financiación en cuotas", "pct": 30.3}]},
    "extras": {"acciones": {"pvp_min": 36990.0, "descuento_max": 2000.0, "periodo": "2026-09",
                            "acciones": ["DESCUENTO MAXIMO SOLO VALIDO PARA VTA CARTERA SUDAMERIS", "-"]}},
}


def _ultimas_personas():
    rutas = sorted(glob.glob(os.path.join(ROOT, "output", "raw", "personas_*.json")))
    if not rutas:
        return []
    with open(rutas[-1], encoding="utf-8") as fh:
        return json.load(fh)


def test_personas_reales_sin_problemas():
    for p in _ultimas_personas():
        ad = GEN._gen_google_ads(p)
        assert validar_google_ads(ad) == [], (p.get("name"), validar_google_ads(ad))


def test_no_copia_el_analisis_interno():
    texto = json.dumps(GEN._gen_google_ads(KOLEOS), ensure_ascii=False)
    for frase in ("Necesita", "Kardian", "verificable", "360"):
        assert frase not in texto, frase


def test_oferta_sale_de_la_planilla():
    of = GEN._gen_google_ads(KOLEOS)["offer"]
    assert of["titulos"] == ["Desde USD 36.990", "Hasta USD 2.000 de Descuento"]
    assert "septiembre" in of["descripcion"] and len(of["descripcion"]) <= 90
    assert of["condiciones"] == ["DESCUENTO MAXIMO SOLO VALIDO PARA VTA CARTERA SUDAMERIS"]


def test_sin_oferta_en_planilla_no_hay_oferta():
    p = dict(KOLEOS, extras={})
    assert GEN._gen_google_ads(p)["offer"] is None


def test_usado_no_habla_de_0km_ni_excluye_usados():
    p = {"name": "Renew Jetour", "segment": {"type": "model", "name": "Renew Jetour", "brand": "Renew"},
         "observed_interests": {"temas": [{"tema": "Primer auto / primera SUV"}, {"tema": "Garantía y respaldo posventa"}]}}
    ad = GEN._gen_google_ads(p)
    assert ad["used"] and not any("0km" in x for x in ad["headlines"] + ad["descriptions"])
    assert "usado" not in ad["negative_keywords"]
    assert validar_google_ads(ad) == []


def test_nombre_corto_va_con_la_marca():
    p = {"name": "Jetour X70", "segment": {"type": "model", "name": "Jetour X70", "brand": "Jetour", "category": "SUV"}}
    kws = GEN._gen_google_ads(p)["keyword_groups"]["Modelo"]
    assert '"jetour x70"' in kws and '"x70"' not in kws


def test_validador_detecta_lo_de_antes():
    viejo = {"headlines": ["SUV Renault", "Garantía de 5 Años", "Financiación Sin Interés"],
             "descriptions": ["Descubrí el Renault Kwid. Necesita ubicar qué escalón de precio/equipamiento. Test drive gratis en tu ciudad.",
                              "El SUV que necesitás."],
             "sitelinks": [{"text": "Financiación", "desc1": "Hasta 60 meses", "desc2": "Sin interés"}]}
    problemas = " | ".join(validar_google_ads(viejo))
    assert "caracteres" in problemas and "promesa sin respaldo" in problemas


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in pruebas:
        t()
        print("ok ", t.__name__)
    print(f"{len(pruebas)} pruebas OK · personas reales leídas: {len(_ultimas_personas())}")
