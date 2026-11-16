---
name: regenerar-web
description: Regenera las páginas generadas de la web (home EN, páginas por objetivo, blog y sus bloques de sitemap.xml y llms.txt) en el orden correcto y revisa el resultado - diff ES/EN, avisos de traducción y el mismo ?v= en todas las páginas. Úsala después de tocar index.html o un script de scripts/i18n, scripts/pages o scripts/blog, y cuando el hook Stop diga que una generada está desfasada.
argument-hint: "[nuevo]"
allowed-tools:
  - Bash(py -3 -I -B -X utf8 scripts/i18n/seo_ld.py *)
  - Bash(py -3 -I -B -X utf8 scripts/i18n/build_en.py *)
  - Bash(py -3 -I -B -X utf8 scripts/pages/build_race.py *)
  - Bash(py -3 -I -B -X utf8 scripts/blog/build_blog.py *)
  - Bash(git status *)
  - Bash(git diff *)
  - Read
  - Grep
model: sonnet
effort: low
---

# Regenerar la web

Las páginas generadas no se editan a mano (`.claude/rules/paginas-generadas.md`). Si `$ARGUMENTS`
es `nuevo` (o la tarea es añadir un artículo o una página por objetivo), lee antes
`${CLAUDE_SKILL_DIR}/nuevo-articulo-o-pagina.md`.

## 1. Antes
`git status --short`: anota qué estaba ya cambiado, para no atribuirle al script lo que no es suyo.

## 2. Los cuatro scripts, en este orden, desde la raíz del repo
Cada uno usa la salida del anterior; si uno falla, para y cuenta el error (no sigas con el resto).

```
py -3 -I -B -X utf8 scripts/i18n/seo_ld.py index.html es
py -3 -I -B -X utf8 scripts/i18n/build_en.py . scripts/i18n/en-head.html
py -3 -I -B -X utf8 scripts/pages/build_race.py .
py -3 -I -B -X utf8 scripts/blog/build_blog.py .
```

`-I` aísla de variables y rutas del entorno, `-B` no deja `__pycache__` y `-X utf8` hace legible la
salida en Windows. En macOS y Linux, `python3` en lugar de `py -3`.

## 3. Leer los avisos
- `json-ld es preguntas: N` y `json-ld en preguntas: N`: los dos con el mismo N (hoy 10). Si no
  coinciden, al FAQ de una home le falta una pregunta.
- `pares sin uso: N`: la línea base es 172. Si sube, un par de `build_en.py` dejó de casar porque
  cambió el texto ES: actualiza el par.
- `posibles restos: [...]`: la línea base es `['Versión en español']` (el enlace al español). Cualquier
  otro resto es texto español que se quedó en `/en/`: falta su par en `PAIRS`.
- Las líneas `ok <fichero>` dicen qué se escribió.

## 4. Revisar el resultado
- `git status --short` y `git diff --stat`: solo deben cambiar las páginas que dependen de lo que se
  tocó. Sin cambios de entrada, la salida es idéntica (los scripts son idempotentes).
- Paridad: cada cambio de `index.html` tiene su reflejo en `en/index.html` (y en las páginas por
  objetivo y el blog si afecta a cabecera, menú, alta o pie).
- `?v=`: con Grep, `app\.js\?v=` y `landing\.css\?v=` en `*.html` dan un único valor cada uno (sin
  contar `scripts/i18n/en-head.html`). Si cambió `app.js` o `landing.css`, ese valor es nuevo.

## 5. Parte
En 3 a 6 líneas: comandos ejecutados con su resultado, ficheros cambiados agrupados ES/EN, avisos
que se salen de la línea base y lo que queda por mirar en el navegador (375 y 1440 px, sin enviar el
formulario de alta).

Nunca: editar a mano una página generada para «arreglar» la salida, ejecutar
`scripts/send_email_previews.py` ni enviar el formulario (llama a la función de producción).
