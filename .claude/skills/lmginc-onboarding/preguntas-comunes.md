---
version_cuestionario: 2
fecha: 2026-11-15
---

# Preguntas comunes del onboarding LMGINC

Siete rondas. Cada ronda es UNA llamada a AskUserQuestion con sus preguntas en este orden
(1 a 4 por llamada). Las opciones se copian tal cual: la primera es la recomendada.
La herramienta añade sola la opción «Other» para texto libre; no se escribe aquí.
`seccion` es la sección del perfil donde se guarda la respuesta.
Si cambia algo de este fichero que altere el significado de una respuesta, se sube
`version_cuestionario` (el hook avisa entonces de que el perfil es antiguo).

Las rondas de GitHub y de comandos se traducen además en permisos del dispositivo
(`permisos.json`). Esos permisos solo restringen: nunca dan a Claude algo que la regla del
equipo no le dé ya.

# Ronda 1: Comunicación

## idioma
header: Idioma
pregunta: ¿En qué idioma quieres que te responda Claude?
seccion: Comunicación
multiSelect: no
opciones:
- Según el idioma en que escriba (Recomendado): responde en el idioma del mensaje.
- Español: siempre en español, aunque el código o la documentación estén en inglés.
- English: always in English.

## detalle
header: Detalle
pregunta: ¿Cuánto detalle quieres en las explicaciones?
seccion: Comunicación
multiSelect: no
opciones:
- Explicado, con el porqué (Recomendado): qué se hizo y por qué, en lenguaje llano.
- Conciso, solo lo necesario: el resultado y lo que tienes que decidir, sin más.
- Didáctico, paso a paso: cada paso explicado, útil si estás aprendiendo esta parte.

# Ronda 2: Autonomía

## forma-de-trabajar
header: Forma
pregunta: ¿Cómo quieres que Claude trabaje en tareas con cambios?
seccion: Autonomía
multiSelect: no
opciones:
- Según el riesgo (Recomendado): ejecuta lo reversible y pregunta antes de lo irreversible.
- Planificar y pedir permiso: propone un plan antes de cualquier cambio grande.
- Ejecutar y avisar: hace el cambio completo y cuenta después qué ha hecho.

## cuando-preguntar
header: Preguntar
pregunta: ¿Cuándo debe parar Claude a preguntarte?
seccion: Autonomía
multiSelect: no
opciones:
- Solo en decisiones de producto o irreversibles (Recomendado): lo demás lo decide y lo deja escrito.
- Ante cualquier ambigüedad: prefiere preguntar a suponer.
- Casi nunca: decide y deja constancia de lo que decidió.

# Ronda 3: Git

## ramas
header: Ramas
pregunta: ¿Cómo quieres organizar las ramas?
seccion: Git
multiSelect: no
opciones:
- Una rama por tarea (Recomendado): rama corta desde la principal y PR.
- Trabajar en la rama en la que esté: Claude no crea ramas por su cuenta.

## commits
header: Commits
pregunta: ¿Qué tamaño de commit prefieres?
seccion: Git
multiSelect: no
opciones:
- Pequeños y atómicos (Recomendado): un commit por cambio lógico.
- Uno por tarea: todo el trabajo de la tarea en un solo commit.

## formato-commit
header: Formato
pregunta: ¿Qué formato de mensaje de commit usamos?
seccion: Git
multiSelect: no
opciones:
- El convencional que use el repo (Recomendado): sigue el estilo que ya tiene el historial.
- Mensaje libre en español: una línea clara en español, sin prefijos.

# Ronda 4: GitHub

## quien-abre-pr
header: PR
pregunta: ¿Quién abre los pull requests (el merge lo hace siempre una persona)?
seccion: GitHub
multiSelect: no
opciones:
- Claude, pidiéndome permiso (Recomendado): prepara la rama, el título y la descripción, y pregunta antes de abrirlo.
- Lo abro yo: Claude deja la rama lista y te da el texto del PR; no ejecuta gh pr create.

## subir-ramas
header: Push
pregunta: ¿Puede Claude subir ramas de trabajo a GitHub (git push)?
seccion: GitHub
multiSelect: no
opciones:
- Sí, pidiéndome permiso cada vez (Recomendado): solo ramas de trabajo; a la principal y con --force, nunca.
- No, las subo yo: Claude deja los commits hechos y te dice qué rama subir.

## github-extra
header: GitHub
pregunta: Además de los PR, ¿qué más puede hacer Claude en GitHub, siempre pidiéndote permiso?
seccion: GitHub
multiSelect: sí
opciones:
- Nada más (Recomendado): solo consultar PR, issues y el estado de la CI, sin cambiar nada.
- Comentar en PR e issues: gh pr comment, gh pr review y gh issue comment.
- Crear y editar issues: gh issue create, edit y close.
- Relanzar la CI: gh run rerun y gh workflow run.

# Ronda 5: Comandos

## sin-preguntar
header: Libres
pregunta: ¿Qué puede ejecutar Claude sin preguntarte, dentro de lo que el repo permite?
seccion: Comandos
multiSelect: no
opciones:
- Lectura y comprobaciones (Recomendado): leer, buscar, git status, diff y log, tests, lint y build del repo.
- Solo lectura: también los tests, el lint y el build te los pregunta antes.
- Todo lo que el repo permite: sin preguntas extra; los límites los ponen las reglas del equipo.

## pedir-siempre
header: Siempre
pregunta: ¿Qué quieres que Claude te pregunte siempre, aunque el repo lo deje hacer?
seccion: Comandos
multiSelect: sí
opciones:
- Instalar o actualizar dependencias (Recomendado): npm, pnpm, yarn, pip, uv, flutter pub y dart pub.
- Borrar ficheros o carpetas: rm, rmdir, del, Remove-Item, git rm y git clean.
- Hacer commits: git commit, también en una rama de trabajo.
- Nada más: me valen las reglas del equipo.

# Ronda 6: Calidad

## tests
header: Tests
pregunta: ¿Cómo quieres que Claude trate los tests?
seccion: Calidad
multiSelect: no
opciones:
- Después del cambio, cubriendo lo tocado (Recomendado): tests nuevos o ajustados para lo que cambió.
- TDD: primero un test que falla y después el código.
- Solo en lo crítico: tests donde un fallo sería caro (datos, pagos, seguridad).

## revision
header: Revisión
pregunta: ¿Cómo quieres las revisiones de código?
seccion: Calidad
multiSelect: no
opciones:
- Lista priorizada de defectos reales (Recomendado): primero lo que rompe, sin opiniones de estilo.
- Comentarios línea a línea: cada observación junto a su línea.
- Resumen breve con lo grave: solo lo importante, en pocas líneas.

# Ronda 7: Manías

## manias
header: Manías
pregunta: ¿Alguna manía que Claude deba respetar siempre?
seccion: Manías
multiSelect: sí
opciones:
- No reformatear código que no toco (Recomendado): los cambios se limitan a lo pedido.
- Sin emojis: ni en respuestas, ni en commits, ni en código.
- Respuestas sin preámbulo: directamente al grano.
- Nada en especial: sin preferencias extra (el texto libre sigue disponible en Other).
