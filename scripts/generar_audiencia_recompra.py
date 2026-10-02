#!/usr/bin/env python3
"""
Base de RECOMPRA / fidelización desde las ventas reales del ERP.

Pedido de marketing (17-sep-2026): "al que compró una Duster hace 3-4 años
mostrale el anuncio de Boreal". El ERP cargado arranca en abril 2024, así
que hoy la cohorte más vieja tiene ~2,5 años; el script arma cohortes por
meses desde la compra y las va a ir madurando solas con cada corrida.

Salida:
- output/audiencias_meta/recompra/<Marca>/recompra_<cohorte>.csv
  (email/teléfono hasheados SHA-256, formato Custom Audience de Meta;
  carpeta en .gitignore, uso interno)
- Buyer Persona/Buyer Personas/Audiencias/🔁 Base de Recompra (ERP).md
  (solo conteos por marca/modelo/cohorte, sin datos personales)

Uso:  venv/bin/python3 scripts/generar_audiencia_recompra.py [--min-meses 12]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.generar_audiencias_meta import MARCA_MAP, norm_email, norm_phone_py  # noqa: E402

XLSX = ROOT / "data" / "fuentes" / "ventas_unificadas.xlsx"
OUT_DIR = ROOT / "output" / "audiencias_meta" / "recompra"
NOTA = ROOT / "Buyer Persona" / "Buyer Personas" / "Audiencias" / "🔁 Base de Recompra (ERP).md"

# Cohortes por meses desde la compra: (nombre, mínimo, máximo)
COHORTES = [
    ("36m_plus", 36, 999),   # 3+ años: la cohorte que pidió marketing (Duster/Arkana → Boreal)
    ("24_36m", 24, 36),      # 2-3 años: ya en ventana de recompra
    ("18_24m", 18, 24),      # entra este semestre
    ("12_18m", 12, 18),      # precalentar: postventa, service, valor de reventa
]

# Contactos que NO son del cliente (cargados con el importador competidor)
MARCAS_SIN_CONTACTO = {"Mitsubishi"}

# A qué modelo conviene invitar a cada comprador (escalera de recompra).
# Sin entrada → renovación del mismo modelo.
ESCALERA = {
    "Renault": {"KWID": "Kardian", "SANDERO": "Kardian", "STEPWAY": "Kardian", "LOGAN": "Kardian", "SYMBOL": "Kardian",
                "KARDIAN": "Duster / Boreal", "DUSTER": "Boreal", "ARKANA": "Boreal", "CAPTUR": "Boreal",
                "OROCH": "Oroch (renovación)", "KOLEOS": "Boreal / Koleos"},
    "GWM": {"JOLION": "Haval H6", "H6": "Haval H7 / Tank 300", "HAVAL": "Haval H7 / Tank 300",
            "H9": "Tank 500", "TANK": "Tank 500", "POER": "Poer (renovación) / Tank 300",
            "WINGLE": "Poer", "ORA": "Haval Jolion"},
    "Jetour": {"X70": "X90 / T2", "DASHING": "T2", "X50": "X70 / Dashing", "TRAVELLER": "T2 / G700",
               "T1": "T2", "X90": "T2 / G700"},
    "JAC": {"JS4": "JS6 / T9", "T8": "T9", "X200": "X200 (renovación)", "SUNRAY": "Sunray (renovación)"},
    "Soueast": {"S06": "S07", "S07": "S09"},
}


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def meses_desde(fecha: pd.Timestamp, hoy: date) -> int:
    return (hoy.year - fecha.year) * 12 + (hoy.month - fecha.month)


def modelo_base(modelo: str) -> str:
    """'DUSTER 1.6 ICONIC' -> 'DUSTER' (primer token útil, en mayúsculas)."""
    m = str(modelo or "").strip().upper()
    for prefijo in ("HAVAL ", "NEW ", "NUEVO ", "NUEVA "):
        if m.startswith(prefijo) and len(m.split()) > 1:
            return prefijo + m.split()[1]
    return m.split()[0] if m else ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-meses", type=int, default=12, help="ignorar compras más recientes que N meses")
    ap.add_argument("--hoy", default=date.today().isoformat())
    args = ap.parse_args()
    hoy = date.fromisoformat(args.hoy)

    df = pd.read_excel(XLSX, sheet_name="Datos", header=2)
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.dropna(subset=["Fecha"])
    df["marca"] = df["Marca"].astype(str).str.strip().str.upper().map(MARCA_MAP).fillna("OTROS")
    df["modelo"] = df["Modelo"].map(modelo_base)
    df["meses"] = df["Fecha"].map(lambda f: meses_desde(f, hoy))
    df["email"] = df["E-Mail"].map(norm_email)
    df["tel"] = df["Teléfonos"].map(norm_phone_py)
    df = df[df["meses"] >= args.min_meses]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    NOTA.parent.mkdir(parents=True, exist_ok=True)

    resumen_marca: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    contactables: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    por_modelo: dict[str, Counter] = defaultdict(Counter)
    archivos: list[tuple[str, str, int, Path]] = []

    for marca, g in df.groupby("marca"):
        if marca == "OTROS":
            continue
        for nombre, lo, hi in COHORTES:
            c = g[(g["meses"] >= lo) & (g["meses"] < hi)]
            resumen_marca[marca][nombre] = len(c)
            por_modelo[f"{marca}|{nombre}"].update(c["modelo"].tolist())
            if marca in MARCAS_SIN_CONTACTO or c.empty:
                continue
            filas = {(sha(e) if e else "", sha(t) if t else "") for e, t in zip(c["email"], c["tel"]) if e or t}
            contactables[marca][nombre] = len(filas)
            carpeta = OUT_DIR / marca
            carpeta.mkdir(parents=True, exist_ok=True)
            path = carpeta / f"recompra_{nombre}.csv"
            path.write_text("email,phone\n" + "\n".join(f"{e},{t}" for e, t in sorted(filas)) + "\n", encoding="utf-8")
            archivos.append((marca, nombre, len(filas), path))

    # ----- nota (solo agregados) -----
    etiqueta = {"36m_plus": "≥ 36 meses (3+ años)", "24_36m": "24-36 meses (en recompra)",
                "18_24m": "18-24 meses (entra este semestre)", "12_18m": "12-18 meses (precalentar)"}
    L = [
        "---", "type: audiencia-recompra", "tags: [marketing, meta-ads, audiencias, recompra, fidelizacion]", "---",
        "# 🔁 Base de Recompra (ERP)", "",
        f"> Generado el **{hoy.isoformat()}** desde `FacturacionUnidades-7343.xlsx` "
        f"(ventas {df['Fecha'].min():%Y-%m} → {df['Fecha'].max():%Y-%m}, {len(df):,} unidades con ≥{args.min_meses} meses).",
        "> Sirve para la **campaña de fidelización**: mostrarle al que ya compró el modelo al que le toca subir. "
        "Los CSV (hash SHA-256, formato Custom Audience) están en `output/audiencias_meta/recompra/<Marca>/`, fuera de git.",
        "",
        "## Unidades por marca y cohorte", "",
        "| Marca | " + " | ".join(etiqueta[n] for n, _, _ in COHORTES) + " | Contactables (misma secuencia) |",
        "|---|" + "---|" * (len(COHORTES) + 1),
    ]
    for marca in sorted(resumen_marca, key=lambda m: -sum(resumen_marca[m].values())):
        r = resumen_marca[marca]
        if marca in MARCAS_SIN_CONTACTO:
            cont = "⚠️ sin contacto propio (ver nota)"
        else:
            cont = " / ".join(str(contactables[marca].get(n, 0)) for n, _, _ in COHORTES)
        L.append(f"| **{marca}** | " + " | ".join(f"{r.get(n, 0):,}" for n, _, _ in COHORTES) + f" | {cont} |")
    L += ["", "## Qué ofrecerle a cada uno (escalera de recompra)", "",
          "| Marca | Compró | Unidades ≥18m | Invitar a |", "|---|---|---|---|"]
    for marca in sorted(resumen_marca, key=lambda m: -sum(resumen_marca[m].values())):
        tot = Counter()
        for n, lo, _ in COHORTES:
            if lo >= 18:
                tot.update(por_modelo[f"{marca}|{n}"])
        for modelo, n in tot.most_common(8):
            if not modelo:
                continue
            destino = ESCALERA.get(marca, {}).get(modelo, f"{modelo.title()} (renovación)")
            L.append(f"| {marca} | {modelo.title()} | {n:,} | {destino} |")
    L += [
        "", "## Cómo usarla", "",
        "1. Subir el CSV de la cohorte a la cuenta madre de la marca como *Custom Audience → Customer list* "
        "(identificadores ya hasheados, columnas `email` y `phone`).",
        "2. Campaña **separada** de la de generación de leads: objetivo Clientes potenciales, público = esa lista, "
        "creatividad del modelo destino (ver escalera), presupuesto propio.",
        "3. Excluir esa misma lista de las campañas de público frío de la marca (no pagar dos veces por el mismo cliente).",
        "4. Medir en Bitrix con el origen `Meta madre` + nombre de campaña `RECOMPRA <MARCA>`.",
        "",
        "## Notas",
        f"- Solo el {df['email'].notna().mean():.0%} de las filas del ERP trae email y el {df['tel'].notna().mean():.0%} teléfono: "
        "la base contactable es menor que las unidades vendidas. Mejorar la carga en el ERP agranda esta audiencia sola.",
        "- **Mitsubishi:** el ERP tiene cargado el contacto del importador (Nipon) en casi todas las filas; no se genera CSV. "
        "Recuperar contactos reales desde Bitrix antes de usar.",
        "- Base unificada desde julio 2018 (`scripts/unificar_ventas.py`): la cohorte de 3+ años ya existe. "
        "El email/teléfono solo viene cargado para las ventas de abr-2024 en adelante; las anteriores cuentan como unidades "
        "pero no son contactables hasta recuperar el contacto desde Bitrix.",
        "- Un cliente que compró dos veces aparece en la cohorte de cada compra; Meta deduplica al subir.",
        "",
        "Relacionado: [[📊 Semillas Custom Audiences - Ventas Reales]] · [[ Buyer Personas MOC]]",
    ]
    NOTA.write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"Unidades consideradas (≥{args.min_meses}m): {len(df):,}")
    for marca, nombre, n, path in archivos:
        print(f"  {marca:12s} {nombre:8s} {n:5d} contactos → {path.relative_to(ROOT)}")
    print(f"Nota: {NOTA.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
