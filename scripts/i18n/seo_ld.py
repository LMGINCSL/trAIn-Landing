"""Regenera el JSON-LD de la home (ES o EN) a partir de su contenido visible.

El FAQPage sale de las preguntas y respuestas que se ven en la página, así que
nunca se desfasa del texto. Uso: seo_ld.py <index.html> <es|en>
"""
import html
import json
import re
import sys
import pathlib

path, lang = pathlib.Path(sys.argv[1]), sys.argv[2]
s = path.read_text(encoding="utf-8")
body = re.sub(r"<!--.*?-->", "", s, flags=re.S)

def text(fragment):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split()).replace(" .", ".").replace(" ,", ",")

faq = []
for m in re.finditer(r'<div class="faq-item"[^>]*>\s*<button[^>]*class="faq-q"[^>]*><span>(.*?)</span>.*?<div class="faq-a-inner">(.*?)</div>', body, re.S):
    faq.append({"@type": "Question", "name": text(m.group(1)), "acceptedAnswer": {"@type": "Answer", "text": text(m.group(2))}})
assert len(faq) >= 9, len(faq)

BASE = "https://2trainapp.com/"
url = BASE if lang == "es" else BASE + "en/"
T = {
    "es": {
        "org": "LMGINC SL desarrolla 2trAIn, una app de entrenamiento con IA hecha en Madrid.",
        "app": "App de entrenamiento con IA para fuerza, cardio y preparación de pruebas (Hyrox, triatlón, 10K, media maratón y maratón). Construye el plan con tu historial, lo reescribe cada semana con lo que entrenas, eliges y le cuentas, y explica cada cambio con tus datos.",
        "sub": "Entrenamiento personal con IA",
        "features": [
            "Plan de fuerza, cardio o preparación de pruebas con fecha (Hyrox, triatlón, 10K, media maratón, maratón)",
            "El plan se reescribe cada semana con lo que entrenas y lo que le cuentas",
            "Cada cambio de volumen o intensidad llega explicado con tus datos",
            "Decide un motor con periodización y fatiga acumulada; el modelo de lenguaje solo lo explica",
            "Recuerda tu material, tus lesiones y los ejercicios que vetas",
            "Sustituciones al momento: sin barras, con una molestia o por aburrimiento",
            "Aprende a qué ritmo respondes tú, no la media",
            "Más de 1.600 ejercicios, cada uno con vídeo y ficha técnica",
            "Funciona en casa o en el gimnasio, con el material que tengas",
        ],
        "page": "2trAIn · App de entrenamiento con IA: fuerza, cardio y Hyrox",
    },
    "en": {
        "org": "LMGINC SL builds 2trAIn, an AI training app made in Madrid.",
        "app": "AI training app for strength, cardio and race prep (Hyrox, triathlon, 10K, half marathon and marathon). It builds the plan from your history, rewrites it every week from what you train, choose and tell it, and explains every change with your data.",
        "sub": "AI personal training",
        "features": [
            "Strength, cardio or race-prep plans toward a date (Hyrox, triathlon, 10K, half marathon, marathon)",
            "The plan is rewritten every week from what you train and what you tell it",
            "Every change in volume or intensity comes explained with your data",
            "A periodisation and accumulated-fatigue engine decides; the language model only explains",
            "Remembers your equipment, your injuries and the exercises you veto",
            "Instant substitutions: no barbell, a niggle or boredom",
            "Learns how fast you respond, not the average",
            "1,600+ exercises, each with video and a technique card",
            "Works at home or in the gym, with whatever equipment you have",
        ],
        "page": "2trAIn · AI training app for strength, cardio and Hyrox",
    },
}[lang]

graph = [
    {"@type": "Organization", "@id": BASE + "#organization", "name": "2trAIn", "alternateName": ["2train", "2Train", "2trAIn app"],
     "legalName": "LMGINC SL", "taxID": "B93905438", "url": BASE, "logo": BASE + "android-chrome-512x512.png",
     "description": T["org"], "email": "contact@2trainapp.com",
     "address": {"@type": "PostalAddress", "streetAddress": "Calle Lagasca 95", "postalCode": "28001", "addressLocality": "Madrid", "addressCountry": "ES"},
     "sameAs": ["https://www.instagram.com/2trainapp/"]},
    {"@type": "WebSite", "@id": url + "#website", "name": "2trAIn", "url": url, "inLanguage": lang, "publisher": {"@id": BASE + "#organization"}},
    {"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": T["page"], "inLanguage": lang, "isPartOf": {"@id": url + "#website"},
     "about": {"@id": BASE + "#app"}, "primaryImageOfPage": BASE + "og-image.png"},
    {"@type": "MobileApplication", "@id": BASE + "#app", "name": "2trAIn", "alternateName": "2train", "url": url,
     "applicationCategory": "HealthApplication", "applicationSubCategory": T["sub"], "operatingSystem": "iOS, Android",
     "inLanguage": ["es", "en"], "description": T["app"], "featureList": T["features"], "isAccessibleForFree": True,
     "image": BASE + "og-image.png", "publisher": {"@id": BASE + "#organization"},
     "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR", "category": "beta"}},
    {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": faq},
]
block = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)
new = '<script type="application/ld+json">\n' + block + "\n</script>"
s2, n = re.subn(r'<script type="application/ld\+json">.*?</script>', lambda m: new, s, count=1, flags=re.S)
assert n == 1
path.write_text(s2, encoding="utf-8")
print("json-ld", lang, "preguntas:", len(faq))
