---
version_cuestionario: {{VERSION_CUESTIONARIO}}
fecha: {{AAAA-MM-DD}}
---

# Perfil personal LMGINC

> Estas preferencias ajustan la forma de trabajar. No anulan las reglas del equipo de cada repo
> (CLAUDE.md y .claude/rules/). Si una preferencia choca con una regla del equipo, se sigue la
> regla del equipo y se avisa a la persona de qué preferencia no se ha podido aplicar y por qué.

## Comunicación
- Idioma: {{idioma}}
- Detalle: {{detalle}}

## Autonomía
- Forma de trabajar: {{forma-de-trabajar}}
- Cuándo preguntar: {{cuando-preguntar}}

## Git
- Ramas: {{ramas}}
- Tamaño de commits: {{commits}}
- Formato de commit: {{formato-commit}}

## GitHub
- Quién abre el PR: {{quien-abre-pr}}
- Subir ramas (git push): {{subir-ramas}}
- Además de los PR: {{github-extra: las opciones elegidas separadas por « · »}}

## Comandos
- Sin preguntar: {{sin-preguntar}}
- Preguntar siempre: {{pedir-siempre: las opciones elegidas separadas por « · »}}

## Calidad
- Tests: {{tests}}
- Revisión: {{revision}}

## Manías
{{manias: una línea "- ..." por opción elegida; el texto libre de Other, tal cual}}

## Permisos aplicados en este dispositivo
<!-- lmginc-permisos: inicio -->
{{una línea "- ask: Bash(...)" o "- deny: Bash(...)" por regla escrita en ~/.claude/settings.json; "- ninguno" si no se escribió ninguna}}
<!-- lmginc-permisos: fin -->
