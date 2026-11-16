#!/bin/sh
# py.sh: lanzador portable de Python para los hooks de Claude Code (kit comun LMGINC).
# Prueba, en este orden: $PROJECT_PYTHON, python3, python, py. Usa el primero que arranca
# de verdad (en Windows, el python3 de la tienda es un atajo que no ejecuta nada).
# Si no hay ninguno, sale con 2: en un hook PreToolUse eso bloquea la accion (fallo cerrado).
# Uso: sh .claude/hooks/py.sh script.py [args...]
for c in "${PROJECT_PYTHON:-}" python3 python py; do
  [ -n "$c" ] || continue
  if "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' </dev/null >/dev/null 2>&1; then
    exec "$c" "$@"
  fi
done
echo "No hay Python 3 para los hooks de Claude (PROJECT_PYTHON, python3, python, py): se bloquea por seguridad." >&2
exit 2
