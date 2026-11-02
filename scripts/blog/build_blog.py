"""Genera el blog (/blog y /en/blog/) con la home como plantilla, igual que las
páginas por objetivo: cabecera, menú, alta a la beta, pie y modal salen tal cual.
Cada artículo lleva su semana real dibujada (la de scripts/pages/semanas.json),
FAQ, fuentes y datos estructurados (BlogPosting, FAQPage y migas).

Uso (desde la raíz, después de generar el inglés y las páginas por objetivo):
  python3 -I scripts/blog/build_blog.py .
"""
import datetime
import html
import json
import pathlib
import re
import sys

sys.path[:0] = [str(pathlib.Path(__file__).resolve().parent), str(pathlib.Path(__file__).resolve().parent.parent / "pages")]
import build_race as R  # noqa: E402
from posts import INDEX, POSTS, UI  # noqa: E402

ROOT = R.ROOT
BASE = R.BASE
esc = R.esc
ICO_PLUS = R.ICO_PLUS


def url_of(post, lang):
    return BASE + ("blog/" + post["es"]["slug"] if lang == "es" else "en/blog/" + post["en"]["slug"] + "/")


def path_of(post, lang):
    return "/blog/" + post["es"]["slug"] if lang == "es" else "/en/blog/" + post["en"]["slug"] + "/"


def index_url(lang):
    return BASE + ("blog" if lang == "es" else "en/blog/")


def index_path(lang):
    return "/blog" if lang == "es" else "/en/blog/"


def words(h):
    return len(re.sub(r"<[^>]+>", " ", h).split())


def minutes(post, lang):
    t = post[lang]
    n = words(t["lead"] + t["body"]) + sum(words(q + a) for q, a in t["faq"]) + 260  # + la semana dibujada
    return max(3, round(n / 220))


def fecha(post, lang):
    d = datetime.date.fromisoformat(post["date"])
    m = UI[lang]["months"][d.month - 1]
    return f"{d.day} {m} {d.year}" if lang == "es" else f"{m} {d.day}, {d.year}"


def photo(post, sizes, cls, lazy=True):
    """Foto de portada (Unsplash, licencia libre) en dos tamaños."""
    f = f'/assets/fotos/{post["photo"]}'
    return (f'<img class="{cls}" src="{f}-640.webp" srcset="{f}-640.webp 640w, {f}-1280.webp 1280w" sizes="{sizes}" '
            f'alt="" width="1280" height="720"{" loading=lazy" if lazy else ""} decoding="async">')


def visual(post, lang):
    return f'<span class="post-card__media">{photo(post, "(min-width: 961px) 360px, (min-width: 681px) 50vw, 100vw", "post-card__img")}</span>'


def card(post, lang):
    t = post[lang]
    return (f'<a class="post-card" href="{path_of(post, lang)}">{visual(post, lang)}'
            f'<span class="post-card__body"><span class="post-card__cat">{esc(t["cat"])}</span>'
            f'<span class="post-card__t">{esc(t["title"])}</span>'
            f'<span class="post-card__d">{esc(t["desc"])}</span>'
            f'<span class="post-card__m">{minutes(post, lang)} {INDEX[lang]["min"]}</span></span></a>')


def byline(post, lang):
    return (f'<p class="post-by"><time datetime="{post["date"]}">{fecha(post, lang)}</time>'
            f' · {minutes(post, lang)} {INDEX[lang]["min"]}</p>')


