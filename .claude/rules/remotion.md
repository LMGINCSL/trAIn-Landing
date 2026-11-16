---
paths:
  - "remotion/**"
---

# Remotion (vídeos y OG image)

Subproyecto Node aparte (Remotion 4 + React 18). Nada de aquí se publica: `.vercelignore` excluye
`remotion/`; lo que llega a la web son los ficheros que se copian a mano.

- Dependencias: `cd remotion && npm ci` (avisa de vulnerabilidades transitivas de `npm audit`; no se
  arreglan aquí).
- Tipos: `npx tsc --noEmit` da **1 error conocido** (`src/kit.tsx:44`, `overshootClamping` fuera de
  `config` en `spring()`). No impide renderizar; si tocas `kit.tsx`, arréglalo.
- Composiciones (`src/Root.tsx`): `OgImage`, `ReelWhy`, `ReelMejora`, `ReelSustituciones` y sus
  `...EN`. Editor: `npm run studio`.
- Render: `npm run render:why|render:mejora|render:sust|render:all` solo cubre los reels ES; los EN y
  la OG van a mano, p. ej. `npx remotion render ReelWhyEN out/reel-why-en.mp4 --codec=h264` y
  `npx remotion still OgImage out/og-image.png`. Si Remotion no encuentra navegador, añade
  `--browser-executable=<ruta de tu Chrome>` (en el comando, nunca en un fichero del repo).
- La salida va a `remotion/out/` (ignorada). Se copia a mano con el nombre que esperan los HTML:
  `assets/reel-why.mp4`, `reel-problema.mp4`, `reel-solucion.mp4` y sus `-en.mp4`; la OG a
  `og-image.png` en la raíz (1200×630). Un vídeo nuevo con contenido distinto lleva nombre nuevo o
  cambio de `?v=` en sus `<source>`: `/assets/` se cachea 30 días.
- Vídeos ligeros: la web promete el titular en menos de 1 s en 4G; revisa el tamaño antes de copiar.
