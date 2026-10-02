"""Pruebas del cliente de Bitrix (sin red): venv/bin/python -m unittest scripts/test_bitrix_cliente.py

Reproducen lo que tumbó `tableros-semanales` los lunes 7 y 14 de septiembre de 2026: un 503 de
Bitrix a mitad de las ~377 páginas de `crm.lead.list` abortaba el tablero entero, sin reintento
y con la URL del webhook (token incluido) dentro del mensaje de error que Hermes guarda.
"""
import unittest

import requests

from bitrix_cliente import CuotaAgotada, llamar, listar_todo

BASE = "https://portal.bitrix24.es/rest/1/secretoxyz"


class Respuesta:
    def __init__(self, status, cuerpo=None):
        self.status_code = status
        self._cuerpo = cuerpo

    def json(self):
        if self._cuerpo is None:
            raise ValueError("sin JSON")
        return self._cuerpo


class Fakes:
    """`post` devuelve las respuestas en orden (o lanza si el elemento es una excepción); registra todo."""

    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.pedidos = []
        self.dormido = []
        self.log = []

    def post(self, url, json=None, timeout=None):
        self.pedidos.append((url, json))
        r = self.respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def dormir(self, s):
        self.dormido.append(round(s, 3))

    def kw(self, **extra):
        return {"post": self.post, "dormir": self.dormir, "log": self.log.append, "ahora": lambda: 1_000.0, **extra}


class LlamarTest(unittest.TestCase):
    def test_ok_directo(self):
        f = Fakes([Respuesta(200, {"result": [1]})])
        self.assertEqual(llamar(BASE, "crm.status.list", {"a": 1}, **f.kw()), {"result": [1]})
        self.assertEqual(f.pedidos, [(f"{BASE}/crm.status.list.json", {"a": 1})])
        self.assertEqual(f.dormido, [])

    def test_503_transitorio_se_reintenta_con_backoff(self):
        f = Fakes([Respuesta(503, {"error": "QUERY_LIMIT_EXCEEDED"}), Respuesta(503, None), Respuesta(200, {"result": []})])
        self.assertEqual(llamar(BASE, "crm.lead.list", **f.kw()), {"result": []})
        self.assertEqual(f.dormido, [0.5, 1.0])
        self.assertEqual(len(f.pedidos), 3)
        self.assertTrue(any("503" in l and "QUERY_LIMIT_EXCEEDED" in l for l in f.log))

    def test_cuatro_fallos_seguidos_abortan_sin_revelar_la_url(self):
        f = Fakes([Respuesta(503, None)] * 4)
        with self.assertRaises(RuntimeError) as cm:
            llamar(BASE, "crm.lead.list", **f.kw())
        self.assertNotIn("secretoxyz", str(cm.exception))
        self.assertNotIn(BASE, str(cm.exception))
        self.assertIn("503", str(cm.exception))
        self.assertEqual(f.dormido, [0.5, 1.0, 2.0])

    def test_error_de_red_tambien_se_reintenta(self):
        f = Fakes([requests.ConnectionError("reset"), requests.Timeout("t"), Respuesta(200, {"result": 1})])
        self.assertEqual(llamar(BASE, "x", **f.kw())["result"], 1)
        self.assertEqual(f.dormido, [0.5, 1.0])

    def test_429_operation_time_limit_espera_al_reset_y_no_martilla(self):
        # Bitrix manda `operating_reset_at` (epoch): se espera hasta ahí (con tope), UNA vez, y se reintenta.
        f = Fakes([Respuesta(429, {"error": "OPERATION_TIME_LIMIT", "time": {"operating": 480.1, "operating_reset_at": 1_000 + 300}}), Respuesta(200, {"result": 2})])
        self.assertEqual(llamar(BASE, "x", **f.kw())["result"], 2)
        self.assertEqual(f.dormido, [300.0])
        # si vuelve a pasar tras esperar, no tiene sentido insistir
        f = Fakes([Respuesta(429, {"error": "OPERATION_TIME_LIMIT", "time": {"operating_reset_at": 1_000 + 30}})] * 2)
        with self.assertRaises(CuotaAgotada):
            llamar(BASE, "x", **f.kw())
        self.assertEqual(f.dormido, [30.0])
        # sin reset conocido: espera mínima; reset absurdo: tope
        f = Fakes([Respuesta(429, {"error": "OPERATION_TIME_LIMIT"}), Respuesta(200, {"result": 1})])
        llamar(BASE, "x", **f.kw())
        self.assertEqual(f.dormido, [5.0])
        f = Fakes([Respuesta(429, {"error": "OPERATION_TIME_LIMIT", "time": {"operating_reset_at": 1_000 + 99_999}}), Respuesta(200, {"result": 1})])
        llamar(BASE, "x", **f.kw())
        self.assertEqual(f.dormido, [660.0])

    def test_429_de_otro_tipo_es_transitorio(self):
        f = Fakes([Respuesta(429, {"error": "QUERY_LIMIT_EXCEEDED"}), Respuesta(200, {"result": 1})])
        self.assertEqual(llamar(BASE, "x", **f.kw())["result"], 1)
        self.assertEqual(f.dormido, [0.5])

    def test_error_logico_de_bitrix_no_se_reintenta_ni_revela_la_url(self):
        f = Fakes([Respuesta(200, {"error": "INVALID_TOKEN", "error_description": "Token inválido"})])
        with self.assertRaises(RuntimeError) as cm:
            llamar(BASE, "x", **f.kw())
        self.assertEqual(str(cm.exception), "x: Token inválido")
        self.assertEqual(len(f.pedidos), 1)
        f = Fakes([Respuesta(404, {"error": "ERROR_METHOD_NOT_FOUND"})])
        with self.assertRaises(RuntimeError) as cm:
            llamar(BASE, "x", **f.kw())
        self.assertNotIn("secretoxyz", str(cm.exception))
        self.assertEqual(len(f.pedidos), 1)


