"""stop_check.py: hook Stop de trAIn-Landing. Solo stdlib y git, sin red (~0,3 s).

Con cambios sin commitear respecto a HEAD, comprueba lo que se olvida al cerrar un turno:
  1. Paginas generadas: una plantilla o un script cambio y su pagina generada es mas antigua
     (falta /regenerar-web), o una pagina generada se edito a mano sin tocar su plantilla
     (el siguiente /regenerar-web lo pisaria).
  2. Paridad ES/EN en las paginas escritas a mano (legales de la web): una cambio y su par no.
  3. Cache-busting: cambio app.js o assets/css/landing.css y el ?v= de index.html sigue igual, o el
     ?v= no es el mismo en todas las paginas.
  4. Ficheros nuevos que Vercel publicaria y no son contenido web (mismo criterio que el guard).
Si encuentra algo, devuelve decision "block" con el motivo UNA sola vez: respeta stop_hook_active y
no repite el aviso con el mismo estado (huella en el directorio .git, nunca versionada).
Un fallo propio no estorba: sale con 0 sin decir nada.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import public_guard as pg  # noqa: E402

RACE = ["hyrox", "triatlon", "10k", "maraton", "fuerza", "en/hyrox", "en/triathlon", "en/10k", "en/marathon", "en/strength"]
GRUPOS = [
    {"nombre": "home EN", "salidas": ["en/index.html"],
     "entradas": ["index.html", "scripts/i18n/build_en.py", "scripts/i18n/en-head.html", "scripts/i18n/seo_ld.py"]},
    {"nombre": "paginas por objetivo", "salidas": [f"{p}/index.html" for p in RACE],
     "entradas": ["index.html", "en/index.html", "scripts/pages/build_race.py", "scripts/pages/semanas.json"]},
    {"nombre": "blog", "salidas": ["blog/**", "en/blog/**"],
     "entradas": ["index.html", "en/index.html", "scripts/blog/*.py", "scripts/pages/build_race.py",
                  "scripts/pages/semanas.json"]},
]
PARES = [("privacidad", "en/privacy"), ("terminos", "en/terms"), ("aviso-legal", "en/legal-notice"),
         ("cookies", "en/cookies"), ("soporte", "en/support"), ("eliminar-cuenta", "en/delete-account")]
ACTIVOS = {"app.js": re.compile(r"/app\.js\?v=([A-Za-z0-9._-]+)"),
           "assets/css/landing.css": re.compile(r"/assets/css/landing\.css\?v=([A-Za-z0-9._-]+)")}
NO_CUENTA_V = {"scripts/i18n/en-head.html"}  # cabecera EN antigua de la que build_en.py saca metas


def cambios(raiz):
    """{ruta: estado} de lo que difiere de HEAD (indice, arbol y sin seguir no ignorados)."""
    rc, out = pg.git(["status", "--porcelain", "--untracked-files=all", "--no-renames"], raiz)
    if rc != 0:
        return None
    res = {}
    for l in out.splitlines():
        if len(l) > 3:
            res[l[3:].strip().strip('"')] = l[:2]
    return res


def mtime(raiz, rel):
    try:
        return os.path.getmtime(os.path.join(raiz, rel))
    except OSError:
        return 0.0


def generadas(raiz, ch):
    problemas = []
    rutas = list(ch)
    for g in GRUPOS:
        entradas = [r for r in rutas if pg.casa(r, g["entradas"])]
        salidas = [r for r in rutas if pg.casa(r, g["salidas"])]
        if entradas:
            ultima = max(mtime(raiz, r) for r in entradas)
            fijas = [s for s in g["salidas"] if "*" not in s] or ["blog/index.html", "en/blog/index.html"]
            viejas = [s for s in fijas if os.path.exists(os.path.join(raiz, s)) and mtime(raiz, s) + 1 < ultima]
            if viejas:
                problemas.append(f"{g['nombre']}: cambiaste {', '.join(entradas[:3])} y {len(viejas)} pagina(s) "
                                 f"generada(s) son mas antiguas (p. ej. {viejas[0]}). Ejecuta /regenerar-web.")
        elif salidas:
            problemas.append(f"{g['nombre']}: editaste a mano {', '.join(salidas[:3])}, que sale(n) de un script; "
                             "el siguiente /regenerar-web lo pisa. Cambia la plantilla o el script y regenera.")
    return problemas


def paridad(ch):
    problemas = []
    for es, en in PARES:
        a, b = f"{es}/index.html", f"{en}/index.html"
        if (a in ch) != (b in ch):
            hecho, falta = (a, b) if a in ch else (b, a)
            problemas.append(f"paridad ES/EN: cambio {hecho} y no {falta} (todo cambio va en los dos idiomas en el mismo commit)")
    return problemas


def versiones(raiz, ch):
    problemas = []
    tocados = [a for a in ACTIVOS if a in ch]
    if tocados:
        rc, antes = pg.git(["show", "HEAD:index.html"], raiz)
        ahora = pg.texto_de(os.path.join(raiz, "index.html")) or ""
        for a in tocados:
            v0 = ACTIVOS[a].search(antes) if rc == 0 else None
            v1 = ACTIVOS[a].search(ahora)
            if v0 and v1 and v0.group(1) == v1.group(1):
                problemas.append(f"cambiaste {a} y su ?v= sigue en '{v1.group(1)}': se cachea 30 dias. "
                                 "Sube el ?v= en index.html y regenera (/regenerar-web) para que llegue a todas las paginas.")
    if tocados or any(r.endswith(".html") for r in ch):
        rc, out = pg.git(["ls-files", "--cached", "--others", "--exclude-standard", "--", "*.html"], raiz)
        vistos = {a: {} for a in ACTIVOS}
        for rel in out.splitlines():
            if rel in NO_CUENTA_V:
                continue
            t = pg.texto_de(os.path.join(raiz, rel)) or ""
            for a, rx in ACTIVOS.items():
                for m in rx.finditer(t):
                    vistos[a].setdefault(m.group(1), []).append(rel)
        for a, vals in vistos.items():
            if len(vals) > 1:
                resumen = ", ".join(f"?v={v} en {len(r)} (p. ej. {r[0]})" for v, r in sorted(vals.items()))
                problemas.append(f"{a} no tiene el mismo ?v= en todas las paginas: {resumen}")
    return problemas


def publicadas(raiz, ch):
    nuevos = [r for r, e in ch.items() if e == "??"]
    if not nuevos:
        return []
    return pg.publicados(raiz, nuevos, pg.cargar_allow())


def main():
    try:
        ev = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
        if ev.get("stop_hook_active"):
            return 0
        raiz = pg.raiz_de(os.environ.get("CLAUDE_PROJECT_DIR") or ev.get("cwd") or os.getcwd())
        if not raiz:
            return 0
        ch = cambios(raiz)
        if not ch:
            return 0
        problemas = generadas(raiz, ch) + paridad(ch) + versiones(raiz, ch) + publicadas(raiz, ch)
        if not problemas:
            return 0
        huella = hashlib.sha256(json.dumps([sorted(ch.items()), problemas]).encode("utf-8")).hexdigest()
        rc, ruta = pg.git(["rev-parse", "--git-path", "claude-stop-check.txt"], raiz)
        ruta = os.path.join(raiz, ruta.strip()) if rc == 0 and ruta.strip() else None
        if ruta and os.path.isfile(ruta):
            with open(ruta, encoding="utf-8") as f:
                if f.read().strip() == huella:
                    return 0
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(huella)
        motivo = ("[stop trAIn-Landing] Antes de terminar: " + " | ".join(problemas)
                  + " Si es intencionado, dilo y termina; este aviso no se repite con el mismo estado.")
        sys.stdout.write(json.dumps({"decision": "block", "reason": motivo[:3000]}, ensure_ascii=True))
    except Exception:  # noqa: BLE001 - un fallo del hook no debe estorbar
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
