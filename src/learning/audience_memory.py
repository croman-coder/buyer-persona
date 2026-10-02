"""
Memoria de audiencia: lo que el sistema va aprendiendo corrida tras corrida.

Cada corrida del pipeline sobrescribe las notas de persona con la foto de
hoy. Esta memoria guarda la SERIE: una fila por modelo y por día en
``Sistema/Memoria/historial_audiencia.jsonl`` y, a partir de esa serie,
escribe ``Sistema/🧠 Memoria de Audiencia.md`` con:

- lo que ya está confirmado (mismo público N corridas seguidas),
- lo que cambió hoy (género/edad/brecha que se movió, modelos nuevos),
- tendencias por marca a 7 y 30 días (CPL, leads, gasto, % público frío),
- el mercado (precios de la competencia que se movieron),
- reglas aprendidas (recomendaciones sostenidas en el tiempo).

Sin datos personales: solo agregados. Hermes lee esta nota para afinar la
pauta; los aprendizajes durables los guarda en su propia memoria.
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CONFIRMED_RUNS = 3      # corridas seguidas con el mismo público → "confirmado"
SOLID_RUNS = 7          # → "sólido"
GENDER_SHIFT_PTS = 8.0  # cambio de % de género que se reporta como movimiento


# --------------------------------------------------------------------------- snapshot
def _snapshot_rows(personas: list[dict[str, Any]], data_sources: dict[str, Any], today: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in personas:
        seg = p.get("segment", {}) or {}
        if seg.get("type") not in ("brand", "model"):
            continue
        demo = p.get("demographics", {}) or {}
        meta = demo.get("meta") or {}
        b = p.get("budget") or {}
        mix = p.get("audience_mix") or {}
        comp = p.get("competitors") or {}
        rows.append({
            "date": today,
            "name": p.get("name", ""),
            "type": seg.get("type"),
            "brand": seg.get("brand") or seg.get("name"),
            "gender": demo.get("gender"),
            "gender_share": meta.get("gender_share"),
            "age_range": demo.get("age_range"),
            "age_share": meta.get("age_share"),
            "clicks": meta.get("weight"),
            "level": demo.get("meta_level") or "",
            "orders": seg.get("orders"),
            "orders_365d": seg.get("orders_last_365d"),
            "ad_count": seg.get("ad_count"),
            "active_ads": seg.get("active_ads"),
            "gap": seg.get("gap"),
            "sales_share": seg.get("sales_share"),
            "ad_share": seg.get("ad_share"),
            "spend_month": b.get("spend_month"),
            "cpl": b.get("cpl"),
            "leads_90d": b.get("leads_90d"),
            "current_month_est": b.get("current_month_est"),
            "suggested_month": b.get("suggested_month"),
            "frio_pct": mix.get("frio_pct"),
            "adsets": mix.get("adsets"),
            "competitors": len(comp.get("competitors") or []) if isinstance(comp, dict) else None,
        })
    return rows


def _load_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _save_history(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


# --------------------------------------------------------------------------- análisis
def _series(history: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in history:
        by[r["name"]].append(r)
    for k in by:
        by[k].sort(key=lambda r: r["date"])
    return by


def _run_streak(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> int:
    """Cuántas corridas seguidas (desde la última) mantienen los mismos valores."""
    if not rows:
        return 0
    last = tuple(rows[-1].get(k) for k in keys)
    n = 0
    for r in reversed(rows):
        if tuple(r.get(k) for k in keys) == last:
            n += 1
        else:
            break
    return n


def _row_on_or_before(rows: list[dict[str, Any]], day: str) -> dict[str, Any] | None:
    prev = [r for r in rows if r["date"] <= day]
    return prev[-1] if prev else None


def _pct(a, b) -> float | None:
    try:
        if a is None or b in (None, 0):
            return None
        return round((a - b) / b * 100, 1)
    except TypeError:
        return None


def analyze(history: list[dict[str, Any]], today: str) -> dict[str, Any]:
    by = _series(history)
    days = sorted({r["date"] for r in history})
    d7 = (date.fromisoformat(today) - timedelta(days=7)).isoformat()
    d30 = (date.fromisoformat(today) - timedelta(days=30)).isoformat()
    yesterday = days[-2] if len(days) >= 2 else None

    confirmed, shifts, gap_changes, new_models = [], [], [], []
    rules = []
    for name, rows in by.items():
        last = rows[-1]
        if last["date"] != today:
            continue
        if last["type"] != "model":
            continue
        if len(rows) == 1 and len(days) > 1:
            new_models.append(name)
        # confirmaciones de público
        if last.get("level") == "modelo" and last.get("gender"):
            streak = _run_streak(rows, ("gender", "age_range"))
            if streak >= CONFIRMED_RUNS:
                confirmed.append({
                    "name": name, "gender": last["gender"], "gender_share": last.get("gender_share"),
                    "age_range": last["age_range"], "streak": streak,
                    "since": rows[-streak]["date"], "clicks": last.get("clicks"),
                    "status": "sólido" if streak >= SOLID_RUNS else "confirmado",
                })
        # movimientos de público vs hace 7 días
        ref = _row_on_or_before(rows, d7) or (rows[-2] if len(rows) >= 2 else None)
        if ref and ref is not last and last.get("level") == "modelo" and ref.get("level") == "modelo":
            gs, gr = last.get("gender_share"), ref.get("gender_share")
            if last.get("gender") != ref.get("gender"):
                shifts.append(f"**{name}**: el género dominante pasó de {ref.get('gender')} a {last.get('gender')} ({gs}%) desde el {ref['date']}.")
            elif gs is not None and gr is not None and abs(gs - gr) >= GENDER_SHIFT_PTS:
                shifts.append(f"**{name}**: {last.get('gender')} {gr}% → {gs}% desde el {ref['date']}.")
            if last.get("age_range") != ref.get("age_range"):
                shifts.append(f"**{name}**: la edad dominante pasó de {ref.get('age_range')} a {last.get('age_range')} desde el {ref['date']}.")
        # brecha que cambió desde ayer
        if yesterday:
            y = _row_on_or_before(rows, yesterday)
            if y and y is not last and y.get("gap") != last.get("gap") and last.get("gap"):
                gap_changes.append(f"**{name}**: {y.get('gap')} → {last.get('gap')}.")
        # reglas: sugerencia sostenida de presupuesto
        sug, cur = last.get("suggested_month"), last.get("current_month_est")
        # solo modelos con peso real: ≥10 ventas y al menos USD 100/mes en juego
        if sug and cur is not None and len(rows) >= CONFIRMED_RUNS and (last.get("orders_365d") or last.get("orders") or 0) >= 10 and max(sug, cur) >= 100:
            recent = rows[-CONFIRMED_RUNS:]
            if all((r.get("suggested_month") or 0) > (r.get("current_month_est") or 0) * 1.5 for r in recent):
                rules.append(f"**{name}** lleva {len(recent)}+ corridas con presupuesto sugerido ≥1,5× el actual (USD {cur:,.0f} → {sug:,.0f}/mes): escalar.")
            elif all((r.get("suggested_month") or 0) < (r.get("current_month_est") or 0) * 0.5 for r in recent):
                rules.append(f"**{name}** lleva {len(recent)}+ corridas con presupuesto sugerido ≤0,5× el actual (USD {cur:,.0f} → {sug:,.0f}/mes): revisar creatividad u oferta antes de seguir invirtiendo.")

    # tendencias por marca
    brands = {}
    for name, rows in by.items():
        last = rows[-1]
        if last["type"] != "brand" or last["date"] != today:
            continue
        r7 = _row_on_or_before(rows, d7)
        r30 = _row_on_or_before(rows, d30)
        brands[last["brand"]] = {
            "cpl": last.get("cpl"), "cpl_7": _pct(last.get("cpl"), (r7 or {}).get("cpl")), "cpl_30": _pct(last.get("cpl"), (r30 or {}).get("cpl")),
            "leads": last.get("leads_90d"), "leads_7": _pct(last.get("leads_90d"), (r7 or {}).get("leads_90d")),
            "spend": last.get("spend_month"), "spend_7": _pct(last.get("spend_month"), (r7 or {}).get("spend_month")),
            "frio": last.get("frio_pct"), "frio_7": None if not r7 or r7.get("frio_pct") is None or last.get("frio_pct") is None else round(last["frio_pct"] - r7["frio_pct"], 1),
            "gender": last.get("gender"), "gender_share": last.get("gender_share"), "age_range": last.get("age_range"),
        }
        if r7 and r7.get("frio_pct") is not None and last.get("frio_pct") is not None and last["frio_pct"] - r7["frio_pct"] <= -10:
            rules.append(f"**{last['brand']}** bajó el público frío de {r7['frio_pct']}% a {last['frio_pct']}% en 7 días: seguir así y medir CPL.")

    confirmed.sort(key=lambda c: (-c["streak"], -(c.get("clicks") or 0)))
    return {
        "days": days, "runs": len(days), "first": days[0] if days else today,
        "confirmed": confirmed, "shifts": shifts, "gap_changes": gap_changes,
        "new_models": new_models, "brands": brands, "rules": rules,
    }


# --------------------------------------------------------------------------- nota
def _fmt_delta(v, unit="%") -> str:
    if v is None:
        return "—"
    arrow = "▲" if v > 0 else "▼" if v < 0 else "="
    return f"{arrow} {abs(v):g}{unit}"


def render_note(a: dict[str, Any], today: str, market: dict[str, Any], hermes_lessons: str = "") -> str:
    L = [
        "---", "type: memoria-audiencia", f"updated: {today}",
        "tags: [buyer-persona, sistema, memoria, aprendizaje]", "---",
        "# 🧠 Memoria de Audiencia", "",
        f"> Lo que el sistema aprendió de nuestra audiencia real de compra, corrida tras corrida. "
        f"**{a['runs']} corridas** acumuladas desde el {a['first']}; última: **{today}**. "
        "Fuentes: Meta (edad/género por anuncio, targeting, gasto), ERP (ventas), Bitrix (embudo), Datacar (precios de mercado). "
        "Serie completa en `Sistema/Memoria/historial_audiencia.jsonl`.",
        "",
        "> [!tip] Para Hermes y para quien pauta",
        "> Antes de armar o tocar una campaña: (1) usar el público **confirmado** del modelo, no el de la marca; "
        "(2) mirar *Qué cambió* por si el público se movió; (3) aplicar las *Reglas aprendidas*; "
        "(4) no nombrar competidores en copies públicos (ley PY).",
        "",
        "## ✅ Lo que ya sabemos (público confirmado por modelo)", "",
    ]
    if a["confirmed"]:
        L += ["| Modelo | Público | Corridas iguales | Desde | Clics | Estado |", "|---|---|---|---|---|---|"]
        for c in a["confirmed"]:
            L.append(f"| {c['name']} | {c['gender']} {c['gender_share']}% · {c['age_range']} | {c['streak']} | {c['since']} | {c['clicks']:,} | {'🟢 ' if c['status']=='sólido' else '🟡 '}{c['status']} |")
    else:
        L.append(f"_Todavía no hay {CONFIRMED_RUNS} corridas seguidas con el mismo público. Empieza a confirmar a partir del {(date.fromisoformat(a['first']) + timedelta(days=CONFIRMED_RUNS-1)).isoformat()}._")
    L += ["", "## 🔄 Qué cambió", ""]
    changed = a["shifts"] + a["gap_changes"] + [f"**{m}**: modelo nuevo en el sistema." for m in a["new_models"]]
    L += [f"- {x}" for x in changed] or ["- Sin movimientos relevantes frente a la semana pasada."]
    L += ["", "## 📈 Tendencias por marca (hoy vs hace 7 / 30 días)", "",
          "| Marca | Público | CPL USD | CPL 7d | CPL 30d | Leads 90d | Leads 7d | Gasto/mes | Gasto 7d | Público frío | Frío 7d |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for brand, t in sorted(a["brands"].items(), key=lambda x: -(x[1].get("leads") or 0)):
        L.append(f"| **{brand}** | {t.get('gender','')} {t.get('gender_share') or ''}% · {t.get('age_range','')} | "
                 f"{t['cpl'] if t['cpl'] is not None else '—'} | {_fmt_delta(t['cpl_7'])} | {_fmt_delta(t['cpl_30'])} | "
                 f"{(t['leads'] or 0):,} | {_fmt_delta(t['leads_7'])} | {('USD ' + format(t['spend'], ',.0f')) if t['spend'] else '—'} | {_fmt_delta(t['spend_7'])} | "
                 f"{t['frio'] if t['frio'] is not None else '—'}% | {_fmt_delta(t['frio_7'], ' pts')} |")
    L += ["", "_CPL ▼ es bueno; frío ▼ es bueno (más base propia). Leads y gasto son ventana móvil de 90 días._", "",
          "## ⚔️ Mercado y competencia", ""]
    if market.get("changes"):
        L.append(f"- **{market['changes']} precios de lista** se movieron en el mercado desde la corrida anterior (Datacar). Detalle: [[💰 Precios Mercado 0km (Datacar)]].")
    else:
        L.append("- Sin cambios de precio de lista en el mercado desde la corrida anterior (Datacar).")
    if market.get("versions"):
        L.append(f"- {market['versions']} versiones 0km con precio en el mercado PY; nuestros modelos se comparan contra ±25% de precio en cada nota.")
    L.append("- Promociones y anuncios de la competencia: [[📢 Promociones Competencia]] · Playbook: [[🎯 Playbook Meta Ads]].")
    L += ["", "## 📏 Reglas aprendidas (sostenidas en el tiempo)", ""]
    L += [f"- {r}" for r in a["rules"]] or ["- Todavía no hay reglas sostenidas: se generan cuando una recomendación se repite 3 corridas seguidas."]
    L += ["", "## 🤖 Lecciones de Hermes", "",
          "_Las escribe Hermes cada lunes (cron `aprendizaje-audiencia`) en `Sistema/Memoria/lecciones_hermes.md`; "
          "el pipeline las incrusta acá. Editar ese archivo, no esta nota._", "",
          "<!-- hermes:lecciones -->",
          (hermes_lessons.strip() if hermes_lessons.strip() else "_Todavía sin lecciones semanales._"),
          "<!-- /hermes:lecciones -->", "",
          "---", f"*Actualizado el {today} por el pipeline diario. Relacionado: [[📘 Manual Buyer Persona]] · [[🎧 Feedback Marketing 2026-09-17]] · [[ Buyer Personas MOC]]*"]
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- entrada
def update_memory(personas: list[dict[str, Any]], data_sources: dict[str, Any], vault: Path, today: str | None = None) -> Path:
    today = today or date.today().isoformat()
    mem_dir = vault / "Sistema" / "Memoria"
    hist_path = mem_dir / "historial_audiencia.jsonl"
    note_path = vault / "Sistema" / "🧠 Memoria de Audiencia.md"

    history = [r for r in _load_history(hist_path) if r.get("date") != today]
    history.extend(_snapshot_rows(personas, data_sources, today))
    _save_history(hist_path, history)

    a = analyze(history, today)
    dc = data_sources.get("datacar") or {}
    market = {"changes": len(dc.get("changes") or []), "versions": (dc.get("counts") or {}).get("versions")}
    lessons_path = mem_dir / "lecciones_hermes.md"
    if not lessons_path.exists():
        lessons_path.write_text(
            "<!-- Lecciones semanales de Hermes (cron aprendizaje-audiencia). Bloque nuevo ARRIBA: '### Semana del AAAA-MM-DD' + viñetas. -->\n",
            encoding="utf-8")
    lessons = "\n".join(l for l in lessons_path.read_text(encoding="utf-8").splitlines() if not l.startswith("<!--"))
    text = render_note(a, today, market, lessons)
    note_path.write_text(text, encoding="utf-8")
    (mem_dir / "aprendizajes.json").write_text(
        json.dumps({k: v for k, v in a.items() if k != "days"}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    logger.info("Memoria de audiencia: %d corridas, %d públicos confirmados, %d cambios",
                a["runs"], len(a["confirmed"]), len(a["shifts"]) + len(a["gap_changes"]))
    return note_path
