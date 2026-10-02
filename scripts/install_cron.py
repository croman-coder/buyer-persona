#!/usr/bin/env python3
"""
Instala / desinstala / muestra el cron del pipeline de Buyer Persona.

Uso:
    venv/bin/python3 scripts/install_cron.py --install      # Instala (diario 06:00)
    venv/bin/python3 scripts/install_cron.py --install --schedule "0 6,18 * * *"
    venv/bin/python3 scripts/install_cron.py --status
    venv/bin/python3 scripts/install_cron.py --uninstall

El cron ejecuta scripts/run_pipeline.sh, que a su vez corre main.py,
guarda logs en logs/ y deja estado en logs/last_status.txt.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path("/home/croman/Escritorio/BUYER PERSONA")
SCRIPT_PATH = PROJECT_DIR / "scripts" / "run_pipeline.sh"
MARKER_BEGIN = "# >>> BEGIN buyer-persona cron >>>"
MARKER_END = "# <<< END buyer-persona cron <<<"


def _current_crontab() -> str:
    """Devuelve el crontab actual del usuario (string vacío si no hay)."""
    try:
        out = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            check=False,
        )
        # crontab -l devuelve exit 1 si no hay crontab → string vacío
        return out.stdout if out.returncode == 0 else ""
    except FileNotFoundError:
        print("❌ El comando 'crontab' no está disponible en este sistema.")
        sys.exit(1)


def _write_crontab(content: str) -> None:
    """Escribe el crontab completo (via stdin)."""
    proc = subprocess.run(
        ["crontab", "-"],
        input=content,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        print(f"❌ No se pudo escribir el crontab: {proc.stderr}")
        sys.exit(1)


def _extract_block(crontab: str) -> tuple[str, str | None]:
    """
    Separa el crontab en (resto, bloque_buyer_persona marcado).
    Si no hay bloque marcado, devuelve (crontab_completo, None).
    """
    if MARKER_BEGIN not in crontab or MARKER_END not in crontab:
        return crontab, None

    before = crontab[: crontab.find(MARKER_BEGIN)]
    after = crontab[crontab.find(MARKER_END) + len(MARKER_END) :]
    block = crontab[
        crontab.find(MARKER_BEGIN) : crontab.find(MARKER_END) + len(MARKER_END)
    ]
    return (before.rstrip() + "\n" + after.rstrip() + "\n").strip() + "\n", block


def _find_unmarked_crons(crontab: str) -> list[str]:
    """
    Busca líneas de crontab que ejecuten run_pipeline.sh pero NO estén dentro
    de un bloque marcado (instaladas manualmente). Devuelve las líneas tal cual.
    """
    script_name = SCRIPT_PATH.name
    found: list[str] = []
    in_block = False
    for ln in crontab.splitlines():
        if MARKER_BEGIN in ln:
            in_block = True
            continue
        if MARKER_END in ln:
            in_block = False
            continue
        if in_block:
            continue
        if script_name in ln and str(SCRIPT_PATH) in ln and not ln.strip().startswith("#"):
            found.append(ln.strip())
    return found


def install(schedule: str = "0 6 * * *") -> None:
    """Instala el cron con el schedule indicado."""
    if not SCRIPT_PATH.exists():
        print(f"❌ No existe {SCRIPT_PATH}")
        sys.exit(1)

    # Permisos de ejecución
    SCRIPT_PATH.chmod(0o755)

    current = _current_crontab()
    rest, existing_block = _extract_block(current)

    line = f'{schedule} "{SCRIPT_PATH}"'

    block = f"""{MARKER_BEGIN}
