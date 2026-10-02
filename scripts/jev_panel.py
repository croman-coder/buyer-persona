#!/usr/bin/env python3
"""Arma los datos del panel «Así lee Jev la pauta» del Cerebro (cerebro.santarosa.lat/jev).

Complementa a clasificar_anuncios.py, que le hace a Jev 8 preguntas por texto. Acá van tres lecturas más, las
mismas que se usan para analizar reels:
  · con qué engancha la primera frase (tipo de gancho),
  · cómo está armado el texto (estructura),
  · qué papel cumple cada frase: gancho, desarrollo, oferta, llamado o letra chica.
Cache propia por hash del texto (output/raw/lectura_anuncios.json): no toca la clasificación ni su cache.

Suma el rendimiento de los últimos 90 días de cada anuncio (gasto en US$, impresiones, clics y contactos) desde
meta_ads.demographics.age_gender_ad del último data_sources_*.json.

Imágenes: la miniatura que arma Meta de cada creativo, en dos tamaños (archivo y ficha), en
Buyer Persona/.cerebro/miniaturas/<ad_id>-c.jpg y -g.jpg. Meta firma esas URLs y vencen: por eso se guardan, y
solo se piden las que faltan.

Salida: Buyer Persona/.cerebro/jev-anuncios.json. El Cerebro lo lee de /vault (montado en solo lectura) y el
portero lo recorta por marca. La carpeta está en .gitignore: no viaja al git del vault.

Uso:
  venv/bin/python3 scripts/jev_panel.py              # lee con Jev los textos nuevos y escribe el panel
  venv/bin/python3 scripts/jev_panel.py --max 3      # prueba: lee como mucho 3 textos nuevos
  venv/bin/python3 scripts/jev_panel.py --sin-jev    # solo rearma el panel con lo que ya está en cache
  venv/bin/python3 scripts/jev_panel.py --solo-imagenes [--max 5]  # solo baja las imágenes que faltan
  venv/bin/python3 scripts/jev_panel.py --minutos 40 # tope de tiempo (el cron): lo que falte queda para mañana
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import requests  # lo usa el pipeline: está en el venv

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clasificar_anuncios as ca  # noqa: E402  mismas credenciales, estados y etiquetas que la clasificación

CACHE = ca.RAW / "lectura_anuncios.json"
SALIDA = ca.RAIZ / "Buyer Persona/.cerebro/jev-anuncios.json"
VERSION_LECTURA = 1  # subir si cambian las preguntas: invalida la cache de lectura
MAX_FRASES = 16      # un texto largo junta renglones vecinos hasta quedar en esto
HILOS = 1
MINIATURAS = SALIDA.parent / "miniaturas"
GRAPH = "https://graph.facebook.com/v21.0/"
TAMANOS = {"c": 200, "g": 600}  # px que se le piden a Meta: c para la grilla del archivo, g para la ficha
LIMITES_META = (4, 17, 613, 80004)  # códigos de «demasiadas llamadas»: esperar y reintentar
PAUSA = 0.4        # segundos entre pedidos: el gateway corta con 429 cuando llegan en ráfaga
GUARDAR_CADA = 20  # textos: si la corrida se corta, se pierde poco

# código: (lo que ve marketing, lo que se le explica a Jev)
GANCHO = {
    "pregunta": ("Pregunta", "le hace una pregunta al lector"),
    "precio_oferta": ("Precio u oferta", "arranca con el precio, la cuota, el bono o la oferta"),
    "novedad": ("Novedad", "anuncia algo nuevo: llegó, lanzamiento, preventa, estreno"),
    "beneficio": ("Beneficio", "promete un beneficio del vehículo: ahorro, espacio, tecnología, seguridad"),
    "emocion": ("Emoción", "apela a una emoción, un sueño o un estilo de vida: aventura, familia, libertad"),
    "urgencia": ("Urgencia", "arranca con un plazo, un cupo o las últimas unidades"),
    "respaldo": ("Respaldo", "arranca con un dato, un premio, la garantía o una prueba de confianza"),
    "modelo": ("Solo el modelo", "solo nombra la marca, el modelo o la unidad, sin otro gancho"),
}
ESTRUCTURA = {
    "oferta_directa": ("Oferta directa", "va directo a la oferta y a los datos, sin historia"),
    "problema_solucion": ("Problema / solución", "plantea una necesidad o un problema y muestra el vehículo como la solución"),
    "lista_beneficios": ("Lista de beneficios", "enumera equipamiento o beneficios, uno por renglón o con emojis"),
    "historia": ("Historia", "cuenta una situación, una historia o un testimonio"),
    "lanzamiento": ("Lanzamiento", "presenta un modelo o una versión nueva"),
    "invitacion": ("Invitación", "invita a un evento, a una prueba de manejo o a visitar el local"),
}
PAPEL = {
    "gancho": ("Gancho", "abre el texto y busca frenar al que pasa: pregunta, promesa, novedad, precio de impacto"),
    "desarrollo": ("Desarrollo", "cuenta cómo es el vehículo o la propuesta: equipamiento, beneficios, respaldo, detalles"),
    "oferta": ("Oferta", "la propuesta concreta: precio, cuotas, bono, descuento, permuta o condición especial"),
    "llamado": ("Llamado", "le pide una acción al cliente o le da cómo contactar: escribir, llamar, visitar, dirección, teléfono"),
    "letra_chica": ("Letra chica", "condiciones, vigencia, aclaraciones legales, imágenes ilustrativas"),
}
# Abreviaturas que terminan en punto sin cerrar la frase («Av. Mariscal López», «Gs. 3.800.000»).
ABREVIATURAS = {"av", "avda", "gs", "sr", "sra", "srta", "dr", "dra", "ing", "lic", "nro", "n", "nº", "km", "kms",
                "hs", "aprox", "ej", "tel", "cel", "art", "inc", "vs", "etc", "pág", "cc", "cv", "hp", "mts"}


def hash_lectura(a: dict) -> str:
    return hashlib.sha1(f"L{VERSION_LECTURA}\n{a.get('title', '')}\n{a.get('body', '')}".encode()).hexdigest()[:16]


def frases(texto: str) -> list[str]:
    """Un trozo por renglón y, dentro del renglón, uno por frase. Un emoji suelto se pega al trozo siguiente.
    Si quedan más de MAX_FRASES, se juntan los vecinos más cortos (las listas largas de equipamiento)."""
    partes: list[str] = []
    for renglon in str(texto or "").splitlines():
        renglon = renglon.strip()
        if not renglon:
            continue
        trozos: list[str] = []
        for t in re.split(r"(?<=[.!?…])\s+(?=\S)", renglon):
            t = t.strip()
            if not t:
                continue
            previa = re.search(r"(\w+)\.$", trozos[-1]) if trozos else None
            if previa and previa.group(1).lower() in ABREVIATURAS:
                trozos[-1] += " " + t
            else:
                trozos.append(t)
        partes.extend(trozos)
    juntas: list[str] = []
    for p in partes:
        if juntas and not re.search(r"\w", juntas[-1]):
            juntas[-1] = f"{juntas[-1]} {p}"
        else:
            juntas.append(p)
    while len(juntas) > MAX_FRASES:
        i = min(range(len(juntas) - 1), key=lambda k: len(juntas[k]) + len(juntas[k + 1]))
        juntas[i : i + 2] = [juntas[i] + "\n" + juntas[i + 1]]
    return juntas


def partes_de(a: dict) -> list[str]:
    return frases(a.get("body") or "") or frases(a.get("title") or "")


def preguntas_para(partes: list[str]) -> dict:
    q = {
        "gancho": ca.choice(f"¿Con qué engancha la primera frase del anuncio: «{partes[0]}»?",
                            {k: v[1] for k, v in GANCHO.items()}),
        "estructura": ca.choice("¿Cómo está armado el texto del anuncio?", {k: v[1] for k, v in ESTRUCTURA.items()}),
    }
    for i, f in enumerate(partes, 1):
        q[f"frase_{i}"] = ca.choice(f"¿Qué papel cumple esta frase dentro del anuncio: «{f}»?",
                                    {k: v[1] for k, v in PAPEL.items()})
    return q


def preguntar(prov: tuple, estado: str, preguntas: dict) -> dict:
    """Igual que ca.preguntar pero con otras preguntas: mismos reintentos y mismos cortes (401/402/403)."""
    nombre, url, modelo, clave = prov
    cuerpo = json.dumps({"model": modelo, "state": estado, "questions": preguntas}).encode()
    time.sleep(PAUSA)
    for intento in range(6):
        pedido = urllib.request.Request(url, data=cuerpo, method="POST",
                                        headers={"Authorization": f"Bearer {clave}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(pedido, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (401, 402, 403):
                raise ca.Bloqueado(f"{nombre} {e.code}: {ca._mensaje(e)}") from None
            if e.code in (429, 500, 502, 503, 504) and intento < 5:
                try:
                    espera = float(e.headers.get("retry-after") or 0)
                except ValueError:
                    espera = 0
                espera = espera or (4 if e.code == 429 else 2) * 2 ** intento + random.uniform(0, 2)
                print(f"  {nombre} {e.code}: espero {espera:.0f} s ({ca._mensaje(e)[:80]})", file=sys.stderr, flush=True)
                time.sleep(espera)
                continue
            raise RuntimeError(f"HTTP {e.code}: {ca._mensaje(e)}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            if intento < 5:
                time.sleep(2 ** intento)
                continue
            raise RuntimeError(f"red: {e}") from None
    raise RuntimeError("sin respuesta")


def leer(prov: tuple, estado: str, partes: list[str]) -> dict:
    """Arma las preguntas dentro del pedido: si un texto no se puede leer, falla ese pedido y no toda la corrida."""
    return preguntar(prov, estado, preguntas_para(partes))


def resumir(r: dict, partes: list[str]) -> dict:
    ans = r.get("answers", {})

    def elegido(k: str) -> tuple:
        a = ans.get(k) or {}
        return a.get("choice"), round(float(a.get("confidence") or 0), 2)

    gancho, gancho_conf = elegido("gancho")
    estructura, estructura_conf = elegido("estructura")
    return {
        "gancho": gancho, "gancho_conf": gancho_conf,
        "estructura": estructura, "estructura_conf": estructura_conf,
        "frases": [[f, elegido(f"frase_{i}")[0]] for i, f in enumerate(partes, 1)],
        "tokens": r.get("usage", {}).get("input_tokens", 0),
        "costo": float(r.get("usage", {}).get("cost")                                         # OpenRouter
                       or r.get("provider_metadata", {}).get("gateway", {}).get("cost") or 0),  # Vercel
    }


def rendimiento(meta: dict) -> dict[str, dict]:
    """Totales de los últimos 90 días por anuncio. Meta reporta el gasto en US$."""
    out: dict[str, dict] = collections.defaultdict(
        lambda: {"gasto": 0.0, "impresiones": 0, "clics": 0, "clics_enlace": 0, "contactos": 0})
    for f in meta.get("demographics", {}).get("age_gender_ad", []):
        m = out[str(f.get("ad_id"))]
        m["gasto"] += float(f.get("spend") or 0)
        m["impresiones"] += int(float(f.get("impressions") or 0))
        m["clics"] += int(float(f.get("clicks") or 0))
        m["clics_enlace"] += int(float(f.get("inline_link_clicks") or 0))
        m["contactos"] += int(float(f.get("contactos") or 0))
    return out


def _token_meta() -> str:
    return os.environ.get("META_ADS_ACCESS_TOKEN", "").strip() or ca._leer_env(ca.RAIZ / ".env", "META_ADS_ACCESS_TOKEN")


def _graph(params: dict, token: str) -> dict:
    for intento in range(5):
        try:
            d = requests.get(GRAPH, params={**params, "access_token": token}, timeout=90).json()
        except (requests.RequestException, ValueError):
            time.sleep(10 * (intento + 1))
            continue
        if isinstance(d, dict) and (d.get("error") or {}).get("code") in LIMITES_META:
            time.sleep(60 * (intento + 1))
            continue
        return d if isinstance(d, dict) else {}
    return {"error": {"message": "Meta no respondió tras 5 intentos"}}


def _lotes(xs: list, n: int = 50):
    for i in range(0, len(xs), n):
        yield xs[i : i + n]


def con_imagen(ad_id: str) -> bool:
    return (MINIATURAS / f"{ad_id}-c.jpg").is_file()


def bajar_miniaturas(ads: list[dict], limite: int = 0) -> str:
    """La imagen de cada anuncio: la miniatura que Meta arma del creativo (foto, primer cuadro del video o primera
    tarjeta del carrusel). Se pide el creativo de a 50 anuncios y la miniatura de a 50 creativos, en dos tamaños."""
    MINIATURAS.mkdir(parents=True, exist_ok=True)
    faltan = sorted({str(a["ad_id"]) for a in ads if a.get("ad_id") and not con_imagen(str(a["ad_id"]))})
    if limite:
        faltan = faltan[:limite]
    if not faltan:
        return "imágenes: todas al día"
    token = _token_meta()
    if not token:
        return "imágenes: falta META_ADS_ACCESS_TOKEN en .env"
    t0, sin_respuesta = time.time(), 0
    creativo: dict[str, str] = {}
    for lote in _lotes(faltan):
        d = _graph({"ids": ",".join(lote), "fields": "creative{id}"}, token)
        if "error" in d:
            sin_respuesta += len(lote)
            print(f"  Meta: {str(d['error'].get('message'))[:120]}", file=sys.stderr, flush=True)
            continue
        for ad_id, v in d.items():
            cid = (v.get("creative") or {}).get("id") if isinstance(v, dict) else None
            if cid:
                creativo[ad_id] = cid
    urls: dict[tuple, str] = {}
    for t, px in TAMANOS.items():
        for lote in _lotes(sorted(set(creativo.values()))):
            d = _graph({"ids": ",".join(lote), "fields": "thumbnail_url", "thumbnail_width": px, "thumbnail_height": px}, token)
            for cid, v in d.items():
                if isinstance(v, dict) and v.get("thumbnail_url"):
                    urls[(cid, t)] = v["thumbnail_url"]

    def bajar(ad_id: str) -> bool:
        listo = False
        for t in TAMANOS:
            url = urls.get((creativo.get(ad_id), t))
            if not url:
                continue
            try:
                r = requests.get(url, timeout=60)
            except requests.RequestException:
                continue
            if r.ok and r.headers.get("content-type", "").startswith("image/") and r.content:
                destino = MINIATURAS / f"{ad_id}-{t}.jpg"
                tmp = destino.with_suffix(".tmp")
                tmp.write_bytes(r.content)
                tmp.replace(destino)  # el Cerebro nunca sirve una imagen a medio escribir
                listo = listo or t == "c"
        return listo

    with concurrent.futures.ThreadPoolExecutor(4) as ex:
        bajadas = sum(ex.map(bajar, [a for a in faltan if a in creativo]))
    return (f"imágenes: {bajadas} de {len(faltan)} anuncios nuevos en {time.time() - t0:.0f} s"
            + (f" · {sin_respuesta} sin respuesta de Meta" if sin_respuesta else "")
            + (f" · {len(faltan) - len(creativo) - sin_respuesta} sin creativo" if len(faltan) - len(creativo) - sin_respuesta > 0 else ""))


def armar_panel(ads: list[dict], cls: dict, lec: dict, rend: dict, fuente: str, meta: dict, proveedor: str) -> dict:
    anuncios = []
    for a in ads:
        c = cls.get(ca.hash_texto(a)) or {}
        h = hash_lectura(a)
        lec_a = lec.get(h) or {}
        r = rend.get(str(a.get("ad_id")))
        anuncios.append({
            "id": str(a.get("ad_id", "")),
            "t": h,  # mismo texto, mismo t: el costo y las preguntas se cuentan una vez por texto
            "cuenta": a.get("account", ""),
            "estado": a.get("status", ""),
            "nombre": a.get("ad_name", ""),
            "titulo": a.get("title", ""),
            "boton": a.get("cta", ""),
            "img": con_imagen(str(a.get("ad_id", ""))),
            "oferta": c.get("oferta"), "argumento": c.get("argumento"), "segmento": c.get("segmento"),
            "gancho": lec_a.get("gancho"), "estructura": lec_a.get("estructura"),
            "conf": {"oferta": c.get("oferta_conf"), "argumento": c.get("argumento_conf"),
                     "segmento": c.get("segmento_conf"), "gancho": lec_a.get("gancho_conf"),
                     "estructura": lec_a.get("estructura_conf")},
            "precio": c.get("precio"), "cuotas": c.get("financiacion"), "llamado": c.get("llamado"),
            "urgencia": c.get("urgencia"), "riesgo": c.get("comparativa"),
            "frases": lec_a.get("frases") or [[f, None] for f in partes_de(a)],
            "rend": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()} if r else None,
            "jev": round(float(c.get("costo") or 0) + float(lec_a.get("costo") or 0), 6),
            "preguntas": (len(ca.PREGUNTAS) if c else 0) + ((2 + len(lec_a.get("frases") or [])) if lec_a else 0),
        })
    return {
        "version": 1,
        "generado": datetime.now().astimezone().isoformat(timespec="seconds"),
        "fuente": fuente,
        "periodo": meta.get("date_range") or {},
        "moneda": "US$",
        "proveedor": proveedor,
        "etiquetas": {
            **ca.ETIQUETAS,
            "gancho": {k: v[0] for k, v in GANCHO.items()},
            "estructura": {k: v[0] for k, v in ESTRUCTURA.items()},
            "papel": {k: v[0] for k, v in PAPEL.items()},
            "estado": ca.ESTADO_ES,
            "boton": ca.BOTON_ES,
        },
        "anuncios": anuncios,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=0, help="leer como mucho N textos nuevos (prueba)")
    ap.add_argument("--hilos", type=int, default=HILOS, help=f"pedidos en paralelo (por defecto {HILOS})")
    ap.add_argument("--sin-jev", action="store_true", help="no preguntar nada: rearmar el panel con la cache")
    ap.add_argument("--minutos", type=float, default=0, help="tope de tiempo; lo que falte queda para la próxima corrida")
    ap.add_argument("--sin-imagenes", action="store_true", help="no bajar las imágenes de Meta")
    ap.add_argument("--solo-imagenes", action="store_true", help="solo bajar las imágenes que faltan (no toca caches ni panel)")
    args = ap.parse_args()

    fuentes = sorted(ca.RAW.glob("data_sources_*.json"), key=lambda p: p.stat().st_mtime)
    if not fuentes:
        sys.exit("No hay output/raw/data_sources_*.json (¿corrió el pipeline?)")
    fuente = fuentes[-1]
    meta = json.loads(fuente.read_text(encoding="utf-8")).get("meta_ads", {})
    ads = [a for a in meta.get("ad_creatives", []) if a.get("status") in ca.ESTADOS and (a.get("title") or a.get("body"))]
    if args.solo_imagenes:
        print(bajar_miniaturas(ads, args.max), flush=True)
        return
    cls = (json.loads(ca.CACHE.read_text(encoding="utf-8")) if ca.CACHE.is_file() else {}).get("textos", {})
    lec: dict = (json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.is_file() else {}).get("textos", {})

    nuevos: dict[str, tuple] = {}
    for a in ads:
        h = hash_lectura(a)
        partes = partes_de(a)
        # Un título con solo espacios no deja ninguna frase: no hay nada que leer (y armar las preguntas fallaba).
        if partes and h not in lec and h not in nuevos:
            nuevos[h] = (ca.estado_de(a), partes)
    pendientes = [] if args.sin_jev else (list(nuevos.items())[: args.max] if args.max else list(nuevos.items()))
    print(f"{fuente.name}: {len(ads)} anuncios · {len(lec)} textos leídos en cache · {len(pendientes)} para leer", flush=True)

    prov = ca.credencial() if pendientes else ("", "", "", "")
    costo, errores, bloqueo, ok, t0, sin_tiempo = 0.0, [], "", 0, time.time(), False
    if pendientes:
        print(f"proveedor: {prov[0]} ({prov[2]})", flush=True)
        with concurrent.futures.ThreadPoolExecutor(max(1, args.hilos)) as ex:
            futuros = {ex.submit(leer, prov, estado, partes): (h, partes) for h, (estado, partes) in pendientes}
            for i, f in enumerate(concurrent.futures.as_completed(futuros), 1):
                h, partes = futuros[f]
                try:
                    lec[h] = resumir(f.result(), partes)
                    ok += 1
                    costo += lec[h]["costo"]
                except concurrent.futures.CancelledError:
                    continue
                except ca.Bloqueado as e:
                    errores.append(str(e))
                    if not bloqueo:
                        bloqueo = str(e)
                        for otro in futuros:
                            otro.cancel()
                except Exception as e:  # noqa: BLE001 — cualquier otra falla cuenta como error de ese texto
                    errores.append(f"{type(e).__name__}: {e}")
                if args.minutos and not sin_tiempo and time.time() - t0 > args.minutos * 60:
                    sin_tiempo = True  # el pedido en curso termina; los que esperan quedan para la próxima
                    for otro in futuros:
                        otro.cancel()
                if i % GUARDAR_CADA == 0:
                    print(f"  {i}/{len(pendientes)} · {time.time() - t0:.0f} s · errores {len(errores)}", flush=True)
                    CACHE.write_text(json.dumps({"version": VERSION_LECTURA, "textos": lec}, ensure_ascii=False),
                                     encoding="utf-8")
        print(f"leídos {ok} de {len(pendientes)} en {time.time() - t0:.0f} s · US$ {costo:.4f} · errores {len(errores)}"
              + (f" · se acabó el tiempo ({args.minutos:g} min)" if sin_tiempo else ""), flush=True)
        for e in sorted(set(errores))[:5]:
            print("  error:", e)
    vigentes = {hash_lectura(a) for a in ads}  # como la clasificación: la cache guarda solo los textos actuales
    lec = {h: v for h, v in lec.items() if h in vigentes}
    CACHE.write_text(json.dumps({"version": VERSION_LECTURA, "textos": lec}, ensure_ascii=False), encoding="utf-8")

    if not args.sin_imagenes:
        print(bajar_miniaturas(ads), flush=True)
    panel = armar_panel(ads, cls, lec, rendimiento(meta), fuente.name, meta, prov[0])
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    tmp = SALIDA.with_suffix(".tmp")
    tmp.write_text(json.dumps(panel, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(SALIDA)  # el Cerebro nunca lee un archivo a medio escribir
    leidos = sum(1 for x in panel["anuncios"] if x["gancho"])
    print(f"panel: {SALIDA.relative_to(ca.RAIZ)} · {len(ads)} anuncios · {leidos} con lectura · "
          f"{SALIDA.stat().st_size // 1024} KB")
    faltan = len({hash_lectura(a) for a in ads if partes_de(a)} - set(lec))  # los que no tienen texto no cuentan
    if faltan:
        print(f"pendientes para la próxima corrida: {faltan} textos", flush=True)
    # Quedarse sin tiempo es lo esperable cuando el proveedor está saturado: no es una falla. Sí lo es que corte
    # (sin saldo, clave inválida) o que haya errores con tiempo de sobra.
    if bloqueo or (faltan and not (args.max or args.sin_jev or sin_tiempo)):
        sys.exit(f"incompleta: faltan {faltan} textos" + (f" ({bloqueo})" if bloqueo else ""))


if __name__ == "__main__":
    main()
