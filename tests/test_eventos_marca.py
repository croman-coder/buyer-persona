"""Bloque «Para eventos» de la ficha de marca: dónde están los leads, quién es por modelo y qué NO sabemos todavía. Datos inventados.

Pedido de un brand de Mitsubishi (audio del 16-10-2026): tener en el Buyer Persona lo que sirva para sus eventos.

Corre con pytest o directo: venv/bin/python3 tests/test_eventos_marca.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.exporters.obsidian_exporter import ObsidianExporter  # noqa: E402


def marca(nombre="Mitsubishi", ciudades=None):
    return {"name": f"Comprador {nombre}", "segment": {"type": "brand", "name": nombre, "brand": nombre},
            "real_leads": {"total_leads": 2615, "city": ciudades if ciudades is not None
                           else {"Asunción": 563, "Ciudad del Este": 143, "San Lorenzo": 97, "Luque": 93}},
            "demographics": {"source": "meta", "age_range": "35-44", "gender": "Masculino", "meta_level": "marca",
                             "meta": {"gender_share": 84.9, "age_share": 31.7, "basis": "contactos", "weight": 3512}},
            "observed_interests": {"temas": [{"tema": "Financiación en cuotas", "pct": 52.8}, {"tema": "Garantía y respaldo posventa", "pct": 48.6},
                                             {"tema": "Tecnología y conectividad", "pct": 39.7}, {"tema": "Diseño y estatus", "pct": 30.9}]}}


def modelo(nombre, edad, genero, share, nivel, leads, pct):
    return {"name": f"Mitsubishi {nombre}", "segment": {"type": "model", "name": f"Mitsubishi {nombre}", "brand": "Mitsubishi"},
            "real_leads": {"this_model": {"count": leads, "pct": pct}},
            "demographics": {"source": "meta", "age_range": edad, "gender": genero, "meta_level": nivel,
                             "meta": {"gender_share": share, "basis": "contactos"}}}


def exporter():
    ex = ObsidianExporter({})
    personas = [marca(), modelo("L200", "35-44", "Masculino", 84.6, "modelo", 937, 35.8),
                modelo("Eclipse Cross", "25-34", "Masculino", 72.1, "modelo", 148, 5.7),
                modelo("Mirage", "35-44", "Masculino", 84.9, "marca", 0, 0.0)]
    ex._models_by_brand = {"Mitsubishi": [p["name"] for p in personas[1:]]}
    ex._personas_by_name = {p["name"]: p for p in personas}
    return ex, personas[0]


def test_dice_donde_estan_los_leads_con_su_porcentaje():
    ex, m = exporter()
    t = ex._render_eventos(m)
    assert "## 🎪 Para eventos y presencia de marca" in t
    assert "Asunción** 563 (22 %)" in t and "Ciudad del Este** 143 (5 %)" in t


def test_tabla_por_modelo_con_perfil_propio_o_de_la_marca():
    ex, m = exporter()
    t = ex._render_eventos(m)
    assert "| Mitsubishi L200 | 937 (36 %) | 35-44 | Masculino 85 % | propio |" in t
    assert "| Mitsubishi Eclipse Cross | 148 (6 %) | 25-34 | Masculino 72 % | propio |" in t
    assert "| Mitsubishi Mirage |" in t and "perfil de la marca" in t.split("| Mitsubishi Mirage |")[1].split("\n")[0]


def test_dice_con_claridad_lo_que_no_se_mide():
    ex, m = exporter()
    t = ex._render_eventos(m)
    assert "Qué les gusta (deporte, música, comunidad): hoy no se mide" in t
    assert "Meta dejó de entregar" in t and "pregunta de opciones" in t
    assert "financiación en cuotas (53 %)" in t and "no lo que les gusta" in t   # los temas de los anuncios, dichos como lo que son


def test_mitsubishi_enlaza_su_formulario_de_intereses_y_las_otras_marcas_no():
    ex, m = exporter()
    assert "[[🧪 Formulario de intereses — Mitsubishi 2026-10]]" in ex._render_eventos(m)
    otra = marca(nombre="Jetour")
    assert "Formulario de intereses" not in ex._render_eventos(otra)


def test_solo_va_en_la_ficha_de_marca_y_si_hay_datos():
    ex, m = exporter()
    assert ex._render_eventos(modelo("L200", "35-44", "Masculino", 85, "modelo", 1, 1)) == ""
    sin = marca(ciudades={})
    sin["real_leads"]["total_leads"] = 0
    assert ex._render_eventos(sin) == ""


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"OK: {len(pruebas)} pruebas")
