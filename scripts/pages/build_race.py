"""Genera las páginas por objetivo (/hyrox, /triatlon, /10k, /maraton, /fuerza y
sus versiones en inglés) con la home como plantilla.

Cabecera, menú, alta a la beta, pie, modal y aviso de cookies salen tal cual de
index.html y en/index.html, así que el formulario y app.js funcionan igual. En
medio va el contenido de cada página, y el FAQ visible y el de los datos
estructurados salen de la misma lista. Todo lo que se dice de la app tiene que
estar ya en la home o en la demo: aquí no se prometen funciones nuevas.

Uso (desde la raíz del repo, después de generar el inglés):
  python3 scripts/pages/build_race.py .
"""
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
BASE = "https://2trainapp.com/"
ICO_PLUS = '<svg class="ico" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 4v16m-8-8h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
STATUS_SVG = '<svg width="66" height="12" viewBox="0 0 66 12" fill="#1D1D1F"><rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="6" width="3" height="6" rx="1"/><rect x="10" y="3.5" width="3" height="8.5" rx="1"/><rect x="15" y="1" width="3" height="11" rx="1"/><path d="M29 3.2a7.6 7.6 0 0 1 10 0l-1.3 1.3a5.8 5.8 0 0 0-7.4 0zM31.5 5.8a4.2 4.2 0 0 1 5 0L34 8.3z"/><rect x="43.5" y=".5" width="20" height="11" rx="3.2" fill="none" stroke="#1D1D1F" opacity=".4"/><rect x="45.5" y="2.5" width="14" height="7" rx="1.6"/><rect x="64.5" y="4" width="1.5" height="4" rx=".7" opacity=".4"/></svg>'
ARROW = '<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 8h10m0 0L8.5 3.5M13 8l-4.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'

# Textos comunes por idioma
COMMON = {
    "es": {"placeholder": "tu@email.com", "email_label": "Tu correo electrónico", "cta": "Unirme a la beta",
           "meta": "Sin tarjeta · El acceso te llega por email", "faq_eyebrow": "Preguntas frecuentes",
           "bridge3": '¿Tienes fecha? <b>Empieza hoy.</b>', "start": "Empezar sesión",
           "tile_adjust": ("Se ajusta cada semana", "Lo que entrenas y lo que le cuentas reescriben la semana siguiente. Cada cambio llega con su porqué."),
           "tile_peak": ("Periodizado hasta el día D", "Base, construcción y afinado. La última semana baja el volumen para que llegues fresco a la salida."),
           "faq_taper": "Baja el volumen y mantiene algo de intensidad para que llegues fresco. Es el afinado.",
           "faq_price": ("¿Cuánto cuesta?", "2trAIn está en beta abierta: te apuntas con tu email y el acceso te llega al momento, sin tarjeta."),
           "faq_watch": "No. Solo tu móvil.",
           "viz_plan": {"now": "Hoy", "flag": "Tu carrera", "phases": ["Base", "Construcción", "Afinado"], "cap": "Periodizado hacia el día de la carrera"},
           "viz_bars": "Carga por semana, con su descarga", "week_note": "Sesión a sesión, tal como la generó 2trAIn. La tuya sale de tu historial y de tu fecha."},
    "en": {"placeholder": "you@email.com", "email_label": "Your email", "cta": "Join the beta",
           "meta": "No card · Access arrives by email", "faq_eyebrow": "FAQ",
           "bridge3": 'Got a race date? <b>Start today.</b>', "start": "Start session",
           "tile_adjust": ("Adjusted every week", "Everything you train and tell it reshapes next week. Every change comes with a reason."),
           "tile_peak": ("Periodized to race day", "Base, build and taper. The last week drops the volume so you reach the start line fresh."),
           "faq_taper": "It drops the volume and keeps some intensity so you arrive fresh. That's the taper.",
           "faq_price": ("How much does it cost?", "2trAIn is in open beta: sign up with your email and access arrives right away, no card needed."),
           "faq_watch": "No. Just your phone.",
           "viz_plan": {"now": "Today", "flag": "Your race", "phases": ["Base", "Build", "Taper"], "cap": "Periodized toward race day"},
           "viz_bars": "Weekly load, with a deload week", "week_note": "Session by session, exactly as 2trAIn generated it. Yours is built from your history and your race date."},
}

