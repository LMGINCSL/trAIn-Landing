---
paths:
  - "en/index.html"
  - "hyrox/**"
  - "triatlon/**"
  - "10k/**"
  - "maraton/**"
  - "fuerza/**"
  - "en/hyrox/**"
  - "en/triathlon/**"
  - "en/10k/**"
  - "en/marathon/**"
  - "en/strength/**"
  - "blog/**"
  - "en/blog/**"
  - "scripts/**"
  - "sitemap.xml"
  - "llms.txt"
---

# Páginas generadas

Estos ficheros salen de scripts: **no se editan a mano**. Se cambia la plantilla o el script y se
regenera con `/regenerar-web` (el hook Stop avisa si una generada quedó más antigua que su
plantilla o si se editó a mano). Los cuatro scripts son idempotentes: sin cambios, salida idéntica.

| Salida | Script | Entradas |
|---|---|---|
| JSON-LD de `index.html` (FAQPage sale del FAQ visible) | `scripts/i18n/seo_ld.py index.html es` | `index.html` |
| `en/index.html` (y su JSON-LD EN) | `scripts/i18n/build_en.py . scripts/i18n/en-head.html` | `index.html`, pares de `build_en.py`, `en-head.html` |
| `hyrox/`, `triatlon/`, `10k/`, `maraton/`, `fuerza/` y `en/hyrox/`, `en/triathlon/`, `en/10k/`, `en/marathon/`, `en/strength/` | `scripts/pages/build_race.py .` | las dos homes (cabecera, menú, alta, pie, modal), `PAGES` y `WEEKS` de `build_race.py`, `semanas.json` |
| `blog/**`, `en/blog/**` y los bloques del blog en `sitemap.xml` y `llms.txt` | `scripts/blog/build_blog.py .` | las dos homes, `posts.py`, `build_race.py`, `semanas.json` |

Orden obligatorio: `seo_ld` → `build_en` → `build_race` → `build_blog` (cada uno usa la salida del
anterior). Comandos exactos en `.claude/skills/regenerar-web/SKILL.md`.

- **`build_en.py` traduce con pares exactos ES→EN** (`PAIRS`). Si cambias un texto de `index.html`,
  añade o actualiza su par: si no, el texto queda en español en `/en/` y el script solo avisa.
  Avisos conocidos de la línea base: `pares sin uso: 172` y `posibles restos: ['Versión en español']`
  (el enlace al español). Otro resto = texto sin traducir; más pares sin uso = un par que dejó de casar.
- **`scripts/i18n/en-head.html`** es una página EN antigua de la que `build_en.py` saca las metas de la
  cabecera, el JSON-LD base y los bloques ocultos. Tocarla cambia la cabecera EN. Su `?v=` no cuenta.
- **`semanas.json`** sale de `extraer_semanas.py`, que lee un HTML de revisión que no está en el repo:
  no se regenera desde aquí. Las semanas que enseña la web son reales; no se inventan.
- `sitemap.xml` y `llms.txt` son a mano salvo el bloque del blog. Una página por objetivo nueva se
  añade a mano a los dos (ver `.claude/skills/regenerar-web/nuevo-articulo-o-pagina.md`).
- `llms.txt` es público y lo leen buscadores con IA: solo información que ya está en la web.
- `scripts/send_email_previews.py` **no se ejecuta nunca** (envía emails reales; está en `deny`).
