"""public_guard.py: guard de repo publico (hooks de Claude Code de trAIn-Landing). Solo stdlib.

Este repo es publico en GitHub y Vercel publica en el dominio todo lo que .vercelignore no excluye.
Modos (primer argumento):
  pre-git    PreToolUse de Bash y PowerShell (registrado con `if: git *`). Solo actua en `git commit`
             y `git push`; con cualquier otro comando sale sin decir nada.
  pre-edit   PreToolUse de Edit/Write/MultiEdit: las migraciones de supabase/migrations/ que ya existen
             no se editan (se crea una nueva). Lo demas no lo mira.
  post-edit  PostToolUse de Write/Edit/MultiEdit: revisa las lineas nuevas del fichero editado y avisa
             (no bloquea) de lo que se bloquearia al commitear, y de si Vercel lo publicaria.

Al commitear o empujar revisa solo lo que se ANADE (lo que ya estaba en el repo no cuenta):
  deny  secretos (JWT con role distinto de anon, claves con prefijo conocido, claves privadas,
        asignaciones de claves con valor), ficheros prohibidos (.env, *.key, CLAUDE.local.md...),
        rutas locales de usuario, emails fuera de public_guard.allow.json y terminos internos de
        ~/.claude/lmginc/public-guard.local.json (fuera del repo; si no existe, solo reglas genericas);
        push forzado, push a main, --all y --mirror.
  ask   autor o committer con email fuera de la lista publica (queda publico en GitHub); ficheros
        nuevos que Vercel publicaria y no son contenido web; cualquier otro push (C-4).
La clave anon de Supabase de app.js se acepta porque su payload dice role=anon; el valor no esta aqui.
Nunca imprime el valor encontrado: solo fichero:linea y el tipo. Si gitleaks esta en el PATH, se
ejecuta tambien (salida --redact) y sus hallazgos deniegan. Un fallo del guard deniega (C-3).
"""
from __future__ import annotations

import base64
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
AQUI = os.path.dirname(os.path.abspath(__file__))
PREFIJO = "[guard publico trAIn-Landing]"
MAX_TEXTO = 2 * 1024 * 1024
MAX_COMMITS = 300

# ---------------------------------------------------------------- salida


def salir(obj=None, codigo=0, stderr=None):
    if obj is not None:
        sys.stdout.write(json.dumps(obj, ensure_ascii=True))
    if stderr:
        sys.stderr.buffer.write(stderr.encode("utf-8"))
        sys.stderr.flush()
    sys.exit(codigo)


def decidir(dec, motivo):
    salir({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": dec,
                                  "permissionDecisionReason": f"{PREFIJO} {motivo}"}})


# ---------------------------------------------------------------- git y rutas


def git(args, cwd, entrada=None):
    p = subprocess.run(["git", "-c", "safe.directory=*", "-c", "core.quotepath=off"] + args, cwd=cwd,
                       input=entrada, capture_output=True, timeout=20)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def raiz_de(carpeta):
    if not carpeta or not os.path.isdir(carpeta):
        return None
    rc, out = git(["rev-parse", "--show-toplevel"], carpeta)
    return os.path.normcase(os.path.realpath(out.strip())) if rc == 0 and out.strip() else None


def glob_a_regex(glob):
    i, r = 0, ""
    while i < len(glob):
        if glob.startswith("**/", i):
            r, i = r + "(?:.*/)?", i + 3
        elif glob.startswith("**", i):
            r, i = r + ".*", i + 2
        elif glob[i] == "*":
            r, i = r + "[^/]*", i + 1
        elif glob[i] == "?":
            r, i = r + "[^/]", i + 1
        else:
            r, i = r + re.escape(glob[i]), i + 1
    return re.compile(r + r"\Z")


def casa(rel, globs):
    return any(glob_a_regex(g).match(rel) for g in globs)


