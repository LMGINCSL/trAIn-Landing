---
name: 2trAIn
description: La landing clara del coach con IA que se acuerda de ti — tipografía propia a peso medio, un solo azul y el móvil con la app como protagonista.
colors:
  bg: "#FFFFFF"
  bg-2: "#F5F5F7"
  surface: "#F5F5F7"
  surface-2: "#FFFFFF"
  control: "#E8E8ED"
  fg: "#1D1D1F"
  fg-2: "#424245"
  muted: "#6E6E73"
  line: "#D2D2D7"
  line-soft: "rgba(0, 0, 0, 0.08)"
  accent: "#2A6FDB"
  accent-hover: "#1F5FC8"
  accent-text: "#2563D0"
  accent-soft: "rgba(42, 111, 219, 0.09)"
  ok: "#15803D"
  warn: "#A16207"
  danger: "#D70015"
  glass: "rgba(255, 255, 255, 0.72)"
  device: "#111113"
typography:
  hero:
    fontFamily: "TT Firs Neue, -apple-system, system-ui, sans-serif"
    fontSize: "clamp(44px, 7.4vw, 88px)"
    fontWeight: 600
    lineHeight: 1.03
    letterSpacing: "-0.034em"
  section:
    fontFamily: "{typography.hero.fontFamily}"
    fontSize: "clamp(34px, 5.2vw, 60px)"
    fontWeight: 600
    lineHeight: 1.06
    letterSpacing: "-0.028em"
  keys:
    fontFamily: "{typography.hero.fontFamily}"
    fontSize: "clamp(23px, 3.1vw, 36px)"
    fontWeight: 600
    lineHeight: 1.18
    letterSpacing: "-0.022em"
  title:
    fontFamily: "{typography.hero.fontFamily}"
    fontSize: "clamp(22px, 2.4vw, 28px)"
    fontWeight: 600
    lineHeight: 1.16
    letterSpacing: "-0.018em"
  lead:
    fontFamily: "{typography.hero.fontFamily}"
    fontSize: "clamp(17px, 1.7vw, 21px)"
    fontWeight: 400
    lineHeight: 1.47
    letterSpacing: "-0.01em"
  eyebrow:
    fontFamily: "{typography.hero.fontFamily}"
    fontSize: "clamp(15px, 1.4vw, 17px)"
    fontWeight: 600
    letterSpacing: "-0.01em"
  body:
    fontFamily: "{typography.hero.fontFamily}"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.47
  small:
    fontFamily: "{typography.hero.fontFamily}"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.45
  micro:
    fontFamily: "{typography.hero.fontFamily}"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.4
  num:
    fontFamily: "{typography.hero.fontFamily}"
    fontSize: "clamp(64px, 8.6vw, 116px)"
    fontWeight: 600
    lineHeight: 0.95
    letterSpacing: "-0.045em"
rounded:
  card: "18px"
  tile: "28px"
  block: "32px"
  device: "56px"
  pill: "980px"
  circle: "50%"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#FFFFFF"
    rounded: "{rounded.pill}"
    padding: "15px 28px"
    typography: "17px / 600"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "#FFFFFF"
    rounded: "{rounded.pill}"
  button-ghost:
    backgroundColor: "{colors.control}"
    textColor: "{colors.fg}"
    rounded: "{rounded.pill}"
  link:
    textColor: "{colors.accent-text}"
    suffix: "›"
  tile:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.tile}"
    padding: "30px"
  input-email:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.fg}"
    rounded: "{rounded.pill}"
    focusRing: "inset 0 0 0 1.5px {colors.accent}, 0 0 0 4px rgba(42,111,219,.14)"
  nav:
    backgroundColor: "{colors.glass}"
    backdropFilter: "saturate(180%) blur(20px)"
    height: "56px"
  segmented:
    backgroundColor: "{colors.control}"
    thumb: "#FFFFFF"
    rounded: "{rounded.pill}"
---

# Design System: 2trAIn

## Overview

**Creative North Star: "El producto delante"**

Blanco de página, un solo azul y la tipografía propia a peso medio. La página
habla poco y enseña mucho: el hero es un titular corto y el móvil con la sesión
de hoy ya adaptada, y el scroll va contando el producto con el teléfono fijo
mientras el texto pasa. La referencia es la manera en que Apple presenta un
producto, aplicada a una marca que no vende entusiasmo sino criterio.