def article(post, lang):
    t, ui = post[lang], UI[lang]
    before, after = t["body"].split("{{week}}")
    faq = "\n".join(
        f'          <div class="faq-item">\n'
        f'            <button type="button" class="faq-q" aria-expanded="false" aria-controls="faq-a-{i}"><span>{esc(q)}</span>{ICO_PLUS}</button>\n'
        f'            <div id="faq-a-{i}" class="faq-a"><div class="faq-a-inner">{esc(a)}</div></div>\n'
        f'          </div>' for i, (q, a) in enumerate(t["faq"], 1))
    src = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(s)}</a></li>' for s, u in t["sources"])
    ch, cp, chref, clabel = t["cta"]
    others = [p for p in POSTS if p is not post]
    return f'''<!-- BLOG · artículo ({post["key"]}) -->
<section class="post sec">
  <div class="max-w-page pad-x">
    <nav class="post-crumbs" aria-label="{'Migas' if lang == 'es' else 'Breadcrumb'}"><a href="{index_path(lang)}">{ui["blog"]}</a><span aria-hidden="true">›</span><span>{esc(t["cat"])}</span></nav>
    <header class="post-head">
      <p class="eyebrow">{esc(t["cat"])}</p>
      <h1 class="post-title">{esc(t["title"])}</h1>
      <p class="post-lead">{esc(t["lead"])}</p>
      {byline(post, lang)}
    </header>
    <figure class="post-cover">{photo(post, "(min-width: 980px) 920px, 100vw", "post-cover__img", lazy=False)}</figure>
    <div class="prose">{before}</div>
    <div class="post-wide">
{R.week_html(post["week"], lang)}
    </div>
    <div class="prose">{after}</div>
    <div class="post-cta">
      <p class="post-cta__t">{esc(ch)}</p>
      <p class="post-cta__p">{esc(cp)}</p>
      <div class="post-cta__a"><a class="btn" href="{chref}">{esc(clabel)}</a><button type="button" class="open-modal btn btn--ghost">{esc(ui["cta_beta"])}</button></div>
    </div>
    <div class="post-faq">
      <h2 class="post-h2">{ui["faq"]}</h2>
      <div class="faq-list">
{faq}
      </div>
    </div>
    <aside class="post-src"><h2 class="post-h3">{ui["sources"]}</h2><ol>{src}</ol></aside>
  </div>
</section>

<section class="sec post-more">
  <div class="max-w-page pad-x">
    <h2 class="post-h2">{ui["related"]}</h2>
    <div class="post-grid">{"".join(card(p, lang) for p in others)}</div>
  </div>
</section>
'''


def index_page(lang):
    i = INDEX[lang]
    return f'''<!-- BLOG · índice -->
<section class="sec blog-head">
  <div class="max-w-page pad-x">
    <div class="sec-head sec-head--center">
      <p class="eyebrow">{i["eyebrow"]}</p>
      <h1 class="t-h2">{i["h1"]}</h1>
      <p class="t-lead">{esc(i["lead"])}</p>
    </div>
    <div class="post-grid post-grid--index">{"".join(card(p, lang) for p in POSTS)}</div>
  </div>
</section>
'''


def ld(graph):
    return '<script type="application/ld+json">\n' + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1) + "\n</script>"


def article_ld(post, lang):
    t, u = post[lang], url_of(post, lang)
    home = BASE if lang == "es" else BASE + "en/"
    img = BASE + f"assets/fotos/{post['photo']}-1280.webp"
    return ld([
        {"@type": "BlogPosting", "@id": u + "#article", "mainEntityOfPage": u, "headline": t["title"], "description": t["desc"],
         "inLanguage": lang, "datePublished": post["date"], "dateModified": post["date"], "image": img,
         "author": {"@type": "Organization", "name": "2trAIn", "url": BASE},
         "publisher": {"@type": "Organization", "name": "2trAIn", "url": BASE, "logo": {"@type": "ImageObject", "url": BASE + "android-chrome-512x512.png"}},
         "isPartOf": {"@id": index_url(lang) + "#blog"}, "about": {"@id": BASE + "#app"},
         "citation": [s for s, _ in t["sources"]]},
        {"@type": "BreadcrumbList", "@id": u + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "2trAIn", "item": home},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": index_url(lang)},
            {"@type": "ListItem", "position": 3, "name": t["title"], "item": u}]},
        {"@type": "FAQPage", "@id": u + "#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in t["faq"]]},
    ])


