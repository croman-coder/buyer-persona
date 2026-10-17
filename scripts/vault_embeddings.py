#!/usr/bin/env python3
"""Búsqueda por significado en el vault de Obsidian (Buyer Persona/).

Lee las notas .md, las parte en trozos, pide un embedding de cada trozo al Ollama
LOCAL (EmbeddingGemma, 127.0.0.1:11440) y guarda los vectores en un SQLite que
queda FUERA del vault. Buscar es comparar la consulta contra esos vectores.

  scripts/py.sh scripts/vault_embeddings.py indexar            # incremental: solo lo que cambió
  scripts/py.sh scripts/vault_embeddings.py indexar --todo     # reindexa todo
  scripts/py.sh scripts/vault_embeddings.py buscar "qué publicamos esta semana" -k 6
  scripts/py.sh scripts/vault_embeddings.py buscar "precios JAC" --carpeta Competencia --json
  scripts/py.sh scripts/vault_embeddings.py estado

Qué lee y qué no:
  - Solo archivos .md dentro del vault. Nunca escribe en el vault.
  - Se saltea `.obsidian`, `.trash` y `Seguridad` (hallazgos y datos internos del servidor).
    Cambiarlo con VAULT_EXCLUIR="Seguridad,.obsidian" (lista separada por comas).
  - El texto solo se manda a un Ollama en localhost: con otra dirección el script se
    niega, salvo VAULT_EMBED_REMOTO=1.

Variables: VAULT_PATH, VAULT_INDEX_DB, OLLAMA_EMBED_URL, OLLAMA_EMBED_MODEL.
Los vectores de modelos distintos NO se pueden mezclar: el modelo queda anotado en el
índice y si se cambia hay que reindexar con --todo.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import numpy as np

PROYECTO = Path(__file__).resolve().parent.parent
VAULT = Path(os.environ.get("VAULT_PATH", PROYECTO / "Buyer Persona"))
DB = Path(os.environ.get("VAULT_INDEX_DB", Path.home() / ".local/share/vault-index/vault.sqlite3"))
URL = os.environ.get("OLLAMA_EMBED_URL", "http://127.0.0.1:11440").rstrip("/")
MODELO = os.environ.get("OLLAMA_EMBED_MODEL", "embeddinggemma")
EXCLUIR = {s.strip() for s in os.environ.get("VAULT_EXCLUIR", "Seguridad,.obsidian,.trash").split(",") if s.strip()}
MAX_CAR = 1400          # largo de cada trozo; EmbeddingGemma v1 admite 2K tokens
PREFIJO_DOC = "title: {titulo} | text: "
PREFIJO_CONSULTA = "task: search result | query: "
LOTE = 16


def _verificar_destino() -> None:
    host = urlparse(URL).hostname or ""
    if host not in ("127.0.0.1", "localhost", "::1") and os.environ.get("VAULT_EMBED_REMOTO") != "1":
        sys.exit(f"Me niego a mandar el contenido del vault a {host}: el modelo tiene que estar en localhost "
                 f"(o poné VAULT_EMBED_REMOTO=1 sabiendo lo que implica).")


def embeber(textos: list[str]) -> np.ndarray:
    _verificar_destino()
    cuerpo = json.dumps({"model": MODELO, "input": textos}).encode()
    ultimo = None
    for intento in range(3):
        try:
            req = urllib.request.Request(URL + "/api/embed", cuerpo, {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                v = np.asarray(json.load(r)["embeddings"], dtype=np.float32)
            n = np.linalg.norm(v, axis=1, keepdims=True)
            return v / np.where(n == 0, 1, n)
        except Exception as e:  # noqa: BLE001
            ultimo = e
            time.sleep(2 * (intento + 1))
    sys.exit(f"No pude pedir embeddings a {URL} (modelo {MODELO}): {ultimo}")


def conectar() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript("""
        create table if not exists meta(k text primary key, v text);
        create table if not exists archivos(ruta text primary key, sha text, trozos integer);
        create table if not exists trozos(id integer primary key, ruta text, orden integer,
                                          encabezado text, texto text, vec blob);
        create index if not exists i_trozos_ruta on trozos(ruta);
    """)
    return db


def meta_get(db, k):
    r = db.execute("select v from meta where k=?", (k,)).fetchone()
    return r[0] if r else None


def meta_set(db, k, v):
    db.execute("insert into meta(k,v) values(?,?) on conflict(k) do update set v=excluded.v", (k, str(v)))


def notas() -> list[Path]:
    salida = []
    for p in VAULT.rglob("*.md"):
        rel = p.relative_to(VAULT).parts
        if any(parte in EXCLUIR for parte in rel):
            continue
        salida.append(p)
    return sorted(salida)


def partir(texto: str):
    """(titulo, [(encabezado, trozo), ...]) de una nota."""
    texto = re.sub(r"\A---\n.*?\n---\n", "", texto, flags=re.S)
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S).strip()
    m = re.search(r"(?m)^#\s+(.+)$", texto)
    titulo = m.group(1).strip() if m else ""
    trozos: list[tuple[str, str]] = []
    for sec in re.split(r"(?m)^(?=#{1,4}\s)", texto):
        sec = sec.strip()
        if not sec:
            continue
        h = re.match(r"#{1,4}\s+(.*)", sec)
        enc = h.group(1).strip() if h else ""
        if len(sec) <= MAX_CAR:
            trozos.append((enc, sec))
            continue
        buf = ""
        for par in re.split(r"\n\s*\n", sec):
            while len(par) > MAX_CAR:  # tablas o líneas enormes
                if buf:
                    trozos.append((enc, buf)); buf = ""
                trozos.append((enc, par[:MAX_CAR])); par = par[MAX_CAR:]
            if buf and len(buf) + len(par) + 2 > MAX_CAR:
                trozos.append((enc, buf)); buf = ""
            buf = f"{buf}\n\n{par}" if buf else par
        if buf:
            trozos.append((enc, buf))
    return titulo, [(e, t) for e, t in trozos if len(t.strip()) >= 40]


def indexar(todo: bool) -> None:
    if not VAULT.is_dir():
        sys.exit(f"No encuentro el vault en {VAULT}")
    DB.parent.mkdir(parents=True, exist_ok=True)
    traba = open(DB.with_suffix(".lock"), "w")  # una sola indexación a la vez; se libera sola al terminar
    try:
        fcntl.flock(traba, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("Ya hay una indexación en curso: no hago nada.")
        return
    db = conectar()
    previo = meta_get(db, "modelo")
    if previo and previo != MODELO and not todo:
        sys.exit(f"El índice se hizo con '{previo}' y ahora el modelo es '{MODELO}': los vectores no se pueden mezclar. "
                 f"Corré 'indexar --todo'.")
    if todo:
        db.execute("delete from trozos"); db.execute("delete from archivos")
    t0 = time.time()
    existentes = {r[0]: r[1] for r in db.execute("select ruta, sha from archivos")}
    en_vault = set()
    nuevos = cambiados = 0
    lista = notas()
    for i, p in enumerate(lista, 1):
        rel = p.relative_to(VAULT).as_posix()
        en_vault.add(rel)
        try:
            crudo = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        sha = hashlib.sha1(crudo.encode()).hexdigest()
        if existentes.get(rel) == sha:
            continue
        titulo, trozos = partir(crudo)
        titulo = titulo or p.stem
        db.execute("delete from trozos where ruta=?", (rel,))
        vectores = []
        for j in range(0, len(trozos), LOTE):
            lote = trozos[j:j + LOTE]
            vectores.append(embeber([PREFIJO_DOC.format(titulo=titulo) + t for _, t in lote]))
        mat = np.vstack(vectores) if vectores else np.zeros((0, 768), dtype=np.float32)
        for orden, ((enc, t), v) in enumerate(zip(trozos, mat)):
            db.execute("insert into trozos(ruta,orden,encabezado,texto,vec) values(?,?,?,?,?)",
                       (rel, orden, enc, t, v.tobytes()))
        db.execute("insert into archivos(ruta,sha,trozos) values(?,?,?) "
                   "on conflict(ruta) do update set sha=excluded.sha, trozos=excluded.trozos", (rel, sha, len(trozos)))
        db.commit()
        nuevos += rel not in existentes
        cambiados += rel in existentes
        if (nuevos + cambiados) % 25 == 0:
            print(f"  {nuevos + cambiados} notas procesadas ({i}/{len(lista)}) · {time.time() - t0:.0f} s", flush=True)
    borradas = [r for r in existentes if r not in en_vault]
    for r in borradas:
        db.execute("delete from trozos where ruta=?", (r,)); db.execute("delete from archivos where ruta=?", (r,))
    meta_set(db, "modelo", MODELO)
    meta_set(db, "indexado_en", time.strftime("%Y-%m-%d %H:%M:%S"))
    db.commit()
    n_t = db.execute("select count(*) from trozos").fetchone()[0]
    print(f"Listo: {nuevos} nuevas, {cambiados} modificadas, {len(borradas)} borradas · "
          f"{len(en_vault)} notas, {n_t} trozos · {time.time() - t0:.0f} s")


def cargar(db, carpeta: str | None):
    filas = db.execute("select id, ruta, encabezado, texto, vec from trozos"
                       + (" where ruta like ?" if carpeta else ""), ((carpeta.rstrip('/') + "/%",) if carpeta else ())).fetchall()
    if not filas:
        return [], np.zeros((0, 768), dtype=np.float32)
    return filas, np.vstack([np.frombuffer(f[4], dtype=np.float32) for f in filas])


def buscar(consulta: str, k: int, carpeta: str | None, como_json: bool, por_nota: int) -> None:
    db = conectar()
    modelo = meta_get(db, "modelo")
    if not modelo:
        sys.exit("El índice está vacío. Corré primero: indexar")
    if modelo != MODELO:
        sys.exit(f"El índice es de '{modelo}' pero el modelo configurado es '{MODELO}'.")
    filas, mat = cargar(db, carpeta)
    if not filas:
        sys.exit("No hay trozos indexados" + (f" en '{carpeta}'" if carpeta else ""))
    q = embeber([PREFIJO_CONSULTA + consulta])[0]
    puntajes = mat @ q
    orden = np.argsort(-puntajes)
    vistos: dict[str, int] = {}
    res = []
    for idx in orden:
        _, ruta, enc, texto, _ = filas[idx]
        if vistos.get(ruta, 0) >= por_nota:
            continue
        vistos[ruta] = vistos.get(ruta, 0) + 1
        res.append({"puntaje": round(float(puntajes[idx]), 3), "nota": ruta, "seccion": enc,
                    "texto": re.sub(r"\s+", " ", texto)[:420]})
        if len(res) >= k:
            break
    if como_json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return
    for r in res:
        print(f"{r['puntaje']:.2f}  {r['nota']}" + (f"  › {r['seccion']}" if r["seccion"] else ""))
        print(f"      {r['texto'][:260]}")


def estado() -> None:
    db = conectar()
    n_a, n_t = db.execute("select count(*), coalesce(sum(trozos),0) from archivos").fetchone()
    print(f"índice: {DB}\nmodelo: {meta_get(db, 'modelo')}   indexado: {meta_get(db, 'indexado_en')}\n"
          f"notas: {n_a}   trozos: {n_t}   tamaño: {DB.stat().st_size / 2**20:.1f} MB\n"
          f"vault: {VAULT}\nexcluye: {', '.join(sorted(EXCLUIR))}\nollama: {URL}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("indexar"); a.add_argument("--todo", action="store_true", help="reindexar desde cero")
    b = sub.add_parser("buscar"); b.add_argument("consulta"); b.add_argument("-k", type=int, default=6)
    b.add_argument("--carpeta", help="limitar a una carpeta del vault, ej. Competencia")
    b.add_argument("--json", action="store_true"); b.add_argument("--por-nota", type=int, default=2)
    sub.add_parser("estado")
    args = ap.parse_args()
    if args.cmd == "indexar":
        indexar(args.todo)
    elif args.cmd == "buscar":
        buscar(args.consulta, args.k, args.carpeta, args.json, args.por_nota)
    else:
        estado()


if __name__ == "__main__":
    main()