El sistema es **siempre claro**. Todas las páginas declaran
`<meta name="color-scheme" content="only light">` y
`:root { color-scheme: only light }`: ni el modo oscuro del sistema ni el
oscurecimiento automático de Chrome o Samsung Internet invierten la página.
No hay variante oscura que mantener.

La pieza que sostiene todo sigue siendo **el razonamiento visible**: el chat
de la demo que piensa con tus datos y la sesión que genera, ejercicio a
ejercicio, con su imagen y su prescripción. El hero enseña el resultado de ese
mismo caso (hombro tocado → sesión de empuje sin press vertical) para que lo
que promete el titular se vea antes de leerlo.

Hay un segundo mundo de color, pequeño y con reglas propias: el **modal de
éxito** posterior al alta (tokens `--ms-*`). Con la beta abierta solo confirma
(«Estás dentro», el acceso llega por email) y ofrece compartir. Es la única
superficie que puede usar el verde de WhatsApp.

**Key Characteristics:**
- Fondo blanco continuo; el gris #F5F5F7 solo en tarjetas y paneles
- Una tarjeta se separa de su fondo por tono, nunca por borde ni sombra pesada
- Un único azul: relleno para el botón, `--accent-text` para texto
- Titulares en frase, con punto final, a peso 600
- Un botón primario por pantalla y siempre con el mismo texto
- El móvil (marco oscuro) es el único objeto oscuro de la página

## Colors

### Primary
- **Azul Señal** (`#2A6FDB`): relleno del botón primario, selección, anillos de
  foco, el punto vivo. Con texto blanco da 4,8:1.
- **Azul Profundo** (`#1F5FC8`): hover del botón.
- **Azul Texto** (`#2563D0`): todo texto azul sobre claro (eyebrows, enlaces,
  la palabra acentuada del titular, las cifras). Da 5,6:1 sobre blanco y 5,1:1
  sobre gris.
- **Azul Velo** (`rgba(42,111,219,0.09)`): fondo del razonamiento, del "por qué
  ha cambiado" y de los chips activos.

### Neutral
- **Blanco Página** (`#FFFFFF`) y **Gris Banda** (`#F5F5F7`): las dos superficies.
  Las secciones alternan entre ellas; una tarjeta usa la otra.
- **Gris Control** (`#E8E8ED`): fondo de controles segmentados y botones grises.
- **Tinta** (`#1D1D1F`) y **Tinta 2** (`#424245`): texto principal y texto de
  apoyo fuerte.
- **Gris Texto** (`#6E6E73`): texto secundario. 5,1:1 sobre blanco y 4,7:1 sobre
  gris: vale para texto pequeño.
- **Línea** (`#D2D2D7`) y **Línea suave** (`rgba(0,0,0,.08)`): divisores de la
  FAQ, del pie y de la barra translúcida.

### Secondary (solo estado)
- **Verde** (`#15803D`): el botón de WhatsApp del modal de éxito (5,0:1 con
  blanco).
- **Ámbar** (`#A16207`): avisos de plazas libres en el modal (4,9:1).
- **Rojo** (`#D70015`): errores de formulario y nada más.

### Named Rules

**La Regla del Azul que se Lee.** El azul de relleno (`#2A6FDB`) lleva texto
blanco; el texto azul sobre fondo claro es siempre `#2563D0`. Sobre el gris
#F5F5F7 el azul de relleno como texto se queda en 4,4:1 y no llega a AA.

**La Regla del Tono, no del Borde.** Sobre claro, una tarjeta se distingue del
fondo porque es un tono distinto (blanco sobre gris o gris sobre blanco). No se
le pone borde; la sombra solo existe en lo que flota (modal, formulario de la
beta, chat de la demo).

**La Regla del Después.** Los tokens `--ms-*` pertenecen al modal de éxito y no
salen de él.

**La Regla del Semáforo Mudo.** Verde, ámbar y rojo solo comunican estado.

**La Regla de la Paleta Única.** Landing ES y EN comparten
`assets/css/landing.css`. Las páginas secundarias (legales, soporte, borrado de
cuenta, `/app/`) declaran los mismos valores en su `:root`; si cambia uno, se
cambia en todas en el mismo commit.

