"""public_guard.py: guard de repo publico (hooks de Claude Code de trAIn-Landing). Solo stdlib.

Este repo es publico en GitHub y Vercel publica en el dominio todo lo que .vercelignore no excluye.
Modos (primer argumento):
  pre-git    PreToolUse de Bash y PowerShell (todos los comandos, sin filtro `if`). El comando se
             analiza con el mismo analizador que guard_core.py (comillas, escapes, variables, `cd`,
             `bash -c`, `cmd /c`, `$(...)`, subshells, `timeout`, `env`...), asi que cuenta cualquier
             llamada a git, este donde este. Actua en `git commit`, `git push` y `git am` (tambien
             por alias, de la configuracion o de `-c alias.*`) del repo del proyecto o de uno de sus
             worktrees (`-C`, `--git-dir`, `--work-tree`); con lo demas sale sin decir nada.
  pre-edit   PreToolUse de Edit/Write/MultiEdit: las migraciones de supabase/migrations/ que ya existen
             no se editan (se crea una nueva). Lo demas no lo mira.
  post-edit  PostToolUse de Write/Edit/MultiEdit: revisa las lineas nuevas del fichero editado y avisa
             (no bloquea) de lo que se bloquearia al commitear, y de si Vercel lo publicaria.

Al commitear o empujar revisa solo lo que se ANADE (lo que ya estaba publicado no cuenta):
  deny  secretos (JWT con role distinto de anon, claves con prefijo conocido, claves privadas,
        asignaciones de claves con valor), ficheros prohibidos (.env, *.key, CLAUDE.local.md...),
        rutas locales de usuario, emails fuera de public_guard.allow.json y terminos internos de
        ~/.claude/lmginc/public-guard.local.json (fuera del repo); push forzado, push a main,
        --all y --mirror.
  ask   autor o committer con email fuera de la lista publica (queda publico en GitHub); ficheros
        nuevos que Vercel publicaria y no son contenido web; falta la lista local de terminos
        internos; lo que el guard no puede ver antes de que ocurra (el mismo comando escribe
        ficheros o cambia el indice antes del commit, mensaje calculado o por la entrada sin texto
        visible, alias de shell, git am); cualquier otro push (politica git comun).
El push se revisa contra lo que el remoto TIENE de verdad (git ls-remote de la URL de push), no
contra refs/remotes, que una ref local puede falsear; incluye las etiquetas de --tags, --follow-tags
y refs/tags/*. Si el remoto no responde, revisa contra refs/remotes/<remoto> y pregunta.
La clave anon de Supabase de app.js se acepta porque su payload dice role=anon; el valor no esta aqui.
Nunca imprime el valor encontrado: solo fichero:linea y el tipo. Si gitleaks esta en el PATH, se
ejecuta tambien (salida --redact) y sus hallazgos deniegan. Un fallo del guard deniega.
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
LISTA_LOCAL = "~/.claude/lmginc/public-guard.local.json"

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


def git(args, cwd, entrada=None, timeout=20, env=None):
    p = subprocess.run(["git", "-c", "safe.directory=*", "-c", "core.quotepath=off"] + args, cwd=cwd,
                       input=entrada, capture_output=True, timeout=timeout, env=env)
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
    """Lista local de terminos internos. LMGINC_PUBLIC_GUARD_LOCAL, si esta definida, manda sola (relativa
    a la raiz del proyecto si no es absoluta; si no existe, cuenta como que falta la lista)."""
    forzada = os.environ.get("LMGINC_PUBLIC_GUARD_LOCAL", "")
    if forzada:
        if not os.path.isabs(forzada):
            forzada = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd(), forzada)
        return forzada if os.path.isfile(forzada) else None
    cands = []
    for base in (os.path.expanduser("~"), os.environ.get("USERPROFILE", ""), os.environ.get("HOME", "")):
        if base:
            cands.append(os.path.join(base, ".claude", "lmginc", "public-guard.local.json"))
    return next((c for c in cands if os.path.isfile(c)), None)


def cargar_internos():
    """(patrones, direcciones extra permitidas, hay_lista) del fichero personal."""
    ruta = ruta_local()
    if not ruta:
        return [], [], False
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    pats = [re.compile(r"(?<![A-Za-z0-9_])" + re.escape(t) + r"(?![A-Za-z0-9_])", re.I)
            for t in datos.get("terminos", []) if t]
    pats += [re.compile(r, re.I) for r in datos.get("regex", []) if r]
    return pats, [e.lower() for e in datos.get("emails_publicos_extra", [])], True


FALTA_LISTA = (f"falta la lista local de terminos internos ({LISTA_LOCAL}): sin ella el guard no detecta nombres "
               "internos (repos privados, proyectos, personas, enlaces internos). Instalala con la configuracion de "
               "maquina del equipo antes de publicar")


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


def analizador():
    """Clase que recorre el comando con el analizador de guard_core y guarda cada llamada a git."""
    sys.path.insert(0, AQUI)
    import guard_core as gc  # noqa: E402  (mismo analizador que el guard de comandos del repo)
    from repo_config import ConfigError, cargar  # noqa: E402

    class Recolector(gc.Analisis):
        def __init__(self, *a):
            super().__init__(*a)
            self.gits, self.heredocs = [], []

        def especificos(self, exe, args, entorno, modo, prof, stdin, tuberia):
            if exe == "git":
                self.gits.append({"args": [{"s": t["s"], "din": t["din"]} for t in args],
                                  "entorno": self.entorno_con(entorno), "cwd": self.cwd, "stdin": stdin,
                                  "destinos": list(self.destinos)})
            elif exe == "cat" and stdin is not None:
                self.heredocs.append(stdin)
            super().especificos(exe, args, entorno, modo, prof, stdin, tuberia)

    return gc, cargar, ConfigError, Recolector


GLOBALES_CON_VALOR = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env", "--super-prefix"}
INTERNOS_GIT = {
    "add", "am", "apply", "archive", "bisect", "blame", "branch", "bundle", "cat-file", "check-ignore", "checkout",
    "cherry", "cherry-pick", "clean", "clone", "commit", "commit-tree", "config", "describe", "diff", "difftool",
    "fetch", "for-each-ref", "format-patch", "fsck", "gc", "grep", "help", "init", "log", "ls-files", "ls-remote",
    "ls-tree", "merge", "merge-base", "mv", "notes", "pull", "push", "range-diff", "read-tree", "rebase", "reflog",
    "remote", "reset", "restore", "rev-list", "rev-parse", "revert", "rm", "shortlog", "show", "show-ref", "sparse-checkout",
    "stash", "status", "submodule", "switch", "symbolic-ref", "tag", "update-index", "update-ref", "version",
    "whatchanged", "worktree", "write-tree"}
# Lo que, en el mismo comando y antes del commit, cambia el indice o el arbol sin que el guard lo vea.
CAMBIAN_ANTES = {"apply", "am", "restore", "stash", "cherry-pick", "merge", "pull", "revert", "read-tree",
                 "update-index", "mv", "checkout", "rebase", "notes"}
EMAILS_CONFIG = ("user.email", "author.email", "committer.email")


class Repo:
    """Donde y como ejecutar git para una llamada (carpeta y --git-dir/--work-tree ya absolutos)."""

    def __init__(self, cwd, opts):
        self.cwd, self.opts = cwd, opts

    def run(self, args, entrada=None, timeout=20, env=None, cwd=None):
        return git(self.opts + args, cwd or self.cwd, entrada, timeout, env)

    def valor(self, args):
        rc, out = self.run(args)
        return out.strip() if rc == 0 else ""


def unir(base, ruta):
    return os.path.normpath(ruta if os.path.isabs(ruta) else os.path.join(base, ruta))


def globales(tokens, cwd):
    """(Repo, config de -c, resto de tokens desde el subcomando) de una llamada a git ya analizada."""
    d, opts, cfg_c, i = cwd, [], {}, 0
    git_dir = work_tree = None
    while i < len(tokens) and tokens[i]["s"].startswith("-"):
        t = tokens[i]["s"]
        nombre, igual, valor = t.partition("=")
        if nombre in GLOBALES_CON_VALOR and not igual:
            valor = tokens[i + 1]["s"] if i + 1 < len(tokens) else ""
            i += 1
        if nombre == "-C":
            d = unir(d, valor)
        elif nombre == "-c":
            clave, _, v = valor.partition("=")
            cfg_c[clave.lower()] = v
        elif nombre == "--git-dir":
            git_dir = valor
        elif nombre == "--work-tree":
            work_tree = valor
        i += 1
    if git_dir:
        opts += ["--git-dir", unir(d, git_dir)]
    if work_tree:
        opts += ["--work-tree", unir(d, work_tree)]
    return Repo(d, opts), cfg_c, tokens[i:]


def expandir_alias(resto, repo, cfg_c):
    """(subcomando, argumentos, problema). Sigue los alias (de -c alias.x o de la config del repo)."""
    for _ in range(6):
        if not resto:
            return "", [], None
        sub = resto[0]["s"]
        if resto[0]["din"]:
            return sub, resto[1:], "git con un subcomando calculado"
        if sub.lower() in INTERNOS_GIT:
            return sub.lower(), resto[1:], None
        valor = cfg_c.get(f"alias.{sub.lower()}")
        if valor is None and os.path.isdir(repo.cwd):
            valor = repo.valor(["config", "--get", f"alias.{sub}"]) or None
        if not valor:
            return sub.lower(), resto[1:], None
        if valor.startswith("!"):
            return sub.lower(), resto[1:], f"alias de git '{sub}' que ejecuta un comando del shell"
        try:
            partes = shlex.split(valor)
        except ValueError:
            return sub.lower(), resto[1:], f"alias de git '{sub}' ilegible"
        resto = [{"s": p, "din": False} for p in partes] + resto[1:]
    return "", [], "cadena de alias de git demasiado larga"


def dir_comun(repo):
    rc, out = repo.run(["rev-parse", "--path-format=absolute", "--git-common-dir"])
    return os.path.normcase(os.path.realpath(out.strip())) if rc == 0 and out.strip() else None


def entorno_de(llamada, nombre):
    v = llamada["entorno"].get(nombre)
    return v if nombre in llamada["entorno"] else os.environ.get(nombre)


def larga(nombre, opciones):
    """Opcion larga, tambien abreviada como la acepta git ('--mess' -> '--message')."""
    if nombre in opciones:
        return nombre
    candidatas = [o for o in opciones if o.startswith(nombre)] if len(nombre) >= 4 else []
    return candidatas[0] if len(candidatas) == 1 else None


def escrituras_reales(destinos):
    return [t for t, _ in destinos if (t.get("s") or "").lower() not in ("/dev/null", "nul", "/dev/stdout", "/dev/stderr")]


# ---------------------------------------------------------------- commit

COMMIT_LARGAS = {"--message": "m", "--file": "F", "--author": "autor", "--trailer": "trailer", "--template": "F",
                 "--reuse-message": None, "--reedit-message": None, "--fixup": None, "--squash": None, "--date": None,
                 "--cleanup": None, "--pathspec-from-file": "psf", "--gpg-sign": "opt", "--untracked-files": "opt"}
COMMIT_SIN_VALOR = {"--all": "todo", "--allow-empty": "vacio", "--allow-empty-message": None, "--amend": "amend",
                    "--include": None, "--only": None, "--no-edit": None, "--edit": None, "--no-verify": None,
                    "--signoff": None, "--reset-author": None, "--dry-run": None, "--quiet": None, "--verbose": None}


def analizar_commit(args):
    r = {"todo": False, "vacio": False, "amend": False, "mensajes": [], "ficheros": [], "trailers": [], "autor": None,
         "rutas": [], "psf": False}
    con_valor = {"m": "m", "F": "F", "c": None, "C": None, "t": "F"}
    i, tras_guiones = 0, False
    while i < len(args):
        tok = args[i]
        a = tok["s"]
        if tras_guiones or not a.startswith("-") or a == "-":
            r["rutas"].append(a)
        elif a == "--":
            tras_guiones = True
        elif a.startswith("--"):
            nombre, igual, valor = a.partition("=")
            o = larga(nombre, list(COMMIT_LARGAS) + list(COMMIT_SIN_VALOR))
            if o in COMMIT_SIN_VALOR:
                if COMMIT_SIN_VALOR[o]:
                    r[COMMIT_SIN_VALOR[o]] = True
            elif o in COMMIT_LARGAS:
                vt = {"s": valor, "din": tok["din"]}
                if not igual and COMMIT_LARGAS[o] != "opt":
                    vt = args[i + 1] if i + 1 < len(args) else {"s": "", "din": False}
                    i += 1
                guardar_commit(r, COMMIT_LARGAS[o], vt)
        else:
            j = 1
            while j < len(a):
                ch = a[j]
                if ch == "a":
                    r["todo"] = True
                if ch in con_valor:
                    vt = {"s": a[j + 1:], "din": tok["din"]}
                    if not vt["s"]:
                        vt = args[i + 1] if i + 1 < len(args) else {"s": "", "din": False}
                        i += 1
                    guardar_commit(r, con_valor[ch], vt)
                    break
                j += 1
        i += 1
    return r


def guardar_commit(r, destino, vt):
    if destino == "m":
        r["mensajes"].append(vt)
    elif destino == "F":
        r["ficheros"].append(vt)
    elif destino == "trailer":
        r["trailers"].append(vt)
    elif destino == "autor":
        r["autor"] = vt
    elif destino == "psf":
        r["psf"] = True


def email_de(texto):
    m = re.search(r"<([^>]*)>", texto or "")
    return (m.group(1) if m else (texto or "")).strip()


def pendientes_de_add(previas):
    """[(Repo, pathspecs, forzado)] de los `git add` anteriores del mismo comando."""
    out = []
    for p in previas:
        if p["sub"] != "add":
            continue
        rutas = [a["s"] for a in p["args"] if not a["s"].startswith("-")]
        forzado = any(a["s"] in ("-f", "--force") or (a["s"].startswith("-") and not a["s"].startswith("--")
                                                       and "f" in a["s"][1:]) for a in p["args"])
        out.append((p["repo"], rutas or ["."], forzado))
    return out


def config_del_comando(previas):
    """Emails que un `git config` anterior del mismo comando deja puestos (el hook corre antes que el)."""
    puestos = {}
    for p in previas:
        if p["sub"] != "config":
            continue
        vals = [a["s"] for a in p["args"] if not a["s"].startswith("-")]
        if any(a["s"] in ("--unset", "--unset-all", "--get", "--get-all", "-l", "--list") for a in p["args"]):
            continue
        if len(vals) >= 2 and vals[0].lower() in EMAILS_CONFIG:
            puestos[vals[0].lower()] = vals[1]
    return puestos


def revisar_commit(llamada, previas, an, cfg, rev, hay_lista):
    repo = llamada["repo"]
    raiz = llamada["raiz"]
    raiz_repo = Repo(raiz, repo.opts)
    c = analizar_commit(llamada["args"])
    denegar, preguntar = [], []

    staged = raiz_repo.run(["diff", "--cached", "--unified=0", "--no-color", "--no-ext-diff", "-M"])[1]
    items = lineas_anadidas(staged)
    nuevos = [x for x in raiz_repo.run(["diff", "--cached", "--name-only", "--diff-filter=A", "-M"])[1].splitlines() if x]
    nombres = [x for x in raiz_repo.run(["diff", "--cached", "--name-only", "--diff-filter=d", "-M"])[1].splitlines() if x]
    hay_staged = bool(nombres) or raiz_repo.run(["diff", "--cached", "--quiet"])[0] != 0

    # Lo que el mismo comando va a anadir antes de commitear (commit -a, commit <rutas>, git add ... && commit).
    adds = pendientes_de_add(previas)
    pendientes = []
    if c["todo"] or c["psf"]:
        pendientes.append((raiz_repo, []))
    if c["rutas"]:
        pendientes.append((repo, c["rutas"]))
    pendientes += [(r, rutas) for r, rutas, _ in adds]
    for donde, rutas in pendientes:
        items += lineas_anadidas(donde.run(["diff", "--unified=0", "--no-color", "--no-ext-diff", "--"] + rutas)[1])
        nombres += [x for x in donde.run(["diff", "--name-only", "--diff-filter=d", "--"] + rutas)[1].splitlines() if x]
    for donde, rutas, forzado in adds:
        lista = ["ls-files", "-o", "--full-name"] + ([] if forzado else ["--exclude-standard"]) + ["--"] + rutas
        for rel in [x for x in donde.run(lista)[1].splitlines() if x]:
            nuevos.append(rel)
            nombres.append(rel)
            t = texto_de(os.path.join(raiz, rel))
            if t is not None:
                items += [(rel, n, l) for n, l in enumerate(t.splitlines(), 1)]

    nombres = list(dict.fromkeys(nombres + nuevos))
    prohibidos = [f for f in nombres if casa(f, cfg.get("ficheros_prohibidos", [])) and not casa(f, cfg.get("ficheros_permitidos", []))]
    if prohibidos:
        denegar.append("ficheros que no se commitean nunca: " + ", ".join(prohibidos[:8]))

    # Mensaje: -m, -F, --trailer; lo calculado ($(...)) solo se acepta si es un heredoc literal (cat <<'EOF').
    no_revisable = []
    textos = []
    for vt in c["mensajes"] + c["trailers"]:
        if vt["din"]:
            if an.construcciones or not an.heredocs:
                no_revisable.append("mensaje del commit calculado ($(...), variable)")
            else:
                textos += an.heredocs
        else:
            textos.append(vt["s"])
    for vt in c["ficheros"]:
        if vt["din"]:
            no_revisable.append("fichero de mensaje calculado")
        elif vt["s"] == "-":
            if llamada["stdin"] is None:
                no_revisable.append("mensaje por la entrada estandar (-F -) sin texto visible en el comando")
            else:
                textos.append(llamada["stdin"])
        elif vt["s"]:
            t = texto_de(unir(repo.cwd, vt["s"]))
            if t:
                textos.append(t)
    for t in textos:
        items += [("(mensaje del commit)", 0, l) for l in t.splitlines()]
    hallazgos = rev.lineas(items)
    denegar += [f"{tipo}: {d}" for tipo, d in hallazgos]

    # Lo que el guard no puede ver: escrituras o cambios del indice antes del commit en el mismo comando.
    escrito = escrituras_reales(llamada["destinos"])
    if escrito:
        no_revisable.append("el mismo comando escribe ficheros antes de commitear ("
                            + ", ".join(t.get("s") or "?" for t in escrito[:3]) + ")")
    cambian = sorted({p["sub"] for p in previas if p["sub"] in CAMBIAN_ANTES})
    if cambian:
        no_revisable.append("el mismo comando cambia el arbol o el indice antes de commitear (git " + ", git ".join(cambian) + ")")

    amend = c["amend"] and raiz_repo.run(["rev-parse", "-q", "--verify", "HEAD"])[0] == 0
    crea = hay_staged or c["todo"] or c["psf"] or bool(c["rutas"]) or bool(adds) or c["vacio"] or amend \
        or bool(escrito) or bool(cambian)
    if not crea:
        return denegar, []  # git rechazara el commit (nada que commitear): solo cuenta lo que ya se deniega

    # Autoria: queda publica en GitHub.
    puestos = config_del_comando(previas)

    def conf(clave):
        if clave in llamada["cfg_c"]:
            return llamada["cfg_c"][clave]
        return puestos.get(clave) or repo.valor(["config", "--get", clave])

    if c["autor"] is not None and c["autor"]["din"]:
        preguntar.append("autor del commit calculado: no se puede comprobar que no sea un email personal")
    autor = (email_de(c["autor"]["s"]) if c["autor"] is not None else "") or entorno_de(llamada, "GIT_AUTHOR_EMAIL") \
        or conf("author.email") or conf("user.email") or entorno_de(llamada, "EMAIL")
    committer = entorno_de(llamada, "GIT_COMMITTER_EMAIL") or conf("committer.email") or conf("user.email") \
        or entorno_de(llamada, "EMAIL")
    for papel, em in (("autor", autor), ("committer", committer)):
        if em and not email_autor_ok(em, cfg):
            preguntar.append(f"el email de {papel} del commit no es el noreply de GitHub: quedara publico en GitHub "
                             "(recomendado: <id>+<usuario>@users.noreply.github.com)")
            break
    preguntar += [f"{x}: el guard no puede revisarlo antes; separa los pasos" for x in no_revisable]
    if not hay_lista:
        preguntar.append(FALTA_LISTA)
    preguntar += publicados(raiz, nuevos, cfg)
    denegar += gitleaks(raiz, ["git", "--pre-commit", "--staged"])
    return denegar, preguntar


# ---------------------------------------------------------------- push

PUSH_CON_VALOR = ("--push-option", "--repo", "--receive-pack", "--exec", "--recurse-submodules")
PUSH_LARGAS = ("--force", "--force-with-lease", "--force-if-includes", "--mirror", "--all", "--branches", "--delete",
               "--tags", "--follow-tags", "--dry-run", "--set-upstream", "--no-follow-tags") + PUSH_CON_VALOR


def analizar_push(args):
    r = {"forzado": False, "todo": False, "borrar": False, "tags": False, "follow": None, "remoto": None, "refspecs": [],
         "din": False}
    i, pos = 0, []
    while i < len(args):
        a = args[i]["s"]
        if a.startswith("--") and len(a) > 2:
            nombre, igual, valor = a.partition("=")
            o = larga(nombre, PUSH_LARGAS)
            if o in ("--force", "--force-with-lease", "--force-if-includes"):
                r["forzado"] = True
            elif o in ("--all", "--mirror", "--branches"):
                r["todo"] = True
            elif o == "--delete":
                r["borrar"] = True
            elif o == "--tags":
                r["tags"] = True
            elif o == "--follow-tags":
                r["follow"] = True
            elif o == "--no-follow-tags":
                r["follow"] = False
            elif o == "--repo":
                if not igual:
                    valor = args[i + 1]["s"] if i + 1 < len(args) else ""
                    i += 1
                pos.insert(0, valor)
            elif o in PUSH_CON_VALOR and not igual:
                i += 1
        elif a.startswith("-") and len(a) > 1:
            letras = a[1:]
            r["forzado"] = r["forzado"] or "f" in letras
            r["borrar"] = r["borrar"] or "d" in letras
            if letras.endswith("o"):
                i += 1
        else:
            pos.append(a)
            r["din"] = r["din"] or args[i]["din"]
        i += 1
    if pos:
        r["remoto"], r["refspecs"] = pos[0], pos[1:]
    return r


def refs_del_remoto(repo, remoto, entorno_git):
    """(shas que el remoto tiene y existen aqui, aviso o None). Pregunta al remoto de verdad (ls-remote de la URL
    de push) y, si no responde, usa refs/remotes/<remoto> avisando de que se puede falsear."""
    es_nombre = bool(repo.valor(["config", "--get", f"remote.{remoto}.url"]))
    url = repo.valor(["remote", "get-url", "--push", remoto]) if es_nombre else remoto
    shas, aviso = set(), None
    seguros = ["-c", "protocol.allow=never", "-c", "protocol.https.allow=always", "-c", "protocol.ssh.allow=always",
               "-c", "protocol.git.allow=always", "-c", "protocol.file.allow=always"]
    rc, out = (1, "")
    if url and not url.startswith("-"):
        try:
            rc, out = repo.run(seguros + ["ls-remote", "--", url], timeout=15, env=entorno_git)
        except subprocess.TimeoutExpired:
            rc = 1
    if rc == 0:
        shas = {l.split()[0] for l in out.splitlines() if l.strip()}
    else:
        aviso = (f"no he podido consultar el remoto '{remoto}': reviso contra refs/remotes/{remoto}, que una ref local "
                 "puede falsear; confirma que no sale nada mas")
        if es_nombre:
            out = repo.run(["for-each-ref", "--format=%(objectname)", f"refs/remotes/{remoto}/"])[1]
            shas = set(out.split())
    if shas:
        lote = repo.run(["cat-file", "--batch-check"], entrada=("\n".join(sorted(shas)) + "\n").encode())[1]
        shas = {l.split()[0] for l in lote.splitlines() if l.strip() and not l.endswith("missing")}
    return shas, aviso


def revisar_push(llamada, cfg, rev, principal, hay_lista):
    repo = llamada["repo"]
    raiz = llamada["raiz"]
    p = analizar_push(llamada["args"])
    rama = repo.valor(["symbolic-ref", "--short", "-q", "HEAD"])
    if p["forzado"] or any(x.startswith("+") for x in p["refspecs"]):
        return ["git push forzado: reescribe historia publica. Prohibido desde la sesion."], []
    remoto = p["remoto"]
    if not remoto:
        remoto = (repo.valor(["config", "--get", f"branch.{rama}.pushRemote"]) if rama else "") \
            or repo.valor(["config", "--get", "remote.pushDefault"]) \
            or (repo.valor(["config", "--get", f"branch.{rama}.remote"]) if rama else "") or "origin"
    if p["todo"] or repo.valor(["config", "--bool", "--get", f"remote.{remoto}.mirror"]) == "true":
        return ["git push --all/--mirror/--branches empujaria tambien la rama principal. Prohibido."], []
    preguntar = []
    if p["din"]:
        preguntar.append("git push con un destino calculado: no puedo comprobar que sale")
    fuentes = []
    refspecs = list(p["refspecs"])
    if not refspecs and repo.valor(["config", "--get", f"remote.{remoto}.push"]):
        preguntar.append(f"remote.{remoto}.push esta configurado: el guard no calcula los destinos; revisa a donde va")
    # Sin refspec se empuja la rama actual, salvo con --tags (entonces solo salen las etiquetas).
    for spec in refspecs or ([] if p["tags"] else [""]):
        src, dos_puntos, dst = spec.partition(":")
        if not spec:
            src, dst = "HEAD", rama
        elif p["borrar"]:
            src, dst = "", spec
        elif not dos_puntos:
            dst = spec
        if src in ("@", "HEAD"):
            src = "HEAD"
        dst = re.sub(r"^(?:refs/)?heads/", "", dst or "")
        if dst in ("HEAD", "@"):
            dst = rama
        if dst in principal or any(re.search(r"[*?\[]", dst) and glob_a_regex(dst).match(x) for x in principal):
            return [f"git push a {'/'.join(principal)} (o que la borra): prohibido. Se integra con un PR."], []
        if src:
            fuentes.append(src)
    follow = p["follow"] if p["follow"] is not None else repo.valor(["config", "--bool", "--get", "push.followTags"]) == "true"
    etiquetas = []
    if p["tags"] or follow:
        etiquetas = [x for x in repo.run(["for-each-ref", "--format=%(refname)", "refs/tags/"])[1].split() if x]
    entorno_git = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    remoto_shas, aviso = refs_del_remoto(repo, remoto, entorno_git) if (fuentes or etiquetas) else (set(), None)
    if aviso:
        preguntar.append(aviso)
    # Etiquetas: con --tags, todas; con --follow-tags, las anotadas que apuntan a lo que se empuja.
    tag_objs = []
    for t in etiquetas + [f for f in fuentes if f.startswith("refs/tags/") or repo.valor(["rev-parse", "-q", "--verify", f"refs/tags/{f}"])]:
        sha = repo.valor(["rev-parse", "-q", "--verify", t if t.startswith("refs/") else f"refs/tags/{t}"])
        if not sha or sha in remoto_shas:
            continue
        anotada = repo.valor(["cat-file", "-t", sha]) == "tag"
        if t in etiquetas and not p["tags"]:
            if not anotada or not any(repo.run(["merge-base", "--is-ancestor", f"{sha}^{{}}", f])[0] == 0 for f in fuentes):
                continue
        fuentes.append(t)
        if anotada:
            tag_objs.append(t)
    fuentes = list(dict.fromkeys(fuentes))
    denegar = []
    entrada = ("\n".join(fuentes + ["^" + s for s in sorted(remoto_shas)]) + "\n").encode()
    commits = []
    if fuentes:
        commits = [x for x in repo.run(["rev-list", "--max-count", str(MAX_COMMITS + 1), "--stdin"], entrada=entrada)[1].split() if x]
    if len(commits) > MAX_COMMITS:
        preguntar.append(f"mas de {MAX_COMMITS} commits sin publicar: el guard no los revisa todos")
    elif commits:
        log = repo.run(["log", "-p", "--unified=0", "--no-color", "--no-ext-diff", "--format=commit %H", "--stdin"], entrada=entrada)[1]
        denegar += [f"{tipo}: {d}" for tipo, d in rev.lineas(lineas_anadidas(log))]
        mensajes = repo.run(["log", "--format=%B%x00", "--stdin"], entrada=entrada)[1]
        denegar += [f"{tipo}: {d}" for tipo, d in rev.lineas([("(mensaje de commit)", 0, l) for l in mensajes.splitlines()])]
        nombres = [x for x in repo.run(["log", "--name-only", "--format=", "--diff-filter=AMR", "--stdin"], entrada=entrada)[1].splitlines() if x]
        prohibidos = sorted({f for f in nombres if casa(f, cfg.get("ficheros_prohibidos", [])) and not casa(f, cfg.get("ficheros_permitidos", []))})
        if prohibidos:
            denegar.append("ficheros que no se publican nunca en estos commits: " + ", ".join(prohibidos[:8]))
        emails = set(repo.run(["log", "--format=%ae%n%ce", "--stdin"], entrada=entrada)[1].split())
        if any(not email_autor_ok(e, cfg) for e in emails):
            preguntar.append("hay commits con email de autor o committer fuera del noreply de GitHub: quedara publico en GitHub")
        nuevos = [x for x in repo.run(["log", "--name-only", "--format=", "--diff-filter=A", "--stdin"], entrada=entrada)[1].splitlines() if x]
        preguntar += publicados(raiz, nuevos, cfg)
        denegar += gitleaks(raiz, ["git", "--log-opts=--no-walk " + " ".join(commits)])
    for t in tag_objs:
        texto = repo.run(["for-each-ref", "--format=%(contents)", t if t.startswith("refs/") else f"refs/tags/{t}"])[1]
        denegar += [f"{tipo}: {d}" for tipo, d in rev.lineas([(f"(etiqueta {t})", 0, l) for l in texto.splitlines()])]
        tagger = email_de(repo.valor(["for-each-ref", "--format=%(taggeremail)", t if t.startswith("refs/") else f"refs/tags/{t}"]))
        if tagger and not email_autor_ok(tagger, cfg):
            preguntar.append(f"la etiqueta {t} lleva un email fuera del noreply de GitHub: quedara publico")
    if not hay_lista:
        preguntar.append(FALTA_LISTA)
    destino = ", ".join(p["refspecs"]) or rama or "la rama actual"
    extra = (" y etiquetas (" + ", ".join(e.replace("refs/tags/", "") for e in etiquetas[:5]) + ")") if etiquetas else ""
    preguntar.insert(0, f"git push de {destino}{extra}: publica en GitHub (repo publico); pide permiso")
    return denegar, preguntar


# ---------------------------------------------------------------- modos


def evento():
    return json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")


def proyecto(ev):
    return raiz_de(os.environ.get("CLAUDE_PROJECT_DIR") or ev.get("cwd") or os.getcwd())


def pre_git(ev):
    entrada = ev.get("tool_input") or {}
    if not isinstance(entrada, dict):
        raise ValueError("tool_input no es un objeto")
    cmd = entrada.get("command") or ""
    if not isinstance(cmd, str):
        raise ValueError("tool_input.command no es texto")
    if not cmd.strip():
        return
    gc, cargar, ConfigError, Recolector = analizador()
    dir_proy = os.environ.get("CLAUDE_PROJECT_DIR") or ev.get("cwd") or os.getcwd()
    cwd = ev.get("cwd") or dir_proy
    try:
        reglas = gc.compilar(cargar(dir_proy, comun=True, exigir_comun=True))
    except ConfigError as e:
        decidir("deny", f"configuracion del guard invalida, se deniega por seguridad: {e}")
        return
    an = Recolector(dir_proy, cwd, gc.Rama(cwd), reglas)
    an.analizar(cmd, "ps" if ev.get("tool_name") == "PowerShell" else "bash", 0)
    if not an.gits:
        return
    comun_proy = dir_comun(Repo(dir_proy, []))
    if not comun_proy:
        return
    llamadas, comunes = [], {}
    for g in an.gits:
        repo, cfg_c, resto = globales(g["args"], g["cwd"])
        if not os.path.isdir(repo.cwd):
            continue
        clave = (os.path.normcase(repo.cwd), tuple(repo.opts))
        if clave not in comunes:
            comunes[clave] = dir_comun(repo)
        if comunes[clave] != comun_proy:
            continue  # otro repo: no es el publico
        sub, args, problema = expandir_alias(resto, repo, cfg_c)
        llamadas.append({**g, "repo": repo, "cfg_c": cfg_c, "sub": sub, "args": args, "problema": problema})
    revisar = [x for x in llamadas if x["sub"] in ("commit", "push", "am") or x["problema"]]
    if not revisar:
        return
    cfg = cargar_allow()
    internos, extra, hay_lista = cargar_internos()
    rev = Revisor(cfg, internos, extra)
    principal = reglas["git"]["rama_principal"] or ["main"]
    denegar, preguntar = [], []
    for k, ll in enumerate(llamadas):
        if ll["problema"]:
            preguntar.append(f"{ll['problema']}: el guard no ve si commitea o empuja; pide permiso")
            continue
        if ll["sub"] not in ("commit", "push", "am"):
            continue
        ll["raiz"] = Repo(ll["repo"].cwd, ll["repo"].opts).valor(["rev-parse", "--show-toplevel"]) or ll["repo"].cwd
        if ll["sub"] == "am":
            preguntar.append("git am crea commits con un parche que el guard no ve antes: aplica el parche, revisa el "
                             "diff y commitea (o se revisara al empujar)")
            continue
        d, p = (revisar_commit(ll, llamadas[:k], an, cfg, rev, hay_lista) if ll["sub"] == "commit"
                else revisar_push(ll, cfg, rev, principal, hay_lista))
        denegar += d
        preguntar += p
    if denegar:
        que = "commitear" if any(x["sub"] == "commit" for x in llamadas) else "empujar"
        decidir("deny", f"Este repo es PUBLICO. No se puede {que} porque: " + "; ".join(dict.fromkeys(denegar))[:1800]
                + ". Quitalo del cambio (no lo rodees con otro comando) o, si es un falso positivo, anade la direccion o la "
                  "excepcion a .claude/hooks/public_guard.allow.json.")
    if preguntar:
        decidir("ask", "; ".join(dict.fromkeys(preguntar))[:1800])


def ruta_normal(ruta):
    r""" \\?\C:\x, \\.\C:\x, \\?\UNC\host\share\x y \\localhost\c$\x -> la ruta de siempre (o la misma)."""
    r = (ruta or "").replace("/", "\\")
    for pref in ("\\\\?\\UNC\\", "\\\\.\\UNC\\"):
        if r.upper().startswith(pref):
            r = "\\\\" + r[len(pref):]
    for pref in ("\\\\?\\", "\\\\.\\"):
        if r.startswith(pref):
            r = r[len(pref):]
    m = re.match(r"^\\\\(?:localhost|127\.0\.0\.1|\[?::1\]?|\.)\\([A-Za-z])\$(\\.*)?$", r, re.I)
    if m:
        r = m.group(1) + ":" + (m.group(2) or "\\")
    return r if os.name == "nt" else (ruta or "")


def relativa(ruta, raiz):
    if not ruta or not raiz:
        return None
    absoluta = os.path.normcase(os.path.realpath(ruta_normal(ruta)))
    if not absoluta.startswith(raiz + os.sep):
        return None
    return absoluta[len(raiz) + 1:].replace("\\", "/")


def rel_real(ruta, raiz):
    """Ruta relativa con las mayusculas del disco (normcase las pierde en Windows)."""
    rel = relativa(ruta, raiz)
    if rel is None:
        return None
    real = os.path.realpath(ruta_normal(ruta)).replace("\\", "/")
    return real[len(real) - len(rel):]


def migracion_aplicada(ruta, raiz):
    """La migracion existente a la que apunta la ruta (por samefile: vale para cualquier forma de escribirla)."""
    carpeta = os.path.join(raiz, "supabase", "migrations")
    if not os.path.isdir(carpeta):
        return None
    for nombre in os.listdir(carpeta):
        f = os.path.join(carpeta, nombre)
        for cand in (ruta, ruta_normal(ruta)):
            try:
                if os.path.isfile(f) and os.path.samefile(cand, f):
                    return "supabase/migrations/" + nombre
            except OSError:
                continue
    return None


def pre_edit(ev):
    ti = ev.get("tool_input") or {}
    ruta = ti.get("file_path") or ti.get("notebook_path") or ""
    raiz = proyecto(ev)
    if not raiz or not ruta:
        return
    if not os.path.isabs(ruta_normal(ruta)):
        ruta = os.path.join(ev.get("cwd") or raiz, ruta)
    rel = rel_real(ruta, raiz)
    existente = migracion_aplicada(ruta, raiz)
    if existente is None and (rel is None or not rel.lower().startswith("supabase/migrations/")):
        return
    if existente or ev.get("tool_name") in ("Edit", "MultiEdit") or os.path.exists(ruta_normal(ruta)):
        decidir("deny", f"{existente or rel} es una migracion ya aplicada en la base de datos de produccion: no se edita. "
                        "Crea una nueva supabase/migrations/YYYYMMDDHHMMSS_<nombre>.sql (ver .claude/rules/supabase.md).")


# ---------------------------------------------------------------- publicacion y gitleaks


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
        internos, extra, _ = cargar_internos()
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
    except Exception as e:  # un guard que falla no deja pasar (fallo cerrado)
        if modo == "post-edit":
            salir(codigo=0)
        decidir("deny", f"el guard fallo ({type(e).__name__}: {str(e)[:200]}); se bloquea por seguridad. "
                        "Revisa .claude/hooks/public_guard.py y public_guard.allow.json.")
    salir()


if __name__ == "__main__":
    main()