def excluidos_por_vercel(raiz, rutas):
    """Rutas (relativas, con /) que .vercelignore excluye. Se evalua en un repo vacio aparte para que
    .gitignore no se mezcle (mismo criterio que git ls-files -i --exclude-from=.vercelignore)."""
    vi = os.path.join(raiz, ".vercelignore")
    if not rutas or not os.path.isfile(vi):
        return set()
    with open(vi, encoding="utf-8", errors="replace") as f:
        patrones = f.read()
    with tempfile.TemporaryDirectory(prefix="guard-vercel-") as d:
        git(["init", "-q"], d)
        with open(os.path.join(d, ".gitignore"), "w", encoding="utf-8", newline="\n") as f:
            f.write(patrones)
        vacio = os.path.join(d, ".git", "vacio")
        open(vacio, "w").close()
        p = subprocess.run(["git", "-c", "safe.directory=*", "-c", f"core.excludesFile={vacio}", "check-ignore",
                            "--no-index", "--stdin"], cwd=d, input="\n".join(rutas).encode("utf-8"),
                           capture_output=True, timeout=20)
        return {x.strip() for x in p.stdout.decode("utf-8", "replace").splitlines() if x.strip()}


# ---------------------------------------------------------------- configuracion


def cargar_allow():
    with open(os.path.join(AQUI, "public_guard.allow.json"), encoding="utf-8") as f:
        return json.load(f)


def ruta_local():
    cands = [os.environ.get("LMGINC_PUBLIC_GUARD_LOCAL", "")]
    for base in (os.path.expanduser("~"), os.environ.get("USERPROFILE", ""), os.environ.get("HOME", "")):
        if base:
            cands.append(os.path.join(base, ".claude", "lmginc", "public-guard.local.json"))
    return next((c for c in cands if c and os.path.isfile(c)), None)


def cargar_internos():
    """(patrones, direcciones extra permitidas) del fichero personal, o ([], []) si no existe."""
    ruta = ruta_local()
    if not ruta:
        return [], []
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    pats = [re.compile(r"(?<![A-Za-z0-9_])" + re.escape(t) + r"(?![A-Za-z0-9_])", re.I)
            for t in datos.get("terminos", []) if t]
    pats += [re.compile(r, re.I) for r in datos.get("regex", []) if r]
    return pats, [e.lower() for e in datos.get("emails_publicos_extra", [])]


# ---------------------------------------------------------------- deteccion de contenido

