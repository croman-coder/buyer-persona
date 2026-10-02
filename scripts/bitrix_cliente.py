"""Cliente mínimo de Bitrix24 por webhook, con la política de cuota que ya está probada en el
Dashboard Comercial (santa-rosa-dashboard-bitrix, api/_bitrix-directo.js). Es el MISMO portal y
la MISMA cuota: los dos lados tienen que reaccionar igual o uno tumba al otro.

Lo que Bitrix hace y acá se contempla:
- 503 (QUERY_LIMIT_EXCEEDED, cortes) y errores de red son transitorios: la misma llamada un
  segundo después suele andar. Se reintenta hasta 3 veces con espera 0,5 / 1 / 2 s. Sin esto,
  un pico de cuota a mitad de una paginación de ~377 páginas abortaba el pedido entero
  (tableros-semanales, lunes 7 y 14 de septiembre de 2026, 08:2x: hora pico del portal).
- 429 OPERATION_TIME_LIMIT es la ventana de cómputo de 10 minutos agotada: volver a pegar en
  segundos solo alarga el bloqueo. Se espera hasta `time.operating_reset_at` (máx. 11 min),
  UNA vez, y si sigue bloqueado se aborta con CuotaAgotada.
- La paginación va por `batch`: 50 páginas encadenadas por `$result[pN][49][ID]` en UN pedido.
  Con 18.800 leads en 90 días son 8 pedidos en vez de 377: a página por pedido, este script
  solo consumía los 2 pedidos/s del portal durante 2 minutos y cualquier otra app (dashboard,
  callbot, tasación) lo empujaba al 503 — o él a ellas. Pausa de 120 ms entre batches.

Los mensajes de error nunca llevan la URL: el webhook lleva el token adentro y `requests` lo
mete en su HTTPError (así quedó guardado en el último error del cron de Hermes).
"""
from __future__ import annotations

import sys
import time
from urllib.parse import urlencode

import requests

MAX_INTENTOS = 3            # reintentos además del primer intento (mismo valor que el dashboard)
PAUSA_ENTRE_PAGINAS = 0.12  # segundos
ESPERA_MIN_RESET = 5        # segundos, si el 429 no trae `operating_reset_at`
ESPERA_MAX_RESET = 660      # 11 min: la ventana de Bitrix es de 10
PAGINAS_POR_BATCH = 50      # máximo de comandos por batch en Bitrix
FILAS_POR_PAGINA = 50       # tamaño fijo de página de los métodos *.list


class CuotaAgotada(RuntimeError):
    """OPERATION_TIME_LIMIT que persiste después de esperar al reset."""


