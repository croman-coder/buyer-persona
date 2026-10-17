"""Anuncio de intereses de Mitsubishi: todo en pausa, sin precios, sin sesgar la segmentación. Datos fijos, sin llamar a Meta.

Corre con pytest o directo: venv/bin/python3 tests/test_pauta_intereses.py
"""
import importlib.util
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("pauta_intereses", os.path.join(ROOT, "scripts", "pauta_mmc_intereses_2026_10.py"))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)


def test_todo_se_crea_en_pausa():
    assert P.campana()["status"] == "PAUSED"
    assert P.conjunto("1")["status"] == "PAUSED"
    assert P.anuncio("2", "3")["status"] == "PAUSED"
    assert P.campana()["objective"] == "OUTCOME_LEADS"


def test_presupuesto_valido_en_centavos():
    c = P.conjunto("1")
    assert c["daily_budget"] == P.PRESUPUESTO_DIA_USD * 100 and P.PRESUPUESTO_DIA_USD >= 5     # regla del proyecto: mínimo USD 5/día
    assert c["optimization_goal"] == "LEAD_GENERATION" and c["destination_type"] == "ON_AD"


def test_segmenta_por_vehiculo_y_no_por_pasatiempos():
    nombres = " ".join(i["name"] for i in P.INTERESES).lower()
    assert not re.search(r"f[uú]tbol|deporte|m[uú]sica|pesca|camping|aventura|viaj|famil|gastronom|concierto", nombres), nombres
    assert re.search(r"camioneta|utilitario|montero", nombres)


def test_excluye_a_quienes_ya_dejaron_sus_datos():
    t = P.targeting()
    ids = {a["id"] for a in t["excluded_custom_audiences"]}
    assert {"120252450736180663", "120252959226730663"} <= ids          # LEAD FORM L200 Enviado y Montero abiertos no enviados
    assert t["geo_locations"]["countries"] == ["PY"] and (t["age_min"], t["age_max"]) == (25, 55)
    assert t["targeting_automation"] == {"advantage_audience": 0}        # sin ampliar el público por su cuenta
    assert t["flexible_spec"][0]["interests"] and "custom_audiences" not in t     # no se le pauta al público de la agencia


def test_sin_precios_ni_promesas_inventadas():
    c = P.creativo("123")
    texto = json.dumps(c, ensure_ascii=False)
    assert not re.search(r"USD|\$|cuota|tasa|gratis|garant|descuento|oferta|test drive|sorteo|premio|hoy|último|urgente", texto.replace("lead_gen_form_id", ""), re.I)
    assert c["object_story_spec"]["link_data"]["call_to_action"]["value"]["lead_gen_form_id"] == "123"
    assert "Toyota" not in texto and "Kia" not in texto           # ley de Paraguay: nunca nombrar a la competencia en un texto público


def test_la_imagen_lleva_el_mensaje_en_la_zona_segura_de_stories():
    h = P.html_imagen("AAAA")
    assert "Contanos" in h and "qué te gusta" in h and "COMUNIDAD MITSUBISHI" in h
    assert not re.search(r"USD|\$|cuota|precio|oferta", h, re.I)
    top = int(re.search(r"\.p\{[^}]*top:(\d+)px", h).group(1))
    assert 270 <= top <= 500                                  # fuera del 14 % de arriba (nombre y cierre) y lejos del botón de abajo
    assert P.creativo("1", "NUEVO")["object_story_spec"]["link_data"]["image_hash"] == "NUEVO"


def test_no_toca_lo_de_la_agencia():
    fuente = open(os.path.join(ROOT, "scripts", "pauta_mmc_intereses_2026_10.py"), encoding="utf-8").read()
    assert '"ACTIVE"' not in fuente.replace('{"status": "ACTIVE"}', "")        # lo único que se activa es el formulario
    assert "/campaigns/" not in fuente                                # solo crea cosas nuevas, no edita campañas existentes


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"OK: {len(pruebas)} pruebas")
