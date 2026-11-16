"""repo_config: cargador comun de la configuracion de Claude Code del repo (kit LMGINC). Solo stdlib.

Capas, en este orden (decision C-6):
  1. .claude/hooks/guard-comun.json      capa comun del kit (si existe y comun=True)
  2. .claude/repo-config.json            capa del repo (origen)
  3. .claude/repo-config.fork.json       capa del fork (solo en forks)
Fusion (capa sobre lo anterior), solo en el primer nivel:
  - escalares y objetos simples (repo, producto, upstream, prod, git, tests...): gana la capa;
  - listas de cadenas (hermanos, consumidores...): union;
  - listas de objetos con id (rutas_protegidas, reglas_bash, reglas_contenido...): por id; la entrada
    de la capa sustituye entera a la anterior con el mismo id y una con id nuevo se anade;
  - "quitar": {"lista": ["id o cadena", ...]} elimina entradas de capas anteriores.
Cada capa se valida contra .claude/repo-config.schema.json; si algo no valida, ConfigError
(los guards deniegan: fallo cerrado, C-3). Equivalente en Node: repo-config.mjs.

Uso como modulo:  from repo_config import cargar, ConfigError
Uso directo:      repo_config.py [RAIZ]   imprime la configuracion fusionada
"""
from __future__ import annotations

import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))


class ConfigError(Exception):
    pass


def leer_json(ruta):
    try:
        with open(ruta, "rb") as f:
            return json.loads(f.read().decode("utf-8-sig"))
    except (OSError, ValueError) as e:
        raise ConfigError(f"{os.path.basename(ruta)} no es JSON valido: {e}") from e


def fusionar(base, capa):
    out = dict(base)
    for k, v in capa.items():
        if k in ("quitar", "$schema"):
            continue
        anterior = out.get(k)
        if isinstance(anterior, list) and isinstance(v, list):
            res = list(anterior)
            for item in v:
                if isinstance(item, dict) and "id" in item:
                    pos = next((i for i, x in enumerate(res) if isinstance(x, dict) and x.get("id") == item["id"]), None)
                    if pos is None:
                        res.append(item)
                    else:
                        res[pos] = item
                elif item not in res:
                    res.append(item)
            out[k] = res
        else:
            out[k] = v
    for lista, quitar in (capa.get("quitar") or {}).items():
        if isinstance(out.get(lista), list):
            out[lista] = [x for x in out[lista]
                          if not ((isinstance(x, dict) and x.get("id") in quitar) or (not isinstance(x, dict) and x in quitar))]
    return out


# ---------------------------------------------------------------- JSON Schema (subconjunto, igual en Node)

def _tipo(v, t):
    if t == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t == "null":
        return v is None
    clases = {"string": str, "boolean": bool, "object": dict, "array": list}
    return t in clases and isinstance(v, clases[t])


def validar(v, esq, raiz, ruta="$"):
    """Errores de v frente a esq. Palabras: $ref type enum const pattern minLength minItems minimum
    required properties additionalProperties propertyNames items anyOf."""
    if esq is True or not esq:
        return []
    if "$ref" in esq:
        nodo = raiz
        for parte in esq["$ref"][2:].split("/"):
            nodo = nodo[parte]
        return validar(v, nodo, raiz, ruta)
    errores = []
    if "type" in esq:
        tipos = esq["type"] if isinstance(esq["type"], list) else [esq["type"]]
        if not any(_tipo(v, t) for t in tipos):
            return [f"{ruta}: se esperaba {'/'.join(tipos)}"]
    if "enum" in esq and v not in esq["enum"]:
        errores.append(f"{ruta}: '{v}' no es {'/'.join(str(x) for x in esq['enum'])}")
    if "const" in esq and v != esq["const"]:
        errores.append(f"{ruta}: tiene que valer {esq['const']}")
    if isinstance(v, str):
        if len(v) < esq.get("minLength", 0):
            errores.append(f"{ruta}: vacio")
        if "pattern" in esq and not re.search(esq["pattern"], v):
            errores.append(f"{ruta}: '{v}' no casa con {esq['pattern']}")
    if isinstance(v, (int, float)) and not isinstance(v, bool) and "minimum" in esq and v < esq["minimum"]:
        errores.append(f"{ruta}: menor que {esq['minimum']}")
    if isinstance(v, list):
        if len(v) < esq.get("minItems", 0):
            errores.append(f"{ruta}: necesita al menos {esq['minItems']} elementos")
        for i, x in enumerate(v):
            errores += validar(x, esq.get("items", {}), raiz, f"{ruta}[{i}]")
    if isinstance(v, dict):
        for r in esq.get("required", []):
            if r not in v:
                errores.append(f"{ruta}: falta '{r}'")
        props = esq.get("properties", {})
        for k, x in v.items():
            if "propertyNames" in esq:
                errores += validar(k, esq["propertyNames"], raiz, f"{ruta}.<{k}>")
            if k in props:
                errores += validar(x, props[k], raiz, f"{ruta}.{k}")
            elif esq.get("additionalProperties") is False:
                errores.append(f"{ruta}: clave no permitida '{k}'")
            elif isinstance(esq.get("additionalProperties"), dict):
                errores += validar(x, esq["additionalProperties"], raiz, f"{ruta}.{k}")
    if "anyOf" in esq and not any(not validar(v, s, raiz, ruta) for s in esq["anyOf"]):
        errores.append(f"{ruta}: no cumple ninguna de las formas permitidas")
    return errores


def capas(raiz, comun=True):
    rutas = []
    if comun:
        rutas.append(os.path.join(AQUI, "guard-comun.json"))
    for nombre in ("repo-config.json", "repo-config.fork.json"):
        rutas.append(os.path.join(raiz, ".claude", nombre))
    return [r for r in rutas if os.path.isfile(r)]


def cargar(raiz, comun=True, exigir_comun=False):
    """Configuracion fusionada y validada. Lanza ConfigError."""
    if exigir_comun and not os.path.isfile(os.path.join(AQUI, "guard-comun.json")):
        raise ConfigError("falta .claude/hooks/guard-comun.json")
    lista = capas(raiz, comun)
    esquema = None
    if lista:
        ruta_esq = os.path.join(raiz, ".claude", "repo-config.schema.json")
        if not os.path.isfile(ruta_esq):
            raise ConfigError("falta .claude/repo-config.schema.json")
        esquema = leer_json(ruta_esq)
    cfg = {}
    for ruta in lista:
        capa = leer_json(ruta)
        errores = validar(capa, esquema, esquema)
        if errores:
            raise ConfigError(f"{os.path.basename(ruta)} no cumple el esquema: " + "; ".join(errores[:3]))
        cfg = fusionar(cfg, capa)
    return cfg


if __name__ == "__main__":
    raiz_ = sys.argv[1] if len(sys.argv) > 1 else (os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    try:
        sys.stdout.buffer.write(json.dumps(cargar(raiz_), ensure_ascii=True, sort_keys=True, indent=2).encode("ascii"))
    except ConfigError as e:
        sys.stderr.write(f"repo_config: {e}\n")
        sys.exit(1)
