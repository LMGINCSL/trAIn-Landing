# Auditoría SEO, SEM y buscadores con IA · 2trainapp.com

Fecha: 31 de octubre de 2026. Rama `feat/landing-apple-claro` (sin publicar).
Este fichero no se despliega: `.vercelignore` excluye los `.md`.

## Resumen

La web estaba bien montada en lo básico (canonical, hreflang ES/EN, sitemap,
robots abierto, imágenes con `alt`, una sola H1), pero tenía cuatro problemas:

1. **Título y descripción sin las palabras que busca la gente.** «El coach con
   IA que se acuerda de ti» es buena marca, pero nadie busca eso. Faltaban
   «app», «entrenamiento», «Hyrox», «10K»…
2. **El inglés publicaba datos falsos de la beta.** La descripción decía «Free
   beta for the first 100» y los datos estructurados del FAQ decían «The beta
   opens in waves». Google y los asistentes de IA leen esos textos.
3. **Nada pensado para los buscadores con IA** (ChatGPT, Claude, Perplexity,
   Gemini): no había `llms.txt`, ni una respuesta directa a «¿qué es 2trAIn?».
4. **No se mide ninguna conversión.** El aviso de cookies habla de «cookies de
   analítica», pero la web no carga ninguna herramienta, y la CSP
   (`script-src 'self'`) bloquearía las etiquetas de Google Ads o Meta. Sin esto,
   no tiene sentido invertir en SEM.

Los cuatro están resueltos en esta rama. La medición de altas está montada en
código, pero falta publicarla: ver la sección 3.

## 1. SEO técnico

| Punto | Antes | Ahora |
| --- | --- | --- |
| Título ES | 2trAIn · El coach con IA que se acuerda de ti | 2trAIn · App de entrenamiento con IA: fuerza, cardio y Hyrox |
| Título EN | 2trAIn · The AI coach that remembers you | 2trAIn · AI training app for strength, cardio and Hyrox |
| Descripción ES | Sin «app» ni «IA» al principio | «App de entrenamiento con IA: tu plan de fuerza, cardio, Hyrox, triatlón o 10K se ajusta cada semana…» (≤160 caracteres) |
| Descripción EN | «Free beta for the first 100» (falso) | «AI training app… Open beta.» |
| Encima de la H1 | «Beta abierta» | «Entrenador con IA · Beta abierta» (la H1 no cambia: es la marca) |
| Datos estructurados | Organization, WebSite, SoftwareApplication y FAQ escrito a mano (el EN, desfasado) | Organization (logo cuadrado, `alternateName` 2train), WebSite, WebPage, MobileApplication con `featureList` y FAQPage **generado desde el FAQ visible** en los dos idiomas |
| FAQ | 9 preguntas | 10: nueva «¿Qué es 2trAIn?» con respuesta directa, y la de Hyrox nombra las pruebas (Hyrox, triatlón, 10K, media, maratón) |
| Sitemap | `lastmod` de septiembre | Al día y con las alternativas `hreflang` de la home |
| robots.txt | Todo abierto | Todo abierto y los rastreadores de IA permitidos de forma explícita |
| `llms.txt` | No existía | Resumen de qué es, qué la hace distinta, para quién, enlaces y empresa |

Ya estaba bien y no se ha tocado: canonical, hreflang (es, en, x-default),
`robots` con `max-image-preview:large`, Open Graph y Twitter, `alt` en todas las
imágenes, fuente precargada, scripts con `defer`, imágenes con carga diferida y
en WebP.

Cómo se mantiene: `scripts/i18n/seo_ld.py` regenera el JSON-LD a partir del FAQ
visible, así que el FAQ estructurado no puede volver a desfasarse. Tras tocar
`index.html`:

```bash
python3 scripts/i18n/seo_ld.py index.html es
python3 scripts/i18n/build_en.py . scripts/i18n/en-head.html
```

