"""Compradores reales de Bitrix (ganados + Facturación) con lead de Meta. Datos inventados.

Corre con pytest o directo: venv/bin/python3 tests/test_compradores_bitrix.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.exporters.obsidian_exporter import ObsidianExporter  # noqa: E402
from src.generators import compradores_bitrix as CB  # noqa: E402


def negocio(brand, etapa, certeza, ad="a1", plat="ig", cuenta="madre", dias=20, campana="X50 FORM"):
    return {"brand": brand, "etapa": etapa, "certeza": certeza, "ad_id": ad, "platform": plat, "account_type": cuenta,
            "campaign": campana, "dias": dias, "fecha": "2026-09-01"}


# Contactos por edad y género de cada anuncio (desglose de Meta por anuncio)
DEMO = [{"ad_id": "a1", "age": "35-44", "gender": "male", "contactos": 30}, {"ad_id": "a1", "age": "25-34", "gender": "female", "contactos": 10},
        {"ad_id": "a2", "age": "65+", "gender": "male", "contactos": 5}, {"ad_id": "a2", "age": "45-54", "gender": "male", "contactos": 15}]


def test_la_consulta_no_trae_nombres_de_personas():
    assert "cliente" not in CB.SQL and "asesor_nombre" not in CB.SQL


def test_leer_usa_la_base_del_tablero_y_devuelve_las_filas():
    class R:
        returncode, stderr = 0, ""
        stdout = json.dumps([negocio("JETOUR", "facturacion", "telefono")])
    llamadas = []
    filas = CB.leer(lambda *a, **k: llamadas.append(a[0]) or R())
    assert filas[0]["brand"] == "JETOUR" and llamadas[0][:3] == ["docker", "exec", "-i"]


def test_solo_cuentan_los_cruces_seguros_y_facturacion_vale_como_compra():
    filas = [negocio("JETOUR", "concretada", "telefono", ad="a1", plat="ig", dias=10),
             negocio("JETOUR", "facturacion", "email", ad="a2", plat="fb", cuenta="asesor", dias=30),
             negocio("JETOUR", "facturacion", "posible"),
             negocio("JETOUR", "concretada", "sin_rastro"),
             negocio("GWM", "facturacion", "directa", ad="a1")]
    r = CB.resumir(filas, DEMO)
    j = r["marcas"]["JETOUR"]
    assert (j["negocios"], j["ganados"], j["facturacion"]) == (4, 2, 2)
    assert (j["con_meta"], j["con_meta_ganados"], j["con_meta_facturacion"], j["posibles"]) == (2, 1, 1, 1)
    assert j["plataforma"] == {"Instagram": 1, "Facebook": 1} and j["cuenta"] == {"Cuenta madre": 1, "Cuentas de asesores": 1}
    assert j["dias_mediana"] == 20.0
    assert r["total"]["con_meta"] == 3


def test_la_edad_de_cada_comprador_sale_de_su_anuncio():
    filas = [negocio("JETOUR", "concretada", "telefono", ad="a1"), negocio("JETOUR", "facturacion", "telefono", ad="a2")]
    j = CB.resumir(filas, DEMO)["marcas"]["JETOUR"]
    # a1: 75 % 35-44 y 25 % 25-34; a2: 25 % 65+ y 75 % 45-54 → cada comprador pesa 1
    assert j["edad_estimada"]["35-44"] == 37.5 and j["edad_estimada"]["45-54"] == 37.5
    assert j["edad_estimada"]["25-34"] == 12.5 and j["edad_estimada"]["65+"] == 12.5
    assert j["genero_estimado"] == {"Masculino": 87.5, "Femenino": 12.5}
    assert j["con_anuncio"] == 2


def persona_marca(nombre):
    return {"name": f"Comprador {nombre}", "segment": {"type": "brand", "name": nombre}}


def test_la_ficha_de_marca_muestra_sus_compradores_y_pide_15_para_un_perfil_propio():
    filas = [negocio("JETOUR", "concretada", "telefono", ad="a1")] * 3 + [negocio("SOUEAST", "facturacion", "telefono", ad="a1")] * 16
    ex = ObsidianExporter({})
    ex.compradores = CB.resumir(filas, DEMO)
    jetour = ex._render_compradores(persona_marca("Jetour"))
    assert "3 vinieron de un lead de Meta" in jetour and "pocos para un perfil propio de compra (3 de 15)" in jetour
    soueast = ex._render_compradores(persona_marca("Soueast"))
    assert "Edad estimada de quien compra:** 35-44: 75 %" in soueast
    assert ex._render_compradores({"segment": {"type": "model", "name": "Jetour X50"}}) == ""   # solo en la ficha de marca
    assert ex._render_compradores(persona_marca("XPeng")) == ""                                  # marca sin negocios


def test_la_nota_resume_todas_las_marcas():
    filas = [negocio("JETOUR", "concretada", "telefono")] * 2 + [negocio("SOUEAST", "facturacion", "telefono")] * 16
    texto = CB.nota(CB.resumir(filas, DEMO), "2026-10-14")
    assert "# 🧾 Compradores reales (Bitrix)" in texto
    assert "| Soueast | 16 (0 + 16) | 16 (100 %) |" in texto
    assert "pocos (2 de 15)" in texto


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"OK: {len(pruebas)} pruebas")
