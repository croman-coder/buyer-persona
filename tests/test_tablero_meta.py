"""Publicación del cruce ERP × Meta en el tablero de Meta (ROI Pauta). Todos los datos son inventados.

Corre con pytest o directo: venv/bin/python3 tests/test_tablero_meta.py
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.exporters.tablero_meta import publicar_ventas_erp, script_psql  # noqa: E402

ATRIB = [{"meta_lead_id": "111", "fecha_lead": "2026-08-01", "fecha_venta": "2026-08-20", "marca": "SOUEAST",
          "modelo": "S07, 1.5T", "evidencia": "contacto", "dias": 19},
         {"meta_lead_id": "222", "fecha_lead": "2026-08-05", "fecha_venta": "2026-08-25", "marca": "XPENG",
          "modelo": None, "evidencia": "nombre", "dias": 20}]
CRUCE = {"ventas_desde": "2026-08-07", "ventas_hasta": "2026-09-11", "ventas_evaluadas": 491}


def _psql_falso(conteo="0", falla=None):
    llamadas = []

    def ejecutar(cmd, input="", **kw):
        llamadas.append((cmd, input))
        if falla and falla in input:
            return SimpleNamespace(returncode=1, stdout="", stderr="ERROR: relation does not exist")
        return SimpleNamespace(returncode=0, stdout=conteo + "\n" if input.startswith("SELECT count") else "", stderr="")
    return ejecutar, llamadas


def test_script_reemplaza_solo_las_ventas_evaluadas():
    sql = script_psql(ATRIB, "2026-08-07", "2026-09-11", 491)
    assert sql.startswith("BEGIN;") and sql.rstrip().endswith("COMMIT;")
    assert "DELETE FROM public.erp_ventas_meta WHERE fecha_venta >= DATE '2026-08-07';" in sql
    assert '111,2026-08-01,2026-08-20,SOUEAST,"S07, 1.5T",contacto,19\n' in sql
    assert "222,2026-08-05,2026-08-25,XPENG,,nombre,20\n" in sql, "sin modelo: NULL"
    assert "\n\\.\n" in sql and "DATE '2026-09-11', 491" in sql


def test_script_rechaza_fechas_raras():
    for malo in ("2026-08-07'; DROP TABLE x; --", "ayer"):
        try:
            script_psql(ATRIB, malo, "2026-09-11", 491)
        except ValueError:
            continue
        raise AssertionError(malo)


def test_publica_con_docker_exec_y_psql():
    ejecutar, llamadas = _psql_falso(conteo="1")
    r = publicar_ventas_erp(ATRIB, CRUCE, ejecutar=ejecutar)
    assert r == {"publicado": True, "filas": 2, "antes": 1}
    cmd, entrada = llamadas[1]
    assert cmd[:4] == ["docker", "exec", "-i", "bitrix-supabase-db"] and "psql" in cmd
    assert "COMMIT;" in entrada


def test_freno_si_el_cruce_trae_mucho_menos_que_lo_que_habia():
    ejecutar, llamadas = _psql_falso(conteo="40")
    r = publicar_ventas_erp(ATRIB, CRUCE, ejecutar=ejecutar)
    assert r["publicado"] is False and "freno" in r["motivo"]
    assert len(llamadas) == 1, "no se escribe nada"


def test_un_error_de_la_base_no_tumba_el_pipeline():
    ejecutar, _ = _psql_falso(falla="SELECT count")
    r = publicar_ventas_erp(ATRIB, CRUCE, ejecutar=ejecutar)
    assert r["publicado"] is False and "relation does not exist" in r["motivo"]


def test_sin_cruce_no_hace_nada():
    ejecutar, llamadas = _psql_falso()
    assert publicar_ventas_erp([], {}, ejecutar=ejecutar)["publicado"] is False
    assert llamadas == []


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in pruebas:
        t()
        print("ok ", t.__name__)
    print(f"{len(pruebas)} pruebas OK")