def index_ld(lang):
    u = index_url(lang)
    home = BASE if lang == "es" else BASE + "en/"
    return ld([
        {"@type": "Blog", "@id": u + "#blog", "url": u, "name": INDEX[lang]["title"], "description": INDEX[lang]["desc"], "inLanguage": lang,
         "publisher": {"@type": "Organization", "name": "2trAIn", "url": BASE},
         "blogPost": [{"@id": url_of(p, lang) + "#article"} for p in POSTS]},
        {"@type": "BreadcrumbList", "@id": u + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "2trAIn", "item": home},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": u}]},
    ])


def write(rel, html_):
    dest = ROOT / rel.strip("/") / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html_, encoding="utf-8")
    print("ok", dest.relative_to(ROOT))


def main():
    for lang in ("es", "en"):
        other = "en" if lang == "es" else "es"
        i = INDEX[lang]
        write(index_path(lang), R.shell(lang, i["title"], i["desc"], index_url(lang), index_url("es"), index_url("en"),
                                        index_path(other), index_ld(lang), index_page(lang)))
        for p in POSTS:
            t = p[lang]
            write(path_of(p, lang), R.shell(lang, t["seo"], t["desc"], url_of(p, lang), url_of(p, "es"), url_of(p, "en"),
                                            path_of(p, other), article_ld(p, lang), article(p, lang),
                                            (p.get("legal") or {}).get(lang), og_type="article"))
    sitemap()
    llms()


def sitemap():
    """Añade (o actualiza) las URL del blog en sitemap.xml."""
    sm = ROOT / "sitemap.xml"
    s = sm.read_text(encoding="utf-8")
    s = re.sub(r"\s*<!-- BLOG -->.*?<!-- /BLOG -->", "", s, flags=re.S)

    def entry(loc, es, en, date, pri):
        return (f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{date}</lastmod>\n"
                f'    <xhtml:link rel="alternate" hreflang="es" href="{es}"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="{es}"/>\n'
                f"    <changefreq>monthly</changefreq>\n    <priority>{pri}</priority>\n  </url>")
    last = max(p["date"] for p in POSTS)
    parts = [entry(index_url(l), index_url("es"), index_url("en"), last, "0.6") for l in ("es", "en")]
    for p in POSTS:
        parts += [entry(url_of(p, l), url_of(p, "es"), url_of(p, "en"), p["date"], "0.6") for l in ("es", "en")]
    s = s.replace("</urlset>", "  <!-- BLOG -->\n" + "\n".join(parts) + "\n  <!-- /BLOG -->\n</urlset>")
    sm.write_text(s, encoding="utf-8")
    print("ok sitemap.xml")


def llms():
    """Lista los artículos en llms.txt, dentro de su propio bloque."""
    f = ROOT / "llms.txt"
    s = f.read_text(encoding="utf-8")
    s = re.sub(r"\n## Blog\n.*?(?=\n## |\Z)", "\n", s, flags=re.S)
    lines = ["## Blog", "", f"- [Blog (español)]({index_url('es')}): guías con semanas reales generadas por 2trAIn. En inglés: [Blog]({index_url('en')})."]
    for p in POSTS:
        lines.append(f"- [{p['es']['title']}]({url_of(p, 'es')}): {p['es']['desc']} En inglés: [{p['en']['title']}]({url_of(p, 'en')}).")
    block = "\n".join(lines) + "\n\n"
    s = s.replace("\n## Empresa", "\n" + block + "## Empresa", 1) if "\n## Empresa" in s else s.rstrip("\n") + "\n\n" + block
    f.write_text(re.sub(r"\n{3,}", "\n\n", s).rstrip("\n") + "\n", encoding="utf-8")
    print("ok llms.txt")


if __name__ == "__main__":
    main()
