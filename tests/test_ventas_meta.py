"""Cruce de ventas con leads de Meta, con claves cifradas. Todos los datos son inventados.

Corre con pytest o directo: venv/bin/python3 tests/test_ventas_meta.py
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.generators.ventas_meta import (  # noqa: E402
    clave_de_mail, claves_de_lead, claves_de_telefono, claves_de_venta, cruzar, es_cuenta_de_asesor, nota)

CAMPANAS = [
    {"campaign_id": "1", "campaign_name": "[LEADS] SOUEAST 2026 ASU", "account": "Soueast", "account_name": "Soueast Paraguay", "spend": "300"},
    {"campaign_id": "2", "campaign_name": "NUEVA PAUTA CDE 1", "account": "Renault", "account_name": "Renault Santa Rosa Paraguay", "spend": "200"},
    {"campaign_id": "3", "campaign_name": "PAUTA ASESOR", "account": "Soueast", "account_name": "MATIAS FLORENTIN SOUEAST", "spend": "50"},
]


def _lead(nombre, tel, mail, fecha, campana, marca="Soueast", organico=False):
    campos = [{"name": "full_name", "values": [nombre]}, {"name": "phone_number", "values": [tel]},
              {"name": "email", "values": [mail]}, {"name": "modelo_de_interés", "values": ["S07"]}]
    return claves_de_lead({"created_time": f"{fecha}T10:00:00+0000", "field_data": campos, "campaign_id": campana,
                           "campaign_name": f"C{campana}", "is_organic": organico}, marca)


def _ventas(filas):
    df = pd.DataFrame([{"Fecha": pd.Timestamp(f), "marca": m, "producto": f"{m} X", "tipo_comprador": t,
                        "Cliente": c, "Teléfonos": tel, "E-Mail": mail} for f, m, c, tel, mail, t in filas])
    return claves_de_venta(df)


def test_telefonos_y_mails_en_distintos_formatos():
    assert claves_de_telefono("0981 154 994") == claves_de_telefono("+595 981154994")
    assert claves_de_telefono("021 123456") == claves_de_telefono("+595 21 123456")
    assert clave_de_mail("Ana@Mail.com ") == clave_de_mail("ana@mail.com") and clave_de_mail("sin mail") is None


def test_las_claves_no_guardan_el_dato_crudo():
    texto = repr(_lead("Ana Pérez", "0981111222", "ana@x.com", "2026-08-01", "1")) + repr(
        _ventas([("2026-08-20", "Soueast", "ANA MARIA PEREZ", "0981111222", "ana@x.com", "persona")]))
    for crudo in ("Ana", "ANA", "PEREZ", "0981", "111222", "ana@x.com"):
        assert crudo not in texto, crudo


def test_cuenta_de_asesor():
    assert es_cuenta_de_asesor("CARMEN FRANCO | GWM CDE", "GWM")
    assert es_cuenta_de_asesor("SOUEAST Meta Ads - Cuenta Asesores", "Soueast")
    assert not es_cuenta_de_asesor("GWM Paraguay", "GWM") and not es_cuenta_de_asesor("Renault Santa Rosa Paraguay", "Renault")


def test_cruce():
    leads = [_lead("Ana Pérez", "0981111222", "", "2026-08-01", "1"),       # por teléfono, campaña de la marca
             _lead("Bruno Gómez", "", "", "2026-08-05", "2"),               # por nombre, campaña de Renault
             _lead("Carla Díaz", "0981333444", "", "2026-08-10", "3"),      # por teléfono, cuenta de asesor
             _lead("Juan Benítez", "", "", "2026-08-10", "1"),              # nombre que está en dos ventas: ambiguo
             _lead("Viejo Lead", "0981999888", "", "2026-01-01", "1")]      # más de 120 días antes: no cuenta
    ventas = _ventas([("2026-08-20", "Soueast", "ANA MARIA PEREZ", "+595 981 111222", "", "persona"),
                      ("2026-08-25", "Soueast", "BRUNO ALEJANDRO GOMEZ ROJAS", "", "", "persona"),
                      ("2026-09-01", "Soueast", "CARLA DIAZ", "0981 333 444", "", "persona"),
                      ("2026-09-02", "Soueast", "JUAN BENITEZ", "", "", "persona"),
                      ("2026-09-03", "Soueast", "JUAN CARLOS BENITEZ", "", "", "persona"),
                      ("2026-09-04", "Soueast", "VIEJO LEAD", "0981999888", "", "persona"),
                      ("2026-09-05", "Soueast", "SUBCONCESIONARIO SA", "", "", "revendedor")])
    r = cruzar(ventas, leads, CAMPANAS)
    m = r["por_marca"]["Soueast"]
    assert (m["ventas"], m["con_meta"], m["por_contacto"], m["por_nombre"], m["ambiguas"]) == (6, 3, 2, 1, 2)
    assert m["origen"] == {"Campaña de la marca": 1, "Campaña de otra marca": 1, "Campaña de un asesor": 1}
    assert r["entre_marcas"] == [{"campana_de": "Renault", "venta_de": "Soueast", "ventas": 1}]
    assert {c["campana"]: c["costo_por_venta"] for c in r["campanas"]} == {
        "[LEADS] SOUEAST 2026 ASU": 300.0, "NUEVA PAUTA CDE 1": 200.0, "PAUTA ASESOR": 50.0}
    assert r["dias"]["mediana"] == 20
    texto = nota(r)
    assert "Por marca" in texto and "Soueast" in texto and "ANA" not in texto and "BRUNO" not in texto


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in pruebas:
        t()
        print("ok ", t.__name__)
    print(f"{len(pruebas)} pruebas OK")
