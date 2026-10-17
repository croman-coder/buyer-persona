"""
Publica en el tablero de Meta (dashboardmeta.santarosa.lat, menú ROI Pauta) qué formulario de Meta terminó en una
venta del ERP, según el cruce de ``src/generators/ventas_meta.py`` (Croman, 06-10-2026).

Escribe en la base del tablero (Supabase propio del servidor, contenedor ``bitrix-supabase-db``) con ``docker exec`` y
``psql``: sin claves, igual que la copia de los contactos de Renew. Solo funciona donde está ese contenedor (el
servidor); en la notebook devuelve «no publicado» y el pipeline sigue.

Qué se guarda (tabla ``erp_ventas_meta``): el ID de Meta del lead, la fecha del lead, la fecha, marca y modelo de la
venta, si coincidió por teléfono/mail («contacto», segura) o por nombre («nombre», probable) y los días entre uno y
otra. Ningún nombre, teléfono ni mail. Cada corrida reemplaza las ventas que evaluó (desde ``ventas_desde``) y
conserva las anteriores: Meta borra los leads a los 90 días y el cruce ya no las podría volver a encontrar.
"""

from __future__ import annotations

import csv
import io
import os
import re
import shutil
import subprocess
from typing import Any, Callable

CONTENEDOR = os.environ.get("TABLERO_DB_CONTENEDOR", "bitrix-supabase-db")
PSQL = ["psql", "-U", "postgres", "-d", "postgres", "-v", "ON_ERROR_STOP=1", "-q", "-At"]
COLUMNAS = ("meta_lead_id", "fecha_lead", "fecha_venta", "marca", "modelo", "evidencia", "dias")
# Si el cruce trae menos de la mitad de las ventas que ya había en las mismas fechas, es más probable una lectura
# rota (Meta o el ERP) que la realidad: no se pisa.
FRENO_PARTE, FRENO_MIN = 0.5, 10
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _fecha(x: Any) -> str:
    s = str(x or "")
    if not FECHA.match(s):
        raise ValueError(f"fecha inválida: {s[:30]!r}")
    return s


def script_psql(atribuciones: list[dict[str, Any]], ventas_desde: str, ventas_hasta: str, ventas_evaluadas: int) -> str:
    """El script de psql que reemplaza, en una transacción, las ventas evaluadas desde ``ventas_desde``."""
    desde, hasta, evaluadas = _fecha(ventas_desde), _fecha(ventas_hasta), int(ventas_evaluadas)
    datos = io.StringIO()
    w = csv.writer(datos, lineterminator="\n")
    for a in atribuciones:
        w.writerow(["" if a.get(c) is None else a.get(c) for c in COLUMNAS])   # vacío sin comillas = NULL
    return "\n".join([
        "BEGIN;",
        "CREATE TEMP TABLE paso (meta_lead_id text, fecha_lead date, fecha_venta date, marca text, modelo text, "
        "evidencia text, dias integer) ON COMMIT DROP;",
        f"\\copy paso ({', '.join(COLUMNAS)}) from stdin with (format csv)",
        datos.getvalue() + "\\.",
        f"DELETE FROM public.erp_ventas_meta WHERE fecha_venta >= DATE '{desde}';",
        f"INSERT INTO public.erp_ventas_meta ({', '.join(COLUMNAS)}) SELECT {', '.join(COLUMNAS)} FROM paso;",
        "INSERT INTO public.erp_ventas_meta_estado (id, actualizado_at, ventas_desde, ventas_hasta, ventas_evaluadas, filas)",
        f"  VALUES (1, now(), DATE '{desde}', DATE '{hasta}', {evaluadas}, (SELECT count(*) FROM public.erp_ventas_meta))",
        "  ON CONFLICT (id) DO UPDATE SET actualizado_at = EXCLUDED.actualizado_at, ventas_desde = EXCLUDED.ventas_desde,",
        "    ventas_hasta = EXCLUDED.ventas_hasta, ventas_evaluadas = EXCLUDED.ventas_evaluadas, filas = EXCLUDED.filas;",
        "COMMIT;",
        "",
    ])


def _psql(ejecutar: Callable[..., Any], entrada: str) -> str:
    r = ejecutar(["docker", "exec", "-i", CONTENEDOR, *PSQL], input=entrada, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or f"psql salió con {r.returncode}").strip()[:300])
    return r.stdout or ""


def publicar_ventas_erp(atribuciones: list[dict[str, Any]], cruce: dict[str, Any],
                        ejecutar: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Publica las atribuciones de una corrida del cruce. Nunca lanza: devuelve qué hizo, para el log."""
    if not cruce or not cruce.get("ventas_desde"):
        return {"publicado": False, "motivo": "sin datos del cruce"}
    if ejecutar is None:
        if shutil.which("docker") is None:
            return {"publicado": False, "motivo": "acá no está la base del tablero (solo se publica en el servidor)"}
        ejecutar = subprocess.run
    try:
        desde = _fecha(cruce["ventas_desde"])
        antes = int((_psql(ejecutar, f"SELECT count(*) FROM public.erp_ventas_meta WHERE fecha_venta >= DATE '{desde}';")
                     .strip() or "0"))
        if antes >= FRENO_MIN and len(atribuciones) < antes * FRENO_PARTE:
            return {"publicado": False,
                    "motivo": f"freno: el cruce trajo {len(atribuciones)} ventas contra {antes} que ya había en las mismas fechas"}
        _psql(ejecutar, script_psql(atribuciones, desde, cruce["ventas_hasta"], cruce["ventas_evaluadas"]))
        return {"publicado": True, "filas": len(atribuciones), "antes": antes}
    except Exception as exc:  # el tablero no debe tumbar el pipeline
        return {"publicado": False, "motivo": str(exc)[:300]}