SECRETOS = [
    ("clave privada", re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----")),
    ("clave de GitHub", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})")),
    ("clave de Stripe", re.compile(r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{10,}")),
    ("clave de Google", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}")),
    ("clave de AWS", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("token de Slack", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("clave de Anthropic u OpenAI", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{32,}")),
    ("clave de Resend", re.compile(r"\bre_(?=[A-Za-z0-9_]*[0-9])(?=[A-Za-z0-9_]*[A-Z])[A-Za-z0-9_]{20,}")),
]
JWT = re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.(eyJ[A-Za-z0-9_-]{8,})\.[A-Za-z0-9_-]{8,}")
ASIGNACION_ENV = re.compile(r"^\s*(?:export\s+|\$env:)?([A-Z][A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD))\s*=\s*[\"']?([^\s\"'#]{8,})")
ASIGNACION_CODIGO = re.compile(
    r"(?i)(?:api[_-]?key|secret[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token|private[_-]?key|"
    r"service[_-]?role[_-]?key|password|passwd)[\"']?\s*[:=]\s*[\"']([^\"'\s]{12,})[\"']")
MARCADOR = re.compile(r"^(?:\$|<|\{|%|process\.env|Deno\.env|os\.environ|import\.meta|x{4,}|\*{3,}|\.\.\.|your|tu[_-]|"
                      r"changeme|example|ejemplo|placeholder|dummy|fake)", re.I)
EMAIL = re.compile(r"(?<![A-Za-z0-9._%+-])([A-Za-z0-9._%+-]+)@((?:[A-Za-z0-9-]+\.)+([A-Za-z]{2,}))(?![A-Za-z0-9-])")
RUTAS = [
    ("ruta de Windows", re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:(?:\\{1,2}|/)[A-Za-z0-9_.$~-]")),
    ("ruta de red", re.compile(r"(?<![A-Za-z0-9\\])\\\\[A-Za-z0-9._-]{2,}\\[A-Za-z0-9$._-]+")),
    ("carpeta de usuario", re.compile(r"(?<![A-Za-z0-9_.~-])(?:/[A-Za-z])?/(?:Users|home)/[A-Za-z0-9._-]+/")),
]


def jwt_es_anon(payload):
    try:
        datos = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except (ValueError, TypeError):
        return False
    return isinstance(datos, dict) and datos.get("role") == "anon"


def carpetas_de_usuario():
    vistas = set()
    for k in ("USERPROFILE", "HOME"):
        v = os.environ.get(k, "")
        if len(v) > 3 and "/" not in v[:1]:
            vistas.add(v)
            vistas.add(v.replace("\\", "/"))
    return [v.lower() for v in vistas]


class Revisor:
    def __init__(self, allow, internos, emails_extra):
        self.allow = allow
        self.internos = internos
        em = allow.get("emails", {})
        self.dominios = [d.lower() for d in em.get("dominios", [])]
        self.direcciones = {d.lower() for d in em.get("direcciones", [])} | set(emails_extra)
        self.no_email = {e.lower() for e in em.get("extensiones_que_no_son_email", [])}
        self.excepciones = allow.get("excepciones", [])
        self.usuario = carpetas_de_usuario()

    def ignorados(self, fichero):
        fuera = set()
        for e in self.excepciones:
            if casa(fichero, [e.get("glob", "")]):
                fuera.update(x for x in e.get("ignorar", []) if x != "secretos")
        return fuera

    def email_publico(self, direccion, dominio):
        d = dominio.lower()
        return direccion.lower() in self.direcciones or any(d == x or d.endswith("." + x) for x in self.dominios)

    def linea(self, texto, ignorar=()):
        """Lista de (tipo, detalle) de una linea. Nunca devuelve el valor encontrado."""
        out = []
        for m in JWT.finditer(texto):
            if not jwt_es_anon(m.group(1)):
                out.append(("secreto", "JWT que no es la clave anon publica"))
        sin_jwt = JWT.sub("", texto)
        for nombre, rx in SECRETOS:
            if rx.search(sin_jwt):
                out.append(("secreto", nombre))
        for rx in (ASIGNACION_ENV, ASIGNACION_CODIGO):
            m = rx.search(texto)
            if m:
                valor = m.group(m.lastindex)
                if not MARCADOR.match(valor) and not (JWT.fullmatch(valor) and jwt_es_anon(JWT.fullmatch(valor).group(1))):
                    if rx is ASIGNACION_ENV or (re.search(r"[0-9]", valor) and re.search(r"[A-Za-z]", valor)):
                        out.append(("secreto", "clave o contrasena asignada con valor"))
        if "emails" not in ignorar:
            for m in EMAIL.finditer(texto):
                if m.group(3).lower() in self.no_email:
                    continue
                if not self.email_publico(m.group(0), m.group(2)):
                    out.append(("email", "email fuera de la lista publica"))
        if "rutas" not in ignorar:
            for nombre, rx in RUTAS:
                if rx.search(texto):
                    out.append(("ruta", nombre))
            bajo = texto.lower()
            if any(u in bajo for u in self.usuario):
                out.append(("ruta", "carpeta de tu usuario"))
        if "internos" not in ignorar:
            if any(rx.search(texto) for rx in self.internos):
                out.append(("interno", "termino interno de la lista local"))
        return out

    def lineas(self, items):
        """items: [(fichero, n, texto)] -> [(tipo, 'fichero:n (detalle)')] sin repetir."""
        hallazgos, vistos = [], set()
        cache = {}
        for fichero, n, texto in items:
            if fichero not in cache:
                cache[fichero] = self.ignorados(fichero)
            for tipo, det in self.linea(texto, cache[fichero]):
                clave = (tipo, fichero, n, det)
                if clave not in vistos:
                    vistos.add(clave)
                    hallazgos.append((tipo, f"{fichero}:{n} ({det})" if n else f"{fichero} ({det})"))
        return hallazgos


def lineas_anadidas(diff):
    """[(fichero, n, texto)] de un diff unificado (--unified=0). Sirve para varios commits seguidos."""
    items, fichero, n = [], None, 0
    for l in diff.splitlines():
        if l.startswith("+++ "):
            fichero = l[6:] if l.startswith("+++ b/") else None
        elif l.startswith("@@"):
            m = re.match(r"@@ -\S+ \+(\d+)", l)
            n = int(m.group(1)) if m else 0
        elif l.startswith("+") and fichero:
            items.append((fichero, n, l[1:]))
            n += 1
        elif l.startswith("diff --git"):
            fichero = None
    return items


def texto_de(ruta):
    try:
        if os.path.getsize(ruta) > MAX_TEXTO:
            return None
        with open(ruta, "rb") as f:
            b = f.read()
    except OSError:
        return None
    return None if b"\0" in b[:8192] else b.decode("utf-8", "replace")


# ---------------------------------------------------------------- comandos


def segmentos(cmd):
    """Trozos del comando separados por && || ; | y saltos de linea, respetando comillas."""
    out, actual, q, i = [], "", None, 0
    while i < len(cmd):
        c = cmd[i]
        if q:
            actual += c
            if c == q:
                q = None
            elif c == "\\" and q == '"' and i + 1 < len(cmd):
                actual += cmd[i + 1]
                i += 1
        elif c in "\"'":
            q = c
            actual += c
        elif cmd.startswith(("&&", "||"), i):
            out.append(actual)
            actual, i = "", i + 2
            continue
        elif c in ";|\n":
            out.append(actual)
            actual = ""
        else:
            actual += c
        i += 1
    out.append(actual)
    return [s.strip() for s in out if s.strip()]


def tokens(seg):
    try:
        return shlex.split(seg, posix=True)
    except ValueError:
        return seg.split()


GLOBALES_CON_VALOR = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env", "--super-prefix"}


def llamada_git(toks):
    """(entorno, opciones globales [(opcion, valor)], subcomando, argumentos) o None."""
    entorno, i = {}, 0
    while i < len(toks):
        t = toks[i]
        m = re.match(r"^(?:\$env:)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$", t)
        if m:
            entorno[m.group(1)] = m.group(2)
            i += 1
        elif t in ("env", "command", "time", "nohup", "exec", "&", "."):
            i += 1
        else:
            break
    if i >= len(toks) or re.sub(r"\.exe$", "", os.path.basename(toks[i].replace("\\", "/")).lower()) != "git":
        return None
    i += 1
    globales = []
    while i < len(toks) and toks[i].startswith("-"):
        t = toks[i]
        if t in GLOBALES_CON_VALOR and i + 1 < len(toks):
            globales.append((t, toks[i + 1]))
            i += 2
        elif "=" in t and t.split("=", 1)[0] in GLOBALES_CON_VALOR:
            globales.append(tuple(t.split("=", 1)))
            i += 1
        else:
            globales.append((t, None))
            i += 1
    if i >= len(toks):
        return None
    return entorno, globales, toks[i], toks[i + 1:]


def entorno_powershell(cmd):
    return {m.group(1): m.group(2) for m in re.finditer(r"\$env:([A-Za-z_][A-Za-z0-9_]*)\s*=\s*['\"]?([^'\";\s]+)", cmd)}


# ---------------------------------------------------------------- commit


def analizar_commit(args):
    r = {"todo": False, "mensajes": [], "ficheros_mensaje": [], "autor": None, "rutas": []}
    con_valor = {"m": "mensajes", "F": "ficheros_mensaje", "c": None, "C": None, "t": None}
    i, tras_guiones = 0, False
    while i < len(args):
        a = args[i]
        if tras_guiones or not a.startswith("-") or a == "-":
            r["rutas"].append(a)
        elif a == "--":
            tras_guiones = True
        elif a.startswith("--"):
            nombre, _, valor = a.partition("=")
            largos = {"--message": "mensajes", "--file": "ficheros_mensaje", "--author": "autor",
                      "--reuse-message": None, "--reedit-message": None, "--template": None, "--fixup": None,
                      "--squash": None, "--date": None, "--cleanup": None, "--trailer": None, "--pathspec-from-file": None}
            if nombre in ("--all", "--include", "--only"):
                r["todo"] = r["todo"] or nombre == "--all"
            elif nombre in largos:
                if not _:
                    valor = args[i + 1] if i + 1 < len(args) else ""
                    i += 1
                destino = largos[nombre]
                if destino == "autor":
                    r["autor"] = valor
                elif destino:
                    r[destino].append(valor)
        else:
            j = 1
            while j < len(a):
                ch = a[j]
                if ch == "a":
                    r["todo"] = True
                if ch in con_valor:
                    valor = a[j + 1:]
                    if not valor:
                        valor = args[i + 1] if i + 1 < len(args) else ""
                        i += 1
                    if con_valor[ch]:
                        r[con_valor[ch]].append(valor)
                    break
                j += 1
        i += 1
    return r


def adds_previos(segs, hasta):
    """Pathspecs de los `git add` que van antes del commit en el mismo comando (None si no hay)."""
    rutas, hay = [], False
    for s in segs[:hasta]:
        g = llamada_git(tokens(s))
        if g and g[2] == "add":
            hay = True
            rutas += [a for a in g[3] if not a.startswith("-")] or ["."]
    return rutas if hay else None


def email_de(texto):
    m = re.search(r"<([^>]*)>", texto or "")
    return (m.group(1) if m else (texto or "")).strip()


def revisar_commit(raiz, cwd, g, segs, idx, cfg, rev):
    entorno, globales, _, args = g
    entorno = {**entorno_powershell(" ; ".join(segs)), **entorno}
    c = analizar_commit(args)
    denegar, preguntar = [], []

    staged = git(["diff", "--cached", "--unified=0", "--no-color", "--no-ext-diff", "-M"], raiz)[1]
    items = lineas_anadidas(staged)
    nuevos = [x for x in git(["diff", "--cached", "--name-only", "--diff-filter=A", "-M"], raiz)[1].splitlines() if x]
    nombres = [x for x in git(["diff", "--cached", "--name-only", "--diff-filter=d", "-M"], raiz)[1].splitlines() if x]

    # Lo que el mismo comando va a anadir antes de commitear (commit -a, commit <rutas>, git add ... && commit).
    previos = adds_previos(segs, idx)
    pendientes = []
    if c["todo"]:
        pendientes.append((raiz, []))
    if c["rutas"] or previos:
        pendientes.append((cwd, c["rutas"] + (previos or [])))
    for donde, rutas in pendientes:
        items += lineas_anadidas(git(["diff", "--unified=0", "--no-color", "--no-ext-diff", "--"] + rutas, donde)[1])
        nombres += [x for x in git(["diff", "--name-only", "--diff-filter=d", "--"] + rutas, donde)[1].splitlines() if x]
    if previos:
        sin_seguir = [x for x in git(["ls-files", "-o", "--exclude-standard", "--full-name", "--"] + previos, cwd)[1].splitlines() if x]
        for rel in sin_seguir:
            nuevos.append(rel)
            nombres.append(rel)
            t = texto_de(os.path.join(raiz, rel))
            if t is not None:
                items += [(rel, n, l) for n, l in enumerate(t.splitlines(), 1)]

    nombres = list(dict.fromkeys(nombres + nuevos))
    prohibidos = [f for f in nombres if casa(f, cfg.get("ficheros_prohibidos", [])) and not casa(f, cfg.get("ficheros_permitidos", []))]
    if prohibidos:
        denegar.append("ficheros que no se commitean nunca: " + ", ".join(prohibidos[:8]))

    for m in c["mensajes"]:
        items += [("(mensaje del commit)", 0, l) for l in m.splitlines()]
    for fm in c["ficheros_mensaje"]:
        if fm and fm != "-":
            t = texto_de(os.path.join(cwd, fm))
            if t:
                items += [("(mensaje del commit)", 0, l) for l in t.splitlines()]
    hallazgos = rev.lineas(items)
    denegar += [f"{tipo}: {d}" for tipo, d in hallazgos]

    # Autoria: queda publica en GitHub.
    cfg_email = dict(v.split("=", 1) for o, v in globales if o == "-c" and v and "=" in v)
    autor = email_de(c["autor"]) or entorno.get("GIT_AUTHOR_EMAIL") or cfg_email.get("user.email")
    committer = entorno.get("GIT_COMMITTER_EMAIL") or cfg_email.get("user.email")
    if not autor or not committer:
        configurado = git(["config", "user.email"], cwd)[1].strip()
        autor, committer = autor or configurado, committer or configurado
    for papel, em in (("autor", autor), ("committer", committer)):
        if em and not email_autor_ok(em, cfg):
            preguntar.append(f"el email de {papel} del commit no es el noreply de GitHub ni de la lista publica: "
                             "quedara publico en GitHub (recomendado: <id>+<usuario>@users.noreply.github.com)")
            break

    preguntar += publicados(raiz, nuevos, cfg)
    denegar += gitleaks(raiz, ["git", "--pre-commit", "--staged"])
    return denegar, preguntar


def email_autor_ok(em, cfg):
    dom = em.lower().rsplit("@", 1)[-1]
    return "@" in em and any(dom == d or dom.endswith("." + d) for d in cfg.get("autores", {}).get("dominios", []))


def publicados(raiz, nuevos, cfg):
    nuevos = sorted(set(nuevos))
    if not nuevos:
        return []
    fuera = excluidos_por_vercel(raiz, nuevos)
    sueltos = [f for f in nuevos if f not in fuera and not casa(f, cfg.get("publicacion_esperada", []))]
    if not sueltos:
        return []
    base = cfg.get("dominio_publicado", "")
    return ["ficheros nuevos que Vercel publicaria y no son contenido web (anadelos a .vercelignore si no deben "
            "verse): " + ", ".join(f"{f} -> {base}{f}" for f in sueltos[:6])]


def gitleaks(raiz, args):
    exe = shutil.which("gitleaks")
    if not exe:
        return []
    try:
        p = subprocess.run([exe] + args + ["--redact", "--no-banner", "--exit-code", "3", raiz], cwd=raiz,
                           capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return [f"gitleaks no pudo ejecutarse ({type(e).__name__}): revisa a mano o quitalo del PATH"]
    if p.returncode == 3:
        n = len(re.findall(r"^Finding:", p.stdout.decode("utf-8", "replace"), re.M)) or "algun"
        return [f"secreto: gitleaks encontro {n} hallazgo(s); ejecuta gitleaks con --redact para ver donde"]
    if p.returncode != 0:
        return [f"gitleaks fallo (codigo {p.returncode}): revisa a mano o quitalo del PATH"]
    return []


# ---------------------------------------------------------------- push


def analizar_push(args):
    r = {"forzado": False, "todo": False, "borrar": False, "remoto": None, "refspecs": []}
    i = 0
    posicionales = []
    while i < len(args):
        a = args[i]
        if a in ("--force", "--force-if-includes") or a.startswith("--force-with-lease"):
            r["forzado"] = True
        elif a in ("--all", "--mirror", "--branches"):
            r["todo"] = True
        elif a in ("--delete",):
            r["borrar"] = True
        elif a in ("-o", "--push-option", "--repo", "--receive-pack", "--exec"):
            i += 1
        elif a.startswith("--"):
            pass
        elif a.startswith("-") and len(a) > 1:
            letras = a[1:]
            if "f" in letras:
                r["forzado"] = True
            if "d" in letras:
                r["borrar"] = True
            if "o" in letras:
                i += 1
        else:
            posicionales.append(a)
        i += 1
    if posicionales:
        r["remoto"], r["refspecs"] = posicionales[0], posicionales[1:]
    return r


def revisar_push(raiz, cwd, g, cfg, rev, principal):
    p = analizar_push(g[3])
    rama = git(["symbolic-ref", "--short", "-q", "HEAD"], cwd)[1].strip()
    if p["forzado"] or any(x.startswith("+") for x in p["refspecs"]):
        return ["git push forzado: reescribe historia publica. Prohibido desde la sesion."], []
    if p["todo"]:
        return ["git push --all/--mirror/--branches empujaria tambien la rama principal. Prohibido."], []
    fuentes = []
    for spec in p["refspecs"] or [""]:
        src, _, dst = spec.partition(":")
        if not spec:
            src, dst = "HEAD", rama
        elif ":" not in spec:
            dst = rama if spec == "HEAD" else spec
        src = src or ""
        dst = re.sub(r"^refs/heads/", "", dst or "")
        if dst == "HEAD":
            dst = rama
        if dst in principal:
            return [f"git push a {'/'.join(principal)} (o que la borra): prohibido. Se integra con un PR."], []
        if src:
            fuentes.append(src)
    denegar, preguntar = [], []
    commits = [x for x in git(["rev-list", "--max-count", str(MAX_COMMITS + 1)] + fuentes + ["--not", "--remotes"], cwd)[1].split() if x] if fuentes else []
    if len(commits) > MAX_COMMITS:
        preguntar.append(f"mas de {MAX_COMMITS} commits sin publicar: el guard no los revisa todos")
    elif commits:
        rango = fuentes + ["--not", "--remotes"]
        log = git(["log", "-p", "--unified=0", "--no-color", "--no-ext-diff", "--format=commit %H"] + rango, cwd)[1]
        denegar += [f"{tipo}: {d}" for tipo, d in rev.lineas(lineas_anadidas(log))]
        mensajes = git(["log", "--format=%B%x00"] + rango, cwd)[1]
        denegar += [f"{tipo}: {d}" for tipo, d in rev.lineas([("(mensaje de commit)", 0, l) for l in mensajes.splitlines()])]
        nombres = [x for x in git(["log", "--name-only", "--format=", "--diff-filter=AMR"] + rango, cwd)[1].splitlines() if x]
        prohibidos = sorted({f for f in nombres if casa(f, cfg.get("ficheros_prohibidos", [])) and not casa(f, cfg.get("ficheros_permitidos", []))})
        if prohibidos:
            denegar.append("ficheros que no se publican nunca en estos commits: " + ", ".join(prohibidos[:8]))
        emails = set(git(["log", "--format=%ae%n%ce"] + rango, cwd)[1].split())
        if any(not email_autor_ok(e, cfg) for e in emails):
            preguntar.append("hay commits con email de autor o committer fuera del noreply de GitHub y de la lista "
                             "publica: quedara publico en GitHub")
        nuevos = [x for x in git(["log", "--name-only", "--format=", "--diff-filter=A"] + rango, cwd)[1].splitlines() if x]
        preguntar += publicados(raiz, nuevos, cfg)
        denegar += gitleaks(raiz, ["git", f"--log-opts={' '.join(rango)}"])
    destino = ", ".join(p["refspecs"]) or rama or "la rama actual"
    preguntar.insert(0, f"git push de {destino}: publica en GitHub (repo publico); pide permiso (C-4)")
    return denegar, preguntar


# ---------------------------------------------------------------- modos


def evento():
    return json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")


def proyecto(ev):
    return raiz_de(os.environ.get("CLAUDE_PROJECT_DIR") or ev.get("cwd") or os.getcwd())


def pre_git(ev):
    cmd = ((ev.get("tool_input") or {}).get("command") or "")
    if not re.search(r"\bgit(?:\.exe)?\b", cmd, re.I):
        return
    segs = segmentos(cmd)
    llamadas = [(i, llamada_git(tokens(s))) for i, s in enumerate(segs)]
    llamadas = [(i, g) for i, g in llamadas if g and g[2] in ("commit", "push")]
    if not llamadas:
        return
    cfg = cargar_allow()
    internos, extra = cargar_internos()
    rev = Revisor(cfg, internos, extra)
    raiz_proy = proyecto(ev)
    principal = ["main"]
    try:
        with open(os.path.join(raiz_proy or AQUI, ".claude", "repo-config.json"), encoding="utf-8") as f:
            rp = json.load(f).get("git", {}).get("rama_principal", "main")
            principal = [rp] if isinstance(rp, str) else list(rp)
    except (OSError, ValueError):
        pass
    denegar, preguntar = [], []
    base = ev.get("cwd") or os.getcwd()
    for i, g in llamadas:
        cwd = base
        for o, v in g[1]:
            if o == "-C" and v:
                cwd = os.path.join(cwd, v)
        raiz = raiz_de(cwd)
        if not raiz or raiz != raiz_proy:
            continue  # otro repo: no es el publico
        d, p = (revisar_commit(raiz, cwd, g, segs, i, cfg, rev) if g[2] == "commit"
                else revisar_push(raiz, cwd, g, cfg, rev, principal))
        denegar += d
        preguntar += p
    if denegar:
        decidir("deny", "Este repo es PUBLICO. No se puede " + ("commitear" if llamadas[0][1][2] == "commit" else "empujar")
                + " porque: " + "; ".join(dict.fromkeys(denegar))[:1800]
                + ". Quitalo del cambio (no lo rodees con otro comando) o, si es un falso positivo, anade la direccion o la "
                  "excepcion a .claude/hooks/public_guard.allow.json.")
    if preguntar:
        decidir("ask", "; ".join(dict.fromkeys(preguntar))[:1800])


def relativa(ruta, raiz):
    if not ruta or not raiz:
        return None
    absoluta = os.path.normcase(os.path.realpath(ruta))
    if not absoluta.startswith(raiz + os.sep):
        return None
    return absoluta[len(raiz) + 1:].replace("\\", "/")


def rel_real(ruta, raiz):
    """Ruta relativa con las mayusculas del disco (normcase las pierde en Windows)."""
    rel = relativa(ruta, raiz)
    if rel is None:
        return None
    real = os.path.realpath(ruta).replace("\\", "/")
    return real[len(real) - len(rel):]


def pre_edit(ev):
    ti = ev.get("tool_input") or {}
    ruta = ti.get("file_path") or ti.get("notebook_path") or ""
    raiz = proyecto(ev)
    rel = rel_real(ruta, raiz)
    if rel is None or not rel.lower().startswith("supabase/migrations/"):
        return
    if ev.get("tool_name") in ("Edit", "MultiEdit") or os.path.exists(ruta):
        decidir("deny", f"{rel} es una migracion ya aplicada en la base de datos de produccion: no se edita. "
                        "Crea una nueva supabase/migrations/YYYYMMDDHHMMSS_<nombre>.sql (ver .claude/rules/supabase.md).")


def post_edit(ev):
    ti = ev.get("tool_input") or {}
    ruta = ti.get("file_path") or ""
    raiz = proyecto(ev)
    rel = rel_real(ruta, raiz)
    if rel is None or not os.path.isfile(ruta):
        return
    if git(["check-ignore", "-q", "--", rel], raiz)[0] == 0:
        return  # git lo ignora: no se commitea
    cfg = cargar_allow()
    avisos = []
    if casa(rel, cfg.get("ficheros_prohibidos", [])) and not casa(rel, cfg.get("ficheros_permitidos", [])):
        avisos.append(f"{rel} es un fichero que no se commitea nunca en este repo")
    texto = texto_de(ruta)
    rc, anterior = git(["show", f"HEAD:{rel}"], raiz)
    if texto is not None:
        previas = set(anterior.splitlines()) if rc == 0 else set()
        items = [(rel, n, l) for n, l in enumerate(texto.splitlines(), 1) if l not in previas]
        internos, extra = cargar_internos()
        avisos += [f"{tipo}: {d}" for tipo, d in Revisor(cfg, internos, extra).lineas(items)]
    if rc != 0:
        avisos += publicados(raiz, [rel], cfg)
    if avisos:
        salir(codigo=2, stderr=f"{PREFIJO} Repo PUBLICO: esto se bloqueara al commitear o se publicara. Corrigelo ahora: "
                                + "; ".join(dict.fromkeys(avisos))[:1800] + "\n")


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        ev = evento()
        if modo == "pre-git":
            pre_git(ev)
        elif modo == "pre-edit":
            pre_edit(ev)
        elif modo == "post-edit":
            post_edit(ev)
        else:
            raise ValueError(f"modo desconocido: {modo!r}")
    except SystemExit:
        raise
    except Exception as e:  # C-3: un guard que falla no deja pasar
        if modo == "post-edit":
            salir(codigo=0)
        decidir("deny", f"el guard fallo ({type(e).__name__}: {str(e)[:200]}); se bloquea por seguridad. "
                        "Revisa .claude/hooks/public_guard.py y public_guard.allow.json.")
    salir()


if __name__ == "__main__":
    main()