PAGES = {
    "hyrox": {
        "es": {
            "path": "hyrox/index.html", "url": BASE + "hyrox", "other": "/en/hyrox/", "crumb": "Preparar HYROX",
            "title": "Plan de entrenamiento HYROX con IA · 2trAIn",
            "desc": "Prepara tu HYROX con un plan que va hacia tu fecha: carrera, estaciones y fuerza, ajustado cada semana y con cada cambio explicado. Beta abierta.",
            "eyebrow": "Preparación HYROX con IA · Beta abierta",
            "h1": 'Tu plan para HYROX, <span class="accent">hasta el día de la carrera.</span>',
            "lead": "Le dices la fecha. 2trAIn reparte carrera, estaciones y fuerza útil hasta ese día, y reescribe cada semana con lo que entrenas, con cada cambio explicado.",
            "meta_link": "Ver el formato",
            "phone": ("Martes · Fuerza", "Empuje, remo y trineo", "Por qué esta semana",
                      "Pierna y tirón pesan más que el empuje, y los gestos de la prueba aparecen en cada sesión de gimnasio."),
            "phone_rows": [("c-1476-th", "Press de banca con barra", "4×8"),
                           ("c-4-th", "Remo con torso inclinado", "4×8"),
                           ("c-500523-th", "Arrastre de trineo con saco pesado", "40 s · final"),
                           ("c-1505-th", "Zancada con barra", "3×10")],
            "bridge1": 'Primero, <b>qué te espera.</b>',
            "fmt": {"eyebrow": "El formato", "h2": '8 km de carrera. <span class="muted">8 estaciones entre medias.</span>',
                    "lead": "Cada kilómetro de carrera termina en una estación. Este es el orden del formato estándar:",
                    "items": [(str(i), n, "tras 1 km de carrera", d) for i, (n, d) in enumerate(
                        [("SkiErg", "1.000 m"), ("Empuje de trineo", "50 m"), ("Arrastre de trineo", "50 m"),
                         ("Burpees con salto largo", "80 m"), ("Remo", "1.000 m"), ("Paseo del granjero", "200 m"),
                         ("Zancadas con saco", "100 m"), ("Wall balls", "100 rep.")], 1)],
                    "note": "Los pesos cambian según la categoría (Open, Pro, Dobles o Relevos). Revisa siempre el reglamento oficial de tu edición."},
            "bridge2": 'Y para eso, <b>un plan con fecha.</b>',
            "how_eyebrow": "Cómo lo prepara 2trAIn", "how_h2": 'Un plan que va <span class="accent">hacia tu fecha.</span>', "viz": "plan",
            "tiles": ["peak", ("Carrera, estaciones y fuerza", "Zona 2 para la base, estaciones con técnica y carga, y al menos un día de fuerza para no perder lo ganado."),
                      "adjust", ("Con tu material", "¿Tu gimnasio no tiene trineo ni SkiErg? Lo cambia por alternativas con lo que tengas y lo recuerda.")],
            "week_eyebrow": "Una semana real", "week_h2": 'Así se ve <span class="accent">una semana.</span>',
            "faq_h2": 'Preparar HYROX, <span class="muted">sin dudas.</span>',
            "faq": [("¿Con cuánto tiempo tengo que empezar a preparar un HYROX?", "Cuanto antes, más progresivo. Le dices la fecha y el plan reparte las semanas que haya entre base, construcción y afinado. Si hay poco margen, se adapta a esas semanas."),
                    ("¿Necesito trineo, SkiErg o remo en mi gimnasio?", "No. Si te falta algo, lo cambia por alternativas con el material que tengas y lo recuerda para las semanas siguientes."),
                    ("¿Sirve si es mi primer HYROX?", "Sí. El plan parte de lo que ya haces y sube la carga poco a poco. Si vienes de fuerza, refuerza la carrera; si vienes de correr, las estaciones."),
                    ("¿Puedo seguir haciendo fuerza mientras lo preparo?", "Sí. Mantiene al menos un día de fuerza para que no pierdas lo ganado mientras sube la carrera."),
                    ("¿Qué pasa la semana de la carrera?", "taper"), "price",
                    ("¿2trAIn es la app oficial de HYROX?", "No. 2trAIn es una app independiente de entrenamiento con IA. HYROX es una marca registrada de su titular.")],
            "legal": "HYROX es una marca registrada de su titular. 2trAIn no está afiliada a HYROX ni cuenta con su patrocinio.",
        },
        "en": {
            "path": "en/hyrox/index.html", "url": BASE + "en/hyrox/", "other": "/hyrox", "crumb": "HYROX training",
            "title": "HYROX training plan with AI · 2trAIn",
            "desc": "Prepare for HYROX with a plan built around your race date: running, stations and strength, adjusted every week with every change explained. Open beta.",
            "eyebrow": "AI HYROX training · Open beta",
            "h1": 'Your HYROX plan, <span class="accent">all the way to race day.</span>',
            "lead": "Tell it the date. 2trAIn spreads running, stations and race-specific strength up to that day, and rewrites your plan every week based on what you train, with every change explained.",
            "meta_link": "See the format",
            "phone": ("Tuesday · Strength", "Push, row and sled", "Why this week",
                      "Legs and pulling outweigh pushing, and race movements show up in every gym session."),
            "phone_rows": [("c-1476-th", "Barbell bench press", "4×8"),
                           ("c-4-th", "Barbell bent-over row", "4×8"),
                           ("c-500523-th", "Heavy sandbag sled drag", "40 s · finisher"),
                           ("c-1505-th", "Barbell lunge", "3×10")],
            "bridge1": 'First, <b>what to expect.</b>',
            "fmt": {"eyebrow": "The format", "h2": '8 km of running. <span class="muted">8 stations in between.</span>',
                    "lead": "Every kilometer of running ends at a station. This is the order of the standard format:",
                    "items": [(str(i), n, "after 1 km of running", d) for i, (n, d) in enumerate(
                        [("SkiErg", "1,000 m"), ("Sled push", "50 m"), ("Sled pull", "50 m"),
                         ("Burpee broad jumps", "80 m"), ("Rowing", "1,000 m"), ("Farmers carry", "200 m"),
                         ("Sandbag lunges", "100 m"), ("Wall balls", "100 reps")], 1)],
                    "note": "Weights change by division (Open, Pro, Doubles or Relay). Always check the official rulebook for your event."},
            "bridge2": 'That\'s why you need <b>a plan with a date.</b>',
            "how_eyebrow": "How 2trAIn builds it", "how_h2": 'A plan built <span class="accent">around your race date.</span>', "viz": "plan",
            "tiles": ["peak", ("Running, stations and strength", "Zone 2 for the base, stations with technique and load, and at least one strength day so you keep what you've built."),
                      "adjust", ("With your equipment", "No sled or SkiErg at your gym? It swaps in alternatives using the equipment you have, and remembers.")],
            "week_eyebrow": "A real week", "week_h2": 'What <span class="accent">a week looks like.</span>',
            "faq_h2": 'HYROX prep, <span class="muted">answered.</span>',
            "faq": [("How early should I start preparing for a HYROX?", "The earlier you start, the more gradual the build. Tell it the date and the plan spreads the weeks you have across base, build and taper. If time is short, it works with the weeks you have."),
                    ("Do I need a sled, SkiErg or rower at my gym?", "No. If something is missing, it swaps it for alternatives with the equipment you have and remembers it for the following weeks."),
                    ("Does it work for my first HYROX?", "Yes. The plan starts from what you already do and raises the load gradually. If you have a strength background, it builds your running; if you're a runner, it builds your station work."),
                    ("Can I keep doing strength while I prepare?", "Yes. It keeps at least one strength day so you don't lose what you've built while the running goes up."),
                    ("What happens in race week?", "taper"), "price",
                    ("Is 2trAIn the official HYROX app?", "No. 2trAIn is an independent AI training app. HYROX is a registered trademark of its owner.")],
            "legal": "HYROX is a registered trademark of its owner. 2trAIn is not affiliated with or sponsored by HYROX.",
        },
    },
    "triatlon": {
        "es": {
            "path": "triatlon/index.html", "url": BASE + "triatlon", "other": "/en/triathlon/", "crumb": "Preparar un triatlón",
            "title": "Plan de entrenamiento de triatlón con IA · 2trAIn",
            "desc": "Prepara tu triatlón con un plan que va hacia tu fecha: natación, bici, carrera y fuerza, ajustado cada semana y con cada cambio explicado. Beta abierta.",
            "eyebrow": "Preparación de triatlón con IA · Beta abierta",
            "h1": 'Tu plan de triatlón, <span class="accent">hasta la línea de meta.</span>',
            "lead": "Le dices la prueba y la fecha. 2trAIn reparte natación, bici, carrera y fuerza en los días que entrenas, y reescribe cada semana con lo que haces, con cada cambio explicado.",
            "meta_link": "Ver las distancias",
            "phone": ("Semana 2 · Base", "Camino al triatlón", "Por qué esta semana",
                      "Hiciste la semana pasada con margen: entra un bloque de tempo en bici y otro en natación, y la tirada larga pasa de 75 a 85 min."),
            "phone_rows": [("LUN", "Bici con tempo", "60 min · 20 min a tempo"), ("MAR", "Natación continua", "60 min · Zona 2"),
                           ("MIÉ", "Rodaje con progresivos", "63 min · 6 progresivos"), ("DOM", "Tirada larga", "85 min · Zona 2")],
            "bridge1": 'Primero, <b>tu distancia.</b>',
            "fmt": {"eyebrow": "Las distancias", "h2": 'Nadar, pedalear, correr. <span class="muted">En ese orden.</span>',
                    "lead": "Las distancias más habituales:",
                    "items": [("1", "Sprint", "750 m nadando · 20 km en bici · 5 km corriendo", ""),
                              ("2", "Olímpico", "1,5 km nadando · 40 km en bici · 10 km corriendo", ""),
                              ("3", "Media distancia", "1,9 km nadando · 90 km en bici · 21,1 km corriendo", ""),
                              ("4", "Larga distancia", "3,8 km nadando · 180 km en bici · 42,2 km corriendo", "")],
                    "note": "Las distancias pueden variar según la organización. Revisa siempre el reglamento de tu prueba."},
            "bridge2": 'Y para eso, <b>un plan con fecha.</b>',
            "how_eyebrow": "Cómo lo prepara 2trAIn", "how_h2": 'Tres disciplinas, <span class="accent">un solo plan.</span>', "viz": "plan",
            "tiles": ["peak", ("Natación, bici y carrera", "Las tres repartidas en tus días, con descanso para asimilar la carga."),
                      "adjust", ("Encaja en tu semana", "Le dices cuántos días entrenas y el plan reparte las sesiones en esos días.")],
            "week_eyebrow": "Una semana real", "week_h2": 'Así se ve <span class="accent">una semana.</span>',
            "faq_h2": 'Preparar un triatlón, <span class="muted">sin dudas.</span>',
            "faq": [("¿Sirve para mi primer triatlón?", "Sí. El plan parte de lo que ya haces. Si vienes de correr, refuerza natación y bici; si vienes de nadar, la carrera."),
                    ("¿Qué distancias puedo preparar?", "Sprint, olímpico, media o larga distancia. Le dices la prueba y la fecha, y el plan se construye hacia ese día."),
                    ("¿Cuántos días a la semana necesito?", "Los que tengas. Le dices cuántos días entrenas y el plan reparte las tres disciplinas y la fuerza en ellos."),
                    ("¿Necesito reloj o potenciómetro?", "watch"),
                    ("¿Qué pasa la semana de la prueba?", "taper"), "price"],
        },
        "en": {
            "path": "en/triathlon/index.html", "url": BASE + "en/triathlon/", "other": "/triatlon", "crumb": "Triathlon training",
            "title": "Triathlon training plan with AI · 2trAIn",
            "desc": "Prepare for your triathlon with a plan built around your race date: swim, bike, run and strength, adjusted every week with every change explained. Open beta.",
            "eyebrow": "AI triathlon training · Open beta",
            "h1": 'Your triathlon plan, <span class="accent">all the way to the finish line.</span>',
            "lead": "Tell it the race and the date. 2trAIn spreads swim, bike, run and strength across the days you train, and rewrites your plan every week based on what you do, with every change explained.",
            "meta_link": "See the distances",
            "phone": ("Week 2 · Base", "Road to your triathlon", "Why this week",
                      "You handled last week comfortably, so there's a tempo block on the bike and another in the pool, and the long run goes from 75 to 85 min."),
            "phone_rows": [("MON", "Bike with tempo", "60 min · 20 min at tempo"), ("TUE", "Continuous swim", "60 min · Zone 2"),
                           ("WED", "Run with strides", "63 min · 6 strides"), ("SUN", "Long run", "85 min · Zone 2")],
            "bridge1": 'First, <b>your distance.</b>',
            "fmt": {"eyebrow": "The distances", "h2": 'Swim, bike, run. <span class="muted">In that order.</span>',
                    "lead": "The most common distances:",
                    "items": [("1", "Sprint", "750 m swim · 20 km bike · 5 km run", ""),
                              ("2", "Olympic", "1.5 km swim · 40 km bike · 10 km run", ""),
                              ("3", "Middle distance", "1.9 km swim · 90 km bike · 21.1 km run", ""),
                              ("4", "Long distance", "3.8 km swim · 180 km bike · 42.2 km run", "")],
                    "note": "Distances can vary by organizer. Always check your race's rulebook."},
            "bridge2": 'That\'s why you need <b>a plan with a date.</b>',
            "how_eyebrow": "How 2trAIn builds it", "how_h2": 'Three disciplines, <span class="accent">one plan.</span>', "viz": "plan",
            "tiles": ["peak", ("Swim, bike and run", "All three spread across your days, with rest to absorb the load."),
                      "adjust", ("Fits your week", "Tell it how many days you train and the plan spreads the sessions across those days.")],
            "week_eyebrow": "A real week", "week_h2": 'What <span class="accent">a week looks like.</span>',
            "faq_h2": 'Triathlon prep, <span class="muted">answered.</span>',
            "faq": [("Does it work for my first triathlon?", "Yes. The plan starts from what you already do. If you're a runner, it builds your swim and bike; if you're a swimmer, your bike and run."),
                    ("Which distances can I prepare for?", "Sprint, Olympic, middle or long distance. Tell it the race and the date, and the plan builds toward that day."),
                    ("How many days a week do I need?", "Whatever you have. Tell it how many days you train and the plan spreads the three disciplines and strength across them."),
                    ("Do I need a watch or a power meter?", "watch"),
                    ("What happens in race week?", "taper"), "price"],
        },
    },
    "10k": {
        "es": {
            "path": "10k/index.html", "url": BASE + "10k", "other": "/en/10k/", "crumb": "Preparar un 10K",
            "title": "Plan de entrenamiento 10K con IA · 2trAIn",
            "desc": "Prepara tu 10K con un plan que va hacia tu fecha: rodajes, series y fuerza, ajustado cada semana a tu ritmo y con cada cambio explicado. Beta abierta.",
            "eyebrow": "Preparación de 10K con IA · Beta abierta",
            "h1": 'Tu 10K, <span class="accent">a tu ritmo y con fecha.</span>',
            "lead": "Le dices la fecha. 2trAIn reparte rodajes, series y fuerza hasta ese día, aprende a qué ritmo respondes tú y reescribe cada semana, con cada cambio explicado.",
            "meta_link": "Para quién es",
            "phone": ("Semana 2 · Base", "Camino a tu 10K", "Por qué esta semana",
                      "Te saltaste el umbral por cansancio: el viernes vuelve, más contenido, y la tirada larga del domingo se mantiene."),
            "phone_rows": [("LUN", "Rodaje suave y core", "60 min · Zona 2"), ("MIÉ", "Ritmo sostenido", "60 min · 25 min continuos"),
                           ("VIE", "Umbral", "60 min · firme y controlado"), ("DOM", "Tirada larga", "78 min · Zona 2")],
            "bridge1": 'Primero, <b>de dónde partes.</b>',
            "fmt": {"eyebrow": "Para quién es", "h2": 'Primer 10K o mejor marca. <span class="muted">El plan cambia.</span>',
                    "lead": "Tu punto de partida y lo que buscas deciden cómo se construye:",
                    "items": [("1", "Tu primer 10K", "Llegar a meta corriendo, con el volumen subiendo poco a poco", ""),
                              ("2", "Bajar tu marca", "Más calidad: series y ritmos cerca de tu objetivo", ""),
                              ("3", "Volver a correr", "Retomar sin pasarte, con la carga controlada", ""),
                              ("4", "Correr y hacer fuerza", "Sin elegir: las dos cosas en el mismo plan", "")],
                    "note": ""},
            "bridge2": 'Y para eso, <b>un plan con fecha.</b>',
            "how_eyebrow": "Cómo lo prepara 2trAIn", "how_h2": 'Un plan que aprende <span class="accent">tu ritmo.</span>', "viz": "plan",
            "tiles": ["peak", ("Aprende tu ritmo", "Mide cómo respondes tú a cada semana y ajusta la progresión a tu ritmo, no al de la media."),
                      "adjust", ("Fuerza en el mismo plan", "Un día de fuerza que encaja con la carrera, sin tener que montarlo tú aparte.")],
            "week_eyebrow": "Una semana real", "week_h2": 'Así se ve <span class="accent">una semana.</span>',
            "faq_h2": 'Preparar un 10K, <span class="muted">sin dudas.</span>',
            "faq": [("¿Con cuánto tiempo tengo que empezar a preparar un 10K?", "Cuanto antes, más progresivo. Le dices la fecha y el plan reparte las semanas que haya entre base, construcción y afinado. Si hay poco margen, se adapta a esas semanas."),
                    ("¿Sirve si nunca he corrido 10 km?", "Sí. El plan parte de lo que ya haces y sube el volumen poco a poco hasta la distancia."),
                    ("¿Necesito reloj?", "watch"),
                    ("¿Puedo hacer fuerza a la vez?", "Sí. La fuerza va en el mismo plan, colocada para que encaje con la carrera."),
                    ("¿Qué pasa la semana de la carrera?", "taper"), "price"],
        },
        "en": {
            "path": "en/10k/index.html", "url": BASE + "en/10k/", "other": "/10k", "crumb": "10K training",
            "title": "10K training plan with AI · 2trAIn",
            "desc": "Prepare for your 10K with a plan built around your race date: easy runs, intervals and strength, adjusted every week to your pace with every change explained. Open beta.",
            "eyebrow": "AI 10K training · Open beta",
            "h1": 'Your 10K. <span class="accent">Your pace. Your race day.</span>',
            "lead": "Tell it the date. 2trAIn spreads easy runs, intervals and strength across the weeks leading up to it, learns how fast you respond and rewrites your plan every week, with every change explained.",
            "meta_link": "Who it's for",
            "phone": ("Week 2 · Base", "Road to your 10K", "Why this week",
                      "You skipped the threshold run because you were tired: it's back on Friday, a little lighter, and Sunday's long run stays."),
            "phone_rows": [("MON", "Easy run and core", "60 min · Zone 2"), ("WED", "Steady pace", "60 min · 25 min continuous"),
                           ("FRI", "Threshold", "60 min · firm but controlled"), ("SUN", "Long run", "78 min · Zone 2")],
            "bridge1": "First, <b>where you're starting from.</b>",
            "fmt": {"eyebrow": "Who it's for", "h2": 'First 10K or a new PR. <span class="muted">The plan changes.</span>',
                    "lead": "Where you're starting from and what you're after shape the plan:",
                    "items": [("1", "Your first 10K", "Run all the way to the finish, with volume rising gradually", ""),
                              ("2", "A new PR", "More quality: intervals and paces close to your goal", ""),
                              ("3", "Getting back to running", "Return without overdoing it, with the load under control", ""),
                              ("4", "Running and strength", "No need to choose: both in the same plan", "")],
                    "note": ""},
            "bridge2": 'That\'s why you need <b>a plan with a date.</b>',
            "how_eyebrow": "How 2trAIn builds it", "how_h2": 'A plan that learns <span class="accent">your pace.</span>', "viz": "plan",
            "tiles": ["peak", ("Learns your pace", "It measures how you respond each week and adjusts the progression to you, not the average."),
                      "adjust", ("Strength in the same plan", "One strength day that fits around your running, without you having to plan it separately.")],
            "week_eyebrow": "A real week", "week_h2": 'What <span class="accent">a week looks like.</span>',
            "faq_h2": '10K prep, <span class="muted">answered.</span>',
            "faq": [("How early should I start preparing for a 10K?", "The earlier you start, the more gradual the build. Tell it the date and the plan spreads the weeks you have across base, build and taper. If time is short, it works with the weeks you have."),
                    ("Does it work if I've never run 10 km?", "Yes. The plan starts from what you already do and builds up to the full distance gradually."),
                    ("Do I need a watch?", "watch"),
                    ("Can I do strength at the same time?", "Yes. Strength goes in the same plan, placed so it fits around your running."),
                    ("What happens in race week?", "taper"), "price"],
        },
    },
    "maraton": {
        "es": {
            "path": "maraton/index.html", "url": BASE + "maraton", "other": "/en/marathon/", "crumb": "Preparar un maratón",
            "title": "Plan de entrenamiento para maratón y media con IA · 2trAIn",
            "desc": "Prepara tu maratón o media maratón con un plan hacia tu fecha: tiradas largas, ritmos y fuerza, ajustado cada semana a cómo respondes. Beta abierta.",
            "eyebrow": "Maratón y media con IA · Beta abierta",
            "h1": 'Tu maratón, <span class="accent">kilómetro a kilómetro.</span>',
            "lead": "Le dices la carrera y la fecha. 2trAIn construye las tiradas largas, los ritmos y la fuerza hasta ese día, y reescribe cada semana según cómo respondes, con cada cambio explicado.",
            "meta_link": "Ver las distancias",
            "phone": ("Semana 2 · Base", "Camino al maratón", "Por qué esta semana",
                      "Te saltaste la tirada larga por un viaje: vuelve el sábado tal cual, y el lunes y el jueves suman una serie más."),
            "phone_rows": [("LUN", "Series cortas", "60 min · 11 × 90 s"), ("MAR", "Rodaje suave y core", "60 min · Zona 2"),
                           ("JUE", "Series de 2 minutos", "60 min · 7 series"), ("SÁB", "Tirada larga", "86 min · Zona 2")],
            "bridge1": 'Primero, <b>tu distancia.</b>',
            "fmt": {"eyebrow": "Las distancias", "h2": 'Media o maratón. <span class="muted">Cada una con su plan.</span>',
                    "lead": "Le dices cuál preparas y para cuándo:",
                    "items": [("1", "Media maratón", "La mitad de la distancia, la mitad de tiradas largas", "21,1 km"),
                              ("2", "Maratón", "Más volumen y tiradas largas que suben con cabeza", "42,2 km")],
                    "note": ""},
            "bridge2": 'Y para eso, <b>un plan con fecha.</b>',
            "how_eyebrow": "Cómo lo prepara 2trAIn", "how_h2": 'Volumen que sube <span class="accent">con cabeza.</span>', "viz": "bars",
            "tiles": [("Tiradas largas con descarga", "El volumen sube poco a poco y con semanas de descarga, según cómo lo absorbes."),
                      "peak", "adjust", ("Fuerza en el mismo plan", "Un día de fuerza que encaja con la carrera, sin tener que montarlo tú aparte.")],
            "week_eyebrow": "Una semana real", "week_h2": 'Así se ve <span class="accent">una semana.</span>',
            "faq_h2": 'Preparar un maratón, <span class="muted">sin dudas.</span>',
            "faq": [("¿Sirve para mi primer maratón?", "Sí. El plan parte de lo que ya haces y sube el volumen poco a poco, con semanas de descarga."),
                    ("¿Prepara también la media maratón?", "Sí. Le dices si preparas media o maratón y la fecha, y el plan se construye hacia ese día."),
                    ("¿Cuántos días a la semana necesito?", "Los que tengas. Le dices cuántos días entrenas y el plan reparte las sesiones en ellos."),
                    ("¿Necesito reloj?", "watch"),
                    ("¿Qué pasa las últimas semanas?", "taper"), "price"],
        },
        "en": {
            "path": "en/marathon/index.html", "url": BASE + "en/marathon/", "other": "/maraton", "crumb": "Marathon training",
            "title": "Marathon and half marathon training plan with AI · 2trAIn",
            "desc": "Prepare for your marathon or half marathon with a plan built around your race date: long runs, paces and strength, adjusted every week to how you respond. Open beta.",
            "eyebrow": "AI marathon and half training · Open beta",
            "h1": 'Your marathon, <span class="accent">one kilometer at a time.</span>',
            "lead": "Tell it the race and the date. 2trAIn builds the long runs, paces and strength up to that day, and rewrites your plan every week based on how you respond, with every change explained.",
            "meta_link": "See the distances",
            "phone": ("Week 2 · Base", "Road to the marathon", "Why this week",
                      "You skipped the long run because of a trip: it's back on Saturday as it was, and Monday and Thursday each get one extra rep."),
            "phone_rows": [("MON", "Short intervals", "60 min · 11 × 90 s"), ("TUE", "Easy run and core", "60 min · Zone 2"),
                           ("THU", "2-minute intervals", "60 min · 7 reps"), ("SAT", "Long run", "86 min · Zone 2")],
            "bridge1": 'First, <b>your distance.</b>',
            "fmt": {"eyebrow": "The distances", "h2": 'Half or full. <span class="muted">Each with its own plan.</span>',
                    "lead": "Tell it which one and when:",
                    "items": [("1", "Half marathon", "Half the distance, shorter long runs", "21.1 km"),
                              ("2", "Marathon", "More volume and long runs that build sensibly", "42.2 km")],
                    "note": ""},
            "bridge2": 'That\'s why you need <b>a plan with a date.</b>',
            "how_eyebrow": "How 2trAIn builds it", "how_h2": 'Volume that builds <span class="accent">sensibly.</span>', "viz": "bars",
            "tiles": [("Long runs with deloads", "Volume rises gradually, with deload weeks, depending on how your body handles it."),
                      "peak", "adjust", ("Strength in the same plan", "One strength day that fits around your running, without you having to plan it separately.")],
            "week_eyebrow": "A real week", "week_h2": 'What <span class="accent">a week looks like.</span>',
            "faq_h2": 'Marathon prep, <span class="muted">answered.</span>',
            "faq": [("Does it work for my first marathon?", "Yes. The plan starts from what you already do and raises the volume gradually, with deload weeks."),
                    ("Does it work for the half marathon too?", "Yes. Tell it whether it's a half or a full and the date, and the plan builds toward that day."),
                    ("How many days a week do I need?", "Whatever you have. Tell it how many days you train and the plan spreads the sessions across them."),
                    ("Do I need a watch?", "watch"),
                    ("What happens in the last weeks?", "taper"), "price"],
        },
    },
    "fuerza": {
        "es": {
            "path": "fuerza/index.html", "url": BASE + "fuerza", "other": "/en/strength/", "crumb": "Entrenamiento de fuerza",
            "title": "Plan de entrenamiento de fuerza con IA · 2trAIn",
            "desc": "Gana fuerza o músculo con un plan que progresa solo: cada semana ajusta cargas y volumen con lo que entrenas, y te explica cada cambio. Beta abierta.",
            "eyebrow": "Entrenamiento de fuerza con IA · Beta abierta",
            "h1": 'Más fuerte cada semana, <span class="accent">sin adivinar las cargas.</span>',
            "lead": "Le dices tu objetivo y tu material. 2trAIn construye bloques de empuje, tirón y pierna, sube la carga cuando toca y te explica cada cambio con tus datos.",
            "meta_link": "Elige tu objetivo",
            "phone": ("Semana 2 · Descarga", "Sentadilla y banca", "Por qué esta semana",
                      "La semana pasada lo hiciste todo al límite: mantienes los cuatro días, con menos series y más margen para recuperar."),
            "phone_rows": [("c-47108-th", "Sentadilla con barra baja", "4×5 · 2-3 en reserva"),
                           ("c-1476-th", "Press de banca con barra", "3×5"),
                           ("c-1494-th", "Sentadilla completa con barra", "3×8"),
                           ("c-3462-th", "Peso muerto rumano con mancuernas", "3×10")],
            "bridge1": 'Primero, <b>tu objetivo.</b>',
            "fmt": {"eyebrow": "Tu objetivo", "h2": 'Músculo o fuerza. <span class="muted">Con lo que tengas.</span>',
                    "lead": "Lo que buscas y tu material deciden cómo se construye:",
                    "items": [("1", "Hipertrofia", "Más músculo: volumen y repeticiones para crecer", ""),
                              ("2", "Fuerza", "Más carga en los básicos: sentadilla, peso muerto y press", ""),
                              ("3", "En casa o en el gimnasio", "Con el material que tengas, sin ejercicios que no puedas hacer", ""),
                              ("4", "Con lesiones o molestias", "Se lo cuentas una vez y adapta los ejercicios", "")],
                    "note": ""},
            "bridge2": 'Y para eso, <b>un plan que progresa.</b>',
            "how_eyebrow": "Cómo lo construye 2trAIn", "how_h2": 'Progresión de carga, <span class="accent">explicada.</span>', "viz": "bars",
            "tiles": [("Progresión con descarga", "Sube peso o repeticiones cuando las sesiones lo dicen, y mete descargas cuando tocan."),
                      ("Cada cambio, explicado", "Si sube, baja o cambia algo, te dice por qué con tus propios datos."),
                      ("Más de 1.600 ejercicios", "Cada uno con vídeo y ficha técnica, y sustituciones al momento si te falta material."),
                      ("Recuerda lo tuyo", "Lesiones, material y vetos: se lo dices una vez y no vuelve a proponerlo.")],
            "week_eyebrow": "Una semana real", "week_h2": 'Así se ve <span class="accent">una semana.</span>',
            "week_lead": "Sesión a sesión, tal como la generó 2trAIn. La tuya sale de tu historial, tu objetivo y tu material.",
            "faq_h2": 'Entrenar fuerza, <span class="muted">sin dudas.</span>',
            "faq": [("¿Sirve para ganar músculo o solo fuerza?", "Para las dos. Eliges hipertrofia o fuerza y el plan ajusta el volumen y las repeticiones a ese objetivo."),
                    ("¿Puedo entrenar en casa?", "Sí. Le dices el material que tienes y el plan se construye con eso, sin ejercicios que no puedas hacer."),
                    ("¿Cómo sabe cuándo subir el peso?", "Con lo que registras: si las series salen con margen, sube; si te cuestan más de la cuenta, mantiene o baja. Y te dice por qué."),
                    ("¿Y si tengo una lesión o una molestia?", "Se lo cuentas y lo recuerda: quita lo que te molesta y busca alternativas que mantengan el estímulo."),
                    ("¿Necesito experiencia?", "No. El plan parte de lo que ya haces y cada ejercicio tiene su vídeo y su ficha técnica."),
                    "price"],
        },
        "en": {
            "path": "en/strength/index.html", "url": BASE + "en/strength/", "other": "/fuerza", "crumb": "Strength training",
            "title": "Strength training plan with AI · 2trAIn",
            "desc": "Build strength or muscle with a plan that progresses on its own: every week it adjusts loads and volume from what you train, and explains every change. Open beta.",
            "eyebrow": "AI strength training · Open beta",
            "h1": 'Stronger every week, <span class="accent">without guessing your weights.</span>',
            "lead": "Tell it your goal and your equipment. 2trAIn builds push, pull and leg blocks, raises the load when it's time and explains every change with your data.",
            "meta_link": "Pick your goal",
            "phone": ("Week 2 · Deload", "Squat and bench", "Why this week",
                      "Last week every set was at your limit: you keep all four days, with fewer sets and more room to recover."),
            "phone_rows": [("c-47108-th", "Barbell low-bar squat", "4×5 · 2–3 reps in reserve"),
                           ("c-1476-th", "Barbell bench press", "3×5"),
                           ("c-1494-th", "Barbell full squat", "3×8"),
                           ("c-3462-th", "Dumbbell Romanian deadlift", "3×10")],
            "bridge1": 'First, <b>your goal.</b>',
            "fmt": {"eyebrow": "Your goal", "h2": 'Muscle or strength. <span class="muted">With what you have.</span>',
                    "lead": "What you're after and your equipment shape the plan:",
                    "items": [("1", "Hypertrophy", "More muscle: volume and reps to grow", ""),
                              ("2", "Strength", "More load on the basics: squat, deadlift and press", ""),
                              ("3", "At home or in the gym", "With the equipment you have, no exercises you can't do", ""),
                              ("4", "With injuries or aches", "Tell it once and it adapts the exercises", "")],
                    "note": ""},
            "bridge2": 'That\'s why you need <b>a plan that progresses.</b>',
            "how_eyebrow": "How 2trAIn builds it", "how_h2": 'Load progression, <span class="accent">explained.</span>', "viz": "bars",
            "tiles": [("Progression with deloads", "It adds weight or reps when your sessions show you're ready, and schedules deloads when they're due."),
                      ("Every change, explained", "If something goes up, down or changes, it tells you why with your own data."),
                      ("1,600+ exercises", "Each with video and a technique card, and instant swaps if you're missing equipment."),
                      ("Remembers your limits", "Injuries, equipment and exercises you've ruled out: tell it once and it plans around them.")],
            "week_eyebrow": "A real week", "week_h2": 'What <span class="accent">a week looks like.</span>',
            "week_lead": "Session by session, exactly as 2trAIn generated it. Yours comes from your history, your goal and your equipment.",
            "faq_h2": 'Strength training, <span class="muted">answered.</span>',
            "faq": [("Does it work for building muscle or just strength?", "Both. Pick hypertrophy or strength and the plan adjusts volume and reps to that goal."),
                    ("Can I train at home?", "Yes. Tell it what equipment you have and the plan is built with that, no exercises you can't do."),
                    ("How does it know when to add weight?", "From what you log: if your sets have reps in reserve, it goes up; if they're harder than they should be, it holds or drops. And it tells you why."),
                    ("What if I have an injury or a nagging ache?", "Tell it and it remembers: it removes what bothers you and finds alternatives that keep the stimulus."),
                    ("Do I need experience?", "No. The plan starts from what you already do and every exercise has its video and technique card."),
                    "price"],
        },
    },
}

