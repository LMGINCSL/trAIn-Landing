"""Genera las páginas por prueba (/hyrox y /en/hyrox/) con la home como plantilla.

Cabecera, menú, alta a la beta, pie, modal y aviso de cookies salen tal cual de
index.html y en/index.html, así que el formulario y app.js funcionan igual. En
medio va el contenido de la prueba, y el FAQ visible y el de los datos
estructurados salen de la misma lista.

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

HYROX = {
    "es": {
        "path": "hyrox/index.html", "url": BASE + "hyrox", "home": "/", "other": "/en/hyrox/",
        "title": "Plan de entrenamiento HYROX con IA · 2trAIn",
        "desc": "Prepara tu HYROX con un plan que va hacia tu fecha: carrera, estaciones y fuerza, ajustado cada semana y con cada cambio explicado. Beta abierta.",
        "crumb": "Preparar HYROX",
        "eyebrow": "Preparación HYROX con IA · Beta abierta",
        "h1": 'Tu plan para HYROX, <span class="accent">hasta el día de la carrera.</span>',
        "lead": "Le dices la fecha. 2trAIn reparte carrera, estaciones y fuerza útil hasta ese día, y reescribe cada semana con lo que entrenas, con cada cambio explicado.",
        "placeholder": "tu@email.com", "email_label": "Tu correo electrónico", "cta": "Unirme a la beta",
        "meta": "Sin tarjeta · El acceso te llega por email", "meta_link": "Ver el formato",
        "phone": {"kicker": "Semana 6 · Construcción", "title": "Camino a HYROX", "why_t": "Por qué esta semana",
                  "why": "Te quedan 9 semanas. Subo la carrera en Zona 2, sumo estaciones y mantengo un día de fuerza para no perder lo ganado.",
                  "start": "Empezar sesión"},
        "phone_rows": [("ski-erg", "Tracción básica en ski erg", "1000 m · ritmo controlado"),
                       ("empuje-trineo", "Empuje de trineo", "6×20 m · carga media"),
                       ("paseo-granjero", "Paseo del granjero con mancuernas", "5×40 m · agarre fuerte"),
                       ("sentadilla-balon", "Sentadilla frontal con balón medicinal", "4×15 · 6/9 kg")],
        "bridge1": 'Primero, <b>qué te espera.</b>',
        "fmt_eyebrow": "El formato", "fmt_h2": '8 km de carrera. <span class="muted">8 estaciones entre medias.</span>',
        "fmt_lead": "Cada kilómetro de carrera termina en una estación. Este es el orden del formato estándar:",
        "fmt_after": "tras 1 km de carrera",
        "stations": [("SkiErg", "1.000 m"), ("Empuje de trineo", "50 m"), ("Arrastre de trineo", "50 m"),
                     ("Burpees con salto largo", "80 m"), ("Remo", "1.000 m"), ("Paseo del granjero", "200 m"),
                     ("Zancadas con saco", "100 m"), ("Wall balls", "100 rep.")],
        "fmt_note": "Los pesos cambian según la categoría (Open, Pro, Dobles o Relevos). Revisa siempre el reglamento oficial de tu edición.",
        "bridge2": 'Y para eso, <b>un plan con fecha.</b>',
        "how_eyebrow": "Cómo lo prepara 2trAIn", "how_h2": 'Un plan que va <span class="accent">hacia tu fecha.</span>',
        "tiles": [("Periodizado hasta el día D", "Base, construcción y afinado. La última semana baja el volumen para que llegues fresco a la salida."),
                  ("Carrera, estaciones y fuerza", "Zona 2 para la base, estaciones con técnica y carga, y al menos un día de fuerza para no perder lo ganado."),
                  ("Se ajusta cada semana", "Lo que entrenas y lo que le cuentas reescriben la semana siguiente. Cada cambio llega con su porqué."),
                  ("Con tu material", "¿Tu gimnasio no tiene trineo ni SkiErg? Lo cambia por alternativas con lo que tengas y lo recuerda.")],
        "viz": {"now": "Hoy", "flag": "Tu carrera", "phases": ["Base", "Construcción", "Afinado"], "cap": "Periodizado hacia el día de la carrera"},
        "week_eyebrow": "Una semana tipo", "week_h2": 'Así se ve <span class="accent">una semana.</span>',
        "week_note": "Orientativa: la tuya sale de tu historial y de tu fecha.",
        "week": [("ski-erg", "Estación", "Tracción básica en ski erg", "1000 m · ritmo controlado"),
                 ("empuje-trineo", "Estación", "Empuje de trineo", "6×20 m · carga media"),
                 ("paseo-granjero", "Estación", "Paseo del granjero con mancuernas", "5×40 m · agarre fuerte"),
                 ("sentadilla-balon", "Fuerza", "Sentadilla frontal con balón medicinal", "4×15 · 6/9 kg"),
                 ("zancada-mancuernas", "Fuerza", "Zancada con mancuernas", "4×20 m · alternas"),
                 ("burpee", "Estación", "Burpee", "4×8 · estación")],
        "faq_eyebrow": "Preguntas frecuentes", "faq_h2": 'Preparar HYROX, <span class="muted">sin dudas.</span>',
        "faq": [("¿Con cuánto tiempo tengo que empezar a preparar un HYROX?",
                 "Cuanto antes, más progresivo. Le dices la fecha y el plan reparte las semanas que haya entre base, construcción y afinado. Si hay poco margen, se adapta a esas semanas."),
                ("¿Necesito trineo, SkiErg o remo en mi gimnasio?",
                 "No. Si te falta algo, lo cambia por alternativas con el material que tengas y lo recuerda para las semanas siguientes."),
                ("¿Sirve si es mi primer HYROX?",
                 "Sí. El plan parte de lo que ya haces y sube la carga poco a poco. Si vienes de fuerza, refuerza la carrera; si vienes de correr, las estaciones."),
                ("¿Puedo seguir haciendo fuerza mientras lo preparo?",
                 "Sí. Mantiene al menos un día de fuerza para que no pierdas lo ganado mientras sube la carrera."),
                ("¿Qué pasa la semana de la carrera?",
                 "Baja el volumen y mantiene algo de intensidad para que llegues fresco. Es el afinado."),
                ("¿Cuánto cuesta?",
                 "2trAIn está en beta abierta: te apuntas con tu email y el acceso te llega al momento, sin tarjeta."),
                ("¿2trAIn es la app oficial de HYROX?",
                 "No. 2trAIn es una app independiente de entrenamiento con IA. HYROX es una marca registrada de su titular.")],
        "bridge3": '¿Tienes fecha? <b>Empieza hoy.</b>',
        "legal": "HYROX es una marca registrada de su titular. 2trAIn no está afiliada a HYROX ni cuenta con su patrocinio.",
    },
    "en": {
        "path": "en/hyrox/index.html", "url": BASE + "en/hyrox/", "home": "/en/", "other": "/hyrox",
        "title": "HYROX training plan with AI · 2trAIn",
        "desc": "Prepare for HYROX with a plan built toward your date: running, stations and strength, adjusted every week with every change explained. Open beta.",
        "crumb": "HYROX training",
        "eyebrow": "AI HYROX training · Open beta",
        "h1": 'Your HYROX plan, <span class="accent">all the way to race day.</span>',
        "lead": "Tell it the date. 2trAIn spreads running, stations and useful strength up to that day, and rewrites every week from what you train, with every change explained.",
        "placeholder": "you@email.com", "email_label": "Your email", "cta": "Join the beta",
        "meta": "No card · Access arrives by email", "meta_link": "See the format",
        "phone": {"kicker": "Week 6 · Build", "title": "Road to HYROX", "why_t": "Why this week",
                  "why": "9 weeks to go. I'm adding Zone 2 running and stations, and keeping one strength day so you don't lose what you've built.",
                  "start": "Start session"},
        "phone_rows": [("ski-erg", "Ski erg basic pull", "1000 m · controlled pace"),
                       ("empuje-trineo", "Sled push", "6×20 m · moderate load"),
                       ("paseo-granjero", "Dumbbell farmer walk", "5×40 m · strong grip"),
                       ("sentadilla-balon", "Med ball front squat", "4×15 · 6/9 kg")],
        "bridge1": 'First, <b>what to expect.</b>',
        "fmt_eyebrow": "The format", "fmt_h2": '8 km of running. <span class="muted">8 stations in between.</span>',
        "fmt_lead": "Every kilometre of running ends at a station. This is the order of the standard format:",
        "fmt_after": "after 1 km of running",
        "stations": [("SkiErg", "1,000 m"), ("Sled push", "50 m"), ("Sled pull", "50 m"),
                     ("Burpee broad jumps", "80 m"), ("Rowing", "1,000 m"), ("Farmers carry", "200 m"),
                     ("Sandbag lunges", "100 m"), ("Wall balls", "100 reps")],
        "fmt_note": "Weights change by division (Open, Pro, Doubles or Relay). Always check the official rulebook for your event.",
        "bridge2": 'So you need <b>a plan with a date.</b>',
        "how_eyebrow": "How 2trAIn prepares it", "how_h2": 'A plan that builds <span class="accent">toward your date.</span>',
        "tiles": [("Periodised to race day", "Base, build and taper. The last week drops the volume so you reach the start line fresh."),
                  ("Running, stations and strength", "Zone 2 for the base, stations with technique and load, and at least one strength day so you keep what you've built."),
                  ("Adjusted every week", "What you train and what you tell it rewrite next week. Every change comes with its why."),
                  ("With your equipment", "No sled or SkiErg at your gym? It swaps them for alternatives with what you have and remembers it.")],
        "viz": {"now": "Today", "flag": "Your race", "phases": ["Base", "Build", "Taper"], "cap": "Periodised toward race day"},
        "week_eyebrow": "A sample week", "week_h2": 'What <span class="accent">a week looks like.</span>',
        "week_note": "Indicative: yours comes from your history and your date.",
        "week": [("ski-erg", "Station", "Ski erg basic pull", "1000 m · controlled pace"),
                 ("empuje-trineo", "Station", "Sled push", "6×20 m · moderate load"),
                 ("paseo-granjero", "Station", "Dumbbell farmer walk", "5×40 m · strong grip"),
                 ("sentadilla-balon", "Strength", "Med ball front squat", "4×15 · 6/9 kg"),
                 ("zancada-mancuernas", "Strength", "Dumbbell alternating lunge", "4×20 m · alternating"),
                 ("burpee", "Station", "Burpee", "4×8 · station")],
        "faq_eyebrow": "FAQ", "faq_h2": 'HYROX prep, <span class="muted">answered.</span>',
        "faq": [("How early should I start preparing for a HYROX?",
                 "The earlier, the more gradual. Tell it the date and the plan spreads the weeks you have across base, build and taper. If time is short, it adapts to those weeks."),
                ("Do I need a sled, SkiErg or rower at my gym?",
                 "No. If something is missing, it swaps it for alternatives with the equipment you have and remembers it for the following weeks."),
                ("Does it work for my first HYROX?",
                 "Yes. The plan starts from what you already do and raises the load gradually. If you come from strength, it builds your running; if you come from running, the stations."),
                ("Can I keep doing strength while I prepare?",
                 "Yes. It keeps at least one strength day so you don't lose what you've built while the running goes up."),
                ("What happens in race week?",
                 "It drops the volume and keeps some intensity so you arrive fresh. That's the taper."),
                ("How much does it cost?",
                 "2trAIn is in open beta: sign up with your email and access arrives right away, no card needed."),
                ("Is 2trAIn the official HYROX app?",
                 "No. 2trAIn is an independent AI training app. HYROX is a registered trademark of its owner.")],
        "bridge3": 'Got a date? <b>Start today.</b>',
        "legal": "HYROX is a registered trademark of its owner. 2trAIn is not affiliated with or sponsored by HYROX.",
    },
}


def esc(t):
    return html.escape(t, quote=True)


def bridge(t):
    return ('<!-- Hilo -->\n<div class="bridge" aria-hidden="false">\n'
            '  <span class="bridge__line"></span><span class="bridge__dot"></span>\n'
            f'  <p class="bridge__t">{t}</p>\n</div>\n')


def sections(c):
    p = c["phone"]
    rows = "\n".join(
        f'              <div class="app-ex"><img src="/assets/ej/{s}.jpg" alt="" width="640" height="360" decoding="async"><div><b>{esc(n)}</b><span>{esc(m)}</span></div></div>'
        for s, n, m in c["phone_rows"])
    hero = f'''<section id="hero" class="hero">
  <div class="max-w-page pad-x hero__grid">
    <div class="hero__copy">
      <p class="eyebrow"><span class="live-dot" aria-hidden="true"></span>{esc(c["eyebrow"])}</p>
      <h1 class="t-hero hero__title">{c["h1"]}</h1>
      <p class="hero__sub">{esc(c["lead"])}</p>
      <div class="hero__cta">
        <form id="hero-form" class="hero-form">
          <input id="hero-email" type="email" name="email" required placeholder="{esc(c["placeholder"])}" aria-label="{esc(c["email_label"])}" autocomplete="email" />
          <button type="submit" class="btn" aria-label="{esc(c["cta"])}">
            <span class="btn-label">{esc(c["cta"])}</span>
            {ARROW}
          </button>
        </form>
        <div class="hero__meta">
          <span>{esc(c["meta"])}</span>
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
                <div class="app-ui__kicker">{esc(p["kicker"])}</div>
                <div class="app-ui__title">{esc(p["title"])}</div>
              </div>
            </div>
            <div class="app-ui__why">
              <b>{esc(p["why_t"])}</b>
              <span>{esc(p["why"])}</span>
            </div>
            <div class="app-ui__list">
{rows}
            </div>
            <span class="app-ui__cta">{esc(p["start"])}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
'''
    stations = "\n".join(
        f'      <li><span class="race-format__n">{i}</span><span><b>{esc(n)}</b><small>{esc(c["fmt_after"])}</small></span><span class="race-format__d">{esc(d)}</span></li>'
        for i, (n, d) in enumerate(c["stations"], 1))
    fmt = f'''<section id="formato" class="sec">
  <div class="max-w-page pad-x">
    <div class="sec-head sec-head--center" data-reveal>
      <p class="eyebrow">{esc(c["fmt_eyebrow"])}</p>
      <h2 class="t-h2">{c["fmt_h2"]}</h2>
      <p class="t-lead">{esc(c["fmt_lead"])}</p>
    </div>
    <ol class="race-format" data-reveal-stagger>
{stations}
    </ol>
    <p class="race-note">{esc(c["fmt_note"])}</p>
  </div>
</section>
'''
    v = c["viz"]
    viz = (f'<span class="viz" aria-hidden="true"><span class="viz__plan"><span class="viz__now">{esc(v["now"])}</span>'
           '<span class="viz__track"><i style="--w:45%;--i:0"></i><i style="--w:35%;--i:1"></i><i style="--w:20%;--i:2"></i></span>'
           f'<span class="viz__phases"><b style="--w:45%">{esc(v["phases"][0])}</b><b style="--w:35%">{esc(v["phases"][1])}</b><b style="--w:20%">{esc(v["phases"][2])}</b></span>'
           f'<span class="viz__flag"><svg viewBox="0 0 24 24" fill="none"><path d="M5 21V4m0 0h11l-2 4 2 4H5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>{esc(v["flag"])}</span></span>'
           f'<span class="viz__cap">{esc(v["cap"])}</span></span>')
    tiles = []
    for i, (t, d) in enumerate(c["tiles"]):
        tiles.append(f'      <div class="race-tile"><h3>{esc(t)}</h3><p>{esc(d)}</p>{viz if i == 0 else ""}</div>')
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
    week = "\n".join(
        f'      <div class="demo-ex"><div class="demo-ex__media"><img src="/assets/ej/{s}.jpg" alt="{esc(n)}" width="640" height="360" loading="lazy" decoding="async"></div>'
        f'<div class="demo-ex__body"><span class="demo-ex__tag">{esc(tag)}</span><div class="demo-ex__name">{esc(n)}</div><div class="demo-ex__meta">{esc(m)}</div></div></div>'
        for s, tag, n, m in c["week"])
    wk = f'''<section id="semana" class="sec">
  <div class="max-w-page pad-x">
    <div class="sec-head sec-head--center" data-reveal>
      <p class="eyebrow">{esc(c["week_eyebrow"])}</p>
      <h2 class="t-h2">{c["week_h2"]}</h2>
      <p class="t-lead">{esc(c["week_note"])}</p>
    </div>
    <div class="race-week" data-reveal-stagger>
{week}
    </div>
  </div>
</section>
'''
    items = "\n".join(
        f'          <div class="faq-item">\n'
        f'            <button type="button" class="faq-q" aria-expanded="false" aria-controls="faq-a-{i}"><span>{esc(q)}</span>{ICO_PLUS}</button>\n'
        f'            <div id="faq-a-{i}" class="faq-a"><div class="faq-a-inner">{esc(a)}</div></div>\n'
        f'          </div>'
        for i, (q, a) in enumerate(c["faq"], 1))
    faq = f'''<section id="faq" class="sec">
  <div class="max-w-page pad-x">
    <div class="faq-grid">
      <div class="faq-head" data-reveal>
        <p class="eyebrow">{esc(c["faq_eyebrow"])}</p>
        <h2 class="t-h2">{c["faq_h2"]}</h2>
      </div>
      <div>
        <div class="faq-list">
{items}
        </div>
      </div>
    </div>
  </div>
</section>
'''
    return (f"<!-- PREPARAR HYROX · contenido propio; el resto sale de la home -->\n{hero}\n"
            f"{bridge(c['bridge1'])}\n{fmt}\n{bridge(c['bridge2'])}\n{how}\n{wk}\n{faq}\n{bridge(c['bridge3'])}\n")


def jsonld(c, lang):
    home = BASE if lang == "es" else BASE + "en/"
    graph = [
        {"@type": "WebPage", "@id": c["url"] + "#webpage", "url": c["url"], "name": c["title"], "description": c["desc"],
         "inLanguage": lang, "isPartOf": {"@id": home + "#website"}, "about": {"@id": BASE + "#app"},
         "breadcrumb": {"@id": c["url"] + "#breadcrumb"}, "primaryImageOfPage": BASE + "og-image.png"},
        {"@type": "BreadcrumbList", "@id": c["url"] + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "2trAIn", "item": home},
            {"@type": "ListItem", "position": 2, "name": c["crumb"], "item": c["url"]}]},
        {"@type": "FAQPage", "@id": c["url"] + "#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in c["faq"]]},
    ]
    return '<script type="application/ld+json">\n' + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1) + "\n</script>"


def build(lang, c):
    tpl = (ROOT / ("index.html" if lang == "es" else "en/index.html")).read_text(encoding="utf-8")
    home_url = BASE if lang == "es" else BASE + "en/"
    es_url, en_url = HYROX["es"]["url"], HYROX["en"]["url"]

    def rep(s, a, b, n=1):
        assert s.count(a) == n, (lang, a[:70], s.count(a))
        return s.replace(a, b)

    # Cabecera: título, descripción, canonical, hreflang, Open Graph y JSON-LD propios
    s = tpl
    s = re.sub(r"<title>.*?</title>", f"<title>{esc(c['title'])}</title>", s, count=1)
    s = re.sub(r'<meta name="description" content="[^"]*" />', f'<meta name="description" content="{esc(c["desc"])}" />', s, count=1)
    s = rep(s, f'<link rel="canonical" href="{home_url}" />', f'<link rel="canonical" href="{c["url"]}" />')
    s = rep(s, '<link rel="alternate" hreflang="es" href="https://2trainapp.com/">', f'<link rel="alternate" hreflang="es" href="{es_url}">')
    s = rep(s, '<link rel="alternate" hreflang="en" href="https://2trainapp.com/en/">', f'<link rel="alternate" hreflang="en" href="{en_url}">')
    s = rep(s, '<link rel="alternate" hreflang="x-default" href="https://2trainapp.com/">', f'<link rel="alternate" hreflang="x-default" href="{es_url}">')
    s = rep(s, f'<meta property="og:url" content="{home_url}" />', f'<meta property="og:url" content="{c["url"]}" />')
    for prop in ("og:title", "twitter:title"):
        attr = "property" if prop.startswith("og") else "name"
        s = re.sub(rf'<meta {attr}="{prop}" content="[^"]*" />', f'<meta {attr}="{prop}" content="{esc(c["title"])}" />', s, count=1)
    for prop in ("og:description", "twitter:description"):
        attr = "property" if prop.startswith("og") else "name"
        s = re.sub(rf'<meta {attr}="{prop}" content="[^"]*" />', f'<meta {attr}="{prop}" content="{esc(c["desc"])}" />', s, count=1)
    s, n = re.subn(r'<script type="application/ld\+json">.*?</script>', lambda m: jsonld(c, lang), s, count=1, flags=re.S)
    assert n == 1

    # Cuerpo: menú y pie de la home con los enlaces apuntando a la home; en medio, la prueba
    a = s.index('<section id="hero"')
    b = s.index('<section id="beta"')
    head, tail = s[:a], s[b:]
    head = re.sub(r'href="#(objetivos|como|faq|demo)"', rf'href="{c["home"]}#\1"', head)
    head = rep(head, '<a href="#" aria-label="2trAIn, inicio">' if lang == "es" else '<a href="#" aria-label="2trAIn, home">',
               f'<a href="{c["home"]}" aria-label="2trAIn, {"inicio" if lang == "es" else "home"}">')
    if lang == "es":
        head = rep(head, 'href="/en/" class="nav-lang"', f'href="{c["other"]}" class="nav-lang"')
        head = re.sub(r'href="/en/"( class="mobile-nav-link)', rf'href="{c["other"]}"\1', head)
    else:
        head = rep(head, 'href="/" class="nav-lang"', f'href="{c["other"]}" class="nav-lang"')
        head = re.sub(r'href="/"( class="mobile-nav-link)', rf'href="{c["other"]}"\1', head)
    tail = re.sub(r'href="#(objetivos|como|faq|demo)"', rf'href="{c["home"]}#\1"', tail)
    legal = f'<p class="race-legal">{esc(c["legal"])}</p>\n\n'
    fb = tail.index('<footer')
    tail = tail[:fb] + legal + tail[fb:]
    out = head + sections(c) + "\n" + tail
    dest = ROOT / c["path"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print("ok", c["path"], len(out.splitlines()), "líneas")


for lang in ("es", "en"):
    build(lang, HYROX[lang])
