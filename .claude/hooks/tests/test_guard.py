"""Pruebas de public_guard.py y stop_check.py sobre una copia temporal del repo (no toca el arbol real).

Uso, desde la raiz del repo:  py -3 -B .claude/hooks/tests/test_guard.py   (macOS/Linux: python3 -B ...)
Sale con 0 si todo pasa. Necesita git y Git Bash (en Windows lo localiza a partir de `git --exec-path`;
se puede forzar con la variable GIT_BASH).

Complementa a .claude/hooks/casos.json, que el verificador del kit pasa contra los PreToolUse: aqui van
los escenarios que necesitan un arbol con cambios (contenido preparado, push de commits, post-edit y el
hook Stop). Los valores sensibles de prueba se construyen en tiempo de ejecucion para que este fichero
no contenga ninguno literal: el repo es publico.
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def git_bash():
    """Git Bash en Windows (nunca el bash de WSL); bash del sistema en macOS/Linux."""
    if os.environ.get("GIT_BASH"):
        return os.environ["GIT_BASH"]
    if os.name != "nt":
        return shutil.which("bash") or "sh"
    exe = subprocess.run(["git", "--exec-path"], capture_output=True, text=True).stdout.strip()
    raiz = os.path.normpath(os.path.join(exe, "..", "..", ".."))
    for cand in (os.path.join(raiz, "bin", "bash.exe"), os.path.join(raiz, "usr", "bin", "bash.exe")):
        if os.path.isfile(cand):
            return cand
    sys.exit("No encuentro Git Bash: define GIT_BASH")


BASH = git_bash()
T = tempfile.mkdtemp(prefix="ltr-guard-")
D = os.path.join(T, "repo")
HOME = os.path.join(T, "home")
os.makedirs(HOME)
fallos = []


def sh(args, cwd=D, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"{args}: {p.stderr.decode('utf-8', 'replace')}")
    return p.stdout.decode("utf-8", "replace")


def g(*a):
    return sh(["git", "-c", "safe.directory=*", "-c", "user.name=t", "-c", "user.email=1+t@users.noreply.github.com",
               "-c", "core.autocrlf=false"] + list(a))


def escribir(rel, texto):
    p = os.path.join(D, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)


def hook(script, modo, ev, extra_env=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
    env.update({"CLAUDE_PROJECT_DIR": D, "HOME": HOME, "USERPROFILE": HOME})
    env.update(extra_env or {})
    ev = {"session_id": "t", "cwd": D, **ev}
    cmd = f'sh "{D}/.claude/hooks/py.sh" "{D}/.claude/hooks/{script}"' + (f" {modo}" if modo else "")
    t0 = time.time()
    p = subprocess.run([BASH, "-c", cmd], input=json.dumps(ev).encode(), capture_output=True, env=env, cwd=D)
    out = p.stdout.decode("utf-8", "replace").strip()
    return p.returncode, out, p.stderr.decode("utf-8", "replace").strip(), int((time.time() - t0) * 1000)


def pre(cmd, tool="Bash", **kw):
    rc, out, err, ms = hook("public_guard.py", "pre-git", {"hook_event_name": "PreToolUse", "tool_name": tool,
                                                          "tool_input": {"command": cmd}}, **kw)
    dec = json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None
    motivo = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"] if out else ""
    return dec, motivo, ms


def check(nombre, cond, detalle=""):
    print(("ok    " if cond else "FALLO ") + nombre + ("" if cond else f"  -> {detalle[:400]}"))
    if not cond:
        fallos.append(nombre)


# ---- repo temporal con la estructura relevante
os.makedirs(D)
for rel in (".claude", ".vercelignore", ".gitignore", "app.js", "index.html", "en/index.html", "assets/css/landing.css",
            "privacidad/index.html", "en/privacy/index.html", "hyrox/index.html", "en/hyrox/index.html",
            "blog/index.html", "en/blog/index.html", "scripts/i18n/build_en.py", "scripts/pages/build_race.py"):
    src = os.path.join(REPO, rel)
    dst = os.path.join(D, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    (shutil.copytree if os.path.isdir(src) else shutil.copy2)(src, dst)
shutil.rmtree(os.path.join(D, ".claude", "context"), ignore_errors=True)
g("init", "-q", "-b", "main")
g("add", "-A")
g("commit", "-q", "-m", "base")
g("switch", "-q", "-c", "trabajo")

NOREPLY = "git -c user.email=1+t@users.noreply.github.com commit -m x"

# 1. limpio
check("commit sin nada staged: sin opinion", pre(NOREPLY)[0] is None)

# 2. anon key en app.js: se acepta; JWT service_role: se deniega
def jwt(role):
    b = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return b({"alg": "HS256", "typ": "JWT"}) + "." + b({"iss": "supabase", "role": role, "ref": "abcdefgh"}) + ".firmaFirmaFirma123"

escribir("app.js", open(os.path.join(D, "app.js"), encoding="utf-8").read() + f"\nconst OTRA_ANON_KEY = '{jwt('anon')}';\n")
g("add", "app.js")
d, m, ms = pre(NOREPLY)
check(f"JWT anon nuevo: sin opinion ({ms} ms)", d is None, m)
escribir("app.js", open(os.path.join(D, "app.js"), encoding="utf-8").read() + f"\nconst K = '{jwt('service_' + 'role')}';\n")
g("add", "app.js")
d, m, _ = pre(NOREPLY)
check("JWT service_role: deny", d == "deny" and "JWT" in m, m)
check("el motivo no imprime el valor", jwt("service_" + "role")[:30] not in m and "app.js:" in m, m)
g("checkout", "-q", "HEAD", "--", "app.js")

# 3. secretos varios
for nombre, linea in [("resend", "RESEND_API_KEY=re_" + "Ab12Cd34Ef56Gh78Ij90Kl12"),
                      ("github", "t = 'gh" + "p_" + "A" * 36 + "'"),
                      ("privada", "-----BEGIN " + "RSA PRIVATE KEY-----"),
                      ("aws", "AKIA" + "ABCDEFGHIJKLMNOP"),
                      ("asignacion", 'config = {"api_key": "' + "abc123" * 4 + '"}')]:
    escribir("scripts/x.py", linea + "\n")
    g("add", "scripts/x.py")
    d, m, _ = pre(NOREPLY)
    check(f"secreto {nombre}: deny", d == "deny" and "secreto" in m, m)
    g("rm", "-q", "--cached", "scripts/x.py")
    os.remove(os.path.join(D, "scripts", "x.py"))

# 4. emails y rutas en contenido
escribir("soporte/index.html", "<p>contact@2trainapp.com tu@email.com logo@2x.png</p>\n")
escribir("en/support/index.html", "<p>contact@2trainapp.com you@email.com</p>\n")
g("add", "soporte", "en/support")
check("emails publicos y @2x.png: sin opinion", pre(NOREPLY)[0] is None, pre(NOREPLY)[1])
escribir("soporte/index.html", "<p>escribe a alguien" + "@" + "gmail.com</p>\n")
g("add", "soporte")
d, m, _ = pre(NOREPLY)
check("email personal: deny", d == "deny" and "soporte/index.html:1" in m and "email" in m, m)
escribir("soporte/index.html", "<p>ver C:" + "\\Users\\alguien\\x</p>\n")
g("add", "soporte")
check("ruta de Windows: deny", pre(NOREPLY)[0] == "deny")
escribir("soporte/index.html", "<p>https://example.com/home/abc/ y data:image/png</p>\n")
g("add", "soporte")
check("URLs con /home/ y data: no son rutas", pre(NOREPLY)[0] is None, pre(NOREPLY)[1])
g("reset", "-q")
shutil.rmtree(os.path.join(D, "soporte"))
shutil.rmtree(os.path.join(D, "en", "support"))

# 5. ficheros prohibidos y publicacion
escribir(".env", "X=1\n")
g("add", "-f", ".env")
d, m, _ = pre(NOREPLY)
check(".env staged: deny", d == "deny" and ".env" in m, m)
g("rm", "-q", "--cached", ".env")
os.remove(os.path.join(D, ".env"))
escribir("notas.txt", "hola\n")
g("add", "notas.txt")
d, m, _ = pre(NOREPLY)
check("fichero nuevo publicable: ask", d == "ask" and "notas.txt" in m and "2trainapp.com/notas.txt" in m, m)
g("rm", "-q", "--cached", "notas.txt")
escribir("scripts/nuevo.py", "print(1)\n")
escribir("assets/img/x.svg", "<svg/>\n")
g("add", "scripts/nuevo.py", "assets/img/x.svg")
check("nuevo excluido por Vercel o contenido web: sin opinion", pre(NOREPLY)[0] is None, pre(NOREPLY)[1])
g("reset", "-q")

# 6. git add ... && git commit: se revisa lo que se va a anadir
d, m, _ = pre("git add notas.txt && " + NOREPLY)
check("git add <nuevo publicable> && commit: ask", d == "ask" and "notas.txt" in m, m)
escribir("notas2.md", "mail persona" + "@" + "hotmail.es\n")
d, m, _ = pre("git add -A && " + NOREPLY)
check("git add -A && commit con email personal en un .md: deny", d == "deny" and "notas2.md" in m, m)
os.remove(os.path.join(D, "notas2.md"))
os.remove(os.path.join(D, "notas.txt"))
escribir("index.html", open(os.path.join(D, "index.html"), encoding="utf-8").read() + "<!-- C:" + "\\Users\\x -->\n")
d, m, _ = pre("git -c user.email=1+t@users.noreply.github.com commit -am x")
check("commit -a con ruta en un modificado: deny", d == "deny" and "index.html" in m, m)
g("checkout", "-q", "--", "index.html")

# 7. terminos internos desde el fichero personal
os.makedirs(os.path.join(HOME, ".claude", "lmginc"))
with open(os.path.join(HOME, ".claude", "lmginc", "public-guard.local.json"), "w", encoding="utf-8") as f:
    json.dump({"terminos": ["RepoSecreto", "TERMX"], "regex": ["interno-[0-9]+"]}, f)
escribir("blog/index.html", open(os.path.join(D, "blog/index.html"), encoding="utf-8").read() + "<!-- ver RepoSecreto -->\n")
g("add", "blog/index.html")
d, m, _ = pre(NOREPLY)
check("termino interno de la lista local: deny", d == "deny" and "interno" in m and "RepoSecreto" not in m, m)
d, m, _ = pre("git -c user.email=1+t@users.noreply.github.com commit -m 'ver interno-42'")
check("regex interna en el mensaje: deny", d == "deny", m)
g("checkout", "-q", "HEAD", "--", "blog/index.html")
os.remove(os.path.join(HOME, ".claude", "lmginc", "public-guard.local.json"))
d, m, _ = pre("git -c user.email=1+t@users.noreply.github.com commit -m 'ver RepoSecreto'")
check("sin fichero personal: solo reglas genericas", d is None, m)

# 8. push: revisa los commits sin publicar
escribir("legal.txt", "a " + "persona" + "@" + "yahoo.es\n")
g("add", "legal.txt")
g("commit", "-q", "-m", "con email")
d, m, _ = pre("git push origin trabajo")
check("push con un commit que anade un email personal: deny", d == "deny" and "legal.txt" in m, m)
g("reset", "-q", "--hard", "HEAD~1")
escribir("hola.html", "<p>hola</p>\n")
g("add", "hola.html")
sh(["git", "-c", "safe.directory=*", "-c", "user.name=t", "-c", "user.email=persona@corre" + "o.es", "commit", "-q", "-m", "x"])
d, m, _ = pre("git push origin trabajo")
check("push con autor personal: ask con motivo", d == "ask" and "email de autor" in m, m)
g("reset", "-q", "--hard", "HEAD~1")
# push limpio de una rama: ask -> caso ltr-16 de casos.json

# 9. post-edit
def edit(modo, rel, tool="Write", content="x"):
    return hook("public_guard.py", modo, {"hook_event_name": "PreToolUse" if modo == "pre-edit" else "PostToolUse",
                                          "tool_name": tool, "tool_input": {"file_path": os.path.join(D, rel), "content": content}})

# pre-edit de migraciones (existente: deny; nueva: sin opinion) -> casos ltr-34 a ltr-36 de casos.json
escribir("privacidad/index.html", open(os.path.join(D, "privacidad/index.html"), encoding="utf-8").read() + "<p>" + "x" + "@" + "gmail.com</p>\n")
rc, out, err, _ = edit("post-edit", "privacidad/index.html")
check("post-edit: email personal -> aviso por stderr y exit 2", rc == 2 and "privacidad/index.html" in err and "email" in err, f"rc={rc} {err}")
g("checkout", "-q", "--", "privacidad/index.html")
rc, out, err, _ = edit("post-edit", "privacidad/index.html")
check("post-edit: fichero sin cambios nuevos -> silencio", rc == 0 and not err, err)
escribir("borrador.txt", "nada\n")
rc, out, err, _ = edit("post-edit", "borrador.txt")
check("post-edit: fichero nuevo publicable -> aviso", rc == 2 and "borrador.txt" in err, err)
os.remove(os.path.join(D, "borrador.txt"))
escribir("CLAUDE.local.md", "x\n")
rc, out, err, _ = edit("post-edit", "CLAUDE.local.md")
check("post-edit: CLAUDE.local.md ignorado -> silencio", rc == 0 and not err, err)

# 10. Stop
def stop(activo=False):
    rc, out, err, ms = hook("stop_check.py", "", {"hook_event_name": "Stop", "stop_hook_active": activo})
    return (json.loads(out) if out else None), ms

check("stop: arbol limpio -> nada", stop()[0] is None)
time.sleep(1.1)
escribir("index.html", open(os.path.join(D, "index.html"), encoding="utf-8").read() + "<!-- cambio -->\n")
r, ms = stop()
check(f"stop: index.html cambiado y generadas viejas -> block ({ms} ms)", r and r["decision"] == "block" and "regenerar-web" in r["reason"], str(r))
check("stop: no repite con el mismo estado", stop()[0] is None)
check("stop: respeta stop_hook_active", stop(True)[0] is None)
g("checkout", "-q", "--", "index.html")
escribir("en/hyrox/index.html", open(os.path.join(D, "en/hyrox/index.html"), encoding="utf-8").read() + "<!-- a mano -->\n")
r, _ = stop()
check("stop: generada editada a mano -> block", r and "a mano" in r["reason"], str(r))
g("checkout", "-q", "--", "en/hyrox/index.html")
escribir("privacidad/index.html", open(os.path.join(D, "privacidad/index.html"), encoding="utf-8").read() + "<!-- es -->\n")
r, _ = stop()
check("stop: legal ES sin su EN -> paridad", r and "paridad" in r["reason"], str(r))
g("checkout", "-q", "--", "privacidad/index.html")
escribir("app.js", open(os.path.join(D, "app.js"), encoding="utf-8").read() + "\n// cambio\n")
r, _ = stop()
check("stop: app.js cambiado sin subir ?v= -> block", r and "?v=" in r["reason"] and "app.js" in r["reason"], str(r))
g("checkout", "-q", "--", "app.js")
t = open(os.path.join(D, "hyrox/index.html"), encoding="utf-8").read().replace("app.js?v=claro19", "app.js?v=otro1")
escribir("hyrox/index.html", t)
r, _ = stop()
check("stop: ?v= distinto entre paginas -> block", r and "mismo ?v=" in r["reason"], str(r))
g("checkout", "-q", "--", "hyrox/index.html")
escribir("tmp-captura.yml", "x\n")
r, _ = stop()
check("stop: fichero nuevo que Vercel publicaria -> block", r and "tmp-captura.yml" in r["reason"], str(r))
os.remove(os.path.join(D, "tmp-captura.yml"))

shutil.rmtree(T, ignore_errors=True)
print(f"\n{len(fallos)} fallos")
sys.exit(1 if fallos else 0)