# Semana real de cada página (semanas.json, sacada de la revisión de la LLM con
# scripts/pages/extraer_semanas.py). Aquí solo van los textos: por sesión, título
# y una línea de resumen, en el orden de los días entrenados. «picks» elige qué
# ejercicios enseñar en los días de gimnasio (por defecto, los cuatro primeros).
SEMANAS = json.loads((pathlib.Path(__file__).with_name("semanas.json")).read_text(encoding="utf-8"))
WEEKS = {
    "hyrox": [{"src": ("hyrox", "hyrox"),
               "picks": {0: ["1494", "339", "500349", "4536"], 1: ["1476", "4", "500523", "47985"], 4: ["1483", "1493", "500524", "293"]},
               "es": {"note": "Perfil: hombre de 29 años · HYROX el 14 de marzo · 5 días por semana",
                      "days": [("Pierna y tirón con AMRAP", "Pierna y tirón pesados; cierra con granjero, thruster y remoergómetro."),
                               ("Empuje, remo y trineo", "Press, remo y zancada; al final, arrastre de trineo y golpes con balón."),
                               ("Carrera de ritmo", "3 × 10 min en Zona 4, recuperando 2 min."),
                               ("Tirada larga con prueba de ritmo", "30 min de prueba a ritmo de conversación y 30 min más."),
                               ("Gestos de prueba y AMRAP", "Peso muerto y sentadilla frontal; acaba con trineo y burpees.")]},
               "en": {"note": "Profile: man, 29 · HYROX on March 14 · 5 days a week",
                      "days": [("Legs and pull with AMRAP", "Heavy legs and pull; finishes with farmer walk, thrusters and the rower."),
                               ("Push, row and sled", "Press, row and lunge; then sled drag and med ball slams."),
                               ("Tempo run", "3 × 10 min in Zone 4, 2 min easy between."),
                               ("Long run with a pace test", "30-min conversational pace test, then 30 more."),
                               ("Race movements and AMRAP", "Deadlift and front squat; ends with sled and burpees.")]}}],
    "triatlon": [{"src": ("triatlon", "triatlon"),
                  "es": {"note": "Perfil: mujer de 38 años · triatlón · 6 días por semana · semana 2",
                         "days": [("Bici con tempo", "20 min a tempo, estable y sin apretar al final."),
                                  ("Natación continua", "55 min seguidos en Zona 2."),
                                  ("Rodaje con progresivos", "47 min suaves y 6 progresivos de 20 s al final."),
                                  ("Bici suave", "50 min en Zona 2."),
                                  ("Natación con tempo", "15 min de bloque continuo a ritmo estable."),
                                  ("Tirada larga", "75 min en Zona 2.")]},
                  "en": {"note": "Profile: woman, 38 · triathlon · 6 days a week · week 2",
                         "days": [("Bike with tempo", "20 min at tempo, steady, without pushing at the end."),
                                  ("Continuous swim", "55 min non-stop in Zone 2."),
                                  ("Run with strides", "47 easy minutes and 6 × 20 s strides at the end."),
                                  ("Easy bike", "50 min in Zone 2."),
                                  ("Swim with tempo", "15-min continuous block at a steady pace."),
                                  ("Long run", "75 min in Zone 2.")]}}],
    "10k": [{"src": ("10k", "10k"),
             "es": {"note": "Perfil: hombre de 40 años · 10K · 4 días por semana · semana 2",
                    "days": [("Rodaje suave y core", "4 bloques de 13 min en Zona 2 y dead bug al terminar."),
                             ("Calidad: ritmo sostenido", "25 min continuos en Zona 3."),
                             ("Calidad: umbral", "15 min en Zona 4 y 2 bloques más: vuelve, más contenido, tras el cansancio."),
                             ("Tirada larga", "5 bloques de 14 min. Termina sintiendo que podrías seguir.")]},
             "en": {"note": "Profile: man, 40 · 10K · 4 days a week · week 2",
                    "days": [("Easy run and core", "4 × 13 min in Zone 2, dead bugs at the end."),
                             ("Quality: steady pace", "25 min continuous in Zone 3."),
                             ("Quality: threshold", "15 min in Zone 4 plus 2 more blocks, eased back after last week's fatigue."),
                             ("Long run", "5 × 14 min blocks. Finish feeling like you could keep going.")]}}],
    "maraton": [{"src": ("maraton", "maraton"),
                 "es": {"tab": "Maratón", "note": "Perfil: hombre de 45 años · maratón · 5 días por semana · semana 2",
                        "days": [("Series cortas", "11 × 90 s fuertes pero controladas, recuperando 90 s."),
                                 ("Rodaje suave y core", "4 bloques en Zona 2; core: dead bug, plancha y hollow hold."),
                                 ("Series de 2 minutos", "7 × 2 min con el mismo esfuerzo en todas."),
                                 ("Tirada larga", "86 min en Zona 2, por bloques."),
                                 ("Rodaje de recuperación", "Muy suave, para soltar piernas.")]},
                 "en": {"tab": "Marathon", "note": "Profile: man, 45 · marathon · 5 days a week · week 2",
                        "days": [("Short intervals", "11 × 90 s, hard but controlled, 90 s easy between."),
                                 ("Easy run and core", "4 Zone 2 blocks; core: dead bug, plank and hollow hold."),
                                 ("2-minute intervals", "7 × 2 min at the same effort."),
                                 ("Long run", "86 min in Zone 2, in blocks."),
                                 ("Recovery run", "Very easy, to loosen the legs.")]}},
                {"src": ("maraton", "media"),
                 "es": {"tab": "Media maratón", "note": "Perfil: mujer de 33 años · media maratón de 2:05 a 1:55 · 4 días por semana · semana 2",
                        "days": [("Fartlek por sensaciones", "6 cambios de 2 min fuertes, sin parar."),
                                 ("Cuestas en tierra", "7 cuestas de 90 s con zancada corta y firme."),
                                 ("Rodaje continuo suave", "50 min en Zona 2, pudiendo hablar todo el rato."),
                                 ("Tirada larga", "75 min suaves y constantes.")]},
                 "en": {"tab": "Half marathon", "note": "Profile: woman, 33 · half marathon from 2:05 to 1:55 · 4 days a week · week 2",
                        "days": [("Fartlek by feel", "6 hard 2-minute surges, without stopping."),
                                 ("Hill repeats on trail", "7 × 90 s hills with a short, firm stride."),
                                 ("Easy continuous run", "50 min in Zone 2, able to talk the whole time."),
                                 ("Long run", "75 easy, even minutes.")]}}],
    "fuerza": [{"src": ("fuerza", "fuerza"),
                "es": {"note": "Perfil: mujer de 27 años · powerlifting · 4 días · semana de descarga tras una semana al límite",
                       "days": [("Sentadilla y banca", "Descarga: deja 2-3 repeticiones en reserva."),
                                ("Banca con pausa y tirón", "Pausa controlada en el pecho, sin llegar al fallo."),
                                ("Peso muerto y pierna", "Series técnicas y limpias, con margen."),
                                ("Press militar y pierna unilateral", "Pierna controlada y hombro estable.")]},
                "en": {"note": "Profile: woman, 27 · powerlifting · 4 days · deload week after a week at her limit",
                       "days": [("Squat and bench", "Deload: leave 2–3 reps in reserve."),
                                ("Paused bench and pull", "Controlled pause on the chest, never to failure."),
                                ("Deadlift and legs", "Clean, technical sets with room to spare."),
                                ("Military press and single-leg work", "Controlled legs and stable shoulders.")]}}],
}
# Artículo del blog que explica la semana de cada página
ARTICULO = {
    "hyrox": {"es": ("/blog/semana-entrenamiento-hyrox", "Por qué está montada así, sesión a sesión"),
              "en": ("/en/blog/hyrox-training-week/", "Why it's built this way, session by session")},
    "maraton": {"es": ("/blog/semana-entrenamiento-maraton", "Por qué está montada así, sesión a sesión"),
                "en": ("/en/blog/marathon-training-week/", "Why it's built this way, session by session")},
    "fuerza": {"es": ("/blog/semana-de-descarga", "Qué es una semana de descarga y cómo se hace"),
               "en": ("/en/blog/deload-week/", "What a deload week is and how to do one")},
}
DIAS = {"es": ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"], "en": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]}
DIAS_1 = {"es": "LMXJVSD", "en": "MTWTFSS"}
DIA_N = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
WK = {
    "es": {"mod": {"running": "Carrera", "cycling": "Bici", "swimming": "Natación", "gym": "Fuerza"}, "zone": "Zona",
           "sessions": "sesiones", "more": "+{n} ejercicios más", "rep": "rep.", "rest": "Descanso",
           "legend": "Intensidad", "strength": "Fuerza", "prof": "Intensidad de la sesión por tramos"},
    "en": {"mod": {"running": "Run", "cycling": "Bike", "swimming": "Swim", "gym": "Strength"}, "zone": "Zone",
           "sessions": "sessions", "more": "+{n} more exercises", "rep": "reps", "rest": "Rest",
           "legend": "Intensity", "strength": "Strength", "prof": "Session intensity by segment"},
}


def esc(t):
    return html.escape(t, quote=True)


def bridge(t):
    return ('<!-- Hilo -->\n<div class="bridge" aria-hidden="false">\n'
            '  <span class="bridge__line"></span><span class="bridge__dot"></span>\n'
            f'  <p class="bridge__t">{t}</p>\n</div>\n')


def faq_items(c, k):
    out = []
    for f in c["faq"]:
        if f == "price":
            out.append(k["faq_price"])
            continue
        q, a = f
        out.append((q, {"taper": k["faq_taper"], "watch": k["faq_watch"]}.get(a, a)))
    return out


def dose(e, w):
    if e["seg"]:
        return f'{e["sets"]} × {e["seg"]} s' if e["sets"] > 1 else f'{e["seg"]} s'
    return f'{e["sets"]}×{e["reps"]}' if e["sets"] > 1 else f'{e["reps"]} {w["rep"]}'


def week_html(slug, lang):
    """Semana real: resumen (sesiones, tiempo y barra por día) y una tarjeta por
    sesión. Cardio: gráfica de intensidad por tramos. Gimnasio: ejercicios con foto."""
    w = WK[lang]
    variants = WEEKS[slug]
    out = ['    <div class="wk" data-wk>']
    if len(variants) > 1:
        out.append('      <div class="wk-tabs" role="tablist">' + "".join(
            f'<button type="button" role="tab" id="wk-tab-{i}" aria-controls="wk-panel-{i}" aria-selected="{str(i == 0).lower()}"'
            + ("" if i == 0 else ' tabindex="-1"') + f'>{esc(v[lang]["tab"])}</button>'
            for i, v in enumerate(variants)) + '</div>')
    for vi, v in enumerate(variants):
        sem = SEMANAS[v["src"][0]][v["src"][1]]
        t = v[lang]
        dias = sem["dias"]
        assert len(dias) == len(t["days"]), (slug, len(dias), len(t["days"]))
        total = sum(d["min"] for d in dias)
        hm = f'{total // 60} h {total % 60} min' if total % 60 else f'{total // 60} h'
        by_day = {DIA_N[d["dia"]]: d for d in dias}
        top = max(d["min"] for d in dias)

        def zmax(d):
            return max((z for _, z, _ in d["tramos"]), default=2) if d["tipo"] == "cardio" else 0
        strip = []
        for i in range(7):
            d = by_day.get(i)
            if d:
                cls = f'z{zmax(d)}' if d["tipo"] == "cardio" else "gym"
                strip.append(f'<span class="wk-strip__d"><i class="{cls}" style="--h:{round(d["min"] / top * 100)}%"></i><b>{DIAS_1[lang][i]}</b></span>')
            else:
                strip.append(f'<span class="wk-strip__d is-rest"><i></i><b>{DIAS_1[lang][i]}</b></span>')
        legend = []
        if any(d["tipo"] == "cardio" for d in dias):
            legend.append(f'<span>{esc(w["legend"])} <i class="z1"></i><i class="z2"></i><i class="z3"></i><i class="z4"></i> Z1–Z4</span>')
        if any(d["tipo"] != "cardio" for d in dias):
            legend.append(f'<span><i class="gym"></i>{esc(w["strength"])}</span>')
        cards = []
        for di, (d, (title, summ)) in enumerate(zip(dias, t["days"])):
            day = DIAS[lang][DIA_N[d["dia"]]]
            if d["tipo"] == "cardio":
                mod = w["mod"].get(d["modalidad"], w["mod"]["running"])
                chip = f'{mod} · {w["zone"]} {zmax(d)}'
                segs = "".join(f'<i class="z{z}" style="--g:{sec}"></i>' for sec, z, _ in d["tramos"])
                body = f'<div class="wk-prof" role="img" aria-label="{esc(w["prof"])}: {esc(summ)}">{segs}</div>'
                kind = "cardio"
            else:
                chip = w["mod"]["gym"]
                exs = d["ejercicios"]
                pick = v.get("picks", {}).get(di)
                shown = [next(e for e in exs if e["id"] == i) for i in pick] if pick else exs[:4]
                rows = "".join(
                    f'<li><img src="/assets/ej/c-{e["id"]}-th.jpg" alt="" width="240" height="160" loading="lazy" decoding="async">'
                    f'<span><b>{esc(e[lang])}</b><small>{esc(dose(e, w))}</small></span></li>' for e in shown)
                more = len(exs) - len(shown)
                body = f'<ul class="wk-ex">{rows}</ul>' + (f'<p class="wk-more">{esc(w["more"].format(n=more))}</p>' if more > 0 else "")
                kind = "gym"
            cards.append(
                f'        <li class="wk-day wk-day--{kind}">'
                f'<div class="wk-day__head"><span class="wk-day__d">{day}</span>'
                f'<div class="wk-day__t"><span class="wk-chip">{esc(chip)}</span><b>{esc(title)}</b></div>'
                f'<span class="wk-day__min">{d["min"]}<small>min</small></span></div>'
                f'{body}<p class="wk-day__sum">{esc(summ)}</p></li>')
        hidden = "" if vi == 0 else " hidden"
        role = f' role="tabpanel" id="wk-panel-{vi}" aria-labelledby="wk-tab-{vi}"' if len(variants) > 1 else ""
        out.append(f'      <div class="wk-panel" data-anim{role}{hidden}>')
        out.append(f'        <p class="wk-who">{esc(t["note"])}</p>')
        out.append('        <div class="wk-sum">'
                   f'<p class="wk-stats"><b>{len(dias)}</b> {esc(w["sessions"])} · <b>{hm}</b></p>'
                   f'<div class="wk-strip" aria-hidden="true">{"".join(strip)}</div>'
                   f'<p class="wk-legend" aria-hidden="true">{"".join(legend)}</p></div>')
        out.append('        <ol class="wk-days">\n' + "\n".join(cards) + '\n        </ol>')
        out.append('      </div>')
    out.append('    </div>')
    return "\n".join(out)


def viz_html(kind, k):
    if kind == "bars":
        deload = ' class="is-deload"'
        bars = "".join(f'<i{deload if i == 4 else ""} style="--h:{h}%;--i:{i}"></i>' for i, h in enumerate([34, 42, 50, 58, 36, 56, 65, 76]))
        return f'<span class="viz" aria-hidden="true"><span class="viz__bars">{bars}</span><span class="viz__cap">{esc(k["viz_bars"])}</span></span>'
    v = k["viz_plan"]
    return (f'<span class="viz" aria-hidden="true"><span class="viz__plan"><span class="viz__now">{esc(v["now"])}</span>'
            '<span class="viz__track"><i style="--w:45%;--i:0"></i><i style="--w:35%;--i:1"></i><i style="--w:20%;--i:2"></i></span>'
            f'<span class="viz__phases"><b style="--w:45%">{esc(v["phases"][0])}</b><b style="--w:35%">{esc(v["phases"][1])}</b><b style="--w:20%">{esc(v["phases"][2])}</b></span>'
            f'<span class="viz__flag"><svg viewBox="0 0 24 24" fill="none"><path d="M5 21V4m0 0h11l-2 4 2 4H5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>{esc(v["flag"])}</span></span>'
            f'<span class="viz__cap">{esc(v["cap"])}</span></span>')


def sections(slug, c, k):
    kicker, ptitle, why_t, why = c["phone"]
    rows = []
    for img, n, m in c["phone_rows"]:
        if img.isupper():
            media = f'<span class="app-ex__day">{esc(img)}</span>'
        else:
            src = f"/assets/ej/{img}.jpg"
            w, h = (240, 160) if img.endswith("-th") else (640, 360)
            media = f'<img src="{src}" alt="" width="{w}" height="{h}" decoding="async">'
        rows.append(f'              <div class="app-ex">{media}<div><b>{esc(n)}</b><span>{esc(m)}</span></div></div>')
    hero = f'''<section id="hero" class="hero">
  <div class="max-w-page pad-x hero__grid">
    <div class="hero__copy">
      <p class="eyebrow"><span class="live-dot" aria-hidden="true"></span>{esc(c["eyebrow"])}</p>
      <h1 class="t-hero hero__title">{c["h1"]}</h1>
      <p class="hero__sub">{esc(c["lead"])}</p>
      <div class="hero__cta">
        <form id="hero-form" class="hero-form">
          <input id="hero-email" type="email" name="email" required placeholder="{esc(k["placeholder"])}" aria-label="{esc(k["email_label"])}" autocomplete="email" />
          <button type="submit" class="btn" aria-label="{esc(k["cta"])}">
            <span class="btn-label">{esc(k["cta"])}</span>
            {ARROW}
          </button>
        </form>
        <div class="hero__meta">
          <span>{esc(k["meta"])}</span>
          <a href="#formato" class="link">{esc(c["meta_link"])}</a>
        </div>
      </div>
    </div>

    <div class="hero__device" aria-hidden="true">
      <div class="phone">
        <div class="phone-screen phone-screen--light">
          <div class="app-ui">
            <div class="app-ui__status"><span>9:41</span>{STATUS_SVG}</div>
            <div class="app-ui__head">
              <span class="app-ui__ava"><img src="/assets/hexagono.svg" alt="" width="20" height="20"></span>
              <div>
                <div class="app-ui__kicker">{esc(kicker)}</div>
                <div class="app-ui__title">{esc(ptitle)}</div>
              </div>
            </div>
            <div class="app-ui__why">
              <b>{esc(why_t)}</b>
              <span>{esc(why)}</span>
            </div>
            <div class="app-ui__list">
{chr(10).join(rows)}
            </div>
            <span class="app-ui__cta">{esc(k["start"])}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
'''
    f = c["fmt"]
    items = "\n".join(
        f'      <li><span class="race-format__n">{esc(n)}</span><span><b>{esc(t)}</b><small>{esc(sub)}</small></span>'
        + (f'<span class="race-format__d">{esc(val)}</span>' if val else "") + "</li>"
        for n, t, sub, val in f["items"])
    note = f'\n    <p class="race-note">{esc(f["note"])}</p>' if f["note"] else ""
    fmt = f'''<section id="formato" class="sec">
  <div class="max-w-page pad-x">
    <div class="sec-head sec-head--center" data-reveal>
      <p class="eyebrow">{esc(f["eyebrow"])}</p>
      <h2 class="t-h2">{f["h2"]}</h2>
      <p class="t-lead">{esc(f["lead"])}</p>
    </div>
    <ol class="race-format" data-reveal-stagger>
{items}
    </ol>{note}
  </div>
</section>
'''
    tiles = []
    for i, t in enumerate(c["tiles"]):
        title, text = k["tile_peak"] if t == "peak" else k["tile_adjust"] if t == "adjust" else t
        tiles.append(f'      <div class="race-tile"><h3>{esc(title)}</h3><p>{esc(text)}</p>{viz_html(c["viz"], k) if i == 0 else ""}</div>')
    how = f'''<section id="como" class="sec">
  <div class="max-w-page pad-x">
    <div class="sec-head sec-head--center" data-reveal>
      <p class="eyebrow">{esc(c["how_eyebrow"])}</p>
      <h2 class="t-h2">{c["how_h2"]}</h2>
    </div>
    <div class="race-tiles" data-reveal-stagger>
{chr(10).join(tiles)}
    </div>
  </div>
</section>
'''
    body = week_html(slug, lang)
    if slug in ARTICULO:
        href, label = ARTICULO[slug][lang]
        body += f'\n    <p class="wk-link"><a class="link" href="{href}">{esc(label)}</a></p>'
    wk = f'''<section id="semana" class="sec">
  <div class="max-w-page pad-x">
    <div class="sec-head sec-head--center" data-reveal>
      <p class="eyebrow">{esc(c["week_eyebrow"])}</p>
      <h2 class="t-h2">{c["week_h2"]}</h2>
      <p class="t-lead">{esc(c.get("week_lead", k["week_note"]))}</p>
    </div>
{body}
  </div>
</section>
'''
    qs = "\n".join(
        f'          <div class="faq-item">\n'
        f'            <button type="button" class="faq-q" aria-expanded="false" aria-controls="faq-a-{i}"><span>{esc(q)}</span>{ICO_PLUS}</button>\n'
        f'            <div id="faq-a-{i}" class="faq-a"><div class="faq-a-inner">{esc(a)}</div></div>\n'
        f'          </div>'
        for i, (q, a) in enumerate(faq_items(c, k), 1))
    faq = f'''<section id="faq" class="sec">
  <div class="max-w-page pad-x">
    <div class="faq-grid">
      <div class="faq-head" data-reveal>
        <p class="eyebrow">{esc(k["faq_eyebrow"])}</p>
        <h2 class="t-h2">{c["faq_h2"]}</h2>
      </div>
      <div>
        <div class="faq-list">
{qs}
        </div>
      </div>
    </div>
  </div>
</section>
'''
    return (f"<!-- PÁGINA POR OBJETIVO ({slug}) · contenido propio; el resto sale de la home -->\n{hero}\n"
            f"{bridge(c['bridge1'])}\n{fmt}\n{bridge(c['bridge2'])}\n{how}\n{wk}\n{faq}\n{bridge(k['bridge3'])}\n")


def jsonld(c, k, lang):
    home = BASE if lang == "es" else BASE + "en/"
    graph = [
        {"@type": "WebPage", "@id": c["url"] + "#webpage", "url": c["url"], "name": c["title"], "description": c["desc"],
         "inLanguage": lang, "isPartOf": {"@id": home + "#website"}, "about": {"@id": BASE + "#app"},
         "breadcrumb": {"@id": c["url"] + "#breadcrumb"}, "primaryImageOfPage": BASE + "og-image.png"},
        {"@type": "BreadcrumbList", "@id": c["url"] + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "2trAIn", "item": home},
            {"@type": "ListItem", "position": 2, "name": c["crumb"], "item": c["url"]}]},
        {"@type": "FAQPage", "@id": c["url"] + "#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq_items(c, k)]},
    ]
    return '<script type="application/ld+json">\n' + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1) + "\n</script>"


