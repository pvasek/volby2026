"""Build the standalone GitHub Pages site (_site/index.html) from the same template and data as the artifact.

Usage: python scripts/build_site.py [out_dir]
Env (set by GitHub Actions): GITHUB_REPOSITORY, GITHUB_REF_NAME, GITHUB_SHA – used for links to the saved source copies.
"""
import datetime, os, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_artifact  # noqa: E402

REPO = os.environ.get("GITHUB_REPOSITORY", "pvasek/volby2026")
REF = os.environ.get("GITHUB_REF_NAME", "claude/wonderful-davinci-dsr4zp")
SHA = os.environ.get("GITHUB_SHA", "")[:7]

DESCRIPTION = ("Nezávislý přehled komunálních voleb v Liberci 9.–10. 10. 2026: 11 kandidátek, programy, "
               "profily kandidátů, volební kalkulačka a jak zastupitelé hlasovali 2016–2026. Všechny údaje se zdroji.")

FAVICON = ("data:image/svg+xml," + re.sub(r"\s+", " ", """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>
<rect x='2' y='2' width='28' height='28' rx='5' fill='%235a3d9a'/><path d='M9 16.5l4.5 4.5L23 11' fill='none' stroke='white'
stroke-width='3.2' stroke-linecap='round' stroke-linejoin='round'/></svg>""").strip())

HEAD = f"""<!doctype html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{DESCRIPTION}">
<meta property="og:type" content="website">
<meta property="og:title" content="Volby Liberec 2026">
<meta property="og:description" content="{DESCRIPTION}">
<meta name="theme-color" content="#5a3d9a">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="{FAVICON}">
<style>
:root {{ padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px) }}
html {{ scroll-behavior: smooth; -webkit-text-size-adjust: 100% }}
@media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto }} }}
body {{ margin: 0 }} img {{ max-width: 100% }} [hidden] {{ display: none !important }}
body header.hero {{ padding-top: 60px }}
.hero .wrap {{ position: relative }}
.theme-btn {{ position: absolute; top: -44px; right: 20px; font: 600 .8rem/1 var(--f-body); padding: 7px 11px; border-radius: 999px;
  border: 1px solid var(--line); background: var(--surface); color: var(--ink-2); cursor: pointer; display: inline-flex; gap: 6px; align-items: center }}
.theme-btn:hover {{ background: var(--accent-soft); color: var(--ink) }}
.site-foot {{ display: flex; flex-wrap: wrap; gap: 6px 18px; margin-top: 8px }}
</style>
"""

THEME_BTN = """<button type="button" class="theme-btn" id="theme-btn" aria-label="Přepnout barevný režim"><svg id="theme-ico" width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"></svg><span id="theme-lab">Automaticky</span></button>"""

THEME_JS = """<script>
(() => { const modes = ["auto", "light", "dark"], lab = { auto: "Automaticky", light: "Světlý", dark: "Tmavý" }, ico = { auto: '<circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8 2a6 6 0 0 1 0 12z" fill="currentColor"/>',
    light: '<circle cx="8" cy="8" r="3" fill="currentColor"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6L13 13M3 13l1.4-1.4M11.6 4.4L13 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
    dark: '<path d="M13 10.5A6 6 0 0 1 5.5 3a6 6 0 1 0 7.5 7.5z" fill="currentColor"/>' };
  let m = "auto"; try { m = localStorage.getItem("volby-lbc-theme") || "auto"; } catch (e) {}
  const apply = () => { if (m === "auto") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", m);
    const b = document.getElementById("theme-btn"); if (b) { document.getElementById("theme-lab").textContent = lab[m]; document.getElementById("theme-ico").innerHTML = ico[m]; } };
  apply();
  document.addEventListener("DOMContentLoaded", () => { apply(); document.getElementById("theme-btn").onclick = () => { m = modes[(modes.indexOf(m) + 1) % 3]; try { localStorage.setItem("volby-lbc-theme", m); } catch (e) {} apply(); }; });
})();
</script>
"""


def main():
    out_dir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"
    build_artifact.main()  # writes site/volby-liberec-2026.html (artifact fragment)
    frag = (ROOT / "site/volby-liberec-2026.html").read_text(encoding="utf-8")

    # point "kopie" links at the branch this build runs from
    frag = re.sub(r'const REPO = "https://github\.com/[^"]+/blob/[^"]+/";',
                  f'const REPO = "https://github.com/{REPO}/blob/{REF}/";', frag, count=1)

    split = frag.index('<header class="hero">')
    head_part, body_part = frag[:split], frag[split:]
    assert '<div class="wrap hero-grid">' in body_part
    body_part = body_part.replace('<div class="wrap hero-grid">', '<div class="wrap hero-grid">\n    ' + THEME_BTN, 1)
    built = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body_part = body_part.replace('<footer class="wrap"><p id="foot"></p></footer>',
                                  f'<footer class="wrap"><p id="foot"></p><p class="site-foot">'
                                  f'<a href="https://github.com/{REPO}/tree/{REF}">Zdrojový kód a data na GitHubu</a>'
                                  f'<span>Sestaveno {built}{" · " + SHA if SHA else ""}</span></p></footer>', 1)

    html = HEAD + THEME_JS + head_part + "</head>\n<body>\n" + body_part + "\n</body>\n</html>\n"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    print("wrote", out_dir / "index.html", f"{len(html.encode()) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
