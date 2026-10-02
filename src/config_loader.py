"""
Carga y resuelve la configuración del proyecto.

- Lee ``config/settings.yaml``
- Carga variables de entorno desde ``.env``
- Resuelve placeholders ``${VAR}`` con valores de entorno
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Patrón para detectar placeholders tipo ${VAR_ENTORNO}
_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _resolve_env_placeholders(obj: Any) -> Any:
    """Recorre recursivamente un diccionario/lista resolviendo ``${VAR}``."""
    if isinstance(obj, str):
        def _replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            return os.getenv(var_name, "")
        return _VAR_PATTERN.sub(_replacer, obj)
    if isinstance(obj, dict):
        return {k: _resolve_env_placeholders(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_placeholders(v) for v in obj]
    return obj


def load_config(config_path: str | Path = "config/settings.yaml") -> dict[str, Any]:
    """
    Carga la configuración YAML resolviendo variables de entorno.

    Args:
        config_path: Ruta al archivo ``settings.yaml``.

    Returns:
        Diccionario de configuración con todos los placeholders resueltos.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {config_path}")

    # Cargar .env si existe (busca en el directorio raíz del proyecto)
    project_root = config_path.parent.parent if config_path.parent.name == "config" else Path.cwd()
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    with open(config_path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    if not isinstance(raw_config, dict):
        raise ValueError("El archivo de configuración debe contener un diccionario en la raíz.")

    return _resolve_env_placeholders(raw_config)