# Buyer Persona — recopilación automática de Google Ads + Meta Ads
# Instalado: {os.popen('date').read().strip()}
# Para editar: venv/bin/python3 scripts/install_cron.py --status
{line}
{MARKER_END}"""

    if existing_block:
        print("ℹ️  Ya existe un cron de buyer-persona marcado. Se reemplazará.")
        print(f"   Anterior:\n   {existing_block.replace(chr(10), chr(10)+'   ')}")

    # Detectar crons manuales (sin marcar) que ya ejecutan run_pipeline.sh
    manual = _find_unmarked_crons(current)
    if manual and not existing_block:
        print("\n⚠️  ATENCIÓN: detecté cron(s) EXISTENTE(s) (instalado(s) a mano):")
        for ln in manual:
            print(f"   → {ln}")
        print(
            "\nSi continuás, voy a AGREGAR un bloque marcado además del existente.\n"
            "Para evitar duplicados, recomendación:\n"
            "   1. Cancelá (Ctrl+C)\n"
            "   2. Borralo a mano con: crontab -e\n"
            "   3. Volvé a correr este script\n"
        )
        try:
            resp = input("¿Continuar igualmente? [s/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelado.")
            sys.exit(0)
        if resp not in ("s", "si", "sí", "y", "yes"):
            print("Cancelado. No se modificó el crontab.")
            sys.exit(0)

    new_crontab = rest.rstrip()
    if new_crontab and not new_crontab.endswith("\n"):
        new_crontab += "\n"
    new_crontab += "\n" + block + "\n"

    _write_crontab(new_crontab)
    print(f"✅ Cron instalado con schedule: {schedule}")
    print(f"   Ejecuta: {SCRIPT_PATH}")
    print(f"   Logs en: {PROJECT_DIR / 'logs'}")
    print("\nPara verificar:")
    print("   crontab -l")
    print("\nPara desinstalar:")
    print("   venv/bin/python3 scripts/install_cron.py --uninstall")


def uninstall() -> None:
    """Remueve el bloque de cron de buyer-persona."""
    current = _current_crontab()
    rest, block = _extract_block(current)

    if block is None:
        print("ℹ️  No hay cron de buyer-persona instalado. Nada que desinstalar.")
        return

    _write_crontab(rest if rest.strip() else "")
    print("✅ Cron de buyer-persona desinstalado.")


def status() -> None:
    """Muestra el estado del cron de buyer-persona (y todo el crontab)."""
    current = _current_crontab()
    _, block = _extract_block(current)

    print("=" * 60)
    if block:
        print("✅ Cron de buyer-persona INSTALADO:")
        print("-" * 60)
        for ln in block.splitlines():
            if (
                ln.strip()
                and not ln.startswith("#")
                and MARKER_BEGIN not in ln
                and MARKER_END not in ln
            ):
                print(f"   Schedule + comando: {ln}")
        print("-" * 60)
    else:
        print("❌ Cron de buyer-persona NO instalado.")
        print("   Instalar con: venv/bin/python3 scripts/install_cron.py --install")

    # Detectar crons manuales no marcados
    manual = _find_unmarked_crons(current)
    if manual:
        print("\n⚠️  CRON(S) DETECTADO(S) SIN MARCAR (instalado(s) a mano):")
        for ln in manual:
            print(f"   → {ln}")
        print("   Estos NO se pueden desinstalar con --uninstall (borrar a mano: crontab -e)")

    print("\n📝 Crontab completo:")
    print("-" * 60)
    if current.strip():
        print(current.rstrip())
    else:
        print("(vacío)")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gestiona el cron del pipeline de Buyer Persona."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--install",
        action="store_true",
        help="Instala el cron (diario a las 06:00 por defecto)",
    )
    group.add_argument(
        "--uninstall",
        action="store_true",
        help="Desinstala el cron de buyer-persona",
    )
    group.add_argument(
        "--status",
        action="store_true",
        help="Muestra el estado del cron",
    )
    parser.add_argument(
        "--schedule",
        default="0 6 * * *",
        help='Schedule cron (default: "0 6 * * *" = diario 06:00). '
        'Ej: "0 6,18 * * *" (2 veces/día), "0 6 * * 1" (lunes).',
    )

    args = parser.parse_args()

    if args.install:
        install(args.schedule)
    elif args.uninstall:
        uninstall()
    elif args.status:
        status()


if __name__ == "__main__":
    main()