El segundo genera `en/index.html` con los pares de traducción y vuelve a
pasar `seo_ld.py` en inglés. La cabecera inglesa (título, descripción y Open
Graph) sale de `scripts/i18n/en-head.html`.

## 2. Buscadores con IA (GEO)

Qué se ha hecho:
- `llms.txt` en la raíz, en español y en inglés.
- Permiso explícito en `robots.txt` para GPTBot, OAI-SearchBot, ChatGPT-User,
  ClaudeBot, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User,
  Google-Extended, Applebot-Extended y CCBot.
- Una definición clara y citable en el FAQ («2trAIn es una app de entrenamiento
  con IA…») y en los datos estructurados.
- Los diferenciales, escritos igual en la web, en `featureList` y en `llms.txt`.

Lo que más pesa y no se arregla con código (pendiente, por orden):
1. **Páginas por intención:** `/hyrox`, `/triatlon`, `/10k`, `/maraton` y
   `/fuerza`, con su versión en inglés. Cada una responde de verdad a «cómo
   preparar X con una app»: cómo se construye el plan, una semana tipo, su FAQ.
   Es lo que los asistentes citan cuando alguien pregunta «¿qué app uso para
   preparar un Hyrox?». También sirven como landings de SEM.
2. **Menciones fuera de la web.** Los modelos se apoyan en lo que otros dicen:
   ficha en App Store y Google Play con la misma descripción, reseñas cuando
   salga de beta, comunidades (Hyrox, triatlón y running en español), artículos
   de «mejores apps para preparar…», Product Hunt y prensa.
3. **Datos propios.** Publicar los resultados del experimento público (IA contra
   coach humano) en cuanto existan. Los datos originales son lo que más se cita.
4. **Bing Webmaster Tools y Google Search Console.** Las búsquedas de ChatGPT
   usan el índice de Bing. Hay que dar de alta el dominio, enviar el sitemap y
   activar IndexNow.
5. **Nombre coherente** en Instagram, tiendas y LinkedIn: «2trAIn» y, en el
   texto, también «2train», porque así lo escribe la gente. Cuando existan,
   añadir LinkedIn, TikTok o YouTube a `sameAs`.

A confirmar: los datos estructurados dicen `iOS, Android`. Si la beta solo está
en una plataforma, hay que cambiarlo en `scripts/i18n/seo_ld.py`.

## 3. SEM (anuncios de pago)

**Medición de altas (hecha en código, falta publicarla).** Cada alta guarda de
dónde viene, sin herramientas de terceros ni cambios en la CSP:

- **Qué se guarda** junto al email: `utm_source`, `utm_medium`, `utm_campaign`,
  `utm_term`, `utm_content`, `gclid` (Google Ads), `fbclid` (Meta), la página de
  entrada, la web de procedencia y la página donde se apuntó.
- **En el navegador**, `app.js` lo lee de la URL. Solo lo guarda (90 días) si la
  persona aceptó las cookies; si no, vale para esa visita. Una visita nueva con
  UTM sustituye a la anterior.
- **En el servidor**, `join-waitlist` lo limpia (`attribution.ts`) y lo guarda
  solo en el primer alta. Si la migración aún no está aplicada, el alta sigue
  funcionando sin esos campos.
- **Para verlo**, la vista `waitlist_by_source` agrupa por semana, origen,
  medio, campaña y página. Sin UTM, el origen es «referido», la web de
  procedencia o «(directo)». Desde el editor SQL de Supabase:

```sql
select * from waitlist_by_source order by semana desc, altas desc;
-- Altas de Google Ads con gclid, para importarlas como conversión offline
select email, gclid, created_at from waitlist where gclid is not null order by created_at desc;
```

**Para publicarlo, en este orden:**
1. Aplicar `supabase/migrations/20261101090000_waitlist_attribution.sql`.
2. Desplegar la función: `supabase functions deploy join-waitlist`.
3. Publicar la web.
4. Añadir a la política de privacidad que, con el email, se guarda el origen de
   la visita (campaña, anuncio y páginas) para medir qué canales funcionan.

