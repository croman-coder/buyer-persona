#!/usr/bin/env bash
# =============================================================================
# Publica en GitHub una copia FILTRADA de este repo.
#
# Por cada corrida con cambios, el remoto `github` recibe un commit en la rama
# `main` con el árbol de HEAD menos las rutas de EXCLUIR. No toca el árbol de
# trabajo ni el índice, y solo viaja lo que está versionado.
#
# Antes de subir revisa, y si encuentra algo NO sube:
#   - secretos (tokens, claves privadas, contraseñas, webhooks) en cualquier archivo;
#   - archivos que nunca deben viajar por su nombre (.env, claves, planillas, semillas).
#
# Uso:
#   scripts/publicar_github.sh --probar     arma el árbol y revisa, sin subir
#   scripts/publicar_github.sh              publica
# El remoto se agrega una vez:  git remote add github https://github.com/croman-coder/buyer-persona.git
# =============================================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

REMOTO="${GITHUB_REMOTO:-github}"
RAMA="${GITHUB_RAMA:-main}"

# Rutas que NO viajan a GitHub.
EXCLUIR=(
  "Buyer Persona/Seguridad"   # hallazgos, puertos e inventario de los servidores
  ".github/workflows"         # el pipeline real corre en el servidor; GitHub tampoco deja subirlo sin el permiso `workflow`
)

# Formatos de token reconocibles: distinguen mayúsculas (un hash hexadecimal puede contener «eaa»).
PATRON_FORMATOS='EAA[A-Za-z0-9]{40,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{35}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}|/rest/[0-9]+/[A-Za-z0-9]{12,}/'
# Asignaciones tipo CLAVE=valor largo: no distinguen mayúsculas.
PATRON_ASIGNACION='(TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY)[A-Za-z_]*[[:space:]]*[=:][[:space:]]*.?[A-Za-z0-9/_+=.-]{20,}'
PATRON_NOMBRE='(^|/)\.env($|\.)|\.pem$|\.key$|id_rsa|emails?\.csv$|phones?\.csv$|(^|/)ENCUESTA|(^|/)data/fuentes/|(^|/)audiencias_meta/|\.xlsx?$|\.sqlite3?$|\.db$'

# 1. Árbol de HEAD sin lo excluido, armado en un índice temporal.
IDX="$(mktemp)"
trap 'rm -f "$IDX"' EXIT
export GIT_INDEX_FILE="$IDX"
git read-tree HEAD
TOTAL="$(git ls-files | wc -l)"
for ruta in "${EXCLUIR[@]}"; do
  git rm -r -q --cached --ignore-unmatch -- "$ruta"
done
ARBOL="$(git write-tree)"
IN="$(git ls-files | wc -l)"
unset GIT_INDEX_FILE
echo "Árbol a publicar: $IN archivos de $TOTAL (excluidos: $((TOTAL - IN)) en ${EXCLUIR[*]})"

# 2. Revisión de secretos y de nombres de archivo. Solo se imprimen rutas, nunca el contenido.
SECRETOS="$( { git grep -I -l -E "$PATRON_FORMATOS" "$ARBOL" 2>/dev/null || true
               git grep -I -l -i -E "$PATRON_ASIGNACION" "$ARBOL" 2>/dev/null || true; } | sed "s#^$ARBOL:##" | sort -u )"
NOMBRES="$(git ls-tree -r --name-only "$ARBOL" | grep -E "$PATRON_NOMBRE" | grep -vE '\.env\.example$' || true)"
if [[ -n "$SECRETOS" || -n "$NOMBRES" ]]; then
  echo "❌ NO se publica. Revisar antes:" >&2
  [[ -n "$SECRETOS" ]] && { echo "  Posibles secretos en:" >&2; echo "$SECRETOS" | sed 's/^/    /' >&2; }
  [[ -n "$NOMBRES" ]] && { echo "  Archivos que no deben viajar:" >&2; echo "$NOMBRES" | sed 's/^/    /' >&2; }
  echo "  Si es un falso positivo, corregir el texto o sumar la ruta a EXCLUIR." >&2
  exit 1
fi
echo "✅ Revisión de secretos y nombres: limpia"
[[ "${1:-}" == "--probar" ]] && { echo "(modo --probar: no se sube nada)"; exit 0; }

# 2b. Estado actual del remoto (si todavía no tiene la rama, se parte de cero).
git fetch -q "$REMOTO" "$RAMA" 2>/dev/null || true
PREV="$(git rev-parse -q --verify "refs/remotes/$REMOTO/$RAMA" || true)"
if [[ -n "$PREV" && "$(git rev-parse "$PREV^{tree}")" == "$ARBOL" ]]; then
  echo "Sin cambios desde la última exportación ($(git rev-parse --short "$PREV"))."
  exit 0
fi

# 3. Un commit por exportación, encadenado al anterior.
MSG="Exportación $(date '+%Y-%m-%d %H:%M') · repo del servidor en $(git rev-parse --short HEAD) · $IN archivos"
COMMIT="$(git commit-tree "$ARBOL" ${PREV:+-p "$PREV"} -m "$MSG")"
git push -q "$REMOTO" "$COMMIT:refs/heads/$RAMA"
git fetch -q "$REMOTO" "$RAMA" 2>/dev/null || true
echo "📤 Publicado en $REMOTO/$RAMA: $(git rev-parse --short "$COMMIT") · $MSG"
