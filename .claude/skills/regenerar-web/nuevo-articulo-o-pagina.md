# Añadir un artículo del blog o una página por objetivo

Todo se hace en los scripts y se regenera; nada se escribe directamente en `blog/`, `en/blog/` ni en
las carpetas de las páginas por objetivo. Siempre ES y EN a la vez.

## Artículo del blog
1. En `scripts/blog/posts.py`, una entrada nueva en `POSTS` con `key`, `date` (`AAAA-MM-DD`), `week`,
   `photo`, `legal` (o `None`) y los bloques `es` y `en`, cada uno con `slug`, `cat`, `title`, `seo`,
   `desc`, `lead`, `body` (HTML; `{{week}}` marca dónde va la semana dibujada), `faq`, `sources` y `cta`.
   Copia la forma de un artículo existente.
2. `week` es una página de `scripts/pages/semanas.json` (`hyrox`, `triatlon`, `10k`, `maraton`,
   `fuerza`): las semanas son reales y salen de `extraer_semanas.py` con un fichero de revisión que
   facilita el equipo; no se inventan ni se escriben a mano.
3. Foto de portada en `assets/fotos/<photo>-640.webp` y `<photo>-1280.webp` (1280×720), con licencia
   libre. Nombre nuevo: `/assets/` se cachea 30 días.
4. Las reglas de `posts.py`: cada artículo responde a una búsqueda concreta, enlaza a su página por
   objetivo, cita fuentes cuando da cifras y no promete nada que la app no haga.
5. `/regenerar-web`. `build_blog.py` añade el artículo al índice del blog, a `sitemap.xml` y al bloque
   del blog de `llms.txt`.
6. Si la página por objetivo debe enlazar al artículo, entrada en `ARTICULO` de
   `scripts/pages/build_race.py` y otra vez `/regenerar-web`.

## Página por objetivo
1. En `scripts/pages/build_race.py`: la entrada en `PAGES` (`es` y `en`, con `path`, `url`, `other`,
   textos y `faq`), su semana en `WEEKS` y, si hay artículo, en `ARTICULO`. Todo lo que diga de la app
   tiene que estar ya en la home o en la demo.
2. Su semana real en `scripts/pages/semanas.json` (la regenera el equipo con `extraer_semanas.py`).
3. `/regenerar-web`.
4. A mano, porque `build_race.py` no los toca: la URL ES y EN en `sitemap.xml` (con `hreflang`), la
   línea en «Enlaces» de `llms.txt` y, si procede, el enlace en el menú o el pie de las dos homes
   (y entonces otra vez `/regenerar-web`).
5. La carpeta nueva es contenido web: Vercel la publica (es lo esperado). Revisa a 375 y 1440 px.