**Cómo nombrar las campañas** (siempre en minúsculas):
`utm_source` = google, instagram, meta, newsletter…; `utm_medium` = cpc,
social, email…; `utm_campaign` = `{prueba}_{idioma}_{mes}`, por ejemplo
`hyrox_es_2026-11`. Enlace de ejemplo:
`https://2trainapp.com/hyrox?utm_source=google&utm_medium=cpc&utm_campaign=hyrox_es_2026-11`.
En Google Ads basta con activar el etiquetado automático: añade `gclid` solo.

**Pendiente:** el aviso de cookies promete «cookies de analítica», pero solo se
usa el almacenamiento del origen descrito arriba. Conviene ajustar el texto.
Para contar visitas (no solo altas), la opción más sencilla es Vercel Web
Analytics: no usa cookies, se sirve desde el propio dominio y entra en la CSP.

**Estructura de campañas** (volúmenes y pujas por validar en el Planificador de
palabras clave; aquí no hay cifras inventadas):

| Grupo | Palabras clave de ejemplo | Landing |
| --- | --- | --- |
| Hyrox | plan entrenamiento hyrox, preparar hyrox, app hyrox, entrenamiento hyrox principiante | /hyrox |
| Triatlón | plan entrenamiento triatlón, preparar triatlón sprint, app triatlón | /triatlon |
| Carrera | plan 10k, plan media maratón, app para entrenar maratón | /10k, /maraton |
| Fuerza y general | app entrenador personal, entrenador personal ia, app gimnasio con ia, plan de fuerza | / o /fuerza |

- **Negativas de partida:** pdf, excel, plantilla, curso, certificación,
  empleo, trabajo.
- «Hyrox» es una marca registrada. Como palabra clave suele permitirse, pero en
  el texto del anuncio Google puede limitarla si el titular reclama: mejor
  «preparación para pruebas híbridas» en el título y Hyrox en la palabra clave.
- **Apps:** cuando esté en tiendas, Apple Search Ads y campañas de apps de
  Google son el canal más directo para instalaciones.
- **Meta (Instagram):** vídeo real de la app. Necesita la API de conversiones
  del lado del servidor por la misma razón de la CSP.
- **Prueba pequeña primero:** pocos grupos, dos o tres semanas, mirar el coste
  por alta y escalar solo lo que funcione.

## 4. Diseño: espacios y móvil

- **Ritmo único:** del título de una sección a su contenido siempre 24 px en
  móvil y 36 px en escritorio (`--head-gap`). Todas las secciones llevan el mismo
  margen arriba y abajo. Antes eran 10, 24, 32, 36 o 60 px según la sección.
- **Sin scroll lateral en móvil:** la galería de «Por qué» y los carruseles de
  ejercicios de la demo son ahora carruseles automáticos con puntos. Avanzan
  solos, se paran al pasar el ratón o al enfocarlos, se pueden deslizar y
  respetan «reducir movimiento». Comprobado de 320 a 1920 px: ningún elemento
  con scroll lateral y la página sin desbordes.
- **Objetivos:** título, pestañas y panel siguen cabiendo en un portátil de
  1440×790.

## 5. Próximos pasos

1. Publicar la rama y dar de alta Search Console y Bing Webmaster, con el sitemap.
2. Publicar la medición de altas (migración, función y política de privacidad).
3. Decidir qué pasa con el aviso de cookies.
4. ~~Páginas por intención~~: hechas `/hyrox`, `/triatlon`, `/10k`, `/maraton` y
   `/fuerza` (y sus versiones en inglés) con `scripts/pages/build_race.py`. Tras
   publicar, vigilar en Search Console qué búsquedas traen y ampliar su contenido.
5. Ficha en las tiendas y primeras menciones externas.
6. Confirmar las plataformas (iOS o Android) en los datos estructurados.
