"""guard_core: guard de comandos y de escritura del kit comun LMGINC (Claude Code). Solo stdlib.

Hook PreToolUse (matcher Bash|PowerShell y Edit|Write|MultiEdit|NotebookEdit). Lee el JSON del evento
por stdin y responde con hookSpecificOutput.permissionDecision = deny | ask, o no imprime nada si
no tiene opinion. Nunca devuelve allow: no salta las preguntas de permiso de Claude Code.

Configuracion: la carga repo_config.py (guard-comun.json + .claude/repo-config.json +
.claude/repo-config.fork.json, fusionados y validados contra .claude/repo-config.schema.json).
Usa reglas_bash, requiere_env, rutas_protegidas, reglas_contenido y git (politica C-4).

Comandos: antes de decidir, el comando se analiza como lo haria el shell (Bash, PowerShell o cmd):
comillas, escapes y backticks fuera; troceo por ; && || | & y saltos de linea; variables asignadas
antes en el mismo comando; y se entra en lo que ejecuta otro comando (bash -c, cmd /c,
powershell -Command/-EncodedCommand, $(...), backticks, eval, source, subshell, xargs, env, una
variable en posicion de comando...). Si dentro hay algo que una regla deniega, se deniega; si no,
esas construcciones piden permiso. Las rutas (Write/Edit y destinos de redirecciones, cp, mv, tee,
sed -i, Set-Content...) se normalizan antes de casar con rutas_protegidas.

Falla cerrado (C-3): si la configuracion no se puede leer o no valida, o el evento no se entiende,
deniega (salvo editar los propios ficheros de configuracion, que pide permiso para poder arreglarlos).
La salida es JSON en ASCII: en Windows un acento rompia la salida del hook.

Uso:
  guard_core.py                  modo hook (stdin -> stdout)
  guard_core.py --config [RAIZ]  imprime la configuracion fusionada (diagnostico y pruebas)
  guard_core.py --version
Equivalente en Node: guard_core.mjs (mismo esquema, mismas decisiones, mismos casos de prueba).
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repo_config import ConfigError, cargar  # noqa: E402

VERSION = "2.1.0"
PESO = {"ask": 1, "deny": 2}
RX = re.ASCII  # \w, \b, \d y \s en ASCII, como JavaScript sin la bandera u
SEGMENTOS = re.compile(r"\s*(?:&&|\|\||;|\|&?|(?<![<>&|])&(?![>&])|\n)\s*")
EDITA_CONFIG = re.compile(r"^\.claude/(?:repo-config[^/]*\.json|hooks/guard-comun\.json)$", re.I)
GIT_DEFECTO = {"activo": True, "rama_principal": ["main"], "ramas_protegidas": [], "push": "ask",
               "commit_en_principal": "ask", "pr_create": "ask", "pr_merge": "deny"}
GH_CON_VALOR = ("-R", "--repo", "--hostname")
PROF_MAX = 8
HOSTS_LOCALES = r"(?:https?://)?(?:localhost|127(?:\.\d{1,3}){3}|\[::1\]|::1|0\.0\.0\.0)(?::\d{1,5})?(?:/\S*)?"
# CLI -> opciones globales que llevan el valor en el siguiente token (identico en guard_core.mjs).
# Las de la forma --opcion=valor y las que no llevan valor se quitan siempre.
OPCIONES_GLOBALES = [
    (r"(?:terraform|tofu)(?:\.exe)?", ["-chdir"]),
    (r"git(?:\.exe)?", ["-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"]),
    (r"gcloud(?:\.cmd)?", ["--project", "--account", "--configuration", "--impersonate-service-account", "--verbosity",
                           "--format", "--billing-project", "--flags-file", "--trace-token", "--region", "--zone"]),
    (r"(?:npm|pnpm|yarn)(?:\.cmd)?", ["--prefix", "-C", "--dir", "--filter", "-F", "--workspace", "-w", "--cwd",
                                      "--loglevel", "--registry", "--userconfig"]),
    (r"gh(?:\.exe)?", list(GH_CON_VALOR)),
    (r"(?:docker|podman)(?:\.exe)?", ["-H", "--host", "--context", "-c", "--config", "-l", "--log-level", "--tlscacert",
                                      "--tlscert", "--tlskey", "--connection", "--url", "--root", "--runroot"]),
    (r"kubectl(?:\.exe)?", ["-n", "--namespace", "--context", "--kubeconfig", "--cluster", "--user", "-s", "--server",
                            "--token", "--as", "--as-group", "--request-timeout", "-v"]),
    (r"firebase(?:\.cmd)?", ["-P", "--project", "--account", "--config", "-c", "--token"]),
    (r"supabase(?:\.exe)?", ["--workdir", "--profile", "--network-id", "--dns-resolver", "-o", "--output"]),
    (r"vercel(?:\.cmd)?", ["--cwd", "--scope", "-S", "--token", "-t", "-A", "--local-config", "-Q", "--global-config",
                           "--team", "-T"]),
    (r"(?:uv|poetry)(?:\.exe)?", ["--directory", "--project", "--cache-dir", "--config-file", "-C", "-P"]),
]
_VALOR = "(?:\"[^\"]*\"|'[^']*'|[^\\s;&|]+)"


def _patron_normalizar(nombres, con_valor):
    opcion = ("(?:--?[\\w.-]+=" + _VALOR + "|(?:" + "|".join(con_valor) + ")\\s+" + _VALOR
              + "|--?[A-Za-z][\\w.-]*)")
    return re.compile("(?<![\\w.-])(" + nombres + ")(?:\\s+" + opcion + ")+(?=\\s+[^\\s-])", re.I | RX)


NORMALIZAR = [_patron_normalizar(n, v) for n, v in OPCIONES_GLOBALES]
HERRAMIENTAS_COMANDO = ("Bash", "PowerShell")
HERRAMIENTAS_ESCRITURA = ("Edit", "Write", "MultiEdit", "NotebookEdit")
# Construcciones de regex que Python y JavaScript no entienden igual (AUD-kit-16).
REGEX_NO_PORTABLE = re.compile(r"\\[AZzQE]|\(\?[aiLmsux-]+[:)]|\(\?P=|\(\?#|\(\?>|[*+?}]\+")

# ---------------------------------------------------------------- compilar la configuracion


def regex_py(patron):
    """Acepta grupos con nombre de JavaScript (?<n>...) ademas de los de Python (?P<n>...)."""
    return re.sub(r"\(\?<(?=[A-Za-z_])", "(?P<", patron)


def _re(patron, distinguir=False, donde=""):
    if not isinstance(patron, str):
        raise ConfigError(f"{donde}: regex invalida (no es texto)")
    if REGEX_NO_PORTABLE.search(patron):
        raise ConfigError(f"{donde}: regex invalida (usa una construccion que Python y JavaScript no entienden igual)")
    try:
        return re.compile(regex_py(patron), RX if distinguir else (re.I | RX))
    except (re.error, TypeError) as e:
        raise ConfigError(f"{donde}: regex invalida ({e})") from e


def _glob_parte(g):
    out, i = "", 0
    while i < len(g):
        c = g[i]
        if g.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif g.startswith("**", i):
            out, i = out + ".*", i + 2
        elif c == "*":
            out, i = out + "[^/]*", i + 1
        elif c == "?":
            out, i = out + "[^/]", i + 1
        elif c == "{" and "}" in g[i:]:
            j = g.index("}", i)
            out += "(?:" + "|".join(_glob_parte(a) for a in g[i + 1:j].split(",")) + ")"
            i = j + 1
        elif c in ".^$+()|[]{}\\":
            out, i = out + "\\" + c, i + 1
        else:
            out, i = out + c, i + 1
    return out


def glob_re(glob):
    """Glob relativo a la raiz -> regex anclada, sin distinguir mayusculas (igual en guard_core.mjs)."""
    return re.compile("^" + _glob_parte(glob) + "$", re.I | re.S)


def _shell_parte(patron):
    out, i = "", 0
    while i < len(patron):
        c = patron[i]
        if c == "*":
            out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        elif c == "[" and "]" in patron[i + 2:]:
            j = patron.index("]", i + 2)
            clase = patron[i + 1:j]
            if clase[:1] in ("!", "^"):
                clase = "^" + clase[1:]
            out += "[" + clase.replace("\\", "\\\\") + "]"
            i = j
        else:
            out += re.escape(c) if c not in "/" else "/"
        i += 1
    return out


def glob_shell_re(patron):
    """Comodin del shell (*, ?, [..]) en un nombre de fichero -> regex anclada."""
    return re.compile("^" + _shell_parte(patron) + "$", re.I | re.S)


COMODIN = re.compile(r"[*?\[]")
PUNTO_PUNTO = re.compile(r"(?:^|[/\\])\.\.(?:[/\\]|$)")


def patron_ruta_re(rel, ocultos=False):
    """Ruta relativa con comodines -> regex anclada, carpeta a carpeta. Como en bash, un comodin al principio de
    una parte no casa con un nombre que empieza por '.' (salvo ocultos=True: PowerShell)."""
    partes = []
    for p in rel.split("/"):
        r = _shell_parte(p)
        partes.append(("(?!\\.)" + r) if (not ocultos and p[:1] in ("*", "?", "[")) else r)
    return re.compile("^" + "/".join(partes) + "$", re.I | re.S)


def expandir_comodin(patron, cwd, ocultos=False, limite=200):
    """Expande un comodin del shell (*, ?, [..]) contra el disco, carpeta a carpeta, como bash sin globstar (un
    nombre que empieza por '.' solo si la parte del patron lo pone, salvo ocultos=True). Devuelve las rutas tal
    como las escribiria el shell, ordenadas; [] si no casa nada."""
    p = (patron or "").replace("\\", "/")
    if p.startswith("~/"):
        p = os.path.expanduser("~").replace("\\", "/") + p[1:]
    m = re.match(r"^(?:[A-Za-z]:)?/", p)
    if m:
        actuales = [(m.group(0), m.group(0))]
        p = p[m.end():]
    else:
        actuales = [((cwd or ".").replace("\\", "/").rstrip("/") + "/", "")]
    for parte in [x for x in p.split("/") if x]:
        nuevos = []
        for disco, visto in actuales:
            if not COMODIN.search(parte):
                nuevos.append((disco + parte + "/", visto + parte + "/"))
                continue
            try:
                nombres = sorted(os.listdir(disco))
                rx = glob_shell_re(parte)
            except (OSError, re.error):
                continue
            for nombre in nombres:
                if nombre.startswith(".") and not parte.startswith(".") and not ocultos:
                    continue
                if rx.match(nombre):
                    nuevos.append((disco + nombre + "/", visto + nombre + "/"))
        actuales = nuevos[:limite]
    return sorted(v[:-1] for d, v in actuales if v and os.path.exists(d[:-1]))


def _muestras(globs, excepto):
    out = []
    for g in globs:
        for relleno in ("local", "production", "development", "x"):
            m = g.replace("**/", "").replace("*", relleno).replace("?", "x")
            if m not in out and not any(e.match(m) for e in excepto):
                out.append(m)
    return out


def _expandir(glob):
    """'{a,b}/c' -> ['a/c', 'b/c'] (llaves sin anidar)."""
    i = glob.find("{")
    j = glob.find("}", i + 1) if i >= 0 else -1
    if i < 0 or j < 0:
        return [glob]
    return [x for alt in glob[i + 1:j].split(",") for x in _expandir(glob[:i] + alt + glob[j + 1:])]


def _muestras_ruta(glob, excepto):
    """Rutas de ejemplo que casan con el glob de una ruta protegida, y sus carpetas (marcadas con True), para saber
    si un destino con comodin puede caer en ella."""
    out = []
    for g in _expandir(glob):
        for relleno in ("", "x"):
            m = g.replace("**/", "").replace("**", "x").replace("*", relleno).replace("?", "x")
            if not m or any(e.match(m) for e in excepto):
                continue
            if (m, False) not in out:
                out.append((m, False))
            partes = m.split("/")
            for k in range(1, len(partes)):
                c = "/".join(partes[:k])
                if (c, True) not in out and (c, False) not in out:
                    out.append((c, True))
    return out


def _prefijos(glob):
    """Carpetas fijas al principio de cada alternativa del glob ('.claude/hooks/**' -> '.claude/hooks/')."""
    out = []
    for g in _expandir(glob):
        k = min([g.find(c) for c in "*?[" if c in g] or [len(g)])
        pref = g[:k]
        pref = pref[:pref.rfind("/") + 1]
        if pref and pref.lower() not in out:
            out.append(pref.lower())
    return out


def compilar(cfg):
    repo = cfg.get("repo")
    out = {"prefijo": f"[guard {repo}]" if repo else "[guard]", "bash": [], "rutas": [], "contenido": [],
           "requiere_env": []}
    git = dict(GIT_DEFECTO)
    git.update(cfg.get("git") or {})
    rp = git["rama_principal"]
    git["rama_principal"] = [x.lower() for x in ([rp] if isinstance(rp, str) else rp)]
    git["ramas_protegidas"] = [x.lower() for x in git.get("ramas_protegidas") or []]
    out["git"] = git
    for r in cfg.get("reglas_bash") or []:
        donde = f"regla {r.get('id')}"
        d = r.get("distinguir_mayusculas", False)
        for mapa in (r.get("entorno_falta") or {}, r.get("entorno_es") or {}):
            for val in mapa.values():
                _re(val, False, donde)
        excepto = [glob_re(g) for g in r.get("ficheros_excepto") or []]
        ficheros = [glob_re(g) for g in r.get("ficheros") or []]
        out["bash"].append({
            "id": r["id"], "decision": r["decision"], "ambito": r.get("ambito", "comando"),
            "regex": _re(r["regex"], d, donde), "y": [_re(p, d, donde) for p in r.get("y") or []],
            "salvo": [_re(p, d, donde) for p in r.get("salvo") or []],
            "entorno_falta": r.get("entorno_falta") or {}, "entorno_es": r.get("entorno_es") or {}, "motivo": r["motivo"],
            "ficheros": ficheros, "ficheros_excepto": excepto,
            "muestras": _muestras(r.get("ficheros") or [], excepto),
            "opciones_con_valor": list(r.get("opciones_con_valor") or [])})
    for r in cfg.get("requiere_env") or []:
        donde = f"regla {r.get('id')}"
        permitidos = [HOSTS_LOCALES if p == "@hosts_locales" else p for p in r.get("valores_permitidos") or []]
        out["requiere_env"].append({
            "id": r["id"], "decision": r["decision"], "motivo": r["motivo"], "variables": list(r["variables"]),
            "regex": _re(r["regex"], False, donde), "permitidos": [_re(p, False, donde) for p in permitidos]})
    for r in cfg.get("rutas_protegidas") or []:
        excepto = [glob_re(g) for g in r.get("excepto") or []]
        out["rutas"].append({"id": r["id"], "modo": r["modo"], "glob": glob_re(r["glob"]),
                             "excepto": excepto, "motivo": r["motivo"],
                             "prefijos": _prefijos(r["glob"]), "comandos": bool(r.get("comandos")),
                             "muestras": _muestras_ruta(r["glob"], excepto)})
    for r in cfg.get("reglas_contenido") or []:
        donde = f"regla {r.get('id')}"
        out["contenido"].append({
            "id": r["id"], "decision": r["decision"], "glob": glob_re(r["glob"]),
            "regex": _re(r["regex"], r.get("distinguir_mayusculas", False), donde),
            "excepto_si": _re(r["excepto_si"], False, donde) if r.get("excepto_si") else None, "motivo": r["motivo"]})
    return out


# ---------------------------------------------------------------- rutas

def _es_absoluta(r):
    return r.startswith("/") or re.match(r"^[A-Za-z]:(?:/|$)", r) is not None


def normalizar_ruta(ruta, raiz, cwd=None):
    """Ruta (de Write/Edit o de un comando) -> relativa a la raiz con '/', o absoluta normalizada si
    queda fuera. Quita flujos NTFS (::$DATA), '.' y espacios finales de cada parte (Windows los
    ignora), '.', '..' y barras repetidas; compara sin distinguir mayusculas."""
    base = (raiz or "").replace("\\", "/")
    r = (ruta or "").replace("\\", "/")
    if r.startswith("~/") or r == "~":
        r = (os.path.expanduser("~").replace("\\", "/")) + r[1:]
    if not _es_absoluta(r):
        r = ((cwd or raiz or "").replace("\\", "/")).rstrip("/") + "/" + r
    m = re.match(r"^/([A-Za-z])(?=/|$)", r)
    if m and re.match(r"^[A-Za-z]:", base):
        r = m.group(1) + ":" + r[2:]
    return _relativa(_partes(r), _partes(base))


def _partes(r):
    pref = ""
    m = re.match(r"^([A-Za-z]:)", r)
    if m:
        pref, r = m.group(1).lower(), r[2:]
    elif r.startswith("/"):
        pref = "/"
    partes = []
    for p in r.split("/"):
        if ":" in p:
            p = p.split(":")[0]
        if p in ("", "."):
            continue
        if p == "..":
            if partes:
                partes.pop()
            continue
        p = p.rstrip(" .")
        if p:
            partes.append(p)
    return pref, partes


def _relativa(ruta, base):
    pref, partes = ruta
    bpref, bpartes = base
    if bpref and pref.lower() == bpref.lower() and len(partes) >= len(bpartes) \
            and [x.lower() for x in partes[:len(bpartes)]] == [x.lower() for x in bpartes]:
        return "/".join(partes[len(bpartes):])
    return (pref if pref == "/" else pref + "/") + "/".join(partes) if pref else "/".join(partes)


def ruta_relativa(ruta, raiz):
    """Compatibilidad: ruta de Write/Edit relativa a la raiz, normalizada."""
    return normalizar_ruta(ruta, raiz)


def es_config_claude(rel):
    partes = rel.lower().split("/")
    return ".claude" in partes or partes[-1] in (".mcp.json", "claude.md", "claude.local.md")


# ---------------------------------------------------------------- troceo de comandos

SUB = "\x00S\x00"


def _var(nombre):
    return "\x00V" + nombre + "\x00"


def buscar_cierre(t, i, abre, cierra, modo):
    """Indice del 'cierra' que equilibra el 'abre' anterior a i, saltando comillas y escapes."""
    prof, n = 1, len(t)
    while i < n:
        c = t[i]
        if (modo == "bash" and c == "\\") or (modo == "ps" and c == "`") or (modo == "cmd" and c == "^"):
            i += 2
            continue
        if modo == "bash" and t.startswith("<<", i) and not t.startswith("<<<", i):
            m = re.match(r"<<-?\s*(?:(['\"])(.*?)\1|([^\s;&|<>()]+))", t[i:], re.S)
            fin_linea = t.find("\n", i)
            if m and fin_linea >= 0:
                delim = m.group(2) if m.group(1) else m.group(3).replace("\\", "")
                k = fin_linea + 1
                while k < n:
                    e = t.find("\n", k)
                    e = n if e < 0 else e
                    if t[k:e].lstrip("\t") == delim:
                        k = e
                        break
                    k = e + 1
                i = k
                continue
        if c == "'" and modo != "cmd":
            j = t.find("'", i + 1)
            i = (j if j >= 0 else n) + 1
            continue
        if c == '"':
            j = i + 1
            while j < n and t[j] != '"':
                if (modo == "bash" and t[j] == "\\") or (modo == "ps" and t[j] == "`"):
                    j += 1
                j += 1
            i = j + 1
            continue
        if c == abre:
            prof += 1
        elif c == cierra:
            prof -= 1
            if prof == 0:
                return i
        i += 1
    return n


ESCAPES_PS = {"0": "\x00", "a": "\x07", "b": "\b", "e": "\x1b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v"}
ESCAPES_C = {"n": "\n", "t": "\t", "r": "\r", "a": "\x07", "b": "\b", "e": "\x1b", "E": "\x1b", "f": "\f", "v": "\v",
             "\\": "\\", "'": "'", '"': '"', "?": "?"}


class Troceador:
    """Trocea un comando de Bash, PowerShell o cmd en segmentos con sus tokens (sin comillas ni
    escapes), redirecciones, sustituciones de comando y entrada (heredoc). Igual en guard_core.mjs."""

    def __init__(self, t, modo):
        self.t, self.modo, self.n, self.i = t, modo, len(t), 0
        self.segs = []
        self.cur, self.hay, self.glob, self.redir = "", False, False, None
        self.pend = []
        self.seg = self._nuevo(0)

    def _nuevo(self, ini):
        return {"tk": [], "redir": [], "subs": [], "stdin": None, "sep": "", "ini": ini, "texto": "", "llamada": False}

    def token(self):
        if self.cur or self.hay:
            tok = {"s": self.cur, "g": self.glob}
            if self.redir == "<<<":
                self.seg["stdin"] = tok
            elif self.redir is not None:
                self.seg["redir"].append([self.redir, tok])
            else:
                self.seg["tk"].append(tok)
            self.redir = None
        self.cur, self.hay, self.glob = "", False, False

    def fin(self, sep, avance):
        self.token()
        self.redir = None
        self.seg["sep"] = sep
        self.seg["texto"] = self.t[self.seg["ini"]:self.i]
        s = self.seg
        if s["tk"] or s["redir"] or s["subs"] or s["stdin"] is not None:
            self.segs.append(s)
        self.i += avance
        self.seg = self._nuevo(self.i)
        if sep == "\n" and self.pend:
            self.heredocs()

    def sub(self, texto, modo, fuerza, tipo):
        self.seg["subs"].append({"texto": texto, "modo": modo, "fuerza": fuerza, "tipo": tipo})

    def heredocs(self):
        for seg, delim, crudo, tabs in self.pend:
            lineas = []
            while self.i < self.n:
                j = self.t.find("\n", self.i)
                j = self.n if j < 0 else j
                linea = self.t[self.i:j]
                self.i = j + 1
                if (linea.lstrip("\t") if tabs else linea) == delim:
                    break
                lineas.append(linea)
            cuerpo = "\n".join(lineas)
            seg["stdin"] = {"s": cuerpo, "g": False}
            if not crudo:
                for m in re.finditer(r"\$\(", cuerpo):
                    k = buscar_cierre(cuerpo, m.end(), "(", ")", "bash")
                    seg["subs"].append({"texto": cuerpo[m.end():k], "modo": "bash", "fuerza": True, "tipo": "$(...)"})
        self.pend = []
        self.seg["ini"] = self.i

    def trocear(self):
        t, n = self.t, self.n
        while self.i < n:
            c = t[self.i]
            if self.modo == "bash":
                self.paso_bash(c)
            elif self.modo == "ps":
                self.paso_ps(c)
            else:
                self.paso_cmd(c)
        self.fin("", 0)
        if self.pend:
            for seg, _, _, _ in self.pend:
                seg["stdin"] = {"s": "", "g": False}
            self.pend = []
        return self.segs

    # -------------------------------------------------- comun
    def separador(self, c):
        t, i = self.t, self.i
        dos = t[i:i + 2]
        if c == "\n":
            self.fin("\n", 1)
        elif c == ";":
            self.fin(";", 2 if dos == ";;" else 1)
        elif dos in ("&&", "||"):
            self.fin(dos, 2)
        elif dos == "|&":
            self.fin("|", 2)
        elif c == "|":
            self.fin("|", 1)
        else:
            self.fin("&", 1)

    def redireccion(self):
        """En t[i] hay '>' (o '&>'): registra la redireccion; el siguiente token es el destino."""
        t = self.t
        if (self.cur.isdigit() or self.cur == "*") and not self.hay:
            self.cur = ""
        self.token()
        op = ">"
        if t.startswith("&>", self.i):
            op, self.i = "&>", self.i + 1
        self.i += 1
        if self.i < self.n and t[self.i] in ">|":
            op += ">" if t[self.i] == ">" else ""
            self.i += 1
        if self.i < self.n and t[self.i] == "&":
            m = re.match(r"&(\d+|-)", t[self.i:])
            if m:
                self.i += len(m.group(0))
                return
            self.i += 1
        if self.modo == "bash" and self.i < self.n and t[self.i] == "(":
            k = buscar_cierre(t, self.i + 1, "(", ")", "bash")
            self.sub(t[self.i + 1:k], "bash", True, ">(...)")
            self.i = k + 1
            return
        self.redir = op

    def dolar(self, en_dobles):
        t, i = self.t, self.i
        sig = t[i + 1] if i + 1 < self.n else ""
        if sig == "(":
            k = buscar_cierre(t, i + 2, "(", ")", self.modo)
            self.sub(t[i + 2:k], self.modo, True, "$(...)")
            self.cur += SUB
            self.hay, self.i = True, k + 1
            return
        if sig == "{":
            k = t.find("}", i + 2)
            k = self.n if k < 0 else k
            m = re.match(r"(?:env:)?([A-Za-z_][A-Za-z0-9_]*)", t[i + 2:k], RX)
            nombre = m.group(1) if m else "?"
            if self.modo == "ps" and not t[i + 2:k].lower().startswith("env:"):
                nombre = "ps:" + nombre.lower()
            self.cur += _var(nombre)
            self.hay, self.i = True, k + 1
            return
        if self.modo == "ps":
            m = re.match(r"env:([A-Za-z_][A-Za-z0-9_]*)", t[i + 1:], re.I | RX)
            if m:
                self.cur += _var(m.group(1))
                self.hay, self.i = True, i + 1 + len(m.group(0))
                return
            m = re.match(r"(?:(?:global|script|local|private|using):)?([A-Za-z_][A-Za-z0-9_]*|\?|\^|\$)", t[i + 1:], re.I | RX)
            if m:
                self.cur += _var("ps:" + m.group(1).lower())
                self.hay, self.i = True, i + 1 + len(m.group(0))
                return
        else:
            m = re.match(r"[A-Za-z_][A-Za-z0-9_]*|[0-9?$!#@*-]", t[i + 1:], RX)
            if m:
                self.cur += _var(m.group(0))
                self.hay, self.i = True, i + 1 + len(m.group(0))
                return
        self.cur += "$"
        self.i += 1

    # -------------------------------------------------- Bash
    def dobles_bash(self):
        t = self.t
        self.i += 1
        self.hay = True
        while self.i < self.n and t[self.i] != '"':
            c = t[self.i]
            if c == "\\" and self.i + 1 < self.n:
                sig = t[self.i + 1]
                if sig == "\n":
                    self.i += 2
                    continue
                self.cur += sig if sig in '$`"\\' else "\\" + sig
                self.i += 2
            elif c == "$":
                self.dolar(True)
            elif c == "`":
                k = self._backtick(self.i + 1)
                self.sub(t[self.i + 1:k], "bash", True, "comillas invertidas")
                self.cur += SUB
                self.i = k + 1
            else:
                self.cur += c
                self.i += 1
        self.i += 1

    def _backtick(self, j):
        while j < self.n and self.t[j] != "`":
            j += 2 if self.t[j] == "\\" else 1
        return min(j, self.n)

    def paso_bash(self, c):
        t, i = self.t, self.i
        sig = t[i + 1] if i + 1 < self.n else ""
        if c == "\\":
            if sig == "\n":
                self.i += 2
            elif sig:
                self.cur += sig
                self.hay, self.i = True, i + 2
            else:
                self.cur += c
                self.i += 1
        elif c == "'":
            k = t.find("'", i + 1)
            k = self.n if k < 0 else k
            self.cur += t[i + 1:k]
            self.hay, self.i = True, k + 1
        elif c == "$" and sig == "'":
            j, out = i + 2, ""
            while j < self.n and t[j] != "'":
                if t[j] == "\\" and j + 1 < self.n:
                    e = t[j + 1]
                    m = re.match(r"x([0-9A-Fa-f]{1,2})|([0-7]{1,3})", t[j + 1:])
                    if m and m.group(1):
                        out, j = out + chr(int(m.group(1), 16)), j + 1 + len(m.group(0))
                    elif m and m.group(2):
                        out, j = out + chr(int(m.group(2), 8)), j + 1 + len(m.group(0))
                    else:
                        out, j = out + ESCAPES_C.get(e, "\\" + e), j + 2
                else:
                    out, j = out + t[j], j + 1
            self.cur += out
            self.hay, self.i = True, j + 1
        elif c == '"':
            self.dobles_bash()
        elif c == "`":
            k = self._backtick(i + 1)
            self.sub(t[i + 1:k], "bash", True, "comillas invertidas")
            self.cur += SUB
            self.hay, self.i = True, k + 1
        elif c == "$":
            self.dolar(False)
        elif c in " \t\r":
            self.token()
            self.i += 1
        elif c == "#" and not self.cur and not self.hay:
            k = t.find("\n", i)
            self.i = self.n if k < 0 else k
        elif c in "\n;|" or (c == "&" and sig != ">"):
            self.separador(c)
        elif c == ">" or (c == "&" and sig == ">"):
            self.redireccion()
        elif c == "<":
            self.menor_bash()
        elif c == "(" and not self.cur and not self.hay and not self.seg["tk"]:
            k = buscar_cierre(t, i + 1, "(", ")", "bash")
            self.sub(t[i + 1:k], "bash", True, "subshell ( )")
            self.i = k + 1
        elif c == ")":
            self.token()
            self.i += 1
        else:
            if c in "*?[":
                self.glob = True
            self.cur += c
            self.i += 1

    def menor_bash(self):
        t, i = self.t, self.i
        if t.startswith("<<<", i):
            self.token()
            self.redir, self.i = "<<<", i + 3
        elif t.startswith("<<", i):
            self.token()
            j = i + 2
            tabs = j < self.n and t[j] == "-"
            j += 1 if tabs else 0
            while j < self.n and t[j] in " \t":
                j += 1
            m = re.match(r"(['\"])(.*?)\1|([^\s;&|<>()]+)", t[j:], re.S)
            if m:
                delim = m.group(2) if m.group(1) else m.group(3).replace("\\", "")
                crudo = bool(m.group(1)) or "\\" in (m.group(3) or "")
                self.pend.append((self.seg, delim, crudo, tabs))
                self.i = j + len(m.group(0))
            else:
                self.i = j
        elif t.startswith("<(", i):
            k = buscar_cierre(t, i + 2, "(", ")", "bash")
            self.sub(t[i + 2:k], "bash", True, "<(...)")
            self.cur += SUB
            self.hay, self.i = True, k + 1
        else:
            if self.cur.isdigit() and not self.hay:
                self.cur = ""
            self.token()
            self.redir, self.i = "<", i + 1

    # -------------------------------------------------- PowerShell
    def dobles_ps(self):
        t = self.t
        self.i += 1
        self.hay = True
        while self.i < self.n:
            c = t[self.i]
            if c == '"':
                if self.i + 1 < self.n and t[self.i + 1] == '"':
                    self.cur += '"'
                    self.i += 2
                    continue
                break
            if c == "`" and self.i + 1 < self.n:
                sig = t[self.i + 1]
                self.cur += ESCAPES_PS.get(sig, sig)
                self.i += 2
            elif c == "$":
                self.dolar(True)
            else:
                self.cur += c
                self.i += 1
        self.i += 1

    def paso_ps(self, c):
        t, i = self.t, self.i
        sig = t[i + 1] if i + 1 < self.n else ""
        inicio = not self.cur and not self.hay
        if c == "`":
            if sig == "\n":
                self.i += 2
            elif sig:
                self.cur += sig
                self.hay, self.i = True, i + 2
            else:
                self.i += 1
        elif c == "'":
            j, out = i + 1, ""
            while j < self.n:
                if t[j] == "'":
                    if j + 1 < self.n and t[j + 1] == "'":
                        out, j = out + "'", j + 2
                        continue
                    break
                out, j = out + t[j], j + 1
            self.cur += out
            self.hay, self.i = True, j + 1
        elif c == '"':
            self.dobles_ps()
        elif c == "$":
            self.dolar(False)
        elif c == "@" and sig == "(":
            k = buscar_cierre(t, i + 2, "(", ")", "ps")
            self.sub(t[i + 2:k], "ps", False, "@(...)")
            self.cur += SUB
            self.hay, self.i = True, k + 1
        elif c == "@" and inicio and re.match(r"[A-Za-z_]", sig):
            m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", t[i + 1:], RX)
            self.cur += _var("ps:@" + (m.group(0).lower() if m else ""))
            self.hay, self.i = True, i + 1 + (len(m.group(0)) if m else 0)
        elif c == "(" and inicio:
            k = buscar_cierre(t, i + 1, "(", ")", "ps")
            self.sub(t[i + 1:k], "ps", False, "( )")
            self.cur += SUB
            self.hay, self.i = True, k + 1
        elif c == "{" and inicio:
            k = buscar_cierre(t, i + 1, "{", "}", "ps")
            self.sub(t[i + 1:k], "ps", False, "{ }")
            self.cur += SUB
            self.hay, self.i = True, k + 1
        elif c in ")}":
            self.token()
            self.i += 1
        elif c == "<" and sig == "#":
            k = t.find("#>", i + 2)
            self.i = self.n if k < 0 else k + 2
        elif c == "#" and inicio:
            k = t.find("\n", i)
            self.i = self.n if k < 0 else k
        elif c in " \t\r,":
            self.token()
            self.i += 1
        elif c == "-" and inicio and t.startswith("--%", i):
            k = t.find("\n", i)
            k = self.n if k < 0 else k
            for p in t[i + 3:k].split():
                self.seg["tk"].append({"s": p, "g": False})
            self.i = k
        elif c == "&" and sig != "&" and inicio and not self.seg["tk"]:
            self.seg["llamada"] = True
            self.i += 1
        elif c in "\n;|" or c == "&":
            self.separador(c)
        elif c == ">":
            self.redireccion()
        else:
            if c in "*?[":
                self.glob = True
            self.cur += c
            self.i += 1

    # -------------------------------------------------- cmd
    def paso_cmd(self, c):
        t, i = self.t, self.i
        sig = t[i + 1] if i + 1 < self.n else ""
        if c == "^":
            if sig:
                self.cur += sig
                self.hay = True
            self.i += 2
        elif c == '"':
            k = t.find('"', i + 1)
            k = self.n if k < 0 else k
            self.cur += t[i + 1:k]
            self.hay, self.i = True, k + 1
        elif c == "%":
            m = re.match(r"%([A-Za-z_][A-Za-z0-9_]*)%", t[i:], RX)
            if m:
                self.cur += _var(m.group(1))
                self.hay, self.i = True, i + len(m.group(0))
            else:
                self.cur += c
                self.i += 1
        elif c in " \t\r":
            self.token()
            self.i += 1
        elif c in "\n|&":
            self.separador(c)
        elif c == ">":
            self.redireccion()
        elif c == "<":
            self.token()
            self.redir, self.i = "<", i + 1
        elif c == "(" and not self.cur and not self.hay and not self.seg["tk"]:
            k = buscar_cierre(t, i + 1, "(", ")", "cmd")
            self.sub(t[i + 1:k], "cmd", False, "( )")
            self.i = k + 1
        elif c == ")":
            self.token()
            self.i += 1
        else:
            if c in "*?":
                self.glob = True
            self.cur += c
            self.i += 1


def segmentos(cmd):
    """Troceo simple del texto por ; && || | & y saltos de linea (compatibilidad y reglas 'segmento')."""
    return [s for s in SEGMENTOS.split(cmd) if s.strip()]


def tokens(seg):
    """Compatibilidad: tokens de un trozo de Bash, sin comillas ni escapes."""
    out = []
    for s in Troceador(seg, "bash").trocear():
        out += [x["s"].replace(SUB, "$(...)") for x in s["tk"]]
    return out


# ---------------------------------------------------------------- analisis de comandos

SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish", "ash", "mksh"}
POWERSHELL = {"powershell", "pwsh"}
PALABRAS_CLAVE = {"{", "}", "!", "then", "do", "else", "elif", "if", "while", "until", "fi", "done", "esac", "foreach",
                  "for", "try", "finally", "elseif"}
ALIAS_EXE = {"firebase-tools": "firebase", "podman": "podman", "docker-compose": "docker-compose",
             # binarios cortos de las mismas CLI (REAUD-07): vc es el alias que instala el paquete vercel
             "vc": "vercel", "ntl": "netlify", "netlify-cli": "netlify", "flyctl": "fly"}
EXTENSIONES = re.compile(r"\.(?:exe|cmd|bat|ps1|com)$", re.I)
# Claves de git que ejecutan un programa o cambian el destino del push (con -c y con git config).
CONFIG_PELIGROSA = re.compile(r"^(?:alias\.|core\.(?!(?:quotepath|autocrlf|safecrlf)$)|diff\.external$|uploadpack\.|"
                              r"receivepack\.|protocol\.|filter\.|include\.|includeif\.|sequence\.editor$|"
                              r"interactive\.difffilter$|remote\..*\.(?:push|mirror|uploadpack|receivepack)$)"
                              r"|\.(?:command|helper|program|textconv|driver|sshcommand|cmd|defaultkeycommand)$", re.I)
# Ademas, escritas de forma persistente (git config): push.*, credential.*, core.* y la URL de un remoto (REAUD-03).
CONFIG_PELIGROSA_PERSISTENTE = re.compile(r"^(?:push\.|credential\.|core\.(?!(?:quotepath|autocrlf|safecrlf)$)|"
                                          r"remote\..*\.(?:url|pushurl)$)", re.I)
# Solo presentacion: con -c no tienen opinion (REAUD-09). pager.* y core.pager, solo con un valor booleano o cat.
CONFIG_PRESENTACION = re.compile(r"^(?:color\.|column\.|log\.|advice\.|i18n\.|diff\.|core\.(?:quotepath|autocrlf|safecrlf)$)",
                                 re.I)
BOOLEANOS = ("true", "false", "yes", "no", "on", "off", "1", "0", "")
SECCION_PELIGROSA = re.compile(r"^(?:alias|core|include|includeif|push|credential|remote|url|filter|protocol|uploadpack|"
                               r"receivepack|pager|sequence|gpg|diff|merge|interactive)(?:\.|\s|$)", re.I)
# Subcomandos de git (git help -a, 2.53) y lfs. Otro nombre puede ser un alias de la configuracion -> ask.
GIT_CONOCIDOS = frozenset((
    "add am annotate apply archive askpass backfill bisect blame branch bugreport bundle cat-file check-attr check-ignore "
    "check-mailmap check-ref-format checkout checkout-index cherry cherry-pick citool clean clone column commit "
    "commit-graph commit-tree config count-objects credential credential-cache credential-manager credential-store "
    "cvsexportcommit cvsimport cvsserver daemon describe diagnose diff diff-files diff-index diff-pairs diff-tree "
    "difftool fast-export fast-import fetch fetch-pack filter-branch fmt-merge-msg for-each-ref for-each-repo "
    "format-patch fsck gc get-tar-commit-id gitk grep gui hash-object help hook http-backend imap-send index-pack init "
    "instaweb interpret-trailers last-modified lfs log ls-files ls-remote ls-tree mailinfo mailsplit maintenance merge "
    "merge-base merge-file merge-index merge-one-file merge-tree mergetool mktag mktree multi-pack-index mv name-rev "
    "notes p4 pack-objects pack-redundant pack-refs patch-id prune prune-packed pull push quiltimport range-diff "
    "read-tree rebase reflog refs remote repack replace replay repo request-pull rerere reset restore rev-list rev-parse "
    "revert rm scalar send-email send-pack sh-i18n sh-setup shortlog show show-branch show-index show-ref "
    "sparse-checkout stash status stripspace submodule survey svn switch symbolic-ref tag unpack-file unpack-objects "
    "update-git-for-windows update-index update-ref update-server-info var verify-commit verify-pack verify-tag version "
    "whatchanged worktree write-tree archimport").split())
GIT_SALIDA = {"log", "diff", "show", "format-patch", "whatchanged", "diff-tree", "diff-index", "diff-files",
              "range-diff", "stash", "cherry", "shortlog", "reflog"}
GIT_REMOTO = {"fetch", "pull", "clone", "ls-remote", "archive", "submodule", "remote"}
ENVOLTORIOS = {
    # exe -> opciones que llevan valor aparte
    "env": ("-u", "--unset", "-C", "--chdir", "-S", "--split-string"),
    "sudo": ("-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U", "-T", "--user", "--group", "--host", "--prompt"),
    "doas": ("-u", "-C"),
    "nohup": (), "setsid": (), "time": (), "command": (), "builtin": (), "exec": ("-a",),
    "nice": ("-n", "--adjustment"), "stdbuf": ("-i", "-o", "-e"),
    "timeout": ("-s", "-k", "--signal", "--kill-after"),
    "xargs": ("-I", "-L", "-l", "-n", "-P", "-s", "-d", "-E", "-e", "-a", "--arg-file", "--delimiter", "--max-args",
              "--max-lines", "--max-procs", "--max-chars", "--replace", "--eof"),
}
EJECUTORES = {"npx": ("-p", "--package", "-c", "--call"), "bunx": ("-p", "--package"), "pnpx": ("-p", "--package"),
              "uvx": ("--from", "--with", "--python", "-p", "--index-url", "--index"),
              }
SUBEJECUTORES = {("npm", "exec"), ("npm", "x"), ("pnpm", "dlx"), ("pnpm", "exec"), ("yarn", "dlx"), ("yarn", "exec"),
                 ("bun", "x"), ("pipx", "run"), ("uv", "run"), ("uv", "tool"), ("poetry", "run"), ("pdm", "run")}
CON_VALOR_EJECUTOR = ("-p", "--package", "-c", "--call", "--with", "--python", "--project", "--directory", "--env-file",
                      "--from", "--index", "--index-url", "--group", "--extra", "--spec")
PS_CON_VALOR = ("windowstyle", "workingdirectory", "wd", "inputformat", "outputformat", "configurationname",
                "settingsfile", "custompipename", "psconsolefile", "version", "executionpolicy")
ESCRIBE_PS = {
    # cmdlet o alias -> (parametros con nombre que son destino, posiciones que son destino)
    "set-content": (("path", "literalpath"), (0,)), "sc": (("path", "literalpath"), (0,)),
    "add-content": (("path", "literalpath"), (0,)), "ac": (("path", "literalpath"), (0,)),
    "out-file": (("filepath", "literalpath", "path"), (0,)),
    "clear-content": (("path", "literalpath"), (0,)), "clc": (("path", "literalpath"), (0,)),
    "new-item": (("path", "name"), (0,)), "ni": (("path", "name"), (0,)),
    "remove-item": (("path", "literalpath"), (-1,)), "ri": (("path", "literalpath"), (-1,)),
    "del": (("path", "literalpath"), (-1,)), "erase": (("path", "literalpath"), (-1,)),
    "rd": (("path", "literalpath"), (-1,)), "rmdir": (("path", "literalpath"), (-1,)),
    "copy-item": (("destination",), (1,)), "cpi": (("destination",), (1,)), "copy": (("destination",), (1,)),
    "move-item": (("path", "literalpath", "destination"), (0, 1)), "mi": (("path", "literalpath", "destination"), (0, 1)),
    "move": (("path", "literalpath", "destination"), (0, 1)),
    "rename-item": (("path", "literalpath"), (0,)), "rni": (("path", "literalpath"), (0,)), "ren": (("path", "literalpath"), (0,)),
    "tee-object": (("filepath", "literalpath"), (0,)), "set-itemproperty": (("path", "literalpath"), (0,)),
    "expand-archive": (("destinationpath",), (1,)), "compress-archive": (("destinationpath",), (1,)),
}
PS_VALORES = ("value", "encoding", "itemtype", "type", "filter", "include", "exclude", "credential", "stream",
              "delimiter", "width", "inputobject", "newname", "variable", "target")

# Destinos de escritura de curl, wget, rsync y tar (REAUD-05). Opciones cortas de curl/wget que llevan valor:
# en un grupo (-sSo F, -qO F) la primera de ellas se come el resto del grupo o el siguiente token.
CURL_CORTAS_VALOR = "AbcCdDeEFHKmoPQrTtuUwxXyYz"
CURL_LARGAS_ESCRIBE = ("--output", "--dump-header", "--cookie-jar", "--trace", "--trace-ascii", "--stderr", "--libcurl",
                       "--etag-save", "--hsts", "--alt-svc")
CURL_LARGAS_VALOR = CURL_LARGAS_ESCRIBE + (
    "--output-dir", "--url", "--data", "--data-raw", "--data-binary", "--data-urlencode", "--data-ascii", "--json",
    "--header", "--user", "--user-agent", "--referer", "--request", "--form", "--form-string", "--cookie", "--cacert",
    "--capath", "--cert", "--key", "--proxy", "--proxy-user", "--max-time", "--connect-timeout", "--retry",
    "--retry-delay", "--retry-max-time", "--config", "--write-out", "--upload-file", "--range", "--variable", "--resolve",
    "--connect-to", "--etag-compare", "--time-cond", "--oauth2-bearer", "--interface", "--limit-rate", "--max-filesize",
    "--continue-at", "--quote", "--netrc-file", "--unix-socket", "--aws-sigv4", "--expect100-timeout")
WGET_CORTAS_VALOR = "eoaiBtOwQTPUDRAIXl"
WGET_LARGAS_ESCRIBE = ("--output-document", "--output-file", "--append-output", "--save-cookies")
WGET_LARGAS_VALOR = WGET_LARGAS_ESCRIBE + (
    "--directory-prefix", "--input-file", "--base", "--tries", "--wait", "--quota", "--timeout", "--user-agent",
    "--domains", "--reject", "--accept", "--include-directories", "--exclude-directories", "--level", "--execute",
    "--header", "--user", "--password", "--http-user", "--http-password", "--post-data", "--post-file", "--body-data",
    "--body-file", "--method", "--load-cookies", "--referer", "--ca-certificate", "--certificate", "--private-key",
    "--limit-rate", "--waitretry", "--cut-dirs", "--default-page", "--config", "--bind-address")
RSYNC_CON_VALOR = ("-f", "--filter", "--exclude", "--include", "--exclude-from", "--include-from", "--files-from", "-T",
                   "--temp-dir", "-B", "--block-size", "--backup-dir", "--suffix", "--port", "--password-file", "--chmod",
                   "--chown", "--partial-dir", "--compare-dest", "--link-dest", "--copy-dest", "-M", "--remote-option",
                   "--rsync-path", "--timeout", "--contimeout", "--max-size", "--min-size", "--bwlimit", "--out-format",
                   "--skip-compress", "--usermap", "--groupmap", "--address", "--iconv", "--max-delete", "--info", "--debug")
TAR_EJECUTA = ("--use-compress-program", "--to-command", "--info-script", "--new-volume-script", "--rsh-command",
               "--checkpoint-action", "--rmt-command")
TAR_LARGAS_VALOR = TAR_EJECUTA + ("--file", "--directory", "--exclude", "--exclude-from", "--files-from", "--transform",
                                  "--xform", "--owner", "--group", "--mode", "--mtime", "--newer", "--after-date",
                                  "--newer-mtime", "--blocking-factor", "--record-size", "--label", "--format", "--suffix",
                                  "--listed-incremental", "--strip-components")
# Herramientas con su propia lectura de destinos (sin la regla generica de -o/--output).
SALIDA_PROPIA = frozenset(("curl", "wget", "git", "tar", "bsdtar", "gtar", "unzip", "7z", "7za", "7zr", "7zz", "rsync", "dd"))
# Herramientas en las que -o no es un fichero de salida.
SIN_O_DE_SALIDA = frozenset(("ls", "dir", "grep", "egrep", "fgrep", "rg", "ag", "ack", "ps", "mount", "ssh", "scp", "sftp",
                             "ssh-keygen", "find", "gh", "sed", "awk", "gawk", "xargs", "jq", "yq", "cut", "pgrep", "pkill",
                             "lsof", "netstat", "ss", "du", "df", "stat", "file", "less", "more", "cat", "head", "tail",
                             "mvn", "gradle", "gradlew", "bash", "sh", "zsh", "set"))
# Metodos .NET que escriben, borran o mueven ficheros, y que argumentos son destinos (REAUD-05).
NET_ESCRIBE = {
    "file": {"writealltext": (0,), "writeallbytes": (0,), "writealllines": (0,), "appendalltext": (0,),
             "appendalllines": (0,), "appendtext": (0,), "create": (0,), "createtext": (0,), "openwrite": (0,),
             "open": (0,), "delete": (0,), "setattributes": (0,), "writealltextasync": (0,), "writeallbytesasync": (0,),
             "writealllinesasync": (0,), "appendalltextasync": (0,), "appendalllinesasync": (0,), "copy": (1,),
             "move": (0, 1), "replace": (0, 1, 2), "createsymboliclink": (0,), "encrypt": (0,), "decrypt": (0,)},
    "directory": {"delete": (0,), "createdirectory": (0,), "move": (0, 1), "createsymboliclink": (0,)},
    "streamwriter": {"new": (0,)}, "filestream": {"new": (0,)},
}
NET_LLAMADA = re.compile(r"\[\s*(?:System\.)?IO\.(File|Directory|StreamWriter|FileStream)\s*\]\s*::\s*([A-Za-z]+)\s*\(|"
                         r"\bNew-Object\s+(?:-TypeName\s+)?(?:System\.)?IO\.(StreamWriter|FileStream)\b\s*(?:-ArgumentList\s*)?\(",
                         re.I | RX)


def nombre_exe(s):
    b = s.replace("\\", "/").rstrip("/").split("/")[-1].lower()
    b = EXTENSIONES.sub("", b)
    return ALIAS_EXE.get(b, b)


def sin_version(s):
    """'vercel@39' -> 'vercel'; '@scope/paq@1' -> '@scope/paq'."""
    return re.sub(r"(?<=.)@[^/@]*$", "", s)


def decodificar_b64(s):
    """Base64 de -EncodedCommand (UTF-16LE), tolerante como Buffer.from(s, 'base64') de Node."""
    limpio = re.sub(r"[^A-Za-z0-9+/]", "", s.replace("-", "+").replace("_", "/"))
    limpio = limpio[:len(limpio) - len(limpio) % 4 if len(limpio) % 4 == 1 else len(limpio)]
    datos = base64.b64decode(limpio + "=" * (-len(limpio) % 4))
    return datos[:len(datos) // 2 * 2].decode("utf-16-le", "surrogatepass")


def larga(tok, nombres, minimo=4):
    """Opcion larga que git o PowerShell aceptan abreviada: '--force-w' -> '--force-with-lease'."""
    nombre = tok.split("=", 1)[0]
    if nombre in nombres:
        return nombre
    if len(nombre) >= minimo:
        for n in nombres:
            if n.startswith(nombre):
                return n
    return None


def clasificar_config(clave, valor, persistente):
    """Clave de git -> 'peligrosa' (ejecuta un programa o cambia el destino del push), 'inocua' (solo
    presentacion: color, columnas, log, diff, core.quotepath...) u 'otra'."""
    c, v = clave.lower(), (valor or "").strip().lower()
    if c.startswith("pager.") or c == "core.pager":
        if v in BOOLEANOS or (c == "core.pager" and v == "cat"):
            return "peligrosa" if persistente and c == "core.pager" else "inocua"
        return "peligrosa"
    if CONFIG_PELIGROSA.search(c):
        return "peligrosa"
    if c == "push.default" and v in ("matching", "upstream", "tracking"):
        return "peligrosa"
    if persistente and CONFIG_PELIGROSA_PERSISTENTE.search(c):
        return "peligrosa"
    return "inocua" if CONFIG_PRESENTACION.search(c) else "otra"


def partir_argumentos(t):
    """Argumentos de una llamada a un metodo de PowerShell ('a', "b", (x, y)) partidos por las comas de primer nivel."""
    out, prof, cur, i, n = [], 0, "", 0, len(t)
    while i < n:
        c = t[i]
        if c in "'\"":
            j = i + 1
            while j < n:
                if t[j] == c:
                    if j + 1 < n and t[j + 1] == c:
                        j += 2
                        continue
                    break
                j += 2 if (c == '"' and t[j] == "`") else 1
            cur += t[i:j + 1]
            i = j + 1
            continue
        if c in "([{":
            prof += 1
        elif c in ")]}":
            prof -= 1
        elif c == "," and prof == 0:
            out.append(cur.strip())
            cur, i = "", i + 1
            continue
        cur += c
        i += 1
    if cur.strip():
        out.append(cur.strip())
    return out


def _ps_param(a):
    """'-Destination' / '-dest' -> 'dest' (sin guion, en minusculas, sin ':valor')."""
    return a[1:].split(":", 1)[0].lower() if a.startswith("-") and len(a) > 1 else None


def _ps_prefijo(p, nombres):
    for n in nombres:
        if n == p or (len(p) >= 2 and n.startswith(p)):
            return n
    return None


class Analisis:
    """Recorre el comando (y lo que ejecuta dentro) y junta comandos simples, destinos de escritura,
    construcciones que ejecutan otro comando y las decisiones de la politica git."""

    def __init__(self, raiz, cwd, rama, reglas):
        self.raiz, self.cwd, self.rama, self.reglas = raiz, cwd, rama, reglas
        self.simples, self.segmentos, self.candidatos, self.construcciones = [], [], [], []
        self.destinos, self.argumentos = [], []
        self.extracciones = []  # carpetas donde se extrae un archivo (tar -x, unzip, 7z x): contenido desconocido
        self.vars, self.exportadas, self.ramas = {}, {}, {}
        self.ultimo = None
        self.entrada_desconocida = None  # comando que recibe argumentos que el guard no ve (xargs, find -exec {})

    # ---------------------------------------------------- utilidades
    def construccion(self, tipo):
        if tipo not in self.construcciones:
            self.construcciones.append(tipo)

    def valor(self, nombre, entorno=None):
        if nombre.startswith("ps:"):
            if nombre == "ps:null":
                return ""
            return self.vars.get(nombre)
        if entorno is not None and nombre in entorno:
            return entorno[nombre]
        if nombre in self.vars:
            return self.vars[nombre]
        if nombre in self.exportadas:
            return self.exportadas[nombre]
        return os.environ.get(nombre) if re.match(r"^[A-Za-z_]", nombre) else None

    def resolver(self, tok, entorno=None):
        din, var = False, False
        partes = re.split(r"\x00(V[^\x00]*|S)\x00", tok["s"])
        out = partes[0]
        for k in range(1, len(partes), 2):
            p = partes[k]
            if p == "S":
                din = True
                out += "$(...)"
            else:
                var = True
                v = self.valor(p[1:], entorno)
                if v is None:
                    din = True
                    out += "$" + p[1:].replace("ps:", "")
                else:
                    out += v
            out += partes[k + 1]
        return {"s": out, "g": tok["g"], "din": din, "var": var}

    def rama_de(self, dir_git):
        d = self.cwd if dir_git is None else self.unir(self.cwd, dir_git)
        clave = normalizar_ruta(d, "", None).lower()
        if clave in self.ramas:
            return self.ramas[clave]
        return self.rama(d)

    def unir(self, base, rel):
        rel = rel.replace("\\", "/")
        return rel if _es_absoluta(rel) else (base or "").replace("\\", "/").rstrip("/") + "/" + rel

    def metodos_net(self, texto):
        """[IO.File]::WriteAllText('ruta', ...), Copy, Move, Delete, [IO.Directory]::..., StreamWriter y FileStream:
        los argumentos que son destino cuentan como escrituras del comando (REAUD-05)."""
        for m in NET_LLAMADA.finditer(texto):
            clase = (m.group(1) or m.group(3) or "").lower()
            indices = NET_ESCRIBE.get(clase, {}).get((m.group(2) or "new").lower())
            if not indices:
                continue
            fin = buscar_cierre(texto, m.end(), "(", ")", "ps")
            argumentos = partir_argumentos(texto[m.end():fin])
            for k in indices:
                if k >= len(argumentos):
                    continue
                trozos = Troceador(argumentos[k], "ps").trocear()
                toks = trozos[0]["tk"] if len(trozos) == 1 and not trozos[0]["subs"] else []
                if len(toks) == 1:
                    r = self.resolver(toks[0])
                    self._destino(r["s"], r["din"], ps=True)
                else:
                    self._destino(argumentos[k], True, ps=True)

    # ---------------------------------------------------- recorrido
    def analizar(self, texto, modo, prof):
        if prof > PROF_MAX:
            self.construccion("anidamiento demasiado profundo")
            return
        tuberia = False
        if modo == "ps":
            self.metodos_net(texto)
        for seg in Troceador(texto, modo).trocear():
            self.segmentos.append(seg["texto"].strip())
            self.segmento(seg, modo, prof, tuberia)
            tuberia = seg["sep"] == "|"

    def segmento(self, seg, modo, prof, tuberia):
        for sub in seg["subs"]:
            if sub["fuerza"] and not re.match(r"^\s*cat\s*<<-?\s*(['\"])[^'\"]+\1\s*\n", sub["texto"]):
                self.construccion(sub["tipo"])
            self.analizar(sub["texto"], sub["modo"], prof + 1)
        if modo == "ps":
            m = re.match(r"^\s*\$(env:)?([A-Za-z_][A-Za-z0-9_]*)\s*[+]?=\s*(.*)$", seg["texto"], re.S | re.I | RX)
            if m:
                derecha = m.group(3).strip()
                trozos = Troceador(derecha, "ps").trocear()
                literal = len(trozos) == 1 and len(trozos[0]["tk"]) == 1 and not trozos[0]["subs"] \
                    and re.match(r"^(?:'|\"|\$|\d|-?\d)", derecha) is not None
                val = None
                if literal:
                    r = self.resolver(trozos[0]["tk"][0])
                    val = None if r["din"] else r["s"]
                elif derecha:
                    self.analizar(derecha, "ps", prof + 1)
                if m.group(1):
                    self.exportadas[m.group(2)] = val
                else:
                    self.vars["ps:" + m.group(2).lower()] = val
                return
        toks = [self.resolver(t) for t in seg["tk"]]
        redirs = [[op, self.resolver(t)] for op, t in seg["redir"]]
        stdin = seg["stdin"]["s"] if seg["stdin"] is not None else None
        self.simple(toks, redirs, modo, prof, stdin, tuberia, seg["llamada"])

    def simple(self, toks, redirs, modo, prof, stdin, tuberia, llamada):
        entorno = {}
        k = 0
        while k < len(toks):
            s = toks[k]["s"]
            if modo == "bash" and not llamada and re.match(r"^[A-Za-z_][A-Za-z0-9_]*\+?=", s, RX):
                nombre, val = s.split("=", 1)
                entorno[nombre.rstrip("+")] = None if toks[k]["din"] else val
                k += 1
                continue
            if s.lower() in PALABRAS_CLAVE and not llamada:
                k += 1
                continue
            break
        for _, t in redirs:
            self.argumentos.append((t, modo))
        self.destinos += [(t, self.cwd) for op, t in redirs if op not in ("<", "<<<")]
        if k >= len(toks):
            if modo == "bash":
                self.vars.update(entorno)
            return
        exe_tok = toks[k]
        if exe_tok["var"] and (modo != "ps" or llamada):
            self.construccion("variable en posicion de comando")
        elif modo == "ps" and (exe_tok["var"] or exe_tok["din"]):
            return
        if exe_tok["din"]:
            if not exe_tok["var"]:
                self.construccion("comando calculado en posicion de comando")
            self.simples.append({"texto": " ".join(t["s"] for t in toks[k:]), "entorno": self.entorno_con(entorno)})
            return
        exe = nombre_exe(exe_tok["s"])
        args = toks[k + 1:]
        for t in args:
            self.argumentos.append((t, modo))
        if modo == "ps" and exe == "." and not llamada:
            self.construccion("source")
        # envoltorios: env, sudo, timeout, xargs... -> el comando que llevan dentro
        if exe in ENVOLTORIOS:
            j = self.saltar_envoltorio(exe, args, entorno, modo, prof)
            if j is None:
                return
            if j < len(args):
                if exe == "env":
                    self.construccion("env con un comando")
                self.registrar(exe, args, entorno, exe_tok["s"])
                if exe == "xargs":
                    self.xargs(args, j, modo, prof, stdin, tuberia)
                else:
                    self.simple(args[j:], [], modo, prof, stdin, tuberia, False)
                return
        if exe in EJECUTORES or (args and (exe, args[0]["s"].lower()) in SUBEJECUTORES):
            j = self.saltar_ejecutor(exe, args, modo, prof)
            self.registrar(exe, args, entorno, exe_tok["s"])
            if j is not None and j < len(args):
                resto = [dict(args[j], s=sin_version(args[j]["s"]))] + args[j + 1:]
                self.simple(resto, [], modo, prof, None, False, False)
            return
        self.registrar(exe, args, entorno, exe_tok["s"])
        self.especificos(exe, args, entorno, modo, prof, stdin, tuberia)
        self.ultimo = (exe, args)

    def entorno_con(self, entorno):
        e = dict(self.exportadas)
        e.update(entorno)
        return e

    def registrar(self, exe, args, entorno, original=None):
        """Comando simple ya normalizado (exe sin ruta ni extension); y tal cual, si el exe llevaba ruta."""
        resto = [t["s"] for t in args]
        self.simples.append({"texto": " ".join([exe] + resto), "entorno": self.entorno_con(entorno), "exe": exe,
                             "programa": exe, "args": list(args)})
        if original and original != exe:
            self.simples.append({"texto": " ".join([original] + resto), "entorno": self.entorno_con(entorno), "exe": exe,
                                 "programa": original, "args": list(args)})
        expandidos = self.expandir_args(args)
        if expandidos is not None:
            self.simples.append({"texto": " ".join([exe] + [t["s"] for t in expandidos]), "entorno": self.entorno_con(entorno),
                                 "exe": exe, "programa": exe, "args": expandidos, "variante": "comodines"})

    def expandir_args(self, args):
        """Variante del comando con los comodines del shell expandidos contra el disco (como bash) y las rutas con
        '..' normalizadas, para que las reglas vean la ruta real ('test/../integration_tes?/x' ->
        'integration_test/x'; REAUD-01). None si no cambia nada. Un comodin que no casa con nada llega tal cual
        al programa (bash sin nullglob), que es lo que ya ven las reglas."""
        out, cambia = [], False
        for t in args:
            s = t["s"]
            if t["din"]:
                out.append(t)
                continue
            m = re.match(r"^(--?[\w.-]+=)(.*)$", s, re.S | RX)
            pref, valor = (m.group(1), m.group(2)) if m else ("", s)
            if t.get("g") and COMODIN.search(valor):
                rutas = expandir_comodin(valor, self.cwd)
                if rutas:
                    out += [dict(t, s=pref + (normalizar_ruta(r, self.raiz, self.cwd) if PUNTO_PUNTO.search(r) else r), g=False)
                            for r in rutas]
                    cambia = True
                    continue
            elif PUNTO_PUNTO.search(valor):
                out.append(dict(t, s=pref + normalizar_ruta(valor, self.raiz, self.cwd)))
                cambia = True
                continue
            out.append(t)
        return out if cambia else None

    def saltar_envoltorio(self, exe, args, entorno, modo, prof):
        """Indice del comando envuelto dentro de args, o None si el envoltorio no ejecuta nada."""
        con_valor = ENVOLTORIOS[exe]
        j = 0
        while j < len(args):
            a = args[j]["s"]
            if a == "--":
                return j + 1
            if exe == "env" and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", a, RX):
                nombre, val = a.split("=", 1)
                entorno[nombre] = None if args[j]["din"] else val
                j += 1
                continue
            if a.startswith("-") and len(a) > 1:
                if exe == "command" and a in ("-v", "-V"):
                    return None
                if exe == "env" and a in ("-S", "--split-string") and j + 1 < len(args):
                    self.construccion("env -S")
                    self.analizar(args[j + 1]["s"], "bash", prof + 1)
                    return None
                j += 2 if a in con_valor else 1
                continue
            if exe == "timeout":
                return j + 1
            return j
        return j

    def xargs(self, args, j, modo, prof, stdin, tuberia):
        """xargs CMD: si se sabe lo que llega por la entrada (echo/printf en la tuberia o <<<), se analiza el comando
        con esos argumentos; si no, el motivo dice lo que se ejecutaria (REAUD-12)."""
        interior = args[j:]
        reemplazo, de_fichero, k = None, False, 0
        while k < j:
            s = args[k]["s"]
            if s in ("-I", "--replace") and k + 1 < j:
                reemplazo, k = args[k + 1]["s"], k + 2
                continue
            if s.startswith("-I") and len(s) > 2:
                reemplazo = s[2:]
            elif s == "-i" or s == "--replace":
                reemplazo = "{}"
            elif s.startswith("-i") or s.startswith("--replace="):
                reemplazo = s.split("=", 1)[1] if "=" in s else s[2:]
            elif s in ("-a", "--arg-file") or s.startswith("--arg-file=") or (s.startswith("-a") and len(s) > 2):
                de_fichero = True
            k += 1
        palabras = None
        if not de_fichero:
            if stdin is not None:
                palabras = stdin.split()
            elif tuberia and self.ultimo and self.ultimo[0] in ("echo", "printf", "write-output", "write-host") \
                    and not any(t["din"] for t in self.ultimo[1]):
                texto = " ".join(t["s"] for t in self.ultimo[1] if not (self.ultimo[0] == "echo" and t["s"] in ("-n", "-e")))
                palabras = re.sub(r"\\[ntr]", " ", texto).split()
        texto_cmd = " ".join(t["s"] for t in interior)
        if palabras is None:
            self.construccion(f"xargs ejecutaria '{texto_cmd} <argumentos de la entrada>'")
            antes = self.entrada_desconocida
            self.entrada_desconocida = f"xargs ejecutaria '{texto_cmd} <argumentos de la entrada>'"
            self.simple(interior, [], modo, prof, stdin, tuberia, False)
            self.entrada_desconocida = antes
            return
        self.construccion("xargs con un comando")
        nuevo = {"g": False, "din": False, "var": False}
        if reemplazo:
            for w in palabras[:20]:
                self.simple([dict(t, s=t["s"].replace(reemplazo, w)) for t in interior], [], modo, prof, stdin, tuberia, False)
        else:
            self.simple(interior + [dict(nuevo, s=w) for w in palabras[:50]], [], modo, prof, stdin, tuberia, False)

    def saltar_ejecutor(self, exe, args, modo, prof):
        j = 0 if exe in EJECUTORES else 1
        if exe == "uv" and j < len(args) and args[j - 1]["s"].lower() == "tool":
            if j < len(args) and args[j]["s"].lower() == "run":
                j += 1
            else:
                return None
        while j < len(args):
            a = args[j]["s"]
            if a == "--":
                return j + 1
            if a.startswith("-"):
                nombre = a.split("=", 1)[0]
                if nombre in ("-c", "--call") and exe in ("npx", "npm") and j + 1 < len(args):
                    self.construccion(f"{exe} -c")
                    self.analizar(args[j + 1]["s"], modo if modo != "cmd" else "bash", prof + 1)
                    return None
                j += 2 if (nombre in CON_VALOR_EJECUTOR and "=" not in a) else 1
                continue
            return j
        return None

    # ---------------------------------------------------- comandos con lectura propia
    def especificos(self, exe, args, entorno, modo, prof, stdin, tuberia):
        if exe in SHELLS:
            self.shell(exe, args, prof, stdin, tuberia)
        elif exe == "cmd":
            for j, a in enumerate(args):
                if a["s"].lower() in ("/c", "/k", "/r"):
                    self.construccion("cmd /c")
                    self.analizar(" ".join(x["s"] for x in args[j + 1:]), "cmd", prof + 1)
                    return
            if stdin is not None or tuberia:
                self.construccion("cmd que lee comandos de la entrada")
        elif exe in POWERSHELL:
            self.powershell(exe, args, prof, stdin, tuberia)
        elif exe == "eval" and modo == "bash":
            self.construccion("eval")
            self.analizar(" ".join(a["s"] for a in args), "bash", prof + 1)
        elif exe in ("source", ".") and modo != "ps":
            self.construccion("source")
        elif exe in ("iex", "invoke-expression"):
            self.construccion("Invoke-Expression")
            resto = [a for a in args if not (_ps_param(a["s"]) and "command".startswith(_ps_param(a["s"]) or "-"))]
            self.analizar(" ".join(a["s"] for a in resto), "ps", prof + 1)
            if not resto and tuberia:
                self.construccion("Invoke-Expression con la entrada")
        elif exe in ("start-process", "saps", "start") or (exe in ("invoke-command", "icm", "start-job", "sajb")):
            self.construccion(exe)
            if exe in ("start-process", "saps", "start"):
                self.start_process(args, modo, prof)
        elif exe == "find":
            for j, a in enumerate(args):
                if a["s"] in ("-exec", "-execdir", "-ok", "-okdir"):
                    fin = next((x for x in range(j + 1, len(args)) if args[x]["s"] in (";", "+")), len(args))
                    interior = args[j + 1:fin]
                    antes = self.entrada_desconocida
                    if any("{}" in x["s"] for x in interior):
                        self.entrada_desconocida = (f"find {a['s']} ejecutaria '{' '.join(x['s'] for x in interior)}' "
                                                    "con cada fichero que encuentre")
                    self.simple(interior, [], "bash", prof + 1, None, False, False)
                    self.entrada_desconocida = antes
        elif exe == "git":
            self.git(args, modo)
        elif exe == "gh":
            self.gh(args)
        elif exe in ("cd", "pushd", "chdir", "set-location", "sl", "push-location"):
            pos = [a for a in args if not a["s"].startswith("-")]
            if pos and not pos[0]["din"]:
                self.cwd = self.unir(self.cwd, pos[0]["s"])
        elif exe in ("export", "declare", "typeset", "local", "readonly") and modo == "bash":
            exporta = exe == "export" or any(a["s"].startswith("-") and "x" in a["s"] for a in args)
            for a in args:
                m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(?:=(.*))?$", a["s"], re.S | RX)
                if not m:
                    continue
                if m.group(2) is not None:
                    self.vars[m.group(1)] = None if a["din"] else m.group(2)
                if exporta:
                    self.exportadas[m.group(1)] = self.vars.get(m.group(1), os.environ.get(m.group(1)))
        elif exe == "unset" and modo == "bash":
            for a in args:
                self.vars.pop(a["s"], None)
                self.exportadas[a["s"]] = None
        elif exe == "set" and modo == "cmd" and args:
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", " ".join(a["s"] for a in args), re.S | RX)
            if m:
                self.exportadas[m.group(1)] = m.group(2)
        self.escrituras(exe, args, modo)

    def shell(self, exe, args, prof, stdin, tuberia):
        j, con_c = 0, False
        while j < len(args):
            a = args[j]["s"]
            if a in ("-o", "+o", "-O", "+O", "--rcfile", "--init-file"):
                j += 2
                continue
            if a == "--":
                j += 1
                break
            if (a.startswith("-") or a.startswith("+")) and len(a) > 1:
                if (not a.startswith("--") and "c" in a[1:]) or a == "--command":
                    con_c = True
                j += 1
                continue
            break
        if con_c:
            self.construccion(f"{exe} -c")
            if j < len(args):
                self.analizar(args[j]["s"], "bash", prof + 1)
            return
        if j >= len(args):
            if stdin is not None:
                self.construccion(f"{exe} con comandos por la entrada")
                self.analizar(stdin, "bash", prof + 1)
            elif tuberia:
                self.construccion(f"{exe} que lee comandos de una tuberia")
                if self.ultimo and self.ultimo[0] in ("echo", "printf", "write-output", "write-host"):
                    self.analizar(" ".join(a["s"] for a in self.ultimo[1]), "bash", prof + 1)

    def powershell(self, exe, args, prof, stdin, tuberia):
        j = 0
        while j < len(args):
            a = args[j]["s"]
            if (a.startswith("-") or a.startswith("/")) and len(a) > 1:
                o = a.lstrip("-/").split(":", 1)[0].lower()
                if o in ("e", "ec") or (len(o) >= 2 and "encodedcommand".startswith(o)):
                    self.construccion(f"{exe} -EncodedCommand")
                    if j + 1 < len(args):
                        self.analizar(decodificar_b64(args[j + 1]["s"]), "ps", prof + 1)
                    return
                if o in ("c", "cwa") or (len(o) >= 2 and ("command".startswith(o) or "commandwithargs".startswith(o))):
                    self.construccion(f"{exe} -Command")
                    resto = " ".join(x["s"] for x in args[j + 1:])
                    if resto.strip() == "-":
                        self.construccion(f"{exe} que lee comandos de la entrada")
                    else:
                        self.analizar(resto, "ps", prof + 1)
                    return
                if o in ("f",) or (len(o) >= 2 and "file".startswith(o)):
                    return
                if _ps_prefijo(o, PS_CON_VALOR) is not None or o in ("ep", "ex", "v", "w", "if", "of"):
                    j += 2
                    continue
                j += 1
                continue
            if a.lower().endswith(".ps1"):
                return
            self.construccion(f"{exe} con un comando")
            self.analizar(" ".join(x["s"] for x in args[j:]), "ps", prof + 1)
            return
        if stdin is not None or tuberia:
            self.construccion(f"{exe} que lee comandos de la entrada")

    def start_process(self, args, modo, prof):
        fichero, lista, pos, j = None, [], [], 0
        while j < len(args):
            a = args[j]["s"]
            p = _ps_param(a) if modo == "ps" else None
            if p is not None:
                nombre = _ps_prefijo(p, ("filepath", "argumentlist", "workingdirectory", "verb", "windowstyle",
                                         "redirectstandardoutput", "redirectstandardinput", "redirectstandarderror",
                                         "credential", "wait", "nonewwindow", "passthru", "loaduserprofile", "usenewenvironment"))
                if nombre == "filepath" and j + 1 < len(args):
                    fichero = args[j + 1]["s"]
                    j += 2
                elif nombre == "argumentlist":
                    j += 1
                    while j < len(args) and not args[j]["s"].startswith("-"):
                        lista.append(args[j]["s"])
                        j += 1
                elif nombre in ("wait", "nonewwindow", "passthru", "loaduserprofile", "usenewenvironment"):
                    j += 1
                else:
                    j += 2
                continue
            if modo != "ps" and (a.startswith("/") or a == ""):
                j += 1
                continue
            pos.append(a)
            j += 1
        if fichero is None and pos:
            fichero, pos = pos[0], pos[1:]
        if fichero:
            self.analizar(" ".join([fichero] + lista + pos), "ps" if modo == "ps" else "cmd", prof + 1)

    # ---------------------------------------------------- escrituras
    def escrituras(self, exe, args, modo):
        if modo == "ps" and (exe in ESCRIBE_PS or exe in ("rm", "mv", "cp")):
            self.escrituras_ps(exe, args)
            return
        cwd = self.cwd

        def opcion(s):
            return (s.startswith("-") and s != "-") or (modo == "cmd" and s.startswith("/"))

        pos = [a for a in args if not opcion(a["s"])]

        def anadir(lista):
            for a in lista:
                self.destinos.append((a, cwd))

        if exe == "tee":
            anadir(pos)
        elif exe in ("cp", "install", "ln", "copy", "xcopy", "robocopy"):
            objetivo = None
            for j, a in enumerate(args):
                if a["s"] in ("-t", "--target-directory") and j + 1 < len(args):
                    objetivo = args[j + 1]
                elif a["s"].startswith("--target-directory="):
                    objetivo = {"s": a["s"].split("=", 1)[1], "din": a["din"]}
            if objetivo is not None:
                anadir([objetivo])
            elif exe == "robocopy" and len(pos) >= 2:
                anadir([pos[1]])
            elif len(pos) >= 2:
                anadir([pos[-1]])
        elif exe in ("mv", "move"):
            if len(pos) >= 2:
                anadir(pos)
        elif exe in ("rm", "rmdir", "unlink", "shred", "touch", "del", "erase", "rd"):
            anadir(pos)
        elif exe == "truncate":
            anadir([a for a in pos if not re.match(r"^[-+<>/%]?\d+[KMGTkmgt]?[Bb]?$", a["s"])])
        elif exe in ("sed", "perl"):
            in_situ = any(a["s"].startswith("--in-place") or (re.match(r"^-[A-Za-z]*i", a["s"]) is not None)
                          for a in args)
            if in_situ:
                con_script = False
                ficheros, j = [], 0
                while j < len(args):
                    s = args[j]["s"]
                    if s in ("-e", "-f", "--expression", "--file") or (re.match(r"^-[A-Za-z]*e$", s) and exe == "perl"):
                        con_script = True
                        j += 2
                        continue
                    if (s == "-l" and exe == "sed") or (s == "-E" and exe == "perl"):
                        j += 2
                        continue
                    if not opcion(s):
                        ficheros.append(args[j])
                    j += 1
                anadir(ficheros if con_script else ficheros[1:])
        elif exe == "dd":
            anadir([{"s": a["s"][3:], "din": a["din"]} for a in args if a["s"].startswith("of=")])
        elif exe in ("curl", "wget"):
            self.descarga(exe, args)
        elif exe == "rsync":
            self.rsync(args)
        elif exe in ("tar", "bsdtar", "gtar"):
            self.tar(args)
        elif exe == "unzip":
            self.unzip(args)
        elif exe in ("7z", "7za", "7zr", "7zz"):
            self.siete_z(args)
        if exe not in SALIDA_PROPIA:
            self.salida_generica(exe, args)

    # destinos de herramientas de descarga, copia y archivo (REAUD-05, REAUD-06)
    def _destino(self, s, din, cwd=None, ps=False):
        self.destinos.append(({"s": s, "din": din, "ps": ps}, cwd or self.cwd))

    def _carpeta_extraida(self, tok, cwd=None):
        """Carpeta donde se extrae un archivo de contenido desconocido: cuenta si es o contiene una ruta protegida
        (tambien la raiz del repo)."""
        self.extracciones.append((tok, cwd or self.cwd))

    def descarga(self, exe, args):
        """curl -o/-D/-c/--output... (tambien agrupadas: -sSo, -sSoFICHERO), -O con el nombre de la URL y
        --output-dir; wget -O/-o/-a, -P y el nombre de la URL por defecto."""
        if exe == "curl":
            cortas_valor, escribe_cortas = CURL_CORTAS_VALOR, "oDc"
            largas_valor, escribe_largas, dir_largas = CURL_LARGAS_VALOR, CURL_LARGAS_ESCRIBE, ("--output-dir",)
        else:
            cortas_valor, escribe_cortas = WGET_CORTAS_VALOR, "Ooa"
            largas_valor, escribe_largas, dir_largas = WGET_LARGAS_VALOR, WGET_LARGAS_ESCRIBE, ("--directory-prefix",)
        salidas, urls, carpeta, remoto, cabecera, recursivo, j = [], [], None, exe == "wget", False, False, 0
        while j < len(args):
            a = args[j]
            s = a["s"]
            if s.startswith("--") and len(s) > 2:
                nombre, igual, val = s.partition("=")
                nombre = nombre.lower()
                lleva = bool(igual) or nombre in largas_valor
                v = {"s": val, "din": a["din"]} if igual else (args[j + 1] if lleva and j + 1 < len(args) else None)
                if v is not None and nombre in escribe_largas:
                    salidas.append(v)
                elif v is not None and nombre in dir_largas:
                    carpeta = v
                elif v is not None and nombre == "--url":
                    urls.append(v)
                elif nombre in ("--remote-name", "--remote-name-all"):
                    remoto = True
                elif nombre == "--remote-header-name":
                    cabecera = True
                elif nombre in ("--recursive", "--mirror"):
                    recursivo = True
                j += 1 if (igual or not lleva) else 2
                continue
            if s.startswith("-") and len(s) > 1:
                if exe == "wget" and s.startswith("-n"):
                    j += 1
                    continue
                k, salto = 1, 1
                while k < len(s):
                    letra = s[k]
                    if letra in cortas_valor:
                        resto = s[k + 1:]
                        v = {"s": resto, "din": a["din"]} if resto else (args[j + 1] if j + 1 < len(args) else None)
                        salto = 1 if resto else 2
                        if v is not None and letra in escribe_cortas:
                            salidas.append(v)
                        elif v is not None and letra == "P" and exe == "wget":
                            carpeta = v
                        break
                    if letra == "O" and exe == "curl":
                        remoto = True
                    elif letra == "J" and exe == "curl":
                        cabecera = True
                    elif letra in "rm" and exe == "wget":
                        recursivo = True
                    k += 1
                j += salto
                continue
            urls.append(a)
            j += 1
        if exe == "wget" and self._wget_documento(args):
            remoto = False
        base = self.cwd if carpeta is None else self.unir(self.cwd, carpeta["s"])
        if carpeta is not None and carpeta["din"]:
            self._destino(carpeta["s"], True)
        for v in salidas:
            if v["s"] != "-":
                self._destino(v["s"], v["din"], base if exe == "curl" else self.cwd)
        if remoto or cabecera:
            for u in urls:
                nombre = re.sub(r"[?#][\s\S]*", "", u["s"]).rstrip("/").split("/")[-1] if "/" in u["s"] else ""
                if cabecera or recursivo or not nombre or u["din"]:
                    self._destino(".", False, base)
                else:
                    self._destino(nombre, False, base)

    def _wget_documento(self, args):
        """wget con -O/--output-document: el nombre de la URL ya no cuenta."""
        for a in args:
            s = a["s"]
            if s.startswith("--output-document") or (s.startswith("-") and not s.startswith("--")
                                                      and not s.startswith("-n") and "O" in s[1:]):
                return True
        return False

    def rsync(self, args):
        pos, j = [], 0
        while j < len(args):
            a = args[j]
            s = a["s"]
            nombre = s.split("=", 1)[0]
            if nombre in ("-e", "--rsh"):
                v = s.split("=", 1)[1] if "=" in s else (args[j + 1]["s"] if j + 1 < len(args) else "")
                self.construccion("rsync -e")
                self.analizar(v, "bash", 1)
                j += 1 if "=" in s else 2
                continue
            if nombre == "--log-file" or nombre == "--write-batch" or nombre == "--only-write-batch":
                v = {"s": s.split("=", 1)[1], "din": a["din"]} if "=" in s else (args[j + 1] if j + 1 < len(args) else None)
                if v is not None:
                    self._destino(v["s"], v["din"])
                j += 1 if "=" in s else 2
                continue
            if s.startswith("-") and len(s) > 1:
                j += 2 if (nombre in RSYNC_CON_VALOR and "=" not in s) else 1
                continue
            pos.append(a)
            j += 1
        if len(pos) >= 2 and not re.match(r"^(?:[^/\\:]{2,}:|[^/\\]*::|rsync://)", pos[-1]["s"]):
            self._destino(pos[-1]["s"], pos[-1]["din"])

    def tar(self, args):
        modo, ficheros, carpeta, a_salida, j = "", [], None, False, 0
        letras_valor = "fCbTXgKNVLIF"
        primera = True
        while j < len(args):
            a = args[j]
            s = a["s"]
            if s.startswith("--") and len(s) > 2:
                nombre, igual, val = s.partition("=")
                lleva = bool(igual) or nombre in TAR_LARGAS_VALOR
                v = {"s": val, "din": a["din"]} if igual else (args[j + 1] if lleva and j + 1 < len(args) else None)
                if nombre in ("--extract", "--get"):
                    modo = "x"
                elif nombre in ("--create", "--append", "--update", "--catenate", "--concatenate"):
                    modo = "c"
                elif nombre in ("--list", "--diff", "--compare", "--test-label"):
                    modo = modo or "t"
                elif nombre in ("--to-stdout",):
                    a_salida = True
                elif nombre == "--file" and v is not None:
                    ficheros.append(v)
                elif nombre == "--directory" and v is not None:
                    carpeta = v
                elif nombre in TAR_EJECUTA:
                    self.construccion(f"tar {nombre}")
                j += 1 if (igual or not lleva) else 2
                continue
            if (s.startswith("-") and len(s) > 1) or (primera and re.match(r"^[A-Za-z]+$", s) and not s.startswith("-")):
                letras = s[1:] if s.startswith("-") else s
                pendientes = []
                for k, letra in enumerate(letras):
                    if letra in "xcrutAd":
                        modo = "x" if letra == "x" else ("c" if letra in "cruA" else (modo or "t"))
                    elif letra == "O":
                        a_salida = True
                    elif letra in letras_valor:
                        if s.startswith("-") and k + 1 < len(letras):
                            pendientes.append((letra, {"s": letras[k + 1:], "din": a["din"]}))
                            break
                        pendientes.append((letra, None))
                        if s.startswith("-"):
                            break
                j += 1
                for letra, v in pendientes:
                    if v is None:
                        v = args[j] if j < len(args) else None
                        j += 1
                    if v is None:
                        continue
                    if letra == "f":
                        ficheros.append(v)
                    elif letra == "C":
                        carpeta = v
                    elif letra in "IF":
                        self.construccion(f"tar -{letra}")
                primera = False
                continue
            primera = False
            j += 1
        if modo == "c":
            for v in ficheros:
                if v["s"] != "-":
                    self._destino(v["s"], v["din"])
        elif modo == "x" and not a_salida:
            self._carpeta_extraida(carpeta or {"s": ".", "din": False})

    def unzip(self, args):
        carpeta, j, lee = None, 0, False
        while j < len(args):
            s = args[j]["s"]
            if s == "-d":
                carpeta = args[j + 1] if j + 1 < len(args) else None
                j += 2
                continue
            if s.startswith("-d") and len(s) > 2:
                carpeta = {"s": s[2:], "din": args[j]["din"]}
            elif s.startswith("-") and re.search(r"[ltvpzcZ]", s[1:]):
                lee = True
            j += 1
        if not lee:
            self._carpeta_extraida(carpeta or {"s": ".", "din": False})

    def siete_z(self, args):
        pos = [a for a in args if not a["s"].startswith("-")]
        carpeta = next(({"s": a["s"][2:], "din": a["din"]} for a in args if a["s"].lower().startswith("-o")), None)
        if not pos:
            return
        orden = pos[0]["s"].lower()
        if orden in ("x", "e") and not any(a["s"].lower() == "-so" for a in args):
            self._carpeta_extraida(carpeta or {"s": ".", "din": False})
        elif orden in ("a", "u", "d", "rn") and len(pos) > 1:
            self._destino(pos[1]["s"], pos[1]["din"])

    def salida_generica(self, exe, args):
        """-o FICHERO, --output, --outputFile (tambien --outputFile.json=), --output-file, --out-file, --outFile,
        --outDir... de cualquier herramienta (npx eslint -o, vitest --outputFile, tsc --outFile): solo cuentan si
        caen en una ruta protegida con comandos=true (REAUD-06)."""
        for j, a in enumerate(args):
            s = a["s"]
            if s == "-o" and exe not in SIN_O_DE_SALIDA and j + 1 < len(args) and not args[j + 1]["s"].startswith("-"):
                self._destino(args[j + 1]["s"], args[j + 1]["din"])
                continue
            m = re.match(r"^--(output|outputfile|output-file|out-file|outfile|out|output-dir|outdir|out-dir|"
                         r"output-directory)(?:\.[\w-]+)?(?:=(.*))?$", s, re.I | re.S | RX)
            if m:
                if m.group(2) is not None:
                    self._destino(m.group(2), a["din"])
                elif j + 1 < len(args) and not args[j + 1]["s"].startswith("-"):
                    self._destino(args[j + 1]["s"], args[j + 1]["din"])

    def escrituras_ps(self, exe, args):
        alias = {"rm": "remove-item", "mv": "move-item", "cp": "copy-item"}
        nombres, posiciones = ESCRIBE_PS[alias.get(exe, exe)]
        conocidos = tuple(nombres) + PS_VALORES + ("path", "literalpath", "filepath", "destination", "name")
        pos, nombrados, j = [], [], 0
        while j < len(args):
            a = args[j]
            p = _ps_param(a["s"])
            if p is not None:
                nombre = _ps_prefijo(p, conocidos)
                if nombre is None:
                    j += 1
                    continue
                if ":" in a["s"]:
                    valor = {"s": a["s"].split(":", 1)[1], "din": a["din"]}
                    j += 1
                elif j + 1 < len(args):
                    valor = args[j + 1]
                    j += 2
                else:
                    break
                if nombre in nombres:
                    nombrados.append((nombre, valor))
                continue
            pos.append(a)
            j += 1
        destinos = list(nombrados)
        for p in posiciones:
            if p == -1:
                destinos += [("", a) for a in pos]
            elif p < len(pos):
                destinos.append(("", pos[p]))
        base = alias.get(exe, exe)
        if base in ("new-item", "ni"):
            nombre = next((v for n, v in destinos if n == "name"), None)
            carpeta = next((v for n, v in destinos if n != "name"), None)
            if nombre is not None and carpeta is not None:
                destinos = [("", {"s": carpeta["s"].rstrip("/\\") + "/" + nombre["s"], "din": carpeta["din"] or nombre["din"]})]
        for _, v in destinos:
            if base == "expand-archive":
                self._carpeta_extraida(v)
            else:
                self._destino(v["s"], v["din"], ps=True)
        if base == "expand-archive" and not destinos:
            self._carpeta_extraida({"s": ".", "din": False})

    # ---------------------------------------------------- git y gh
    def git(self, args, modo):
        git = self.reglas["git"]
        j, dir_git = 0, None
        while j < len(args) and args[j]["s"].startswith("-"):
            a = args[j]["s"]
            if a in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env", "--super-prefix") and j + 1 < len(args):
                v = args[j + 1]
                if a == "-C":
                    dir_git = v["s"] if dir_git is None else self.unir(dir_git, v["s"])
                elif a in ("-c", "--config-env"):
                    self.config_git(v)
                j += 2
                continue
            if a.startswith("--config-env="):
                self.config_git({"s": a.split("=", 1)[1], "din": args[j]["din"]})
            j += 1
        if not git.get("activo", True):
            return
        sub = args[j]["s"].lower() if j < len(args) else ""
        resto = args[j + 1:]
        if j < len(args) and args[j]["din"]:
            self.candidatos.append(("ask", f"git {args[j]['s']}: subcomando calculado; no puedo comprobarlo, pide permiso.",
                                    "git.subcomando-desconocido"))
        elif sub and sub not in GIT_CONOCIDOS:
            self.candidatos.append(("ask", f"git {args[j]['s']}: no es un subcomando de git (puede ser un alias de la "
                                           "configuracion, que ejecuta otra cosa); pide permiso.", "git.subcomando-desconocido"))
        if sub == "config":
            self.git_config(resto)
        elif sub == "remote" and resto and resto[0]["s"].lower() in ("set-url", "add"):
            if resto[0]["s"].lower() == "set-url":
                self.candidatos.append(("deny", "git remote set-url cambia la URL de un remoto (a donde van los push): la "
                                                "cambia una persona.", "git.config-peligrosa"))
            else:
                self.candidatos.append(("ask", "git remote add anade un remoto a la configuracion de git; pide permiso.",
                                        "git.config-escribe"))
        elif sub in ("checkout", "restore", "mv", "rm", "apply"):
            self.git_destinos(sub, resto, self.cwd if dir_git is None else self.unir(self.cwd, dir_git))
        if sub == "push":
            r = self.push(resto, git, dir_git)
            if r:
                self.candidatos.append(r)
        elif sub == "commit" and git["commit_en_principal"] != "ninguna":
            actual = self.rama_de(dir_git)
            if actual and actual.lower() in git["rama_principal"]:
                self.candidatos.append((git["commit_en_principal"],
                                        f"git commit en la rama principal ({actual}): lo normal es una rama por tarea.",
                                        "git.commit-principal"))
        elif sub in ("checkout", "switch"):
            self.cambio_rama(sub, resto, dir_git)
        elif sub in ("rebase", "submodule", "bisect"):
            for k, a in enumerate(resto):
                s = a["s"]
                if sub == "rebase" and (s in ("-x", "--exec") or s.startswith("--exec=")):
                    texto = s.split("=", 1)[1] if "=" in s else (resto[k + 1]["s"] if k + 1 < len(resto) else "")
                    self.construccion("git rebase --exec")
                    self.analizar(texto, "bash", 1)
                elif (sub == "submodule" and s == "foreach") or (sub == "bisect" and s == "run"):
                    self.construccion(f"git {sub} {s}")
                    otros = [x for x in resto[k + 1:] if not x["s"].startswith("-")]
                    self.analizar(" ".join(x["s"] for x in otros), "bash", 1)
                    break
        if sub in GIT_REMOTO or sub == "push":
            for k, a in enumerate(resto):
                s = a["s"]
                o = larga(s, ("--upload-pack", "--receive-pack", "--exec")) if s.startswith("--") else None
                if o or (sub != "push" and re.match(r"^-u", s) and not s.startswith("--")):
                    self.candidatos.append(("deny", f"git {sub} con {o or '-u'}: ejecuta un programa arbitrario.",
                                            "git.ejecuta-programa"))
                    break
                if sub == "clone" and (s in ("-c", "--config") or s.startswith("--config=")):
                    v = {"s": s.split("=", 1)[1], "din": a["din"]} if "=" in s else (resto[k + 1] if k + 1 < len(resto) else None)
                    if v:
                        self.config_git(v)
        if sub in GIT_SALIDA:
            for k, a in enumerate(resto):
                s = a["s"]
                destino = None
                if s.startswith("--") and larga(s, ("--output", "--output-directory"), 5):
                    destino = {"s": s.split("=", 1)[1], "din": a["din"]} if "=" in s else (resto[k + 1] if k + 1 < len(resto) else None)
                elif sub == "format-patch" and re.match(r"^-o", s):
                    destino = {"s": s[2:], "din": a["din"]} if len(s) > 2 else (resto[k + 1] if k + 1 < len(resto) else None)
                if destino is not None:
                    rel = normalizar_ruta(destino["s"], self.raiz, self.cwd)
                    if not destino["din"] and es_config_claude(rel):
                        self.candidatos.append(("deny", f"git {sub} --output escribe en la configuracion de Claude ({rel}): se deniega.",
                                                "git.salida-a-fichero"))
                    else:
                        self.candidatos.append(("ask", f"git {sub} --output escribe un fichero ({rel}): pide permiso.",
                                                "git.salida-a-fichero"))
                        self.destinos.append((destino, self.cwd))

    def git_destinos(self, sub, args, cwd):
        """Ficheros de trabajo que reescriben git checkout [<rev>] -- rutas, restore, mv, rm y apply --directory
        (REAUD-05). restore --staged y rm --cached solo tocan el indice: no cuentan."""
        con_valor = {"checkout": ("-b", "-B", "--orphan", "--conflict", "--pathspec-from-file"),
                     "restore": ("-s", "--source", "--conflict", "--pathspec-from-file"),
                     "rm": ("--pathspec-from-file",), "mv": (),
                     "apply": ("--directory", "--exclude", "--include", "-p", "-C", "--whitespace", "--build-fake-ancestor")}[sub]
        antes, despues, banderas, j, separador = [], [], set(), 0, False
        while j < len(args):
            a = args[j]
            s = a["s"]
            if separador:
                despues.append(a)
            elif s == "--":
                separador = True
            elif s.startswith("-") and len(s) > 1:
                nombre = s.split("=", 1)[0]
                if sub == "apply" and nombre == "--directory":
                    v = {"s": s.split("=", 1)[1], "din": a["din"]} if "=" in s else (args[j + 1] if j + 1 < len(args) else None)
                    if v is not None:
                        self.destinos.append((v, cwd))
                if nombre in con_valor and "=" not in s:
                    j += 2
                    continue
                if not s.startswith("--"):
                    banderas.update("-" + x for x in s[1:])
                banderas.add(nombre)
            else:
                antes.append(a)
            j += 1
        if sub == "apply":
            return
        if sub == "restore" and banderas & {"-S", "--staged"} and not banderas & {"-W", "--worktree"}:
            return
        if sub == "rm" and "--cached" in banderas:
            return
        if sub == "checkout":
            # 'git checkout X' sin '--' es casi siempre cambiar de rama: X solo cuenta si existe como ruta
            rutas = despues if separador else (antes[1:] if len(antes) >= 2 else [
                a for a in antes if not a["din"] and os.path.exists(absoluta_de(normalizar_ruta(a["s"], self.raiz, cwd),
                                                                                 self.raiz))])
        else:
            rutas = antes + despues
        for a in rutas:
            self.destinos.append((a, cwd))

    def config_git(self, v):
        clave, _, valor = v["s"].partition("=")
        if v["din"]:
            self.candidatos.append(("ask", "git -c con un valor calculado: no puedo comprobarlo; pide permiso.", "git.config"))
        elif clasificar_config(clave, valor, False) == "peligrosa":
            self.candidatos.append(("deny", f"git -c {clave}: puede ejecutar comandos o cambiar el destino del push.",
                                    "git.config-peligrosa"))

    def git_config(self, args):
        """git config (forma clasica y subcomandos get/set/unset/list/edit/...): la escritura persistente de
        una clave peligrosa se deniega, cualquier otra escritura pregunta y la lectura no tiene opinion."""
        con_valor = ("-f", "--file", "--blob", "--type", "--default", "--comment", "--value", "--url")
        pos, banderas, fichero, j = [], set(), None, 0
        while j < len(args):
            a = args[j]
            s = a["s"]
            if s.startswith("-") and len(s) > 1:
                nombre = s.split("=", 1)[0]
                if nombre in con_valor:
                    v = {"s": s.split("=", 1)[1], "din": a["din"]} if "=" in s else (args[j + 1] if j + 1 < len(args) else None)
                    if nombre in ("-f", "--file") and v is not None:
                        fichero = v
                    j += 1 if "=" in s else 2
                    continue
                banderas.add(nombre)
                j += 1
                continue
            pos.append(a)
            j += 1
        accion, clave, valor = "leer", None, None
        nuevos = {"get": "leer", "list": "leer", "set": "escribir", "unset": "borrar", "edit": "editar",
                  "rename-section": "renombrar", "remove-section": "borrar"}
        if pos and pos[0]["s"].lower() in nuevos and not pos[0]["din"]:
            accion = nuevos[pos[0]["s"].lower()]
            pos = pos[1:]
        elif banderas & {"--get", "--get-all", "--get-regexp", "--get-urlmatch", "-l", "--list", "--get-color",
                         "--get-colorbool"}:
            accion = "leer"
        elif banderas & {"-e", "--edit"}:
            accion = "editar"
        elif banderas & {"--unset", "--unset-all", "--remove-section"}:
            accion = "borrar"
        elif "--rename-section" in banderas:
            accion = "renombrar"
        elif banderas & {"--add", "--replace-all"} or len(pos) >= 2:
            accion = "escribir"
        if accion == "leer":
            return
        if fichero is not None:
            self.destinos.append((fichero, self.cwd))
        if accion == "editar":
            self.candidatos.append(("ask", "git config --edit abre la configuracion de git en un editor: puede escribir "
                                           "cualquier clave (alias, hooks, push); pide permiso.", "git.config-escribe"))
            return
        if any(p["din"] for p in pos[:2]):
            self.candidatos.append(("ask", "git config con una clave o un valor calculado: no puedo comprobarlo; pide permiso.",
                                    "git.config-escribe"))
            return
        clave = pos[0]["s"] if pos else ""
        valor = pos[1]["s"] if len(pos) > 1 else ""
        if accion == "renombrar":
            if any(SECCION_PELIGROSA.match(p["s"]) for p in pos[:2]):
                self.candidatos.append(("deny", f"git config --rename-section {clave}: crea o mueve una seccion que ejecuta "
                                                "comandos o cambia el destino del push.", "git.config-peligrosa"))
            else:
                self.candidatos.append(("ask", f"git config --rename-section {clave}: cambia la configuracion de git; "
                                               "pide permiso.", "git.config-escribe"))
            return
        if accion == "escribir" and clasificar_config(clave, valor, True) == "peligrosa":
            self.candidatos.append(("deny", f"git config {clave}: configuracion persistente que puede ejecutar comandos o "
                                            "cambiar el destino del push (alias, core, push, remotos, credenciales, "
                                            "include). La cambia una persona.", "git.config-peligrosa"))
            return
        verbo = "borra" if accion == "borrar" else "escribe"
        self.candidatos.append(("ask", f"git config {verbo} {clave or 'una clave'} en la configuracion de git; pide permiso.",
                                "git.config-escribe"))

    def cambio_rama(self, sub, args, dir_git):
        nueva, cambia, descarta, j, pos = None, False, False, 0, []
        crear = ("-b", "-B", "--orphan") if sub == "checkout" else ("-c", "-C", "--create", "--force-create", "--orphan")
        while j < len(args):
            s = args[j]["s"]
            if s == "--":
                pos.append("--")
                break
            if s.startswith("--"):
                o = larga(s, ("--force", "--discard-changes", "--create", "--force-create", "--orphan", "--detach"))
                if o in ("--force", "--discard-changes"):
                    descarta = True
                elif o in crear and j + 1 < len(args):
                    nueva, cambia = args[j + 1]["s"], True
                    j += 2
                    continue
                elif o == "--detach":
                    nueva, cambia = None, True
                j += 1
                continue
            if s.startswith("-") and len(s) > 1:
                if "f" in s[1:]:
                    descarta = True
                letra = next((x for x in s[1:] if "-" + x in crear), None)
                if letra and j + 1 < len(args):
                    nueva, cambia = args[j + 1]["s"], True
                    j += 2
                    continue
                j += 1
                continue
            pos.append(s)
            j += 1
        if descarta:
            self.candidatos.append(("ask", f"git {sub} forzado: descarta los cambios sin commitear; pide permiso.",
                                    "git.descarta-cambios"))
        if not cambia and len(pos) == 1 and pos[0] != "--":
            nueva, cambia = (None if pos[0] == "-" else pos[0]), True
        if cambia:
            d = self.cwd if dir_git is None else self.unir(self.cwd, dir_git)
            self.ramas[normalizar_ruta(d, "", None).lower()] = nueva

    def push(self, args, git, dir_git):
        con_valor = ("--push-option", "--repo", "--receive-pack", "--exec", "--recurse-submodules")
        largas = ("--force", "--force-with-lease", "--force-if-includes", "--mirror", "--all", "--branches", "--delete",
                  "--repo") + con_valor
        forzado, todas, borrar, pos, din, j = False, False, False, [], False, 0
        while j < len(args):
            a = args[j]
            s = a["s"]
            if s.startswith("--") and len(s) > 2:
                o = larga(s, largas)
                if o in ("--force", "--force-with-lease", "--force-if-includes"):
                    forzado = True
                elif o in ("--mirror", "--all", "--branches"):
                    todas = True
                elif o == "--delete":
                    borrar = True
                elif o == "--repo" and "=" in s:
                    pos.insert(0, s.split("=", 1)[1])
                if o in con_valor and "=" not in s:
                    if o == "--repo" and j + 1 < len(args):
                        pos.insert(0, args[j + 1]["s"])
                    j += 2
                    continue
                j += 1
                continue
            if s.startswith("-") and len(s) > 1:
                letras = s[1:]
                forzado = forzado or "f" in letras
                borrar = borrar or "d" in letras
                j += 2 if letras.endswith("o") else 1
                continue
            pos.append(s)
            din = din or a["din"]
            j += 1
        if forzado or any(p.startswith("+") for p in pos[1:]):
            return "deny", "git push forzado: reescribe la historia remota.", "git.push-forzado"
        if todas:
            return "deny", "git push de todas las ramas (incluye la principal).", "git.push-principal"
        protegidas = git["rama_principal"] + git["ramas_protegidas"]
        destinos = []
        for r in pos[1:]:
            if r.startswith("^"):
                continue
            if ":" in r and not borrar:
                src, dst = r.split(":", 1)
                dst = dst or src
            else:
                src, dst = r, r
            dst = re.sub(r"^(?:refs/)?heads/", "", dst, flags=re.I)
            if dst in ("HEAD", "@"):
                dst = self.rama_de(dir_git)
            elif dst.lower().startswith("refs/") and not dst.lower().startswith("refs/heads"):
                continue
            destinos.append(dst)
        if not pos[1:]:
            destinos.append(self.rama_de(dir_git))
        malas = [d for d in destinos if d and any(glob_shell_re(d).match(p) if re.search(r"[*?\[]", d) else d.lower() == p
                                                  for p in protegidas)]
        if malas:
            return ("deny", f"git push a una rama protegida ({malas[0]}): los cambios entran por rama de trabajo y PR.",
                    "git.push-principal")
        if git["push"] == "ninguna":
            return None
        if self.entrada_desconocida:
            return (git["push"], f"{self.entrada_desconocida}: el destino del push no se ve y puede ser la rama "
                                 "principal; pide permiso.", "git.push")
        if din:
            return git["push"], "git push con un destino calculado: no puedo comprobarlo; pide permiso.", "git.push"
        if any(d is None for d in destinos):
            return git["push"], "git push sin rama conocida: pide permiso.", "git.push"
        return git["push"], "git push de una rama de trabajo: pide permiso.", "git.push"

    def gh(self, args):
        git = self.reglas["git"]
        p = _sin_opciones([a["s"] for a in args], 0, GH_CON_VALOR)
        if p >= len(args):
            return
        cmd = args[p]["s"].lower()
        if cmd == "pr":
            a = _sin_opciones([x["s"] for x in args], p + 1, GH_CON_VALOR)
            accion = args[a]["s"].lower() if a < len(args) else ""
            if accion == "merge" and git["pr_merge"] != "ninguna":
                self.candidatos.append((git["pr_merge"], "gh pr merge: el merge lo hace una persona.", "gh.pr-merge"))
            elif accion == "create" and git["pr_create"] != "ninguna":
                self.candidatos.append((git["pr_create"], "gh pr create: abrir un PR pide permiso.", "gh.pr-create"))
        elif cmd == "api":
            self.gh_api(args[p + 1:], git)

    def gh_api(self, resto, git):
        """gh api: mergear un PR o una rama en la principal (/merges, mergeBranch), mover o borrar su ref, escribir
        un commit en ella (/contents) o quitarle la proteccion -> deny; si no se ve la rama -> ask con el motivo
        (REAUD-12); cualquier otra escritura -> ask."""
        todo = " ".join(a["s"] for a in resto)
        metodo, escribe, oculto, campos, endpoint, k = None, False, False, {}, "", 0
        while k < len(resto):
            s, din = resto[k]["s"], resto[k]["din"]
            sig = resto[k + 1] if k + 1 < len(resto) else None
            campo, din_c = None, din
            if s in ("-X", "--method") and sig is not None:
                metodo, k = sig["s"].upper(), k + 2
                continue
            if s.startswith("--method=") or re.match(r"^-X[A-Za-z]+$", s):
                metodo, k = (s.split("=", 1)[1] if "=" in s else s[2:]).upper(), k + 1
                continue
            if s in ("-f", "-F", "--field", "--raw-field") and sig is not None:
                campo, din_c, k = sig["s"], sig["din"], k + 2
            elif re.match(r"^--(?:raw-)?field=", s):
                campo, k = s.split("=", 1)[1], k + 1
            elif re.match(r"^-[fF].", s, re.S):
                campo, k = s[2:], k + 1
            elif s == "--input" or s.startswith("--input="):
                escribe, oculto, k = True, True, k + (1 if "=" in s else 2)
                continue
            elif s in ("-H", "--header", "-q", "--jq", "-t", "--template", "--hostname", "--cache", "-p", "--preview") \
                    and sig is not None:
                k += 2
                continue
            elif s.startswith("-"):
                k += 1
                continue
            else:
                if not endpoint:
                    endpoint = s
                    oculto = oculto or din
                k += 1
                continue
            escribe = True
            nombre, _, valor = campo.partition("=")
            campos[nombre.lower()] = None if (din_c or (s in ("-F", "--field") and valor.startswith("@"))) else valor
        metodo = metodo or ("POST" if escribe else "GET")
        protegidas = git["rama_principal"] + git["ramas_protegidas"]

        def protegida(v):
            return v is not None and re.sub(r"^(?:refs/)?heads/", "", v, flags=re.I).lower() in protegidas

        ep = endpoint.split("?", 1)[0].rstrip("/")
        merge_pr = git["pr_merge"] if git["pr_merge"] != "ninguna" else None
        m_ref = re.search(r"/git/refs/heads/(.+)$", ep, re.I | re.S)
        m_prot = re.search(r"/branches/([^/]+)/protection\b", ep, re.I)
        if (re.search(r"/pulls/[^/\s]+/merge\b", todo) and metodo != "GET") or re.search(r"mergePullRequest|mergeBranch", todo):
            if merge_pr:
                self.candidatos.append((merge_pr, "gh api que mergea un PR o una rama: el merge lo hace una persona.",
                                        "gh.pr-merge"))
        elif re.search(r"(?:^|/)merges$", ep, re.I) and metodo != "GET":
            base, cabeza = campos.get("base"), campos.get("head") or "una rama"
            if oculto or base is None:
                self.candidatos.append(("ask", f"gh api {endpoint} mergea una rama en otra y no veo en cual (--input o un "
                                               "valor calculado): puede ser la rama principal; pide permiso.", "gh.merge-rama"))
            elif protegida(base) and merge_pr:
                self.candidatos.append((merge_pr, f"gh api {endpoint} con base={base}: mergea {cabeza} directamente en la "
                                                  "rama principal, sin PR. El merge lo hace una persona.", "gh.merge-rama"))
            else:
                self.candidatos.append(("ask", f"gh api {endpoint}: mergea {cabeza} en {base}; pide permiso.", "gh.merge-rama"))
        elif re.search(r"/git/refs\b", ep, re.I) and metodo != "GET":
            rama = m_ref.group(1) if m_ref else campos.get("ref")
            if protegida(rama):
                self.candidatos.append(("deny", f"gh api {endpoint}: crea, mueve o borra la rama {rama} (equivale a un push "
                                                "a la rama principal).", "git.push-principal"))
            else:
                self.candidatos.append(("ask", f"gh api {endpoint}: cambia una rama ({rama or 'que no veo'}) en GitHub; "
                                               "pide permiso.", "gh.api-escribe"))
        elif re.search(r"/contents/", ep, re.I) and metodo in ("PUT", "DELETE"):
            rama = campos.get("branch", "") if "branch" in campos or not oculto else None
            if rama == "" or protegida(rama):
                self.candidatos.append(("deny", f"gh api {endpoint}: escribe un commit en la rama "
                                                f"{rama or 'por defecto (la principal)'} sin PR.", "git.push-principal"))
            else:
                self.candidatos.append(("ask", f"gh api {endpoint}: escribe un commit en {rama or 'una rama que no veo'}; "
                                               "pide permiso.", "gh.api-escribe"))
        elif m_prot and metodo != "GET" and protegida(m_prot.group(1)):
            self.candidatos.append(("deny", f"gh api {endpoint}: cambia la proteccion de la rama principal.",
                                    "gh.proteccion"))
        elif re.search(r"\b(?:createCommitOnBranch|updateRefs?|deleteRef)\b", todo):
            if any(re.search(r"(?<![\w./-])(?:refs/heads/)?" + re.escape(r) + r"(?![\w./-])", todo, re.I) for r in protegidas):
                self.candidatos.append(("deny", "gh api graphql que escribe en la rama principal (commit o ref).",
                                        "git.push-principal"))
            else:
                self.candidatos.append(("ask", "gh api graphql que escribe ramas en GitHub; pide permiso.", "gh.api-escribe"))
        elif metodo != "GET" or escribe:
            self.candidatos.append(("ask", "gh api que escribe en GitHub: pide permiso.", "gh.api-escribe"))

    # ---------------------------------------------------- reglas sobre lo analizado
    def toca_ficheros(self, r):
        if not r["ficheros"]:
            return False
        for a, modo in self.argumentos:
            s = a["s"]
            for cand in [s] + ([s.split("=", 1)[1]] if "=" in s else []):
                base = re.split(r"[\\/]", cand)[-1].strip()
                if not base:
                    continue
                if a.get("g") and re.search(r"[*?\[]", base):
                    if modo == "bash" and not base.startswith("."):
                        continue
                    rx = glob_shell_re(base)
                    if any(rx.match(m) for m in r["muestras"]):
                        return True
                elif any(g.match(base) for g in r["ficheros"]) and not any(g.match(base) for g in r["ficheros_excepto"]):
                    return True
        return False


def _sin_opciones(tk, j, con_valor):
    """Primer indice >= j que no es una opcion (salta '-x', '--x=y' y las opciones con valor aparte)."""
    while j < len(tk) and tk[j].startswith("-"):
        j += 2 if tk[j] in con_valor else 1
    return j


def _peor(candidatos):
    mejor = None
    for c in candidatos:
        if c and c[0] in PESO and (mejor is None or PESO[c[0]] > PESO[mejor[0]]):
            mejor = c
    return mejor


def normalizar(texto):
    """Quita las opciones globales entre una CLI conocida y su subcomando ('terraform -chdir=x apply'
    -> 'terraform apply'), para que las reglas escritas como 'terraform\\s+apply' no se salten."""
    for patron in NORMALIZAR:
        texto = patron.sub(lambda m: m.group(1), texto)
    return texto


def variantes(texto):
    out = [texto]
    for v in (normalizar(texto), re.sub(r"(['\"])\s*\+\s*\1", "", texto)):
        if v not in out:
            out.append(v)
    return out


def _entero(val, v):
    return re.fullmatch(regex_py(val), v, re.I | RX) is not None


def _valor_en(entorno, var):
    if var in entorno:
        return entorno[var]
    return os.environ.get(var)


def _entorno(regla, entorno):
    """Devuelve (aplica, faltan)."""
    faltan = []
    for var, val in regla["entorno_falta"].items():
        v = _valor_en(entorno, var)
        if v is None or not _entero(val, v):
            faltan.append(f"{var}={val}")
    if regla["entorno_falta"] and not faltan:
        return False, []
    for var, val in regla["entorno_es"].items():
        v = _valor_en(entorno, var)
        if v is None or not _entero(val, v):
            return False, []
    return True, faltan


class Rama:
    """Rama actual, una vez por directorio (git symbolic-ref: funciona sin commits)."""

    def __init__(self, cwd):
        self.cwd = cwd
        self.cache = {}

    def __call__(self, d=None):
        d = d or self.cwd
        if d not in self.cache:
            try:
                p = subprocess.run(["git", "-c", "safe.directory=*", "-C", d, "symbolic-ref", "--short", "-q", "HEAD"],
                                   capture_output=True, timeout=5)
                r = p.stdout.decode("utf-8", "replace").strip()
                self.cache[d] = r if p.returncode == 0 and r else None
            except (OSError, subprocess.SubprocessError):
                self.cache[d] = None
        return self.cache[d]


def ruta_protegida(rel, absoluta, reglas, sufijo="", carpeta=False):
    """Reglas de rutas_protegidas que tocan rel. Con carpeta=True (destino de un comando, que puede ser
    una carpeta: rm -r, mv, cp -r) solo cuentan las reglas con comandos=true, y tambien si rel contiene
    una ruta protegida."""
    candidatos = []
    for r in reglas["rutas"]:
        if carpeta and not r["comandos"]:
            continue
        casa = r["glob"].match(rel) and not any(g.match(rel) for g in r["excepto"])
        if not casa and carpeta and rel and not _es_absoluta(rel):
            casa = any(p.startswith(rel.lower().rstrip("/") + "/") for p in r["prefijos"])
        if not casa:
            continue
        if r["modo"] == "deny_existentes":
            if os.path.exists(absoluta):
                candidatos.append(("deny", f"{rel}: {r['motivo']}{sufijo}", r["id"]))
        else:
            candidatos.append((r["modo"], f"{rel}: {r['motivo']}{sufijo}", r["id"]))
    return candidatos


def comodin_protegido(patron, raiz, cwd, reglas, ocultos):
    """Destino de un comando con comodin (REAUD-01/05): cuenta lo que casa en el disco y cualquier ruta protegida
    (con comandos=true) con la que podria casar aunque aun no exista. Nunca se da por inocuo."""
    out = []
    sufijo = f" (escritura desde un comando, por el comodin {patron})"
    carpeta, _, nombre = patron.replace("\\", "/").rpartition("/")
    if carpeta and nombre and not COMODIN.search(nombre):
        rutas = [c + "/" + nombre for c in expandir_comodin(carpeta, cwd, ocultos)]  # el fichero aun puede no existir
    else:
        rutas = expandir_comodin(patron, cwd, ocultos)
    for ruta in rutas:
        rel = normalizar_ruta(ruta, raiz, cwd)
        out += ruta_protegida(rel, absoluta_de(rel, raiz), reglas, sufijo, True)
    rel = normalizar_ruta(patron, raiz, cwd)
    if _es_absoluta(rel):
        return out
    try:
        rx = patron_ruta_re(rel, ocultos)
    except re.error:
        return out + [("ask", f"{patron}: destino con un comodin que el guard no entiende; pide permiso.", "comun.comodin")]
    for r in reglas["rutas"]:
        if not r["comandos"]:
            continue
        for m, carpeta in r["muestras"]:
            if rx.match(m):
                modo = "ask" if carpeta or r["modo"] == "deny_existentes" else r["modo"]
                out.append((modo, f"{patron}: el comodin puede caer en {m}: {r['motivo']}{sufijo}", r["id"]))
                break
    return out


def _contiene(rel, r):
    """La carpeta rel es, o contiene, una ruta de la regla r (la raiz del repo lo contiene todo)."""
    if not rel:
        return True
    if r["glob"].match(rel) and not any(g.match(rel) for g in r["excepto"]):
        return True
    if _es_absoluta(rel):
        return False
    pref = rel.lower().rstrip("/") + "/"
    return any(p.startswith(pref) for p in r["prefijos"]) or any(
        m.lower() == rel.lower() or m.lower().startswith(pref) for m, _ in r["muestras"])


def _regla_con_valores(r, a):
    """Regla con opciones_con_valor (REAUD-02): se evalua sobre cada comando simple con los valores de esas opciones
    tapados ('--currency \\ --dry-run' -> '--currency __valor__'), y los argumentos con espacios o calculados
    tambien, asi 'y' y 'salvo' no ven un --dry-run que no llega como opcion. Si 'salvo' casa pero hay un argumento
    calculado (podria ser una opcion que se come el siguiente), pregunta."""
    for s in a.simples:
        if "args" in s:
            texto, dudoso = texto_canonico(s.get("programa", s["exe"]), s["args"], r["opciones_con_valor"])
        else:
            texto, dudoso = s["texto"], True
        for t in variantes(texto):
            if not r["regex"].search(t) or not all(y.search(t) for y in r["y"]):
                continue
            aplica, faltan = _entorno(r, s["entorno"])
            if not aplica:
                continue
            if any(x.search(t) for x in r["salvo"]):
                if dudoso:
                    return [("ask", f"{r['motivo']} (hay un argumento calculado: no puedo saber si la opcion que lo evita "
                                    "llega como opcion; pide permiso)", r["id"])]
                break
            motivo = r["motivo"] + (f" (falta: {', '.join(faltan)})" if faltan else "")
            if any(x.search(s["texto"]) for x in r["salvo"]):
                motivo += " (la opcion que lo evitaria es aqui el valor de otra opcion o no llega como opcion)"
            return [(r["decision"], motivo, r["id"])]
    return []


def texto_canonico(exe, args, opciones_con_valor):
    """'python x.py a --currency \\ --dry-run' -> ('python x.py a --currency __valor__', dudoso). Tapa el valor de
    cada opcion de la lista (tambien abreviada como argparse, '--opcion=v', '-c v', '-cv' y '-xc v'), los argumentos
    con espacios o vacios (__arg__), lo que va detras de '--' con forma de opcion (__arg__) y los calculados
    (__dinamico__, que hacen la decision dudosa)."""
    ov = list(opciones_con_valor)
    largas = [o for o in ov if o.startswith("--")]
    out, j, fin, dudoso = [exe], 0, False, False
    while j < len(args):
        a = args[j]
        s = a["s"]
        j += 1
        if a["din"]:
            out.append("__dinamico__")
            dudoso = True
        elif not s or re.search(r"\s", s):
            out.append("__arg__")
        elif fin:
            out.append("__arg__" if s.startswith("-") else s)
        elif s == "--":
            fin = True
            out.append(s)
        elif s.startswith("--"):
            nombre, igual, _ = s.partition("=")
            if nombre in ov or (len(nombre) > 2 and any(o.startswith(nombre) for o in largas)):
                out.append(nombre + "=__valor__" if igual else nombre)
                if not igual and j < len(args):
                    out.append("__valor__")
                    j += 1
            else:
                out.append(s)
        elif s.startswith("-") and len(s) > 1:
            k = next((k for k in range(1, len(s)) if "-" + s[k] in ov), None)
            if k is None:
                out.append(s)
            elif k + 1 < len(s):
                out.append(s[:k + 1] + "__valor__")
            else:
                out.append(s)
                if j < len(args):
                    out.append("__valor__")
                    j += 1
        else:
            out.append(s)
    return " ".join(out), dudoso


def absoluta_de(rel, raiz):
    return rel if _es_absoluta(rel) else os.path.join(raiz, *rel.split("/")) if rel else raiz


def decidir_comando(cmd, reglas, rama, raiz=None, cwd=None, modo="bash"):
    raiz = raiz or os.getcwd()
    a = Analisis(raiz, cwd or raiz, rama, reglas)
    a.analizar(cmd, modo, 0)
    candidatos = list(a.candidatos)
    crudo = cmd.rstrip("\r\n")
    global_env = {}
    for s in a.simples:
        global_env.update(s["entorno"])
    textos_comando = [(crudo, global_env)]
    if a.simples:
        textos_comando.append((" ; ".join(s["texto"] for s in a.simples), global_env))
    textos_segmento = [(s, global_env) for s in segmentos(crudo)] + [(s, global_env) for s in a.segmentos if s]
    textos_segmento += [(s["texto"], s["entorno"]) for s in a.simples]
    for r in reglas["bash"]:
        if r["opciones_con_valor"]:
            candidatos += _regla_con_valores(r, a)
            continue
        for texto, env in (textos_comando if r["ambito"] == "comando" else textos_segmento):
            hecho = False
            for t in variantes(texto):
                if not r["regex"].search(t) or not all(y.search(t) for y in r["y"]) or any(s.search(t) for s in r["salvo"]):
                    continue
                aplica, faltan = _entorno(r, env)
                if not aplica:
                    continue
                candidatos.append((r["decision"], r["motivo"] + (f" (falta: {', '.join(faltan)})" if faltan else ""), r["id"]))
                hecho = True
                break
            if hecho:
                break
        else:
            if a.toca_ficheros(r):
                candidatos.append((r["decision"], r["motivo"], r["id"]))
    for r in reglas["requiere_env"]:
        for texto, env in [(s["texto"], s["entorno"]) for s in a.simples] + [(s, global_env) for s in segmentos(crudo)]:
            if not r["regex"].search(texto):
                continue
            faltan, malos = [], []
            for var in r["variables"]:
                v = _valor_en(env, var)
                if v is None or not v.strip():
                    faltan.append(var)
                elif r["permitidos"] and not any(p.fullmatch(v.strip()) for p in r["permitidos"]):
                    malos.append(f"{var}={v.strip()}")
            if faltan or malos:
                extra = (f" (falta: {', '.join(faltan)})" if faltan else "") + (f" (valor no permitido: {', '.join(malos)})" if malos else "")
                candidatos.append((r["decision"], r["motivo"] + extra, r["id"]))
            break
    for tok, dcwd in a.destinos:
        if tok.get("din") or not tok["s"] or tok["s"].lower() in ("/dev/null", "nul", "/dev/stdout", "/dev/stderr"):
            continue
        rel = normalizar_ruta(tok["s"], raiz, dcwd)
        candidatos += ruta_protegida(rel, absoluta_de(rel, raiz), reglas, " (escritura desde un comando)", True)
        if COMODIN.search(tok["s"]):
            candidatos += comodin_protegido(tok["s"], raiz, dcwd, reglas, bool(tok.get("ps")))
    for tok, dcwd in a.extracciones:
        if tok.get("din"):
            continue
        rel = normalizar_ruta(tok["s"], raiz, dcwd)
        r = next((r for r in reglas["rutas"] if r["comandos"] and _contiene(rel, r)), None)
        if r is not None:
            candidatos.append(("ask", f"{rel or '.'}: extrae un archivo cuyo contenido el guard no ve en una carpeta con "
                                      f"rutas protegidas ({r['id']}: {r['motivo']}); pide permiso.", r["id"]))
    if a.construcciones:
        candidatos.append(("ask", f"{a.construcciones[0]}: ejecuta un comando dentro de otro y el guard no puede "
                                  "comprobarlo entero; pide permiso.", "comun.construccion"))
    return _peor(candidatos)


# ---------------------------------------------------------------- escritura

def _texto(v, campo):
    if v is None:
        return ""
    if not isinstance(v, str):
        raise ValueError(f"tool_input.{campo} no es texto")
    return v


def _ediciones(entrada):
    edits = entrada.get("edits")
    if edits is None:
        return []
    if not isinstance(edits, list) or not all(isinstance(e, dict) for e in edits):
        raise ValueError("tool_input.edits no es una lista de objetos")
    return edits


def texto_nuevo(tool, entrada):
    if tool == "MultiEdit":
        return "\n".join(_texto(e.get("new_string"), "new_string") for e in _ediciones(entrada))
    if tool == "NotebookEdit":
        return _texto(entrada.get("new_source"), "new_source")
    return _texto(entrada.get("content"), "content") or _texto(entrada.get("new_string"), "new_string")


def texto_viejo(tool, entrada, absoluta):
    if tool == "MultiEdit":
        return "\n".join(_texto(e.get("old_string"), "old_string") for e in _ediciones(entrada))
    if tool == "Write" and os.path.isfile(absoluta):
        with open(absoluta, encoding="utf-8", errors="replace") as f:
            return f.read()
    return _texto(entrada.get("old_string"), "old_string")


def _objetos(regex, texto):
    out = set()
    for m in regex.finditer(texto):
        out.add(m.group("obj") if "obj" in regex.groupindex and m.group("obj") is not None else m.group(0))
    return out


def _ruta_evento(entrada):
    original = entrada.get("file_path")
    if original is None:
        original = entrada.get("notebook_path")
    return _texto(original, "file_path")


def decidir_escritura(tool, entrada, reglas, raiz, cwd=None):
    original = _ruta_evento(entrada)
    ruta = normalizar_ruta(original, raiz, cwd or raiz)
    absoluta = absoluta_de(ruta, raiz)
    candidatos = ruta_protegida(ruta, absoluta, reglas)
    nuevo, viejo = texto_nuevo(tool, entrada), None
    for r in reglas["contenido"]:
        if not r["glob"].match(ruta):
            continue
        if viejo is None:
            viejo = texto_viejo(tool, entrada, absoluta)
        anadidos = _objetos(r["regex"], nuevo) - _objetos(r["regex"], viejo)
        if r["excepto_si"] is not None:
            anadidos = {o for o in anadidos if not r["excepto_si"].search(o)}
        if anadidos:
            candidatos.append((r["decision"], f"{ruta}: {r['motivo']}", r["id"]))
    return _peor(candidatos)


# ---------------------------------------------------------------- hook

def salida(decision, motivo, prefijo):
    obj = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                  "permissionDecisionReason": f"{prefijo} {motivo}"}}
    sys.stdout.buffer.write(json.dumps(obj, ensure_ascii=True, separators=(",", ":")).encode("ascii"))
    sys.stdout.buffer.flush()


def evaluar(datos):
    """Devuelve (decision, motivo, prefijo) o None."""
    tool = datos.get("tool_name") or ""
    entrada = datos.get("tool_input")
    if entrada is None:
        entrada = {}
    if not isinstance(entrada, dict):
        raise ValueError("tool_input no es un objeto")
    raiz = os.environ.get("CLAUDE_PROJECT_DIR") or datos.get("cwd") or os.getcwd()
    cwd = datos.get("cwd") or raiz
    if tool not in HERRAMIENTAS_COMANDO + HERRAMIENTAS_ESCRITURA:
        return None
    try:
        reglas = compilar(cargar(raiz, comun=True, exigir_comun=True))
    except ConfigError as e:
        if tool in HERRAMIENTAS_ESCRITURA and EDITA_CONFIG.search(normalizar_ruta(_ruta_evento(entrada), raiz, cwd)):
            return "ask", f"configuracion del guard invalida ({e}); esta edicion puede arreglarla.", "[guard]"
        return "deny", f"configuracion del guard invalida, se deniega por seguridad: {e}", "[guard]"
    if tool in HERRAMIENTAS_COMANDO:
        cmd = entrada.get("command")
        if cmd is None:
            cmd = ""
        if not isinstance(cmd, str):
            raise ValueError("tool_input.command no es texto")
        r = decidir_comando(cmd, reglas, Rama(cwd), raiz, cwd, "ps" if tool == "PowerShell" else "bash")
    else:
        r = decidir_escritura(tool, entrada, reglas, raiz, cwd)
    return (r[0], r[1], reglas["prefijo"]) if r else None


def main(argv):
    if len(argv) > 1 and argv[1] == "--version":
        print(VERSION)
        return 0
    if len(argv) > 1 and argv[1] == "--config":
        raiz = argv[2] if len(argv) > 2 else (os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
        cfg = cargar(raiz, comun=True, exigir_comun=True)
        compilar(cfg)
        sys.stdout.buffer.write(json.dumps(cfg, ensure_ascii=True, sort_keys=True, indent=2).encode("ascii"))
        return 0
    try:
        crudo = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        datos = json.loads(crudo) if crudo.strip() else {}
        if not isinstance(datos, dict):
            raise ValueError("el evento no es un objeto JSON")
        r = evaluar(datos)
        if r:
            salida(r[0], r[1], r[2])
        return 0
    except Exception as e:  # fallo cerrado
        try:
            salida("deny", f"el guard fallo y deniega por seguridad: {type(e).__name__}: {e}", "[guard]")
            return 0
        except Exception:
            sys.stderr.write("guard_core fallo; se bloquea la accion.\n")
            return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
