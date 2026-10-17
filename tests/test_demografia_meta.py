"""Edad y género de Meta: se ponderan por contactos (formularios y chats), no por clics. Datos inventados.

Caso real del 14-10-2026: en Jetour los mayores de 65 eran el 24,9 % de los clics pero el 20,1 % de los contactos,
y la ficha decía «65+» porque contaba clics. Por contactos, la edad principal es 35-44.

Corre con pytest o directo: venv/bin/python3 tests/test_demografia_meta.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.connectors.meta_ads_connector import MetaAdsConnector  # noqa: E402
from src.exporters.obsidian_exporter import ObsidianExporter  # noqa: E402
from src.generators.persona_generator import PersonaGenerator  # noqa: E402

G = PersonaGenerator


def fila_cuenta(marca, edad, genero, clics, leads=0, chats=0):
    """Fila del desglose edad+género a nivel cuenta: los contactos vienen dentro de `actions`."""
    acciones = [{"action_type": "lead", "value": str(leads)},
                {"action_type": "onsite_conversion.messaging_conversation_started_7d", "value": str(chats)},
                {"action_type": "link_click", "value": str(clics)}]          # no es un contacto
    return {"account": marca, "age": edad, "gender": genero, "clicks": str(clics), "impressions": str(clics * 40),
            "actions": acciones}


def fila_anuncio(modelo, edad, genero, clics, contactos):
    """Fila a nivel anuncio: el conector ya guarda el total de contactos."""
    return {"account": modelo, "age": edad, "gender": genero, "clicks": clics, "impressions": clics * 40, "contactos": contactos}


def test_los_contactos_del_conector_y_del_generador_son_los_mismos():
    assert G.CONTACT_ACTIONS == MetaAdsConnector.CONTACT_ACTIONS


def test_la_edad_sale_de_los_contactos_y_no_de_los_clics():
    filas = [fila_cuenta("Jetour", "65+", "male", clics=250, leads=15, chats=5),     # muchos clics, pocos contactos
             fila_cuenta("Jetour", "35-44", "male", clics=230, leads=20, chats=6),
             fila_cuenta("Jetour", "25-34", "female", clics=190, leads=18, chats=6)]
    d = G._summarize_meta_demographics(filas)["Jetour"]
    assert d["basis"] == "contactos"
    assert d["age_range"] == "35-44"                         # por clics hubiera sido 65+
    assert d["weight"] == 70                                 # 20 + 26 + 24 contactos
    assert d["age_distribution"] == {"35-44": 37.1, "25-34": 34.3, "65+": 28.6}
    assert d["gender"] == "Masculino" and d["gender_share"] == 65.7
    assert d["clicks"] == 670                                # queda a mano cuánto se midió en clics


def test_con_pocos_contactos_se_usan_los_clics_y_se_dice():
    filas = [fila_cuenta("XPeng", "45-54", "male", clics=300, leads=3), fila_cuenta("XPeng", "35-44", "male", clics=100, leads=10)]
    d = G._summarize_meta_demographics(filas)["XPeng"]
    assert d["basis"] == "clics"                             # 13 contactos no alcanzan
    assert d["age_range"] == "45-54" and d["weight"] == 400


def test_las_filas_por_anuncio_traen_los_contactos_sumados():
    filas = [fila_anuncio("Jetour X50", "65+", "male", 400, 6), fila_anuncio("Jetour X50", "35-44", "male", 300, 30)]
    d = G._summarize_meta_demographics(filas)["Jetour X50"]
    assert d["basis"] == "contactos" and d["age_range"] == "35-44" and d["weight"] == 36


def test_el_modelo_usa_su_perfil_solo_con_contactos_suficientes():
    marca = {"basis": "contactos", "weight": 500, "age_range": "35-44"}
    propio = {"basis": "contactos", "weight": 40, "age_range": "25-34"}
    assert G._elegir_demografia_meta(marca, propio) == (propio, "modelo")
    poco = {"basis": "contactos", "weight": 12, "age_range": "65+"}
    demo, nivel = G._elegir_demografia_meta(marca, poco)
    assert nivel == "marca" and demo["age_range"] == "35-44" and demo["model_sample"] == poco
    # un modelo con muchos clics pero pocos contactos no pisa el perfil por contactos de la marca
    solo_clics = {"basis": "clics", "weight": 900, "age_range": "65+"}
    assert G._elegir_demografia_meta(marca, solo_clics)[1] == "marca"
    # si la marca tampoco tiene contactos, vale la regla de siempre: 100 clics
    marca_clics = {"basis": "clics", "weight": 2000, "age_range": "45-54"}
    assert G._elegir_demografia_meta(marca_clics, solo_clics) == (solo_clics, "modelo")
    assert G._elegir_demografia_meta({}, {}) == ({}, "")


def persona_con(meta, nivel="marca"):
    return {"name": "Jetour", "segment": {"type": "brand", "name": "Jetour", "brand": "Jetour"},
            "demographics": {"source": "meta", "age_range": meta["age_range"], "gender": "Masculino", "location": ["Asunción"],
                             "meta": meta, "meta_level": nivel}}


def test_la_ficha_dice_de_qué_sale_la_edad():
    ex = ObsidianExporter({})
    meta = {"age_range": "35-44", "age_share": 25.8, "gender": "Masculino", "gender_share": 66.3, "basis": "contactos",
            "weight": 10784, "age_distribution": {"35-44": 25.8, "25-34": 23.7}}
    resumen = ex._render_summary(persona_con(meta))
    assert "35-44 (25.8% de los contactos) · perfil de la marca" in resumen   # la ficha de marca no «hereda»
    detalle = ex._render_demographics(persona_con(meta))
    assert "ponderado por contactos (formularios y chats)" in detalle and "10,784 contactos" in detalle
    # una corrida vieja, sin `basis`, sigue diciendo clics
    viejo = {k: v for k, v in meta.items() if k != "basis"}
    assert "de los clics" in ex._render_summary(persona_con(viejo))


def test_la_memoria_no_confunde_el_cambio_de_medida_con_un_cambio_de_publico():
    from src.learning.audience_memory import analyze
    def fila(dia, edad, base):
        return {"date": dia, "name": "Jetour X50", "type": "model", "brand": "Jetour", "gender": "Masculino",
                "gender_share": 66.0, "age_range": edad, "age_share": 25.0, "clicks": 500, "level": "modelo", "basis": base}
    historia = [fila(f"2026-10-0{d}", "65+", None) for d in range(1, 8)] + [fila("2026-10-14", "35-44", "contactos")]
    a = analyze(historia, "2026-10-14")
    assert not any("edad dominante" in s for s in a["shifts"]), a["shifts"]
    assert not any(c["name"] == "Jetour X50" for c in a["confirmed"]), "una sola corrida con la medida nueva no confirma nada"


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"OK: {len(pruebas)} pruebas")
