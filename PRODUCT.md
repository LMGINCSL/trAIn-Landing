# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Gente que ya entrena en serio — más de un año de constancia — y que ha usado y
abandonado apps de fitness genéricas. Reconocen la diferencia entre un algoritmo
real y un if-else con marketing, y les molesta que se les hable como a un
principiante.

Cuatro contextos de objetivo, todos igual de válidos en el producto: fuerza
(hipertrofia o fuerza), cardio (condición, Zone 2), una prueba con fecha
(Hyrox, triatlón, 10K) y mantener (volver a entrenar o sostener forma).

El 70–80% del tráfico llega por móvil desde Twitter/X, Reddit y WhatsApp.

## Product Purpose

2trAIn es un coach con IA para deportistas: eliges la meta y construye el plan
contigo, **explicando cada decisión con tus propios datos**. Cada cambio de
volumen o intensidad viene justificado; no hay plantillas genéricas ni caja
negra.

El trabajo de la landing hoy sigue siendo **uno solo: capturar el email para la
waitlist de la beta**. Si el visitante puede hacer cualquier cosa que no sea
apuntarse, la página ha fallado.

## Positioning

"Anti-app de fitness". El diferenciador no es tener IA — todas dicen tenerla —
sino **explicar el porqué**: decisiones técnicas justificadas con datos del
propio usuario, sin motivación infantil ni gamificación.

Segundo diferenciador, el único que la competencia no puede copiar barato: el
**experimento público** comparando la IA contra un coach humano con voluntarios
reales, publicando resultados gane quien gane.

## Operating Context

- Sitio vivo en **https://2trainapp.com**, desplegado en Vercel, bilingüe
  ES (`/`) + EN (`/en/`) con hreflang.
- Waitlist sobre **Supabase**: Edge Function `join-waitlist`, posición en cola,
  posiciones bloqueadas, rate limiting por IP y email transaccional vía Resend.
  Migraciones en `supabase/migrations/`.
- Piezas de vídeo para redes generadas con **Remotion** (`remotion/`), en ES y
  EN: MejoraReel, SustReel, WhyReel, y la propia OgImage.
- Sin build step obligatorio para el HTML: `dist/tailwind.css` está compilado y
  commiteado; GSAP y ScrollTrigger se sirven locales, no por CDN.

## Capabilities and Constraints

Estado confirmado por el usuario (2026-09-02): **sigue en waitlist/beta**. La
landing no pasa a modo lanzamiento todavía; el trabajo es mejorar la conversión
visita→email.

Consecuencia inmediata y no opcional: la página anuncia "La beta abre el 1 de
septiembre · faltan" con una cuenta atrás a `2026-09-01T00:00:00` que **ya ha
vencido**. Hoy el bloque de conversión renderiza literalmente
"La beta abre el 1 de septiembre · faltan / Beta disponible" (y su equivalente
en inglés). Es la promesa temporal central de la página, y está rota en vivo en
los dos idiomas. Cualquier trabajo sobre esta landing empieza por decidir la
fecha o retirar la cuenta atrás.

Compromisos de la oferta, tal como están escritos hoy (2026-10-30):
- **Beta abierta**, sin tope de plazas. El alta sigue siendo el email de la
  waitlist y el acceso llega por email al momento.
- Quien participe en la beta recibe "ventajas exclusivas" cuando termine.
  Ya no se promete figurar como Founding Member ni hay waves.
- "Sin tarjeta · Cancela cuando quieras."

Pendiente y sin decidir:
- Fecha real de apertura de la beta.
- Si `MEJORAS-PENDIENTES.md` (auditoría de 16/05/2026) sigue vigente: **no lo
  está**. Sus bloqueantes de rendimiento ya se resolvieron (favicon extraído a
  archivo, fuente self-hosted, GSAP local, Tailwind compilado). Ese documento
  está obsoleto y no debe usarse como backlog.

## Brand Commitments

- Nombre: **2trAIn**. Dominio 2trainapp.com. Handle @2trainapp.
- Tipografía propia y self-hosted: **TT Firs Neue** (variable 100–900, latin,
  normal e itálica). Es identidad, no una elección reemplazable.
- Voz: honestidad radical, tono de ingeniero, cero humo. Prohibido
  "transforma tu vida en 30 días", stock photos de gimnasio y testimonios sin
  nombre.
- El equipo son los mismos dos fundadores que en 4trAIners: Nacho y Enrique.
- La landing es la cara pública del proyecto; cada visitante que rebota sin
  convertir es un beta tester perdido.

## Evidence on Hand

Real y disponible:
- Capturas y vídeo de producto propios en `assets/`, incluido `hero-poster.jpg`
  y los mockups de la app.
- OG image real 1200×630 generada con Remotion.
- Contador de posición en la cola alimentado por datos reales de Supabase.

Ausencias que no se pueden inventar:
- Sin testimonios de usuarios: la Wave 0 aún no existe.
- Sin resultados publicados del experimento público. Mientras el experimento no
  tenga datos, la sección no puede mostrar gráficas ni cifras.
- La cifra de ejercicios que use el copy debe cuadrar con el catálogo maestro
  real (4.155), no con estimaciones antiguas.

## Product Principles

1. **Un solo trabajo: el email.** Nada de precios, roadmap ni features extra.
2. **Explicar el porqué es el producto.** El copy que no justifica una decisión
   no defiende el posicionamiento.
3. **Honestidad radical, incluida la que duele.** Si el experimento lo pierde la
   IA, se publica igual. Si una fecha vence, se cambia — no se deja correr.
4. **Mobile-first de verdad.** Si no se ve perfecto a 375px, no se ve.
5. **Velocidad como rasgo de marca.** Headline visible en <1s en 4G; nada de
   autoplay pesado ni librerías que no se usen.
6. **Paridad ES/EN.** Todo cambio de copy o estructura se aplica a los dos
   idiomas en el mismo commit; `/en/` no es una traducción de segunda.

## Accessibility & Inclusion

Bilingüe ES/EN con hreflang correcto. La cuenta atrás ya expone `aria-label`.
Objetivo a mantener: Lighthouse accesibilidad alta en móvil, contraste AA sobre
el fondo claro (la paleta de DESIGN.md está medida para ello: el texto gris da
5,1:1 sobre blanco y el azul de texto 5,6:1) y ningún texto de interfaz por
debajo de 11px. La web es siempre clara (`color-scheme: only light`).
