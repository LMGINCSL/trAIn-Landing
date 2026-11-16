---
name: lmginc-onboarding
description: Cuestionario de onboarding personal de LMGINC. Crea o rehace el perfil personal (~/.claude/lmginc/profile.md) y responde las preguntas propias del repo (CLAUDE.local.md). Úsala cuando falte el perfil o lo indique el aviso de inicio de sesión.
argument-hint: "[rehacer|repo]"
allowed-tools:
  - Read
  - Glob
  - Bash(git check-ignore *)
  - Bash(git rev-parse *)
---

# Onboarding personal LMGINC

Corre en la sesión principal (usa AskUserQuestion, que no existe en subagentes). Las preguntas se
hacen con AskUserQuestion, nunca como texto en el chat.

Ficheros de esta skill (léelos con Read antes de empezar):
- `${CLAUDE_SKILL_DIR}/preguntas-comunes.md`: las 5 rondas comunes y `version_cuestionario`.
- `${CLAUDE_SKILL_DIR}/plantilla-perfil.md`: la forma del perfil.

## 1. Elegir el modo

`$ARGUMENTS` es uno de:
- vacío: si `~/.claude/lmginc/profile.md` no existe, rondas comunes y después preguntas del repo.
  Si existe y su `version_cuestionario` es la actual, solo las preguntas del repo, y solo si
  faltan (paso 4). Si todo está hecho, dilo en una línea y recuerda que existe el modo `rehacer`.
- `rehacer`: rondas comunes otra vez. Antes de escribir, copia el perfil existente a
  `~/.claude/lmginc/profile.prev.md` (se sobrescribe la copia anterior). Después, preguntas del repo
  solo si faltan.
- `repo`: solo las preguntas de `.claude/onboarding/questions.md` del repo actual.

`~` es la carpeta personal: `$HOME` en macOS y Linux, `%USERPROFILE%` en Windows. Crea
`~/.claude/lmginc/` si no existe. El perfil es de la persona y del dispositivo: no se copia a ningún
repo ni se sube a ningún sitio.

## 2. Rondas comunes

Una llamada a AskUserQuestion por cada `# Ronda` de `preguntas-comunes.md`, en orden, con todas
las preguntas de esa ronda en la misma llamada (nunca más de 4). Para cada pregunta:
- `header`, `question` y `multiSelect` salen de `header`, `pregunta` y `multiSelect` (`sí` = true).
- `options`: cada línea `- Etiqueta: descripción` da `label` y `description`, en el mismo orden.
  La primera es la recomendada y su etiqueta lleva «(Recomendado)»; no reordenes ni reescribas.
- No añadas una opción de texto libre: la herramienta ya ofrece «Other».

Entre rondas no expliques nada: pasa a la siguiente. Si la persona responde con texto libre,
guárdalo tal cual.

## 3. Escribir el perfil

Escribe `~/.claude/lmginc/profile.md` siguiendo `plantilla-perfil.md`:
- `version_cuestionario`: el de `preguntas-comunes.md`; `fecha`: hoy en `AAAA-MM-DD`.
- La cláusula de precedencia va al principio, literal.
- Cada respuesta en su sección: la etiqueta elegida sin «(Recomendado)», o el texto libre.
- Nada más: ni nombres de repos, ni datos del equipo, ni secretos.

## 4. Preguntas del repo

Si existe `.claude/onboarding/questions.md` en la raíz del repo (`git rev-parse --show-toplevel`):
1. Léelo. Su frontmatter da `version`. Mismo formato que las rondas comunes; agrupa las preguntas
   de 4 en 4 por llamada si el fichero no trae rondas.
2. Escribe las respuestas en `CLAUDE.local.md` de la raíz del repo, en una sección delimitada así:

   ```markdown
   <!-- lmginc-onboarding-repo: v<version> <AAAA-MM-DD> -->
   ## Preferencias personales en este repo
   ### <seccion>
   - <header>: <respuesta>
   <!-- /lmginc-onboarding-repo -->
   ```

   Si `CLAUDE.local.md` no existe, créalo con esa sección. Si existe y ya tiene una sección
   delimitada (de cualquier versión), sustitúyela entera. Si existe sin sección, añádela al final.
   El resto del fichero no se toca.
3. Comprueba que `CLAUDE.local.md` no se va a versionar: `git check-ignore -q CLAUDE.local.md`.
   Si no está ignorado, díselo a la persona y propón añadir `CLAUDE.local.md` a `.git/info/exclude`
   (local, no se versiona) y avisar al equipo de que falta en `.gitignore`. No edites `.gitignore`
   sin que la persona lo pida.

Si el repo no tiene `questions.md`, no hay nada que hacer en este paso.

## 5. Cerrar

En 3 a 5 líneas: qué ficheros se escribieron, que las preferencias se aplican desde la próxima
sesión (o tras `/clear`), y que el `CLAUDE.md` del repo importa el perfil con
`@~/.claude/lmginc/profile.md`: la primera vez Claude Code pide aprobar ese import externo; si se
rechaza, no vuelve a preguntar y el perfil no se carga en este repo.

Si una respuesta choca con una regla del equipo (por ejemplo, «Claude directamente» abre PR pero el
repo pide permiso para `gh pr create`), dilo ahora: gana la regla del equipo.