def shell(lang, title, desc, url, es_url, en_url, other, ld, body, legal=None, og_type=None):
    """Página completa con la home como plantilla: cabecera, menú, alta a la beta,
    pie, modal y cookies salen tal cual; en medio va `body`. También la usa el blog."""
    home_path = "/" if lang == "es" else "/en/"
    home_url = BASE if lang == "es" else BASE + "en/"
    tpl = (ROOT / ("index.html" if lang == "es" else "en/index.html")).read_text(encoding="utf-8")

    def rep(s, a, b, n=1):
        assert s.count(a) == n, (url, a[:70], s.count(a))
        return s.replace(a, b)

    s = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", tpl, count=1)
    s = re.sub(r'<meta name="description" content="[^"]*" />', f'<meta name="description" content="{esc(desc)}" />', s, count=1)
    s = rep(s, f'<link rel="canonical" href="{home_url}" />', f'<link rel="canonical" href="{url}" />')
    s = rep(s, '<link rel="alternate" hreflang="es" href="https://2trainapp.com/">', f'<link rel="alternate" hreflang="es" href="{es_url}">')
    s = rep(s, '<link rel="alternate" hreflang="en" href="https://2trainapp.com/en/">', f'<link rel="alternate" hreflang="en" href="{en_url}">')
    s = rep(s, '<link rel="alternate" hreflang="x-default" href="https://2trainapp.com/">', f'<link rel="alternate" hreflang="x-default" href="{es_url}">')
    s = rep(s, f'<meta property="og:url" content="{home_url}" />', f'<meta property="og:url" content="{url}" />')
    if og_type:
        s = re.sub(r'<meta property="og:type" content="[^"]*" />', f'<meta property="og:type" content="{og_type}" />', s, count=1)
    for attr, prop, val in (("property", "og:title", title), ("name", "twitter:title", title),
                            ("property", "og:description", desc), ("name", "twitter:description", desc)):
        s = re.sub(rf'<meta {attr}="{prop}" content="[^"]*" />', f'<meta {attr}="{prop}" content="{esc(val)}" />', s, count=1)
    s, n = re.subn(r'<script type="application/ld\+json">.*?</script>', lambda m: ld, s, count=1, flags=re.S)
    assert n == 1

    a = s.index('<section id="hero"')
    b = s.index('<section id="beta"')
    head, tail = s[:a], s[b:]
    head = re.sub(r'href="#(objetivos|como|faq|demo)"', rf'href="{home_path}#\1"', head)
    label = "inicio" if lang == "es" else "home"
    head = rep(head, f'<a href="#" aria-label="2trAIn, {label}">', f'<a href="{home_path}" aria-label="2trAIn, {label}">')
    switch = "/en/" if lang == "es" else "/"
    head = rep(head, f'href="{switch}" class="nav-lang"', f'href="{other}" class="nav-lang"')
    head = re.sub(rf'href="{re.escape(switch)}"( class="mobile-nav-link)', rf'href="{other}"\1', head)
    tail = re.sub(r'href="#(objetivos|como|faq|demo)"', rf'href="{home_path}#\1"', tail)
    if legal:
        fb = tail.index("<footer")
        tail = tail[:fb] + f'<p class="race-legal">{esc(legal)}</p>\n\n' + tail[fb:]
    return head + body + "\n" + tail


def build(slug, lang):
    c, k = PAGES[slug][lang], COMMON[lang]
    out = shell(lang, c["title"], c["desc"], c["url"], PAGES[slug]["es"]["url"], PAGES[slug]["en"]["url"],
                c["other"], jsonld(c, k, lang), sections(slug, c, k), c.get("legal"))
    dest = ROOT / c["path"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print("ok", c["path"])


if __name__ == "__main__":
    for slug in PAGES:
        for lang in ("es", "en"):
            build(slug, lang)
