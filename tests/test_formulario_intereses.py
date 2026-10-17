"""Formulario de intereses de Mitsubishi: qué pregunta y qué NO pregunta. Datos fijos, sin llamar a Meta.

Corre con pytest o directo: venv/bin/python3 tests/test_formulario_intereses.py
"""
import importlib.util
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("formulario_intereses", os.path.join(ROOT, "scripts", "crear_formulario_intereses_mmc.py"))
F = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F)

PALABRAS_SENSIBLES = re.compile(r"religi|iglesia|partido|polític|salud|enferm|ingres|sueldo|salario|deuda|raza|etnia|orientaci", re.I)


def test_pregunta_gustos_y_clubes_y_nada_sensible():
    custom = [q for q in F.QUESTIONS if q["type"] == "CUSTOM"]
    claves = [q["key"] for q in custom]
    assert claves == ["tiempo_libre", "comunidad", "cuando"]
    texto = json.dumps(F.QUESTIONS, ensure_ascii=False)
    assert not PALABRAS_SENSIBLES.search(texto), PALABRAS_SENSIBLES.search(texto)
    valores = [o["value"] for q in custom for o in q["options"]]
    for pedido in ("Fútbol y otros deportes", "Música y shows", "Club de autos, motos o 4x4"):
        assert pedido in valores                       # deporte, música y comunidad: lo que pidió el brand


def test_la_estructura_es_la_que_acepta_meta():
    for q in F.QUESTIONS:
        assert q["type"] and q["key"]
        if q["type"] == "CUSTOM":
            assert q["label"].startswith("¿") and 2 <= len(q["options"]) <= 10
            assert len({o["key"] for o in q["options"]}) == len(q["options"]), "claves de opción repetidas"
            assert all(re.fullmatch(r"[a-z0-9_]+", o["key"]) for o in q["options"])
    assert [q["type"] for q in F.QUESTIONS][-4:] == ["FULL_NAME", "PHONE", "EMAIL", "CITY"]          # los campos de contacto de siempre
    assert {q["key"] for q in F.QUESTIONS if q["type"] != "CUSTOM"} == {"full_name", "phone_number", "email", "city"}


def test_sin_precios_ni_promesas_inventadas():
    texto = json.dumps([F.CONTEXT_CARD, F.THANK_YOU], ensure_ascii=False)
    assert not re.search(r"USD|\$|cuota|tasa|gratis|garant|descuento|oferta|test drive|sorteo|premio", texto, re.I)


def test_se_crea_en_pausa_y_sin_campana():
    p = F.payload()
    assert "status" not in p                          # Meta ignora DRAFT: el script lo archiva después de crearlo
    fuente0 = open(os.path.join(ROOT, "scripts", "crear_formulario_intereses_mmc.py"), encoding="utf-8").read()
    assert '"status": "ARCHIVED"' in fuente0 and '"status": "ACTIVE"' in fuente0 and "--activar" in fuente0
    assert p["name"].startswith("SRPY - MITSUBISHI - Buyer Persona - 2026-10")
    assert p["locale"] == "es_LA" and p["is_optimized_for_quality"] == "true"
    assert json.loads(p["privacy_policy"])["url"] == F.WEB
    fuente = open(os.path.join(ROOT, "scripts", "crear_formulario_intereses_mmc.py"), encoding="utf-8").read()
    assert "/campaigns" not in fuente and "/adsets" not in fuente and "/ads\"" not in fuente    # solo el formulario


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"OK: {len(pruebas)} pruebas")