class ListarTodoTest(unittest.TestCase):
    """Paginación por `batch`: 50 páginas por pedido, encadenadas con `$result[pN][49][ID]`."""

    @staticmethod
    def pagina(desde, n=50):
        return [{"ID": str(i)} for i in range(desde, desde + n)]

    @staticmethod
    def batch(paginas: dict, errores: dict | None = None):
        return Respuesta(200, {"result": {"result": paginas, "result_error": errores or [], "result_total": [], "result_next": [], "result_time": {}}})

    def test_un_batch_encadena_50_paginas_por_id(self):
        f = Fakes([self.batch({"p0": self.pagina(1), "p1": self.pagina(51), "p2": [{"ID": "101"}]})])
        filas = listar_todo(BASE, "crm.lead.list", {"select": ["ID", "SOURCE_ID"], "filter": {">=DATE_CREATE": "2026-06-21"}}, **f.kw())
        self.assertEqual([r["ID"] for r in filas], [str(i) for i in range(1, 102)])
        self.assertEqual(len(f.pedidos), 1)
        url, cuerpo = f.pedidos[0]
        self.assertEqual(url, f"{BASE}/batch.json")
        self.assertEqual(cuerpo["halt"], 0)
        self.assertEqual(len(cuerpo["cmd"]), 50)
        self.assertEqual(cuerpo["cmd"]["p0"], "crm.lead.list?select%5B0%5D=ID&select%5B1%5D=SOURCE_ID&filter%5B%3E%3DDATE_CREATE%5D=2026-06-21&filter%5B%3EID%5D=0&order%5BID%5D=ASC&start=-1")
        self.assertIn("filter%5B%3EID%5D=%24result%5Bp0%5D%5B49%5D%5BID%5D", cuerpo["cmd"]["p1"])
        self.assertIn("filter%5B%3EID%5D=%24result%5Bp48%5D%5B49%5D%5BID%5D", cuerpo["cmd"]["p49"])
        self.assertEqual(f.dormido, [])   # un solo pedido: sin pausa

    def test_varios_batches_siguen_desde_el_ultimo_id_con_pausa(self):
        lleno = {f"p{i}": self.pagina(1 + 50 * i) for i in range(50)}          # 2500 filas, todas llenas
        f = Fakes([self.batch(lleno), self.batch({"p0": self.pagina(2501), "p1": self.pagina(2551, 3)})])
        filas = listar_todo(BASE, "crm.lead.list", {"select": ["ID"]}, **f.kw())
        self.assertEqual(len(filas), 2553)
        self.assertEqual(len(f.pedidos), 2)
        self.assertIn("filter%5B%3EID%5D=2500&", f.pedidos[1][1]["cmd"]["p0"])   # el segundo batch arranca del último ID real
        self.assertEqual(f.dormido, [0.12])

    def test_pagina_corta_termina_y_lo_que_venga_despues_se_ignora(self):
        # cuando p0 trae menos de 50, `$result[p0][49][ID]` no existe y Bitrix puede devolver
        # error o repetir filas en p1..p49: nada de eso se mira
        f = Fakes([self.batch({"p0": self.pagina(1, 7), "p1": self.pagina(1, 7)}, {"p1": {"error": "x", "error_description": "no resuelto"}})])
        self.assertEqual(len(listar_todo(BASE, "x", {}, **f.kw())), 7)

    def test_error_en_una_pagina_alcanzada_aborta_sin_url(self):
        f = Fakes([self.batch({"p0": self.pagina(1)}, {"p1": {"error": "QUERY_LIMIT_EXCEEDED", "error_description": "Too many requests"}})])
        with self.assertRaises(RuntimeError) as cm:
            listar_todo(BASE, "x", {}, **f.kw())
        self.assertEqual(str(cm.exception), "x: página 1: Too many requests")
        self.assertNotIn("secretoxyz", str(cm.exception))

    def test_un_503_del_batch_se_reintenta_y_no_tira_todo(self):
        f = Fakes([Respuesta(503, {"error": "QUERY_LIMIT_EXCEEDED"}), self.batch({"p0": self.pagina(1, 3)})])
        self.assertEqual(len(listar_todo(BASE, "x", {}, **f.kw())), 3)
        self.assertEqual(f.dormido, [0.5])

    def test_filas_repetidas_se_descartan(self):
        f = Fakes([self.batch({"p0": self.pagina(1), "p1": self.pagina(1, 3)})])
        self.assertEqual(len(listar_todo(BASE, "x", {}, **f.kw())), 50)

    def test_tope_de_batches(self):
        lleno = {f"p{i}": self.pagina(1 + 50 * i) for i in range(50)}
        f = Fakes([self.batch(lleno)] * 5)
        with self.assertRaises(RuntimeError) as cm:
            listar_todo(BASE, "x", {}, max_paginas=150, **f.kw())
        self.assertIn("150 páginas", str(cm.exception))
        self.assertEqual(len(f.pedidos), 3)

    def test_resultado_vacio_de_bitrix_como_lista(self):
        f = Fakes([Respuesta(200, {"result": {"result": [], "result_error": []}})])   # PHP: [] en vez de {}
        self.assertEqual(listar_todo(BASE, "x", {}, **f.kw()), [])


if __name__ == "__main__":
    unittest.main()
