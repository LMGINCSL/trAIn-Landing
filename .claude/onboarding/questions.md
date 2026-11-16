---
version: 1
---

# Preguntas propias de trAIn-Landing (repo público)

Las hace la skill lmginc-onboarding (modo `repo`) después de las comunes. Las respuestas van a
CLAUDE.local.md (no versionado). Este fichero es público: nada interno.

# Ronda 1: Trabajo y entrega

## zona
header: Zona
pregunta: ¿En qué vas a trabajar sobre todo en la web?
seccion: Contexto
multiSelect: sí
opciones:
- Home y estilos, siempre en ES y EN (Recomendado): index.html, assets/css/landing.css y app.js.
- Páginas por objetivo o blog: se editan los scripts y se regenera con /regenerar-web.
- Alta en la beta (supabase/): todo es producción; solo migraciones nuevas y sin despliegues.
- Vídeos y OG image (remotion/): render local y copia manual a assets/.

## email-commits
header: Email git
pregunta: ¿Con qué email firmas los commits en este repo público?
seccion: Git
multiSelect: no
opciones:
- El noreply de GitHub (Recomendado): el formato id+usuario en users.noreply.github.com; nada personal queda público.
- Mi email habitual: el guard preguntará en cada commit y push, porque quedará visible en GitHub.

## gitleaks
header: gitleaks
pregunta: ¿Tienes gitleaks v8.30.1 instalado en el PATH?
seccion: Herramientas
multiSelect: no
opciones:
- Sí, lo instalo o ya lo tengo (Recomendado): el guard lo usa como segunda capa de secretos, con salida redactada.
- No: solo el guard propio (secretos básicos, emails, rutas locales y .vercelignore).

## verificacion
header: Navegador
pregunta: ¿Cómo vas a comprobar los cambios en el navegador?
seccion: Calidad
multiSelect: no
opciones:
- Servidor local a 375 y 1440 px (Recomendado): py -m http.server 8000, con la consola abierta y sin enviar el formulario de alta.
- Solo revisando el diff: no hay tests, así que los fallos visuales no se detectarán.

# Ronda 2: Entrega

## entrega
header: Entrega
pregunta: ¿Cómo entregas los cambios?
seccion: Git
multiSelect: no
opciones:
- Rama y PR a main (Recomendado): así se ha trabajado hasta ahora; el merge lo hace una persona.
- Commit directo en main: publica en producción en cuanto se hace push (el push a main está bloqueado desde la sesión).
