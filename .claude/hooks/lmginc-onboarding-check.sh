#!/bin/sh
# lmginc-onboarding-check.sh - hook SessionStart (matcher startup|clear) del kit comun LMGINC.
#
# Imprime UNA linea de contexto (la primera que aplique) o nada:
#   1. falta ~/.claude/lmginc/profile.md                         -> el cuestionario es la primera tarea
#   2. el perfil es de una version anterior del cuestionario    -> aviso, se puede rehacer
#   3. el repo tiene .claude/onboarding/questions.md y CLAUDE.local.md no tiene la marca
#      <!-- lmginc-onboarding-repo: vN ... --> de la version actual -> aviso, modo repo
#   4. en otro caso, silencio.
# POSIX sh puro (sin jq, sin python). Nunca sale con 2: nunca bloquea el arranque.
# El mismo fichero vive en el plugin (hooks/) y, como respaldo sin plugin, en .claude/hooks/.

VERSION_DEFECTO=1

# Consumir el JSON del evento (no se necesita). Si stdin es una terminal, no esperar.
if [ ! -t 0 ]; then cat >/dev/null 2>&1; fi

aqui=$(CDPATH='' cd -- "$(dirname -- "$0")" 2>/dev/null && pwd)
comunes="$aqui/../skills/lmginc-onboarding/preguntas-comunes.md"

# leer_numero FICHERO CLAVE -> primer numero de una linea "CLAVE: N" (vacio si no hay)
leer_numero() {
  [ -f "$1" ] || return 0
  sed -n "s/^$2:[[:space:]]*\([0-9][0-9]*\).*/\1/p" "$1" 2>/dev/null | head -n 1
}

if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  skill="/lmginc-core:lmginc-onboarding"
else
  skill="/lmginc-onboarding"
fi

actual=$(leer_numero "$comunes" version_cuestionario)
[ -n "$actual" ] || actual=$VERSION_DEFECTO

perfil="${HOME:-}/.claude/lmginc/profile.md"
if [ ! -f "$perfil" ]; then
  printf '%s\n' "No existe el perfil personal de LMGINC en este dispositivo (~/.claude/lmginc/profile.md). En los repos de LMGINC, la primera tarea de una sesión sin perfil es el cuestionario de la skill lmginc-onboarding ($skill); las demás tareas esperan a que termine."
  exit 0
fi

del_perfil=$(leer_numero "$perfil" version_cuestionario)
[ -n "$del_perfil" ] || del_perfil=0
if [ "$del_perfil" -lt "$actual" ]; then
  printf '%s\n' "El perfil personal de LMGINC (~/.claude/lmginc/profile.md) responde a la versión $del_perfil del cuestionario y la actual es la $actual. Se puede repetir con $skill rehacer; mientras tanto, el perfil actual sigue valiendo."
  exit 0
fi

proyecto="${CLAUDE_PROJECT_DIR:-$PWD}"
preguntas="$proyecto/.claude/onboarding/questions.md"
if [ -f "$preguntas" ]; then
  del_repo=$(leer_numero "$preguntas" version)
  [ -n "$del_repo" ] || del_repo=1
  if ! grep -Eq "<!--[[:space:]]*lmginc-onboarding-repo:[[:space:]]*v$del_repo([^0-9]|\$)" "$proyecto/CLAUDE.local.md" 2>/dev/null; then
    printf '%s\n' "Este repo tiene preguntas propias de onboarding (.claude/onboarding/questions.md, versión $del_repo) que no están respondidas en CLAUDE.local.md. Se responden con $skill repo."
  fi
fi
exit 0
