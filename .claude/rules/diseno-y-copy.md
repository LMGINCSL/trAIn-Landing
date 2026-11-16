---
paths:
  - "**/*.html"
  - "assets/css/**"
  - "app.js"
  - "scripts/blog/posts.py"
  - "scripts/pages/build_race.py"
  - "scripts/i18n/build_en.py"
---

# Diseño, copy y cabeceras

`DESIGN.md` es la autoridad visual (`.impeccable/design.json` es su copia en formato máquina; si
cambia `DESIGN.md`, se regenera con Impeccable). Resumen de sus reglas con nombre:

- **Un solo azul.** Relleno `#2A6FDB` con texto blanco; todo texto azul sobre claro va en `#2563D0`
  (la Regla del Azul que se Lee). Rojo solo para errores; verde solo en el modal de éxito.
- **Tono, no borde.** Una tarjeta se separa del fondo por tono (blanco sobre gris o al revés), sin
  borde; la sombra solo en lo que flota.
- **Titulares en frase**, con punto final, a peso 600. Una sola tipografía: TT Firs Neue, self-hosted.
- **Ningún texto por debajo de 11px.** Contraste AA sobre el fondo claro.
- **Siempre claro:** `color-scheme: only light`; no hay modo oscuro que mantener.
- **Un botón primario por pantalla y siempre el mismo texto:** «Unirme a la beta» / «Join the beta».
- La paleta se repite en el `:root` de las páginas secundarias (legales, objetivo, blog): si cambia,
  cambia en todas a la vez.

Copy (`PRODUCT.md`): honestidad radical, tono de ingeniero. Nada de escasez, fechas ni cuentas
atrás; las cifras tienen que existir («1.600+ ejercicios»). Sin testimonios inventados. La cuenta
atrás que describe `PRODUCT.md` ya no existe en la web: no es autoridad sobre eso.

- **Paridad ES/EN** en el mismo commit. La home EN, las páginas por objetivo y el blog se regeneran
  (`.claude/rules/paginas-generadas.md`); los legales EN (`en/privacy/`, `en/terms/`…) se editan a
  la vez que los ES.
- **Caché de 30 días** en `app.js`, `/assets/` y `/dist/` (`vercel.json`). Si cambia `app.js` o
  `assets/css/landing.css`, sube el `?v=` en `index.html` y regenera: tiene que quedar igual en
  todas las páginas. Un fichero nuevo en `assets/` lleva nombre nuevo, no se reutiliza.
- **CSP y COEP** (`vercel.json`): `script-src 'self' 'unsafe-inline'`, `connect-src` solo a
  Supabase, COEP `require-corp`. Cualquier script, fuente, imagen, vídeo o `fetch` de otro origen se
  rompe en producción si no se ajusta la CSP (y CORP del recurso). Nada de CDN ni analítica sin
  decidirlo.
- **JS:** vanilla, sin módulos, con `defer`. Respeta `prefers-reduced-motion` y pausa lo que no se ve.
- **Accesibilidad:** `alt` en las imágenes con contenido (`alt=""` en las decorativas), `aria-label`
  en los controles sin texto y foco visible.
- **Comprobar en el navegador** a 375 px y 1440 px (`py -m http.server 8000 --bind 127.0.0.1`), con
  `prefers-reduced-motion` y la consola abierta (errores de CSP). Sin enviar el formulario de alta.
