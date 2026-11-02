"""Saca de la hoja de revisión de la LLM (el HTML con el JSON «datos») las semanas
reales que enseñan las páginas por objetivo y las guarda en semanas.json.

Por sesión guarda lo que hace falta para dibujarla: en cardio, los tramos con su
duración y su zona (para la gráfica de intensidad); en gimnasio, los ejercicios
principales con su id del catálogo (para la foto), series y repeticiones.

Uso:
  python3 -I scripts/pages/extraer_semanas.py "<Revisión semana por LLM.html>"
"""
import json
import pathlib
import re
import sys

SRC = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(__file__).with_name("semanas.json")

# página -> [(clave de la semana, perfil, nº de semana)]
SEMANAS = {
    "hyrox": [("hyrox", "e6", 1)],
    "triatlon": [("triatlon", "e9", 2)],
    "10k": [("10k", "e18", 2)],
    "maraton": [("maraton", "e8", 2), ("media", "e19", 2)],
    "fuerza": [("fuerza", "e7", 2)],
}
# Nombres del catálogo que salen mal escritos
NOMBRE_ES = {"Sentadilla bajo con barra barra": "Sentadilla con barra baja"}
ESTIRAMIENTO = re.compile(r"Estiramiento|Postura|Toque de pies", re.I)

d = json.loads(re.search(r'<script type="application/json" id="datos">(.*?)</script>',
                         SRC.read_text(encoding="utf-8"), re.S).group(1))
P = {p["clave"]: p for p in d["perfiles"]}


def tramos(dia):
    """Tramos de una sesión de cardio: [segundos, zona, tipo]."""
    z = (dia.get("cardio_detail") or {}).get("zone") or 2
    segs = [e for e in dia["exercises"] if e.get("bloque") is None and e.get("target_duration_s")]
    notas = [(e.get("notes") or "").strip() for e in segs]
    trabajo = [i for i, n in enumerate(notas) if re.search(r"\(\d+ de \d+\)", n) and "Por bloques" not in n
               or re.search(r"tempo|continuo|firme|umbral", n, re.I) and not n.startswith("Prueba")]
    out = []
    for i, (e, n) in enumerate(zip(segs, notas)):
        s = e["target_duration_s"]
        if n.startswith("Recupera"):
            zz, t = 1, "rec"
        elif i in trabajo:
            zz, t = (4 if "rogresivo" in n else z), "work"
        elif "Por bloques" in n:
            zz, t = z, "steady"
        elif i == 0 and len(segs) > 1 and s <= 900:
            zz, t = 1, "warm"
        elif i == len(segs) - 1 and len(segs) > 1 and s <= 600:
            zz, t = 1, "cool"
        elif trabajo:
            zz, t = 2, "easy"
        else:
            zz, t = min(z, 3), "steady"
        out.append([s, zz, t])
    return out


def ejercicios(dia):
    out = []
    for e in dia["exercises"]:
        if e.get("bloque") not in ("fuerza", "final") or ESTIRAMIENTO.search(e.get("name_es") or ""):
            continue
        es = NOMBRE_ES.get(e["name_es"], e["name_es"])
        en = e["name"][0].upper() + e["name"][1:].lower()
        out.append({"id": str(e["id"]), "es": es, "en": en, "sets": e["sets"], "reps": e["reps"],
                    "seg": e.get("target_duration_s"), "bloque": e["bloque"],
                    "poster": e.get("video")})
    return out


res = {}
for page, lista in SEMANAS.items():
    res[page] = {}
    for clave, perfil, n in lista:
        p = P[perfil]
        w = p["semanas"][n - 1]
        dias = []
        for x in w["dias"]:
            cd = x.get("cardio_detail") or {}
            item = {"dia": x["dia"], "tipo": x["type"], "titulo": x["title"], "min": x["duration_minutes"],
                    "notas": x["notes"], "zona": cd.get("zone"), "modalidad": cd.get("modality")}
            if x["type"] == "cardio":
                item["tramos"] = tramos(x)
                item["core"] = ejercicios(x)
            else:
                item["ejercicios"] = ejercicios(x)
            dias.append(item)
        res[page][clave] = {"perfil": perfil, "nombre": p["nombre"], "semana": n, "mensaje": w["mensaje"],
                            "variacion": p["variacion"] if n > 1 else None,
                            "cardio": p["contexto"].get("cardio"), "dias": dias}
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok", OUT)
