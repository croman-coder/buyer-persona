#!/usr/bin/env python3
"""Arma la nota «📣 Anuncios de la Competencia» con lo que se leyó de la Biblioteca de Anuncios de Meta.

La Biblioteca no se puede leer sola: la API oficial no trae anuncios comerciales de Paraguay y la página pública no
se entrega a navegadores automatizados. Una persona (o una sesión de Claude con navegador real) hace la captura,
con el skill «biblioteca-competencia», y este script la analiza: qué ofrece cada competidor, cómo arma el anuncio,
hace cuánto corre, qué cambió desde la lectura anterior y qué se puede responder con argumentos propios.

Entrada:  output/competencia/biblioteca/AAAA-MM-DD/<competidor>.json   (una captura por competidor)
Salida:   Buyer Persona/Competencia/📣 Anuncios de la Competencia.md
Memoria:  Buyer Persona/Sistema/Memoria/biblioteca_competencia.jsonl    (para comparar una lectura con la anterior)

Solo uso interno: por ley de Paraguay no se nombra a la competencia en un texto público.

Uso:
    venv/bin/python3 scripts/biblioteca_competencia.py [--fecha AAAA-MM-DD] [--capturas DIR] [--raw DIR] [--sin-vault]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.generators import biblioteca_competencia as B  # noqa: E402

VAULT = ROOT / "Buyer Persona"
NOTA = VAULT / "Competencia" / "📣 Anuncios de la Competencia.md"
MEMORIA = VAULT / "Sistema" / "Memoria" / "biblioteca_competencia.jsonl"


def corta(iso: str | None) -> str:
    return f"{iso[8:10]}/{iso[5:7]}" if iso else "—"


def md(t: str) -> str:
    return t.replace("|", "\\|").replace("\n", " ")


def marcas_propias(raw: Path) -> dict[str, Any] | None:
    """Fichas de nuestras marcas (para anclar las pistas en datos propios). Sin ellas, las pistas salen generales."""
    archivos = sorted(raw.glob("personas_*.json"))
    if not archivos:
        return None
    marcas: dict[str, Any] = {}
    for p in json.loads(archivos[-1].read_text(encoding="utf-8")):
        s = p.get("segment", {})
        if s.get("type") == "brand":
            marcas.setdefault(s["name"], {})["marca"] = p
    return marcas


def estructura(r: dict[str, Any]) -> str:
    n = r["n"]
    partes = []
    if r["palabras_mediana"] is not None:
        partes.append(f"texto de unas {r['palabras_mediana']} palabras")
    if r["video"]:
        partes.append(f"video en {r['video']} de {n}")
    if r["ctas"]:
        c, k = next(iter(r["ctas"].items()))
        partes.append(f"botón más usado: «{c}» ({k} de {n})")
    if r["etiquetas"]["test_drive"]:
        partes.append(f"invita a un test drive en {r['etiquetas']['test_drive']}")
    if r["etiquetas"]["urgencia"]:
        partes.append(f"mete urgencia o fecha en {r['etiquetas']['urgencia']}")
    return "; ".join(partes) or "sin datos"


def seccion(slug: str, d: dict[str, Any], marcas: dict[str, Any] | None, previa: dict[str, Any] | None) -> list[str]:
    comp, ads = d["comp"], d["ads"]
    r = B.resumen(ads)
    L = [f"### {comp['nombre']}", "",
         f"**Vende:** {comp['vende']}. **Búsqueda:** «{d['consulta']}» ({d['total_consulta'] or '—'}; se leyeron los primeros "
         f"{d['cargados']} por impresiones y {len(ads)} son de páginas oficiales)."
         + (f" Además hay {d['asesores']} {'anuncio de una página personal de un asesor' if d['asesores'] == 1 else 'anuncios de páginas personales de asesores'}, "
           "que se cuentan sin nombre." if d["asesores"] else ""), ""]
    if comp.get("aviso"):
        L += [f"> [!warning] {comp['aviso']}", ""]
    if not ads:
        return L + ["No se encontraron anuncios activos de una página oficial en esta lectura.", ""]
    L += [f"**Cómo arma el anuncio:** {estructura(r)}.", ""]
    ofertas = B.agrupar_iguales([a for a in ads if a["tema"] == "oferta"])
    if ofertas:
        L += ["**Qué ofrece:**", ""] + [f"- {B.frase_oferta(a)}" + (f" (mismo anuncio en {k} páginas)" if k > 1 else "") for a, k in ofertas[:5]] + [""]
    if previa:
        cmp_ = B.comparar(previa["ids"], [a["id"] for a in ads])
        nuevos = [a for a in ads if a["id"] in cmp_["nuevos"]]
        L += [f"**Desde la lectura del {corta(previa['fecha'])}:** {len(nuevos)} nuevos y {len(cmp_['terminados'])} que ya no aparecen "
              "entre los primeros leídos.", ""]
        L += [f"- Nuevo: {a['gancho']}" for a in nuevos[:5]] + ([""] if nuevos else [])
    pistas = B.que_responder(comp, r, marcas)
    if pistas:
        L += ["**Qué responder** (sugerencia, validar con la marca; argumentos propios y sin nombrarlos):", ""] + [f"- {p}" for p in pistas] + [""]
    L += ["| Desde | Días | Tema | Formato | Botón | Gancho |", "|---|---|---|---|---|---|"]
    for a in sorted(ads, key=lambda a: a["desde"] or "", reverse=True):
        L.append(f"| {corta(a['desde'])} | {a['dias'] if a['dias'] is not None else '—'} | {B.TEMAS[a['tema']]} | {a['formato']} | "
                 f"{a['cta'] or '—'} | {md(a['gancho'])} |")
    L += ["", "> [!quote]- Textos completos"]
    for a in sorted(ads, key=lambda a: a["desde"] or "", reverse=True):
        L.append(f"> **{corta(a['desde'])} · {B.TEMAS[a['tema']]}** — {md(a['texto'])}")
        L.append(">")
    return L + [""]


def nota(leidos: dict[str, dict[str, Any]], marcas: dict[str, Any] | None, historial: list[dict[str, Any]], fecha: str) -> str:
    L = ["---", "type: anuncios-competencia", f"generado: '{fecha}'", "fuente: Biblioteca de Anuncios de Meta (lectura asistida)",
         "uso: interno", "tags: [competencia, meta-ads, biblioteca, uso-interno]", "---",
         "# 📣 Anuncios de la Competencia", "",
         "> [!danger] Solo uso interno",
         "> Por ley de Paraguay **no se puede nombrar marcas ni modelos de la competencia en un texto público**. Esto sirve para entender "
         "qué ofrecen y cómo lo arman, y para responder con argumentos propios.", "",
         f"> [!info] Lectura del **{corta(fecha)}** · lectura asistida, no automática",
         "> - **De dónde sale:** la Biblioteca de Anuncios de Meta (anuncios activos en Paraguay). La API oficial no entrega anuncios comerciales "
         "de Paraguay y la página pública no se entrega a navegadores automatizados, así que la lectura la hace una sesión de Claude con un "
         "navegador real (skill `biblioteca-competencia`).",
         "> - **Qué se lee:** los primeros anuncios por impresiones de cada competidor, solo de sus páginas oficiales. Las páginas personales de "
         "asesores se cuentan sin nombre. Es el texto del anuncio: la imagen y el video no se analizan.",
         "> - **Cuántos hay:** son una muestra de los más vistos, no el total. «Nuevos» y «ya no aparecen» comparan con la lectura anterior.",
         "> - **Tema** lo asigna una regla sobre el texto (oferta, lanzamiento, postventa, marca, modelo): es una ayuda para leer, no un dictamen.", "",
         "Relacionado: [[📢 Promociones Competencia]] · [[⚔️ Benchmark Competitivo]] · [[⚔️ Bitácora de Competencia]] · [[🎯 Playbook Meta Ads]]", "",
         "## Resumen", "",
         "| Competidor | Leídos | Oferta | Lanzamiento | Postventa | Marca o sucursal | Muestra el modelo | Video | Botón principal | Nuevos 7 d | Más de 30 d |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for slug, d in leidos.items():
        r = B.resumen(d["ads"])
        t = r["temas"]
        boton = next(iter(r["ctas"]), "—")
        L.append(f"| {d['comp']['nombre']} | {r['n']} | {t['oferta']} | {t['lanzamiento']} | {t['postventa']} | {t['institucional']} | "
                 f"{t['producto']} | {r['video']} | {boton} | {r['nuevos_7d']} | {r['sostenidos_30d']} |")
    L += ["", "## Lo que se ve de punta a punta", ""]
    todos = [a for d in leidos.values() for a in d["ads"]]
    if todos:
        R = B.resumen(todos)
        n = R["n"]
        L += [f"- De **{n}** anuncios leídos, **{R['temas']['oferta']}** hablan de una oferta concreta (precio, cuotas o bono), "
              f"**{R['temas']['lanzamiento']}** de un lanzamiento y **{R['temas']['postventa']}** de postventa o service.",
              f"- **{R['video']}** son video. El botón más usado es «{next(iter(R['ctas']), '—')}».",
              f"- **{R['etiquetas']['test_drive']}** invitan a un test drive y **{R['etiquetas']['urgencia']}** meten urgencia o fecha límite.", ""]
    L += ["## Por competidor", ""]
    for slug, d in leidos.items():
        L += seccion(slug, d, marcas, B.lectura_anterior(historial, slug, fecha))
    L += ["## Cómo actualizar esta lectura", "",
          "1. Abrir Claude Code en esta carpeta y pedir: **«actualizá la lectura de la Biblioteca de Anuncios de la competencia»**.",
          "2. El skill `biblioteca-competencia` abre la Biblioteca en un navegador real, lee cada competidor (unos 9 a 12 páginas), guarda las "
          "capturas en `output/competencia/biblioteca/<fecha>/` y corre este script.",
          "3. Sin sesión de Claude no se actualiza: esta nota queda con la fecha de la última lectura. Conviene leerla una vez por semana.", ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fecha", default=date.today().isoformat())
    ap.add_argument("--capturas", default=None)
    ap.add_argument("--raw", default=str(ROOT / "output" / "raw"))
    ap.add_argument("--sin-vault", action="store_true", help="no escribe la nota ni la memoria")
    a = ap.parse_args()
    carpeta = Path(a.capturas) if a.capturas else ROOT / "output" / "competencia" / "biblioteca" / a.fecha
    if not carpeta.is_dir():
        raise SystemExit(f"No hay capturas en {carpeta}: hay que leer la Biblioteca primero (skill biblioteca-competencia).")
    leidos = B.leer_capturas(carpeta, date.fromisoformat(a.fecha))
    if not leidos:
        raise SystemExit(f"{carpeta} no tiene capturas de ningún competidor.")
    historial = B.cargar_historial(MEMORIA)
    texto = nota(leidos, marcas_propias(Path(a.raw)), historial, a.fecha)
    if a.sin_vault:
        print(texto)
        return
    NOTA.parent.mkdir(parents=True, exist_ok=True)
    NOTA.write_text(texto, encoding="utf-8")
    B.guardar_lectura(MEMORIA, a.fecha, leidos)
    print(f"  nota: {NOTA.relative_to(ROOT)}\n  memoria: {MEMORIA.relative_to(ROOT)}")
    for slug, d in leidos.items():
        print(f"  {d['comp']['nombre']}: {len(d['ads'])} anuncios")


if __name__ == "__main__":
    main()
