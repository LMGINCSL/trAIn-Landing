# Git en este repo (política común LMGINC)

- Una rama corta por tarea, creada desde la rama principal, y un PR para integrarla.
- Nunca `git push` a la rama principal ni `git push --force`: están bloqueados por permisos y por el guard.
- `git push` de una rama de trabajo pide permiso a la persona.
- `git commit` está permitido en una rama de trabajo; en la rama principal pide permiso (lo normal es crear antes la rama).
- `gh pr create` pide permiso; `gh pr merge` está prohibido: el merge lo hace una persona.
- Si una preferencia personal (perfil o CLAUDE.local.md) choca con esto, gana esta regla y se avisa a la persona.
- Si un bloqueo del guard parece un error, no se rodea con otro comando: se cuenta a la persona qué se quería hacer y por qué.