def _log_stderr(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _cuerpo(r) -> dict | None:
    try:
        c = r.json()
    except ValueError:
        return None
    return c if isinstance(c, dict) else None


def _codigo(cuerpo: dict | None) -> str:
    return str((cuerpo or {}).get("error") or "") if cuerpo else "sin cuerpo JSON"


def llamar(base: str, metodo: str, params: dict | None = None, *, timeout: int = 45,
           post=requests.post, dormir=time.sleep, ahora=time.time, log=_log_stderr) -> dict:
    """POST a `<base>/<metodo>.json`. Devuelve el JSON entero (con `result` y `time`)."""
    url = f"{base.rstrip('/')}/{metodo}.json"
    espero_reset = False
    intento = 0
    while True:
        try:
            r = post(url, json=params or {}, timeout=timeout)
        except requests.RequestException as exc:            # red: reset, timeout, DNS — no HTTP
            if intento < MAX_INTENTOS:
                log(f"{metodo}: sin respuesta ({type(exc).__name__}), reintento {intento + 1}")
                dormir(0.5 * 2 ** intento)
                intento += 1
                continue
            raise RuntimeError(f"{metodo}: sin respuesta tras {MAX_INTENTOS + 1} intentos ({type(exc).__name__})") from None
        cuerpo = _cuerpo(r)
        codigo = _codigo(cuerpo)
        if r.status_code == 429 and codigo in ("OPERATION_TIME_LIMIT", "", "sin cuerpo JSON"):
            if espero_reset:
                raise CuotaAgotada(f"{metodo}: cuota de cómputo de Bitrix agotada (OPERATION_TIME_LIMIT) incluso después de esperar al reset")
            reset = (cuerpo or {}).get("time", {}).get("operating_reset_at") if cuerpo else None
            try:
                espera = float(reset) - ahora()
            except (TypeError, ValueError):
                espera = ESPERA_MIN_RESET
            espera = min(max(espera, ESPERA_MIN_RESET), ESPERA_MAX_RESET)
            log(f"{metodo}: OPERATION_TIME_LIMIT, espero {espera:.0f} s al reset de la ventana")
            dormir(espera)
            espero_reset = True
            continue
        if r.status_code == 429 or r.status_code >= 500:
            if intento < MAX_INTENTOS:
                log(f"{metodo}: HTTP {r.status_code} ({codigo}), reintento {intento + 1}")
                dormir(0.5 * 2 ** intento)
                intento += 1
                continue
            raise RuntimeError(f"{metodo}: HTTP {r.status_code} ({codigo}) tras {MAX_INTENTOS + 1} intentos")
        if r.status_code != 200:
            raise RuntimeError(f"{metodo}: HTTP {r.status_code} ({codigo})")
        if cuerpo is None:
            raise RuntimeError(f"{metodo}: respuesta sin JSON")
        if "error" in cuerpo:
            raise RuntimeError(f"{metodo}: {cuerpo.get('error_description') or cuerpo['error']}")
        return cuerpo


def _aplanar(params: dict) -> list[tuple[str, str]]:
    """{"select": ["ID"], "filter": {">ID": 0}} → [("select[0]", "ID"), ("filter[>ID]", "0")], en orden."""
    plano: list[tuple[str, str]] = []

    def caminar(prefijo: str, v) -> None:
        if isinstance(v, dict):
            for k, x in v.items():
                caminar(f"{prefijo}[{k}]", x)
        elif isinstance(v, (list, tuple)):
            for i, x in enumerate(v):
                caminar(f"{prefijo}[{i}]", x)
        else:
            plano.append((prefijo, str(v)))

    for k, v in params.items():
        caminar(k, v)
    return plano


def _comando(metodo: str, params: dict, desde_id: str) -> str:
    """`crm.lead.list?select[0]=ID&filter[>ID]=<desde>&order[ID]=ASC&start=-1` (paginación rápida)."""
    base = {k: v for k, v in params.items() if k != "filter"}
    filtro = {k: v for k, v in params.get("filter", {}).items() if k != ">ID"}
    plano = _aplanar(base) + _aplanar({"filter": filtro}) + [("filter[>ID]", desde_id), ("order[ID]", "ASC"), ("start", "-1")]
    return f"{metodo}?{urlencode(plano)}"


def listar_todo(base: str, metodo: str, params: dict, *, max_paginas: int = 1000, pausa: float = PAUSA_ENTRE_PAGINAS,
                dormir=time.sleep, **kw) -> list[dict]:
    """Todas las filas de un método de lista, de a 50 páginas por pedido (`batch`), cada página
    arrancando del último ID de la anterior (`$result[pN][49][ID]`). Una página corta termina
    el recorrido: lo que Bitrix haya devuelto para las siguientes no se mira, porque la
    referencia `$result[...][49]` no existe y puede traer error o filas repetidas."""
    filas: list[dict] = []
    vistos: set[str] = set()
    ultimo_id = 0
    paginas_pedidas = 0
    while paginas_pedidas < max_paginas:
        cmd = {f"p{i}": _comando(metodo, params, str(ultimo_id) if i == 0 else f"$result[p{i - 1}][{FILAS_POR_PAGINA - 1}][ID]")
               for i in range(PAGINAS_POR_BATCH)}
        res = llamar(base, "batch", {"halt": 0, "cmd": cmd}, dormir=dormir, **kw).get("result") or {}
        paginas = res.get("result") if isinstance(res.get("result"), dict) else {}
        errores = res.get("result_error") if isinstance(res.get("result_error"), dict) else {}
        for i in range(PAGINAS_POR_BATCH):
            clave = f"p{i}"
            paginas_pedidas += 1
            if clave in errores:
                e = errores[clave] if isinstance(errores[clave], dict) else {}
                raise RuntimeError(f"{metodo}: página {i}: {e.get('error_description') or e.get('error') or errores[clave]}")
            lote = paginas.get(clave) or []
            for fila in lote:
                if str(fila.get("ID")) not in vistos:      # defensa contra repetidos si la referencia no resolvió
                    vistos.add(str(fila.get("ID")))
                    filas.append(fila)
            if len(lote) < FILAS_POR_PAGINA:
                return filas
            ultimo_id = int(lote[-1]["ID"])
        dormir(pausa)
    raise RuntimeError(f"{metodo}: más de {max_paginas} páginas, corto por las dudas")
