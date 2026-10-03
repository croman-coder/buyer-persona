"""El dolor de autonomía/carga es solo de los 100 % eléctricos.

Corre con pytest o directo: venv/bin/python3 tests/test_dolores.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.generators.ad_copy_analyzer import analyze_brand  # noqa: E402
from src.generators.persona_generator import es_electrico, sin_dolor_de_carga  # noqa: E402

DOLOR = "Ansiedad de autonomía/carga: evalúa km reales y tiempo de carga antes de decidir"


def test_equipamiento_y_capacidad_de_carga_no_son_electrico():
    ads = [{"title": "Duster", "body": "Asientos eléctricos, espejos eléctricos, gran capacidad de carga y 900 km de autonomía"}] * 3
    r = analyze_brand(ads) or {}
    assert DOLOR not in r.get("pains", [])


def test_un_electrico_sigue_teniendo_el_dolor():
    ads = [{"title": "C10", "body": "SUV 100% eléctrico con carga rápida y 420 km de autonomía"}] * 3
    assert DOLOR in (analyze_brand(ads) or {}).get("pains", [])


def test_filtro_por_catalogo():
    dolores = [DOLOR, "Compara la cuota mensual"]
    assert sin_dolor_de_carga({"type": "model", "name": "Renault Duster"}, dolores) == ["Compara la cuota mensual"]
    assert sin_dolor_de_carga({"type": "model", "name": "Renew Renault"}, dolores) == ["Compara la cuota mensual"]
    assert sin_dolor_de_carga({"type": "model", "name": "Leapmotor C10"}, dolores) == dolores
    assert es_electrico({"type": "brand", "name": "Zeekr"}) and not es_electrico({"type": "brand", "name": "GWM"})


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in pruebas:
        t()
        print("ok ", t.__name__)
    print(f"{len(pruebas)} pruebas OK")