## Typography

**Familia:** TT Firs Neue (variable 100–900, self-hosted). Es la única familia.

**Carácter:** la misma grotesca propia, ahora a peso 600 en display. El tamaño
impone; el grosor no. El tracking negativo vive solo en tamaños grandes y se
relaja al bajar.

### Hierarchy
- **Hero** (600, `clamp(44px, 7.4vw, 88px)`, 1.03, `-0.034em`)
- **Section** (600, `clamp(34px, 5.2vw, 60px)`, 1.06, `-0.028em`): titulares de
  sección, con la segunda frase en gris (`.muted`) o la palabra clave en azul.
- **Keys** (600, `clamp(23px, 3.1vw, 36px)`, 1.18): la lista de claves bajo el
  hero, en gris con 3–5 palabras en tinta.
- **Num** (600, `clamp(64px, 8.6vw, 116px)`, 0.95, `-0.045em`): cifras reales en
  azul texto.
- **Title** (600, `clamp(22px, 2.4vw, 28px)`): titulares de tarjeta.
- **Lead** (400, `clamp(17px, 1.7vw, 21px)`, gris): entradillas.
- **Eyebrow** (600, 15–17px, azul texto, en frase): nombra la sección.
- **Body** (17px) · **Small** (14px) · **Micro** (12px).
- **11px es el suelo** para cualquier texto funcional, también dentro del móvil
  del hero.

### Named Rules

**La Regla de la Frase.** Ningún titular va en mayúsculas. Frase normal y punto
final. Dos frases cortas que se contestan funcionan mejor que una larga.

**La Regla del Tracking que Cede.** Negativo en display, cero o casi cero por
debajo de 24px.

**La Regla de la Fuente Local.** TT Firs Neue se sirve desde `/assets/fonts/`
con `font-display: swap` y precarga.

## Layout

Una columna de 1180px como máximo, con 22px de margen lateral en móvil y 40px
desde 768px. Secciones con `clamp(48px, 6vw, 80px)` de aire (el resto lo pone el hilo),
sobre un fondo blanco continuo: no hay bandas de color entre secciones, el gris
vive solo dentro de las tarjetas. Orden: hero → objetivos → por qué (móvil
fijo) → demo → cifras → ¿aún no convencido? → FAQ → beta → pie.

- **Hilo entre secciones (`.bridge`):** una línea azul que se dibuja con el
  scroll, un punto y, casi siempre, una frase de 3 a 6 palabras que enlaza con
  lo siguiente («Todo empieza por tu meta.», «Cada cambio llega con su
  porqué.»…). Es lo que hace que la página se lea de un tirón y no como bloques.
- **Hero:** en escritorio, texto a la izquierda y el móvil entero a la derecha,
  dimensionado con el alto del viewport para que se vea completo al cargar
  incluso en un portátil de 720px. En móvil y tablet, texto y formulario
  primero y el móvil debajo. El móvil nunca se recorta ni entra con fundido.
- **Objetivos:** selector segmentado de cuatro opciones y un único panel con el
  plan orientativo en letra grande y su gráfica (carga semanal, tiempo por
  zona, fases hasta la fecha, constancia), que se redibuja al cambiar. Debajo,
  tres ejercicios del catálogo típicos de esa meta: tarjetas en escritorio y
  filas tipo app en móvil.
- **Por qué:** en escritorio, el móvil se queda fijo y su pantalla cambia con
  cada paso. Las tres pantallas son HTML con barra de pestañas y cada una es un
  pequeño vídeo en bucle (GSAP). En ≤860px, galería horizontal con flechas.
- **Cifras:** burbujas que flotan (1.600+ ejercicios, 4 objetivos, 3 formas)
  rodeadas de burbujas con ilustraciones del catálogo.

Mobile-first de verdad: todo se revisa a 375px antes que a 1440px.

## Motion

