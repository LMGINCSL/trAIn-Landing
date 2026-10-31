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
           "viz_bars": "Carga por semana, con su descarga", "week_note": "Orientativa: la tuya sale de tu historial y de tu fecha."},
    "en": {"placeholder": "you@email.com", "email_label": "Your email", "cta": "Join the beta",
           "meta": "No card · Access arrives by email", "faq_eyebrow": "FAQ",
           "bridge3": 'Got a date? <b>Start today.</b>', "start": "Start session",
           "tile_adjust": ("Adjusted every week", "What you train and what you tell it rewrite next week. Every change comes with its why."),
           "tile_peak": ("Periodised to race day", "Base, build and taper. The last week drops the volume so you reach the start line fresh."),
           "faq_taper": "It drops the volume and keeps some intensity so you arrive fresh. That's the taper.",
           "faq_price": ("How much does it cost?", "2trAIn is in open beta: sign up with your email and access arrives right away, no card needed."),
           "faq_watch": "No. Just your phone.",
           "viz_plan": {"now": "Today", "flag": "Your race", "phases": ["Base", "Build", "Taper"], "cap": "Periodised toward race day"},
           "viz_bars": "Weekly load, with its deload", "week_note": "Indicative: yours comes from your history and your date."},
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
            "phone": ("Semana 6 · Construcción", "Camino a HYROX", "Por qué esta semana",
                      "Te quedan 9 semanas. Subo la carrera en Zona 2, sumo estaciones y mantengo un día de fuerza para no perder lo ganado."),
            "phone_rows": [("ski-erg", "Tracción básica en ski erg", "1000 m · ritmo controlado"),
                           ("empuje-trineo", "Empuje de trineo", "6×20 m · carga media"),
                           ("paseo-granjero", "Paseo del granjero con mancuernas", "5×40 m · agarre fuerte"),
                           ("sentadilla-balon", "Sentadilla frontal con balón medicinal", "4×15 · 6/9 kg")],
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
            "week_eyebrow": "Una semana tipo", "week_h2": 'Así se ve <span class="accent">una semana.</span>',
            "cards": [("ski-erg", "Estación", "Tracción básica en ski erg", "1000 m · ritmo controlado"),
                      ("empuje-trineo", "Estación", "Empuje de trineo", "6×20 m · carga media"),
                      ("paseo-granjero", "Estación", "Paseo del granjero con mancuernas", "5×40 m · agarre fuerte"),
                      ("sentadilla-balon", "Fuerza", "Sentadilla frontal con balón medicinal", "4×15 · 6/9 kg"),
                      ("zancada-mancuernas", "Fuerza", "Zancada con mancuernas", "4×20 m · alternas"),
                      ("burpee", "Estación", "Burpee", "4×8 · estación")],
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
            "desc": "Prepare for HYROX with a plan built toward your date: running, stations and strength, adjusted every week with every change explained. Open beta.",
            "eyebrow": "AI HYROX training · Open beta",
            "h1": 'Your HYROX plan, <span class="accent">all the way to race day.</span>',
            "lead": "Tell it the date. 2trAIn spreads running, stations and useful strength up to that day, and rewrites every week from what you train, with every change explained.",
            "meta_link": "See the format",
            "phone": ("Week 6 · Build", "Road to HYROX", "Why this week",
                      "9 weeks to go. I'm adding Zone 2 running and stations, and keeping one strength day so you don't lose what you've built."),
            "phone_rows": [("ski-erg", "Ski erg basic pull", "1000 m · controlled pace"),
                           ("empuje-trineo", "Sled push", "6×20 m · moderate load"),
                           ("paseo-granjero", "Dumbbell farmer walk", "5×40 m · strong grip"),
                           ("sentadilla-balon", "Med ball front squat", "4×15 · 6/9 kg")],
            "bridge1": 'First, <b>what to expect.</b>',
            "fmt": {"eyebrow": "The format", "h2": '8 km of running. <span class="muted">8 stations in between.</span>',
                    "lead": "Every kilometre of running ends at a station. This is the order of the standard format:",
                    "items": [(str(i), n, "after 1 km of running", d) for i, (n, d) in enumerate(
                        [("SkiErg", "1,000 m"), ("Sled push", "50 m"), ("Sled pull", "50 m"),
                         ("Burpee broad jumps", "80 m"), ("Rowing", "1,000 m"), ("Farmers carry", "200 m"),
                         ("Sandbag lunges", "100 m"), ("Wall balls", "100 reps")], 1)],
                    "note": "Weights change by division (Open, Pro, Doubles or Relay). Always check the official rulebook for your event."},
            "bridge2": 'So you need <b>a plan with a date.</b>',
            "how_eyebrow": "How 2trAIn prepares it", "how_h2": 'A plan that builds <span class="accent">toward your date.</span>', "viz": "plan",
            "tiles": ["peak", ("Running, stations and strength", "Zone 2 for the base, stations with technique and load, and at least one strength day so you keep what you've built."),
                      "adjust", ("With your equipment", "No sled or SkiErg at your gym? It swaps them for alternatives with what you have and remembers it.")],
            "week_eyebrow": "A sample week", "week_h2": 'What <span class="accent">a week looks like.</span>',
            "cards": [("ski-erg", "Station", "Ski erg basic pull", "1000 m · controlled pace"),
                      ("empuje-trineo", "Station", "Sled push", "6×20 m · moderate load"),
                      ("paseo-granjero", "Station", "Dumbbell farmer walk", "5×40 m · strong grip"),
                      ("sentadilla-balon", "Strength", "Med ball front squat", "4×15 · 6/9 kg"),
                      ("zancada-mancuernas", "Strength", "Dumbbell alternating lunge", "4×20 m · alternating"),
                      ("burpee", "Station", "Burpee", "4×8 · station")],
            "faq_h2": 'HYROX prep, <span class="muted">answered.</span>',
            "faq": [("How early should I start preparing for a HYROX?", "The earlier, the more gradual. Tell it the date and the plan spreads the weeks you have across base, build and taper. If time is short, it adapts to those weeks."),
                    ("Do I need a sled, SkiErg or rower at my gym?", "No. If something is missing, it swaps it for alternatives with the equipment you have and remembers it for the following weeks."),
                    ("Does it work for my first HYROX?", "Yes. The plan starts from what you already do and raises the load gradually. If you come from strength, it builds your running; if you come from running, the stations."),
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
            "phone": ("Semana 5 · Base", "Camino al triatlón", "Por qué esta semana",
                      "Vienes de correr: subo la bici en Zona 2, sumo técnica de natación y dejo un día de fuerza."),
            "phone_rows": [("LUN", "Natación · técnica", "40 min · Zona 2"), ("MAR", "Bici · base", "75 min · Zona 2"),
                           ("JUE", "Carrera · ritmos", "45 min · 4×5 min"), ("SÁB", "Bici y carrera", "90 + 20 min")],
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
            "tiles": ["peak", ("Natación, bici y carrera", "Las tres repartidas según dónde estás más flojo, con un día de fuerza para sostenerlo todo."),
                      "adjust", ("Encaja en tu semana", "Le dices cuántos días entrenas y el plan reparte las sesiones en esos días.")],
            "week_eyebrow": "Una semana tipo", "week_h2": 'Así se ve <span class="accent">una semana.</span>',
            "days": [("LUN", "Natación técnica", "Técnica y Zona 2", "40 min"), ("MAR", "Fuerza", "Pierna y core", "45 min"),
                     ("MIÉ", "Bici", "Base en Zona 2", "75 min"), ("JUE", "Carrera", "Series cortas", "45 min"),
                     ("SÁB", "Bici y carrera", "Una detrás de otra", "90 + 20 min"), ("DOM", "Descanso", "O movilidad suave", "—")],
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
            "desc": "Prepare for your triathlon with a plan built toward your date: swim, bike, run and strength, adjusted every week with every change explained. Open beta.",
            "eyebrow": "AI triathlon training · Open beta",
            "h1": 'Your triathlon plan, <span class="accent">all the way to the finish line.</span>',
            "lead": "Tell it the race and the date. 2trAIn spreads swim, bike, run and strength across the days you train, and rewrites every week from what you do, with every change explained.",
            "meta_link": "See the distances",
            "phone": ("Week 5 · Base", "Road to your triathlon", "Why this week",
                      "You come from running: I'm adding Zone 2 cycling and swim technique, and keeping one strength day."),
            "phone_rows": [("MON", "Swim · technique", "40 min · Zone 2"), ("TUE", "Bike · base", "75 min · Zone 2"),
                           ("THU", "Run · pace", "45 min · 4×5 min"), ("SAT", "Bike and run", "90 + 20 min")],
            "bridge1": 'First, <b>your distance.</b>',
            "fmt": {"eyebrow": "The distances", "h2": 'Swim, bike, run. <span class="muted">In that order.</span>',
                    "lead": "The most common distances:",
                    "items": [("1", "Sprint", "750 m swim · 20 km bike · 5 km run", ""),
                              ("2", "Olympic", "1.5 km swim · 40 km bike · 10 km run", ""),
                              ("3", "Middle distance", "1.9 km swim · 90 km bike · 21.1 km run", ""),
                              ("4", "Long distance", "3.8 km swim · 180 km bike · 42.2 km run", "")],
                    "note": "Distances can vary by organiser. Always check your race's rulebook."},
            "bridge2": 'So you need <b>a plan with a date.</b>',
            "how_eyebrow": "How 2trAIn prepares it", "how_h2": 'Three disciplines, <span class="accent">one plan.</span>', "viz": "plan",
            "tiles": ["peak", ("Swim, bike and run", "All three spread according to where you're weakest, with one strength day to hold it all together."),
                      "adjust", ("Fits your week", "Tell it how many days you train and the plan spreads the sessions across those days.")],
            "week_eyebrow": "A sample week", "week_h2": 'What <span class="accent">a week looks like.</span>',
            "days": [("MON", "Swim technique", "Technique and Zone 2", "40 min"), ("TUE", "Strength", "Legs and core", "45 min"),
                     ("WED", "Bike", "Zone 2 base", "75 min"), ("THU", "Run", "Short intervals", "45 min"),
                     ("SAT", "Bike and run", "Back to back", "90 + 20 min"), ("SUN", "Rest", "Or easy mobility", "—")],
            "faq_h2": 'Triathlon prep, <span class="muted">answered.</span>',
            "faq": [("Does it work for my first triathlon?", "Yes. The plan starts from what you already do. If you come from running, it builds your swim and bike; if you come from swimming, your run."),
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
            "phone": ("Semana 4 · Construcción", "Camino a tu 10K", "Por qué esta semana",
                      "Respondes bien a las series: subo un poco el ritmo del jueves y mantengo la tirada larga del domingo."),
            "phone_rows": [("LUN", "Rodaje suave", "35 min · Zona 2"), ("MIÉ", "Fuerza", "40 min · pierna y core"),
                           ("JUE", "Series", "6×800 m · ritmo 10K"), ("DOM", "Tirada larga", "60 min · suave")],
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
            "week_eyebrow": "Una semana tipo", "week_h2": 'Así se ve <span class="accent">una semana.</span>',
            "days": [("LUN", "Rodaje suave", "Zona 2", "35 min"), ("MAR", "Fuerza", "Pierna y core", "40 min"),
                     ("JUE", "Series", "6×800 m a ritmo 10K", "45 min"), ("VIE", "Descanso", "O movilidad suave", "—"),
                     ("SÁB", "Rodaje con cambios", "Suave con 6 aceleraciones", "35 min"), ("DOM", "Tirada larga", "Suave", "60 min")],
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
            "desc": "Prepare for your 10K with a plan built toward your date: easy runs, intervals and strength, adjusted every week to your pace with every change explained. Open beta.",
            "eyebrow": "AI 10K training · Open beta",
            "h1": 'Your 10K, <span class="accent">at your pace, with a date.</span>',
            "lead": "Tell it the date. 2trAIn spreads easy runs, intervals and strength up to that day, learns how fast you respond and rewrites every week, with every change explained.",
            "meta_link": "Who it's for",
            "phone": ("Week 4 · Build", "Road to your 10K", "Why this week",
                      "You're responding well to intervals: I'm nudging Thursday's pace up and keeping Sunday's long run."),
            "phone_rows": [("MON", "Easy run", "35 min · Zone 2"), ("WED", "Strength", "40 min · legs and core"),
                           ("THU", "Intervals", "6×800 m · 10K pace"), ("SUN", "Long run", "60 min · easy")],
            "bridge1": 'First, <b>where you start.</b>',
            "fmt": {"eyebrow": "Who it's for", "h2": 'First 10K or a new PB. <span class="muted">The plan changes.</span>',
                    "lead": "Where you start and what you're after decide how it's built:",
                    "items": [("1", "Your first 10K", "Reach the finish running, with volume rising gradually", ""),
                              ("2", "A new PB", "More quality: intervals and paces close to your goal", ""),
                              ("3", "Getting back to running", "Return without overdoing it, with the load under control", ""),
                              ("4", "Running and strength", "No need to choose: both in the same plan", "")],
                    "note": ""},
            "bridge2": 'So you need <b>a plan with a date.</b>',
            "how_eyebrow": "How 2trAIn prepares it", "how_h2": 'A plan that learns <span class="accent">your pace.</span>', "viz": "plan",
            "tiles": ["peak", ("Learns your pace", "It measures how you respond each week and adjusts the progression to you, not the average."),
                      "adjust", ("Strength in the same plan", "One strength day that fits around your running, without you building it separately.")],
            "week_eyebrow": "A sample week", "week_h2": 'What <span class="accent">a week looks like.</span>',
            "days": [("MON", "Easy run", "Zone 2", "35 min"), ("TUE", "Strength", "Legs and core", "40 min"),
                     ("THU", "Intervals", "6×800 m at 10K pace", "45 min"), ("FRI", "Rest", "Or easy mobility", "—"),
                     ("SAT", "Run with strides", "Easy with 6 strides", "35 min"), ("SUN", "Long run", "Easy", "60 min")],
            "faq_h2": '10K prep, <span class="muted">answered.</span>',
            "faq": [("How early should I start preparing for a 10K?", "The earlier, the more gradual. Tell it the date and the plan spreads the weeks you have across base, build and taper. If time is short, it adapts to those weeks."),
                    ("Does it work if I've never run 10 km?", "Yes. The plan starts from what you already do and raises the volume gradually up to the distance."),
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
            "phone": ("Semana 10 · Construcción", "Camino al maratón", "Por qué esta semana",
                      "Me dijiste que el domingo te pesaron las piernas: bajo el volumen del martes y mantengo los ritmos del jueves."),
            "phone_rows": [("MAR", "Rodaje", "50 min · Zona 2"), ("JUE", "Ritmos", "3×3 km · ritmo maratón"),
                           ("VIE", "Fuerza", "40 min · pierna y core"), ("DOM", "Tirada larga", "26 km · suave")],
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
            "week_eyebrow": "Una semana tipo", "week_h2": 'Así se ve <span class="accent">una semana.</span>',
            "days": [("MAR", "Rodaje", "Zona 2", "50 min"), ("MIÉ", "Fuerza", "Pierna y core", "40 min"),
                     ("JUE", "Ritmos", "3×3 km a ritmo maratón", "60 min"), ("VIE", "Descanso", "O movilidad suave", "—"),
                     ("SÁB", "Rodaje suave", "Para soltar", "30 min"), ("DOM", "Tirada larga", "Suave", "26 km")],
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
            "desc": "Prepare for your marathon or half marathon with a plan built toward your date: long runs, paces and strength, adjusted every week to how you respond. Open beta.",
            "eyebrow": "AI marathon and half training · Open beta",
            "h1": 'Your marathon, <span class="accent">one kilometre at a time.</span>',
            "lead": "Tell it the race and the date. 2trAIn builds the long runs, paces and strength up to that day, and rewrites every week from how you respond, with every change explained.",
            "meta_link": "See the distances",
            "phone": ("Week 10 · Build", "Road to the marathon", "Why this week",
                      "You told me your legs felt heavy on Sunday: I'm cutting Tuesday's volume and keeping Thursday's paces."),
            "phone_rows": [("TUE", "Run", "50 min · Zone 2"), ("THU", "Paces", "3×3 km · marathon pace"),
                           ("FRI", "Strength", "40 min · legs and core"), ("SUN", "Long run", "26 km · easy")],
            "bridge1": 'First, <b>your distance.</b>',
            "fmt": {"eyebrow": "The distances", "h2": 'Half or full. <span class="muted">Each with its own plan.</span>',
                    "lead": "Tell it which one and when:",
                    "items": [("1", "Half marathon", "Half the distance, half the long runs", "21.1 km"),
                              ("2", "Marathon", "More volume and long runs that build sensibly", "42.2 km")],
                    "note": ""},
            "bridge2": 'So you need <b>a plan with a date.</b>',
            "how_eyebrow": "How 2trAIn prepares it", "how_h2": 'Volume that builds <span class="accent">sensibly.</span>', "viz": "bars",
            "tiles": [("Long runs with deloads", "Volume rises gradually, with deload weeks, depending on how you absorb it."),
                      "peak", "adjust", ("Strength in the same plan", "One strength day that fits around your running, without you building it separately.")],
            "week_eyebrow": "A sample week", "week_h2": 'What <span class="accent">a week looks like.</span>',
            "days": [("TUE", "Run", "Zone 2", "50 min"), ("WED", "Strength", "Legs and core", "40 min"),
                     ("THU", "Paces", "3×3 km at marathon pace", "60 min"), ("FRI", "Rest", "Or easy mobility", "—"),
                     ("SAT", "Easy run", "To loosen up", "30 min"), ("SUN", "Long run", "Easy", "26 km")],
            "faq_h2": 'Marathon prep, <span class="muted">answered.</span>',
            "faq": [("Does it work for my first marathon?", "Yes. The plan starts from what you already do and raises the volume gradually, with deload weeks."),
                    ("Does it prepare the half marathon too?", "Yes. Tell it whether it's a half or a full and the date, and the plan builds toward that day."),
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
            "phone": ("Semana 3 · Pierna", "Más carga, mismo volumen", "Por qué esta semana",
                      "Tus últimas sentadillas salieron con margen: subo 2,5 kg y mantengo las series."),
            "phone_rows": [("sentadilla-barra-th", "Sentadilla completa con barra", "4×6 · +2,5 kg"),
                           ("peso-muerto-th", "Peso muerto con barra", "3×5 · técnica limpia"),
                           ("hip-thrust-th", "Hip thrust con barra", "3×10 · controlado"),
                           ("sentadilla-goblet-th", "Sentadilla goblet con kettlebell", "3×12 · accesorio")],
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
            "week_eyebrow": "Una semana tipo", "week_h2": 'Así se ve <span class="accent">una semana.</span>',
            "cards": [("sentadilla-barra", "Pierna", "Sentadilla completa con barra", "4×6 · pesada"),
                      ("press-inclinado-mancuernas", "Empuje", "Press inclinado con mancuernas", "3×10 · agarre neutro"),
                      ("dominada", "Tirón", "Dominada con agarre ancho", "4×8 · tirón"),
                      ("peso-muerto", "Pierna", "Peso muerto con barra", "3×5 · técnica limpia"),
                      ("press-pecho-maquina", "Empuje", "Press de pecho en máquina", "4×10 · agarre neutro"),
                      ("remo-barra", "Tirón", "Remo inclinado con barra", "4×8 · controlado")],
            "week_note": "Orientativa: la tuya sale de tu historial, tu objetivo y tu material.",
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
            "h1": 'Stronger every week, <span class="accent">no guessing the loads.</span>',
            "lead": "Tell it your goal and your equipment. 2trAIn builds push, pull and leg blocks, raises the load when it's time and explains every change with your data.",
            "meta_link": "Pick your goal",
            "phone": ("Week 3 · Legs", "More load, same volume", "Why this week",
                      "Your last squats had reps in reserve: I'm adding 2.5 kg and keeping the sets."),
            "phone_rows": [("sentadilla-barra-th", "Barbell full squat", "4×6 · +2.5 kg"),
                           ("peso-muerto-th", "Barbell deadlift", "3×5 · clean technique"),
                           ("hip-thrust-th", "Barbell hip thrust", "3×10 · controlled"),
                           ("sentadilla-goblet-th", "Kettlebell goblet squat", "3×12 · accessory")],
            "bridge1": 'First, <b>your goal.</b>',
            "fmt": {"eyebrow": "Your goal", "h2": 'Muscle or strength. <span class="muted">With what you have.</span>',
                    "lead": "What you're after and your equipment decide how it's built:",
                    "items": [("1", "Hypertrophy", "More muscle: volume and reps to grow", ""),
                              ("2", "Strength", "More load on the basics: squat, deadlift and press", ""),
                              ("3", "At home or in the gym", "With the equipment you have, no exercises you can't do", ""),
                              ("4", "With injuries or niggles", "Tell it once and it adapts the exercises", "")],
                    "note": ""},
            "bridge2": 'So you need <b>a plan that progresses.</b>',
            "how_eyebrow": "How 2trAIn builds it", "how_h2": 'Load progression, <span class="accent">explained.</span>', "viz": "bars",
            "tiles": [("Progression with deloads", "It adds weight or reps when the sessions say so, and schedules deloads when they're due."),
                      ("Every change, explained", "If something goes up, down or changes, it tells you why with your own data."),
                      ("1,600+ exercises", "Each with video and a technique card, and instant swaps if you're missing equipment."),
                      ("Remembers what's yours", "Injuries, equipment and vetoes: tell it once and it won't suggest them again.")],
            "week_eyebrow": "A sample week", "week_h2": 'What <span class="accent">a week looks like.</span>',
            "cards": [("sentadilla-barra", "Legs", "Barbell full squat", "4×6 · heavy"),
                      ("press-inclinado-mancuernas", "Push", "Incline dumbbell press", "3×10 · neutral grip"),
                      ("dominada", "Pull", "Wide-grip pull-up", "4×8 · pull"),
                      ("peso-muerto", "Legs", "Barbell deadlift", "3×5 · clean technique"),
                      ("press-pecho-maquina", "Push", "Machine chest press", "4×10 · neutral grip"),
                      ("remo-barra", "Pull", "Barbell bent-over row", "4×8 · controlled")],
            "week_note": "Indicative: yours comes from your history, your goal and your equipment.",
            "faq_h2": 'Strength training, <span class="muted">answered.</span>',
            "faq": [("Does it work for building muscle or just strength?", "Both. Pick hypertrophy or strength and the plan adjusts volume and reps to that goal."),
                    ("Can I train at home?", "Yes. Tell it what equipment you have and the plan is built with that, no exercises you can't do."),
                    ("How does it know when to add weight?", "From what you log: if your sets have reps in reserve, it goes up; if they're harder than they should be, it holds or drops. And it tells you why."),
                    ("What if I have an injury or a niggle?", "Tell it and it remembers: it removes what bothers you and finds alternatives that keep the stimulus."),
                    ("Do I need experience?", "No. The plan starts from what you already do and every exercise has its video and technique card."),
                    "price"],
        },
    },
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
    if "cards" in c:
        body = '    <div class="race-week" data-reveal-stagger>\n' + "\n".join(
            f'      <div class="demo-ex"><div class="demo-ex__media"><img src="/assets/ej/{s}.jpg" alt="{esc(n)}" width="640" height="360" loading="lazy" decoding="async"></div>'
            f'<div class="demo-ex__body"><span class="demo-ex__tag">{esc(tag)}</span><div class="demo-ex__name">{esc(n)}</div><div class="demo-ex__meta">{esc(m)}</div></div></div>'
            for s, tag, n, m in c["cards"]) + "\n    </div>"
    else:
        body = '    <ol class="race-format race-format--days" data-reveal-stagger>\n' + "\n".join(
            f'      <li><span class="race-format__n">{esc(d)}</span><span><b>{esc(t)}</b><small>{esc(sub)}</small></span><span class="race-format__d">{esc(dur)}</span></li>'
            for d, t, sub, dur in c["days"]) + "\n    </ol>"
    wk = f'''<section id="semana" class="sec">
  <div class="max-w-page pad-x">
    <div class="sec-head sec-head--center" data-reveal>
      <p class="eyebrow">{esc(c["week_eyebrow"])}</p>
      <h2 class="t-h2">{c["week_h2"]}</h2>
      <p class="t-lead">{esc(c.get("week_note", k["week_note"]))}</p>
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


def build(slug, lang):
    c, k = PAGES[slug][lang], COMMON[lang]
    other_lang = "en" if lang == "es" else "es"
    es_url, en_url = PAGES[slug]["es"]["url"], PAGES[slug]["en"]["url"]
    home_path = "/" if lang == "es" else "/en/"
    home_url = BASE if lang == "es" else BASE + "en/"
    tpl = (ROOT / ("index.html" if lang == "es" else "en/index.html")).read_text(encoding="utf-8")

    def rep(s, a, b, n=1):
        assert s.count(a) == n, (slug, lang, a[:70], s.count(a))
        return s.replace(a, b)

    s = re.sub(r"<title>.*?</title>", f"<title>{esc(c['title'])}</title>", tpl, count=1)
    s = re.sub(r'<meta name="description" content="[^"]*" />', f'<meta name="description" content="{esc(c["desc"])}" />', s, count=1)
    s = rep(s, f'<link rel="canonical" href="{home_url}" />', f'<link rel="canonical" href="{c["url"]}" />')
    s = rep(s, '<link rel="alternate" hreflang="es" href="https://2trainapp.com/">', f'<link rel="alternate" hreflang="es" href="{es_url}">')
    s = rep(s, '<link rel="alternate" hreflang="en" href="https://2trainapp.com/en/">', f'<link rel="alternate" hreflang="en" href="{en_url}">')
    s = rep(s, '<link rel="alternate" hreflang="x-default" href="https://2trainapp.com/">', f'<link rel="alternate" hreflang="x-default" href="{es_url}">')
    s = rep(s, f'<meta property="og:url" content="{home_url}" />', f'<meta property="og:url" content="{c["url"]}" />')
    for attr, prop, val in (("property", "og:title", c["title"]), ("name", "twitter:title", c["title"]),
                            ("property", "og:description", c["desc"]), ("name", "twitter:description", c["desc"])):
        s = re.sub(rf'<meta {attr}="{prop}" content="[^"]*" />', f'<meta {attr}="{prop}" content="{esc(val)}" />', s, count=1)
    s, n = re.subn(r'<script type="application/ld\+json">.*?</script>', lambda m: jsonld(c, k, lang), s, count=1, flags=re.S)
    assert n == 1

    a = s.index('<section id="hero"')
    b = s.index('<section id="beta"')
    head, tail = s[:a], s[b:]
    head = re.sub(r'href="#(objetivos|como|faq|demo)"', rf'href="{home_path}#\1"', head)
    label = "inicio" if lang == "es" else "home"
    head = rep(head, f'<a href="#" aria-label="2trAIn, {label}">', f'<a href="{home_path}" aria-label="2trAIn, {label}">')
    switch = "/en/" if lang == "es" else "/"
    head = rep(head, f'href="{switch}" class="nav-lang"', f'href="{c["other"]}" class="nav-lang"')
    head = re.sub(rf'href="{re.escape(switch)}"( class="mobile-nav-link)', rf'href="{c["other"]}"\1', head)
    tail = re.sub(r'href="#(objetivos|como|faq|demo)"', rf'href="{home_path}#\1"', tail)
    if c.get("legal"):
        fb = tail.index("<footer")
        tail = tail[:fb] + f'<p class="race-legal">{esc(c["legal"])}</p>\n\n' + tail[fb:]
    out = head + sections(slug, c, k) + "\n" + tail
    dest = ROOT / c["path"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print("ok", c["path"])


for slug in PAGES:
    for lang in ("es", "en"):
        build(slug, lang)
