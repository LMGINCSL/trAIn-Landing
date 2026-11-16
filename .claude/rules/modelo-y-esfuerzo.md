---
paths:
  - ".claude/agents/**"
  - ".claude/skills/**"
---

# Modelo y esfuerzo de agentes y skills

Al crear o revisar un agente (`.claude/agents/*.md`) o una skill (`.claude/skills/*/SKILL.md`),
fija `model` y `effort` según el tipo de trabajo:

| Trabajo | model | effort |
|---|---|---|
| Búsqueda por el código, partes de tests, resúmenes | `sonnet` o `haiku` | `low` |
| Implementación habitual, skills de un solo uso | `sonnet` | `medium` |
| Revisión de auth, permisos o RLS, migraciones destructivas, prompts del producto | `opus` | `high` |

- Nunca un modelo rebajado en auth, RLS, migraciones destructivas ni prompts que lee el producto.
- En repos muy grandes, la búsqueda va con `sonnet`, no con `haiku`.
- El modelo y el esfuerzo se eligen al empezar: cambiarlos a mitad de sesión obliga a releer todo
  el contexto sin caché.
