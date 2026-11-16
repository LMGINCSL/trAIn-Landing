# trAIn-Landing

Web pública de 2trAIn (https://2trainapp.com), ES en `/` y EN en `/en/`. Su único trabajo es el alta
con email en la beta abierta. HTML estático (en parte a mano, en parte generado con Python), JS
vanilla (`app.js`), CSS propia (`assets/css/landing.css`) y Tailwind 3 precompilado (`dist/`).
Vercel publica la raíz tal cual, sin build. El alta (Supabase `join-waitlist` + Resend) es producción.

## Este repo es PÚBLICO
- GitHub lo enseña entero y Vercel sirve todo lo que `.vercelignore` no excluye. Nada interno: ni
  rutas de tu máquina, ni emails personales, ni nombres de otros repos o personas, ni `.env`.
- Fichero nuevo fuera de las páginas: `git ls-files -c -o -i --exclude-from=.vercelignore -- <ruta>`
  lo imprime si Vercel lo excluye; si no imprime nada, se publicará.
- `public_guard.py` revisa cada `git commit` y `git push` (deniega secretos, `.env`, rutas locales y
  emails fuera de `.claude/hooks/public_guard.allow.json`; pregunta si el autor no es el noreply de
  GitHub o si Vercel publicaría un fichero nuevo) y avisa tras cada edición. Los términos internos
  se leen de `~/.claude/lmginc/public-guard.local.json`, fuera del repo.

## Requisitos
- En Windows, Git for Windows (Git Bash): los hooks de Claude Code de este repo se ejecutan con `sh` (C-2).
- Python 3 (`py -3` en Windows; `python3` en macOS y Linux). Node 22 solo para `remotion/`.

## Comandos
- No hay tests ni linter: `npm test` falla a propósito («no test specified»). Se verifica
  regenerando y mirando en el navegador.
- Regenerar lo generado, en este orden (o `/regenerar-web`); sin cambios, salida idéntica:
  `py -3 -I -B -X utf8 scripts/i18n/seo_ld.py index.html es` →
  `py -3 -I -B -X utf8 scripts/i18n/build_en.py . scripts/i18n/en-head.html` →
  `py -3 -I -B -X utf8 scripts/pages/build_race.py .` → `py -3 -I -B -X utf8 scripts/blog/build_blog.py .`
- Local: `py -m http.server 8000` y revisar a 375 y 1440 px con la consola abierta (CSP). **No
  envíes el formulario**: llama a la función de producción y manda un email real.
- Remotion: `cd remotion && npm ci`; `npx tsc --noEmit` da 1 error conocido (`src/kit.tsx:44`).
- Nunca: `scripts/send_email_previews.py` (envía emails reales), `supabase` deploy/db/link/secrets ni
  `vercel` (están en `deny`).

## Generados: no se editan a mano
`en/index.html`, `hyrox/`, `triatlon/`, `10k/`, `maraton/`, `fuerza/` y sus `en/…`, `blog/**`,
`en/blog/**` y el bloque del blog de `sitemap.xml` y `llms.txt`. Se cambia la plantilla
(`index.html`) o el script y se regenera. `build_en.py` traduce con pares exactos ES→EN: texto nuevo
en la home, par nuevo. Detalle en `.claude/rules/paginas-generadas.md`.

## Reglas que no se rompen
- Paridad ES/EN en el mismo commit.
- Si cambia `app.js` o `landing.css`, sube el `?v=` de `index.html` y regenera (caché de 30 días).
- Recurso de otro origen (script, fuente, imagen, `fetch`): CSP y COEP de `vercel.json`.
- Supabase es producción: las migraciones aplicadas no se tocan (se crea una nueva) y nada se
  despliega desde la sesión (`.claude/rules/supabase.md`).
- Diseño: `DESIGN.md` (resumen en `.claude/rules/diseno-y-copy.md`). Copy: `PRODUCT.md`.

## Documentos
- Valen: `DESIGN.md`, `PRODUCT.md` (salvo la cuenta atrás, que ya no existe), `AUDITORIA-SEO.md`
  (sus comandos dicen `python3`: en Windows, `py -3`) y `GSAP_SCROLL.md`.
- Históricos, no son backlog: `MEJORAS-PENDIENTES.md` y `guia_landing_beta.md`.
- `.impeccable/` configura Impeccable, la herramienta de diseño del equipo.

## Git
- Una rama corta por tarea desde `main` y un PR para integrarla. Un push a `main` publica la web.
- Prohibido: `git push` a `main`, `git push --force` y `gh pr merge`.
- Con permiso, siempre: `git add`, `git commit`, `git push` de una rama de trabajo y `gh pr create`.
  Aquí no hay guard de comandos que distinga la rama, así que `git commit` pregunta también fuera
  de `main`: manda esto sobre `.claude/rules/git.md`.
- Firma con el noreply de GitHub. Si una preferencia personal choca con esto, gana esta regla y se avisa.

## Piezas
`.claude/rules/` (las de `paths` se cargan al tocar su zona), skill `/regenerar-web`, agente
`landing-reviewer` (revisa el diff antes del commit; solo informa) y hook Stop (generadas, paridad
ES/EN, `?v=` y ficheros que se publicarían).

# Compact instructions
Al compactar, conserva:
- la tarea en curso y su criterio de terminado;
- los ficheros tocados y por qué;
- los comandos de prueba ejecutados con su resultado (comando y recuento);
- las decisiones tomadas y lo que queda pendiente.
- Sin suite: la prueba es la salida de los 4 scripts (avisos fuera de la línea base: `pares sin uso` ≠ 172 o
  restos distintos de 'Versión en español') y lo revisado en el navegador.
- Qué cambios ES siguen sin su EN, si el `?v=` está subido y si hay ficheros nuevos fuera de `.vercelignore`.

## Perfil personal
Preferencias de quien trabaja en esta sesión (fuera del repo; no anulan las reglas del equipo):
@~/.claude/lmginc/profile.md
