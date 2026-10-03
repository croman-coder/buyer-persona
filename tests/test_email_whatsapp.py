"""Mail y WhatsApp: sin promesas fijas, sin urgencia inventada y sin test drive si no hay unidad.

Corre con pytest o directo: venv/bin/python3 tests/test_email_whatsapp.py
"""
import glob
from datetime import date
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.generators.marketing_generator import (  # noqa: E402
    MarketingContentGenerator, validar_google_ads, validar_mensajes)

# Con la planilla de septiembre vigente (26-09); los casos de oferta vencida usan GEN_OCTUBRE.
GEN = MarketingContentGenerator({"hoy": date(2026, 9, 26)})
GEN_OCTUBRE = MarketingContentGenerator({"hoy": date(2026, 10, 3)})
KOLEOS = {
    "name": "Renault Koleos",
    "segment": {"type": "model", "name": "Renault Koleos", "brand": "Renault", "category": "SUV"},
    "pains": ["Necesita ubicar qué escalón de precio/equipamiento le corresponde (Kardian vs. Boreal vs. Koleos)"],
    "observed_interests": {"temas": [{"tema": "Probar antes de comprar (test drive)"}, {"tema": "Familia y espacio"}]},
    "extras": {"stock": {"total": 49, "disponible": 43, "test_drive": 2},
               "acciones": {"pvp_min": 36990.0, "descuento_max": 2000.0, "periodo": "2026-09",
                            "acciones": ["DESCUENTO MAXIMO SOLO VALIDO PARA VTA CARTERA SUDAMERIS"]}},
}
SIN_UNIDAD = dict(KOLEOS, name="GWM Tank 300",
                  segment={"type": "model", "name": "GWM Tank 300", "brand": "GWM", "category": "SUV"},
                  extras={"stock": {"total": 6, "disponible": 6, "test_drive": 0}})


def _ultimas_personas():
    rutas = sorted(glob.glob(os.path.join(ROOT, "output", "raw", "personas_*.json")))
    if not rutas:
        return []
    with open(rutas[-1], encoding="utf-8") as fh:
        return json.load(fh)


def test_personas_reales_sin_problemas():
    for p in _ultimas_personas():
        assert validar_mensajes(GEN._gen_email(p)) == [], (p.get("name"), validar_mensajes(GEN._gen_email(p)))
        assert validar_mensajes(GEN._gen_whatsapp(p)) == [], (p.get("name"), validar_mensajes(GEN._gen_whatsapp(p)))


def test_sin_unidad_de_prueba_no_promete_test_drive():
    email, wa, ad = GEN._gen_email(SIN_UNIDAD), GEN._gen_whatsapp(SIN_UNIDAD), GEN._gen_google_ads(SIN_UNIDAD)
    fijos = " ".join([email["subject"], email["body"], email["follow_up_3_days"], *wa["templates"].values(),
                      *wa["auto_replies"].values(), *ad["headlines"], *ad["descriptions"], *ad["callouts"]])
    assert "test drive" not in fijos.lower()
    assert "Conocelo en el Salón" in ad["headlines"]
    assert not any("test drive" in k for k in ad["keywords"])
    assert validar_mensajes(email) == validar_mensajes(wa) == validar_google_ads(ad) == []


def test_con_unidad_invita_a_test_drive():
    assert "test drive" in GEN._gen_email(KOLEOS)["subject"]
    assert "Agendá tu Test Drive" in GEN._gen_google_ads(KOLEOS)["headlines"]


def test_oferta_y_stock_van_aparte():
    email, wa = GEN._gen_email(KOLEOS), GEN._gen_whatsapp(KOLEOS)
    assert "USD" not in email["body"] and "USD" not in " ".join(wa["templates"].values())
    assert email["offer_text"] == ("En septiembre, Renault Koleos está desde USD 36.990 y con hasta USD 2.000 de "
                                   "descuento. Consultá condiciones con tu asesor.")
    assert "USD 2.000" in wa["offer_text"] and email["stock_disponible"] == 43
    assert email["offer"]["condiciones"] == ["DESCUENTO MAXIMO SOLO VALIDO PARA VTA CARTERA SUDAMERIS"]


def test_oferta_vencida_no_se_propone():
    import main
    email = GEN_OCTUBRE._gen_email(KOLEOS)
    assert email["offer"]["vencida"] and email["offer_text"] is None
    assert GEN_OCTUBRE._gen_whatsapp(KOLEOS)["offer_text"] is None
    bloque = "\n".join(main._bloque_oferta_y_stock(email, "email"))
    assert "ya venció" in bloque and "Párrafo para sumar" not in bloque and "Último dato de la planilla" in bloque


def test_no_copia_el_analisis_interno():
    texto = json.dumps([GEN._gen_email(KOLEOS), GEN._gen_whatsapp(KOLEOS)], ensure_ascii=False)
    assert "Necesita" not in texto and "Kardian" not in texto


def test_usados_no_hablan_de_0km():
    p = {"name": "Renew Jetour", "segment": {"type": "model", "name": "Renew Jetour", "brand": "Renew"},
         "observed_interests": {"temas": [{"tema": "Primer auto / primera SUV"}]}}
    email, wa = GEN._gen_email(p), GEN._gen_whatsapp(p)
    assert "0km" not in email["body"] + " ".join(wa["templates"].values())
    assert "Renew" in email["body"] and validar_mensajes(email) == validar_mensajes(wa) == []


def test_validador_detecta_la_plantilla_vieja():
    viejo = {"subject": "🚗 Renault Kwid: Test Drive GRATIS + Financiación Especial",
             "preheader": "Solo por este mes. Reservá tu prueba de manejo.",
             "body": "✅ Financiación a 60 meses sin interés\n✅ Garantía extendida de 5 años\n✅ Entrega inmediata\n"
                     "El equipo de [Concesionaria]",
             "templates": {"promo": "🚨 ¡OFERTA ESPECIAL! 🚨 Solo hasta fin de mes."},
             "auto_replies": {"precio": "El Kwid tiene un precio desde $XX,XXX. Trabajamos con los mejores bancos."}}
    problemas = " | ".join(validar_mensajes(viejo))
    for que in ("promesa sin respaldo", "urgencia sin respaldo", "resto de la plantilla vieja"):
        assert que in problemas, que


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in pruebas:
        t()
        print("ok ", t.__name__)
    print(f"{len(pruebas)} pruebas OK · personas reales leídas: {len(_ultimas_personas())}")
