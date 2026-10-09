"""Write data/raw/hlasovani/SOURCES.md from downloads.json manifest.
usage: python3 -I hlas_sources_md.py RAWDIR"""
import json, os, sys, unicodedata
from collections import defaultdict
raw = sys.argv[1]
man = json.load(open(os.path.join(raw, "downloads.json")))


def kind(n):
    f = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower()
    return "hlasovani" if f.startswith("vysled") else ("zapis" if f.startswith("zapis") else "jine")


by = defaultdict(list)
for dest, m in man.items():
    by[m["session"]].append(m)
nv = sum(1 for m in man.values() if kind(m["name"]) == "hlasovani")
nz = sum(1 for m in man.values() if kind(m["name"]) == "zapis")
fetched = sorted(m["fetched"][:10] for m in man.values())
tot = sum(m["bytes"] for m in man.values())
L = []
L.append("# Zdroje – jmenovitá hlasování Zastupitelstva statutárního města Liberec (2016–2026)\n")
L.append(f"Staženo: {fetched[0]} – {fetched[-1]} (UTC). Celkem {len(man)} souborů, {tot/1e6:.0f} MB "
         f"({nv}× „Výsledky hlasování“, {nz}× „Zápis“), {len(by)} zasedání.\n")
L.append("""## Zdroj

* **Veřejné podklady SML** – `https://podklady.liberec.cz/` (oficiální archiv podkladů Rady a Zastupitelstva města, agenda `zm`).
  * Strom zasedání: `POST https://podklady.liberec.cz/?controller=open&action=loadtree` (`agend=zm&path=<rok>`),
    obsah zasedání: `POST ...&action=loadcontent` (`agend=zm&path=<rok>%2F<YYYY-MM-DD ZM N>`) → JSON.
    Úplný výpis všech zasedání 2016–2026 a souborů je v `podklady_index.json`.
  * Stažení souboru: `https://podklady.liberec.cz/?controller=open&action=download&agend=zm&path=<cesta>`
    (cesta = `<rok>/<YYYY-MM-DD ZM N>/<název souboru>`, URL-kódovaná).
* `www.liberec.cz` z tohoto prostředí nefungoval (reset spojení / 503); podklady.liberec.cz a docs.liberec.cz ano.
  Starší roky (2007–2015) jsou na `https://docs.liberec.cz/Odb_KT/výsledky hlasování zastupitelstva města/` (nestahováno, mimo rozsah).

## Co soubory obsahují

* **„Výsledky hlasování …pdf“** – sken (Konica Minolta) tištěných protokolů hlasovacího zařízení H.E.R. Systém
  (A.S.Partner): 1 strana = 1 hlasování; hlavička „VÝSLEDEK HLASOVÁNÍ č. N – BOD č. X – název bodu“, poznámka,
  číslo a datum zasedání, a tabulka všech 39 zastupitelů (jméno, klub/strana, PRO / PROTI / ZDRŽEL SE /
  NEHLASOVAL / NEPŘÍTOMEN) + součty. Skeny bez textové vrstvy → zpracováno OCR (tesseract, čeština).
  Na skenech bývají ručně psané poznámky (např. o jaký návrh šlo) – OCR je nečte.
* **„Zápis …pdf“** – textový zápis ze zasedání (Word/PDF), obsahuje průběh rozpravy a řádky
  „Hlasování č. N … – pro – a, proti – b, zdržel se – c, návrh (ne)byl přijat“ a čísla usnesení.
  Použito pro kontrolu OCR, popis předmětu hlasování a výsledek.
* `podklady_index.json` – výpis všech souborů zasedání ZM 2016–2026 z API (vč. podkladů „Dle bodů“, které nestahovány).
* `downloads.json` – manifest: lokální cesta → URL, velikost, SHA-256, čas stažení.

## Seznam stažených souborů (podle zasedání)

| Zasedání | Soubor | Typ | Velikost | URL |
|---|---|---|---|---|
""")
for s in sorted(by):
    for m in sorted(by[s], key=lambda m: m["name"]):
        L.append(f"| {s} | {m['name']} | {kind(m['name'])} | {m['bytes']/1e6:.1f} MB | {m['url']} |\n")
L.append("""
## Chybějící / poznámky

* `2016-05-27 ZM 5P` – ve složce je jen zvukový záznam (pokračování 5. ZM), bez výsledků hlasování a zápisu.
* `2018-03-05 ZM 0-2` – mimořádné zasedání: pouze pozvánka a usnesení, výsledky hlasování ani zápis nejsou zveřejněny.
* `2016-06-09 ZM 5N` (náhradní 5. ZM) – samostatný zápis není; hlasování z něj jsou obsažena v zápisu
  `2016-05-26 ZM 5/Zápis z 5. ZM - 26. 5. 2016.pdf`.
* Tajné volby (primátor, náměstci, radní, odvolání) se na hlasovacím zařízení nezaznamenávají – jsou jen v zápisu (součty).
""")
open(os.path.join(raw, "SOURCES.md"), "w").write("".join(L))
print("ok", len(man))