Entradas lentas y una sola vez: opacidad 0 → 1 y 18–28px de subida, 0,8s,
`power2.out`, escalonadas 0,09s en grupos (`[data-reveal]`,
`[data-reveal-stagger]`). Sin rebotes ni escalas. El hero no se anima: el
texto es el LCP y el móvil tiene que verse al cargar. Las piezas que se montan
solas (`[data-anim]`: gráficas de objetivos, burbujas) cambian con la clase
`.is-in`. Lo que va en bucle (las pantallas de «Por qué») son timelines de GSAP que solo corren mientras están
a la vista; antes de reproducirse se ven en su estado final. Si
`app.js` no arranca en 4s, el `<head>` quita `.js` y todo se ve en su estado
final. Con `prefers-reduced-motion` no hay ninguna.

## Elevation & Depth

- **Flotante** (`--shadow-card`): chat de la demo, tarjeta del formulario de
  beta, tiles al pasar el ratón.
- **Dispositivo** (`--shadow-float`): el móvil.
- **Cristal**: barra de navegación, píldora compacta del logo, aviso de cookies.
  `rgba(255,255,255,.72)` con `saturate(180%) blur(20px)`.

## Shapes

Píldora (980px) para botones, inputs del hero, chips y selectores. 18px para
tarjetas pequeñas, 28px para tiles y paneles, 32px para el bloque de la beta,
56px para el marco del móvil. No hay esquinas vivas.

## Components

### Buttons
- **Primario:** píldora azul, 17px a 600, texto blanco. El texto es siempre
  «Unirme a la beta» / «Join the beta».
- **Gris:** píldora `--control` con texto tinta (Instagram, Rechazar cookies).
- **Enlace:** azul texto terminado en «›».

### Selector segmentado
Píldora gris con una píldora blanca que se desliza a la opción activa (la demo).
Funciona con flechas del teclado.

### Objetivos
Cuatro pestañas (`role="tab"`) en un selector segmentado y un único panel. Al
cambiar, el panel cambia el plan orientativo y redibuja su gráfica. Las
gráficas son CSS, sin imágenes, y se dibujan al entrar en pantalla. Son
orientativas, así que ninguna lleva cifras.

### Pantallas de la app
HTML dentro del marco del móvil, no capturas ni vídeo: nítidas, ligeras y
traducibles. Las ilustraciones salen de los vídeos del catálogo maestro
(`assets/ej/`: 16:9, miniatura 3:2 y cuadrada para las burbujas), encuadradas
en la figura y sin marca de agua. Llevan `filter: brightness(1.025)` para que
su fondo gris muy claro quede en blanco. Los nombres son los del catálogo. En pantallas estrechas
(`@container` ≤262px) el hero enseña tres ejercicios en vez de cuatro.

### Pantalla de sustituciones
Cada caso («¿Sin barras?», «¿Lesión?», «¿Aburrido?») enseña el ejercicio de
antes y el de ahora con su miniatura del catálogo, y lo que se guarda en el
perfil.

### Móvil del hero
Barra de estado, cabecera "Hoy · Empuje", el "por qué ha cambiado", la lista de
ejercicios y "Empezar sesión". Es el mismo caso que la demo.

### Modal de éxito (segundo mundo)
Check, «Estás dentro», aviso de que el acceso está en el email y compartir
(WhatsApp, X, copiar enlace), con tokens `--ms-*`. Sin puesto, waves ni
plazas: la beta es abierta.

## Do's and Don'ts

### Do:
- **Do** usar `#2563D0` para texto azul y `#2A6FDB` para rellenos.
- **Do** separar una tarjeta de su fondo por tono.
- **Do** escribir los titulares en frase y con punto final.
- **Do** usar un único texto para el botón primario en toda la página.
- **Do** aplicar cualquier cambio a `/` y a `/en/` en el mismo commit.
- **Do** mantener todo texto funcional en 11px o más.
- **Do** usar solo cifras que existen (1.600+ ejercicios con vídeo, 4 objetivos, 3 formas).
- **Do** unir cada sección con la siguiente con el hilo; nunca bandas de color.

### Don't:
- **Don't** volver a poner titulares en mayúsculas ni a peso 800.
- **Don't** añadir una variante oscura ni quitar `color-scheme: only light`.
- **Don't** poner bordes a las tarjetas ni sombras a lo que no flota.
- **Don't** añadir fotos de stock de gimnasio ni gradientes decorativos.
- **Don't** introducir una segunda familia tipográfica.
- **Don't** vender escasez: la beta es abierta, sin fechas ni plazas contadas.
