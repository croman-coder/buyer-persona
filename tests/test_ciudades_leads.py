"""Ciudades de los formularios de Meta: una misma ciudad escrita distinto cuenta como una. Datos inventados.

Caso real del 16-10-2026: en Mitsubishi salían «Asunción» (497) y «Asuncion» (66) por separado, y el mapa para eventos
subestimaba a la ciudad principal.

Corre con pytest o directo: venv/bin/python3 tests/test_ciudades_leads.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.connectors.meta_ads_connector import normalizar_ciudad  # noqa: E402


def test_con_y_sin_tilde_es_la_misma_ciudad():
    assert normalizar_ciudad("Asuncion") == "Asunción"
    assert normalizar_ciudad("asunción") == "Asunción"
    assert normalizar_ciudad("  ASUNCIÓN ") == "Asunción"
    assert normalizar_ciudad("Capiata") == "Capiatá" and normalizar_ciudad("lambare") == "Lambaré"
    assert normalizar_ciudad("encarnacion") == "Encarnación"


def test_ciudades_de_varias_palabras_y_conectores():
    assert normalizar_ciudad("ciudad del este") == "Ciudad del Este"
    assert normalizar_ciudad("Fernando De La Mora") == "Fernando de la Mora"
    assert normalizar_ciudad("pedro juan caballero") == "Pedro Juan Caballero"
    assert normalizar_ciudad("Mariano  Roque   Alonso") == "Mariano Roque Alonso"


def test_una_ciudad_que_no_conocemos_se_deja_prolija_sin_inventar():
    assert normalizar_ciudad("san estanislao") == "San Estanislao"
    assert normalizar_ciudad("san josé de los arroyos") == "San José de los Arroyos"      # no se le sacan las tildes que ya trae
    assert normalizar_ciudad("Ñemby") == "Ñemby" and normalizar_ciudad("nemby") == "Ñemby"
    assert normalizar_ciudad("") == "" and normalizar_ciudad(None) == ""


def test_el_generador_suma_las_variantes_en_archivos_ya_guardados():
    from src.generators.persona_generator import PersonaGenerator
    r = PersonaGenerator._con_ciudades_unificadas({"Mitsubishi": {"total_leads": 100, "city": {"Asunción": 497, "Luque": 93, "Asuncion": 66, "Ciudad del Este": 143}},
                                                   "Zeekr": {"total_leads": 5}})
    assert r["Mitsubishi"]["city"] == {"Asunción": 563, "Ciudad del Este": 143, "Luque": 93}
    assert r["Mitsubishi"]["total_leads"] == 100 and r["Zeekr"] == {"total_leads": 5}


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"OK: {len(pruebas)} pruebas")
