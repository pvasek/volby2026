"""Assemble site/volby-liberec-2026.html from data/processed/*.json + scripts/template.html."""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"


def load(name, default=None):
    p = P / name
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


FAMILIES = [  # (regex on list name, family label) – first match wins; used to detect party switching
    (r"ANO", "ANO"),
    (r"Starost|SLK|STAROST", "Starostové (SLK/STAN)"),
    (r"SPOLU|Společně pro Liberecký", "koalice SPOLU"),
    (r"Občansk|ODS", "ODS"),
    (r"Unie pro sport|PRO Sport|sportov", "Unie sportovců"),
    (r"Svoboda a př|SPD|Okamur", "SPD"),
    (r"Trikol", "Trikolora"),
    (r"Úsvit", "Úsvit"),
    (r"Právo Respekt|PRO 2016", "PRO / PRO 2016"),
    (r"[Ss]vobodn|Soukromn", "Svobodní/Soukromníci"),
    (r"[Pp]irát|PIRÁT", "Piráti"),
    (r"Změna|ZMĚNA|otevřený lidem|KRAJinu|Zelen|zelen", "Změna/LOL/Zelení"),
    (r"sociálně dem|ČSSD", "ČSSD"),
    (r"Komunist|KSČM|STAČILO", "KSČM/Stačilo"),
    (r"TOP 09", "TOP 09"),
    (r"KDU", "KDU-ČSL"),
    (r"Právo Respekt|PRO 2016", "PRO / PRO 2016"),
    (r"Práv Občanů|SPO", "SPO (Zemanovci)"),
    (r"Volba pro Vrat", "Volba pro Vratislavice"),
    (r"Budoucnost", "Budoucnost pro Liberec"),
]


def family(name):
    for rx, lab in FAMILIES:
        if re.search(rx, name or ""):
            return lab
    return name


TITLE_RX = re.compile(r"(?<![\w])(Ing|Mgr|Bc|PhDr|RNDr|MUDr|MVDr|JUDr|doc|prof|PaedDr|arch|CSc|Ph\.?\s?D|MBA|MPA|LL\.?M|M\.?A)\.?(?![\w])", re.I)


def clean_name(n):
    return " ".join(TITLE_RX.sub(" ", n).replace(",", " ").split())


def rekey_votes(kl, k26):
    """Merge name variants (titles change over time, OCR) into one row per person."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from hlas_aggregate import norm
    import csv, gzip
    cand = {norm(c["jmeno"]): c["jmeno"] for l in k26 for c in l["kandidati"]}
    src = P / "hlasovani_long.csv"
    fh = open(src, encoding="utf-8") if src.exists() else gzip.open(str(src) + ".gz", "rt", encoding="utf-8")
    raw2norm = {r["zastupitel"]: r["jmeno_norm"] for r in csv.DictReader(fh)}
    votes = kl["hlasovani"] if isinstance(kl, dict) else kl
    for v in votes:
        new = {}
        for name, h in (v.get("hlasy") or {}).items():
            base = raw2norm.get(name, name)
            new[cand.get(norm(base), clean_name(base))] = h
        v["hlasy"] = new
        v.pop("hlasy_detail", None)
    return kl


def theme_pct(points, keys):
    """temata_pct = podíl bodů programu v tématu (největší zbytky, aby součet byl 100)."""
    from collections import Counter
    c = Counter(b["tema"] for b in points); n = sum(c.values())
    if not n:
        return None
    raw = {k: 100 * c.get(k, 0) / n for k in keys}
    out = {k: int(v) for k, v in raw.items()}
    for k in sorted(keys, key=lambda k: -(raw[k] - out[k]))[:100 - sum(out.values())]:
        out[k] += 1
    return out


def main():
    sys.path.insert(0, str(ROOT / "scripts"))
    import politika_index
    pol_idx = politika_index.main()  # writes data/processed/politika.json
    k26 = load("kandidati_2026.json")
    hist = load("historie_kandidatu.json", {})
    past = {y: load(f"kandidati_{y}.json", []) for y in (2014, 2018, 2022)}
    strany = {}
    for f in sorted((P / "strany").glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            strany[int(d["cislo"])] = d
        except Exception as e:  # keep building; report
            print("WARN bad party file", f, e, file=sys.stderr)

    lists = []
    for l in k26:
        cands = []
        for c in l["kandidati"]:
            key = next((kk for kk in hist if kk.endswith(f'|{l["cislo"]}|{c["poradi"]}')), None)
            h = hist.get(key, []) if key else []
            fams = []
            for x in h:
                fm = family(x["strana"])
                if not fams or fams[-1] != fm:
                    fams.append(fm)
            cands.append({**c, "historie": h, "rodiny": fams})
        praxe = load("praxe.json", {})
        for c in cands:
            c["praxe"] = praxe.get(f'{l["cislo"]}|{c["poradi"]}')
            c["politika"] = pol_idx.get(f'{l["cislo"]}|{c["poradi"]}')
        an = strany.get(l["cislo"]) or {}
        if an.get("program_body") and an.get("temata_pct"):
            an["temata_odhad"] = an["temata_pct"]
            an["temata_pct"] = theme_pct(an["program_body"], list(an["temata_pct"].keys()))
        pol = [c["politika"]["index"] for c in cands[:5] if c.get("politika")]
        prx = [c["praxe"]["index"] for c in cands[:5] if c.get("praxe")]
        skore = {"politika": round(sum(pol) / len(pol)) if pol else None, "politika_top5": pol,
                 "praxe": round(sum(prx) / len(prx)) if prx else None, "praxe_top5": prx}
        lists.append({k: v for k, v in l.items() if k != "kandidati"} | {"kandidati": cands, "analyza": strany.get(l["cislo"]), "skore": skore})

    results = {}
    for y, d in past.items():
        rows = []
        for l in d:
            pct = l.get("procenta")
            if pct in (None, ""):
                continue
            rows.append({"nazev": l["nazev"], "zkratka": l["zkratka"], "pct": float(pct), "mandaty": int(l.get("mandaty") or 0),
                         "zvoleni": [c["jmeno"] for c in l["kandidati"] if c.get("mandat") == "A"]})
        results[y] = sorted(rows, key=lambda r: -r["pct"])

    kontext, pruzkumy = load("kontext.json"), load("pruzkumy.json")
    # map local copies -> original URLs so the page links to the web, while keeping the local path visible
    url_of = {}
    for src in (kontext or {}).get("zdroje", []) + (pruzkumy or {}).get("zdroje", []):
        if isinstance(src, dict) and src.get("local_file"):
            url_of[src["local_file"]] = src.get("url")
    def resolve(o):
        if isinstance(o, dict):
            return {k: (resolve_src(v) if k == "zdroje" else resolve(v)) for k, v in o.items()}
        if isinstance(o, list):
            return [resolve(x) for x in o]
        return o
    def resolve_src(v):
        if not isinstance(v, list):
            return v
        return [({"url": url_of.get(x, x), "local": x} if isinstance(x, str) and x.startswith("data/") else x) for x in v]
    if kontext:
        kontext = {k: (v if k == "zdroje" else resolve(v)) for k, v in kontext.items()}

    # alluvial: Liberec municipal lists 2014 → 2018 → 2022 → 2026 for 2026 candidates who ran before
    flows = []
    for l in lists:
        for c in l["kandidati"]:
            seq = {x["rok"]: family(x["strana"]) for x in c["historie"] if x["volby"] == "komunální" and x["zastupitelstvo"] == "Liberec"}
            if seq:
                flows.append({"n": c["jmeno"], "cislo": l["cislo"], "poradi": c["poradi"], "s": [seq.get(y) for y in (2014, 2018, 2022)],
                              "z": [bool(next((x["zvolen"] for x in c["historie"] if x["rok"] == y and x["volby"] == "komunální" and x["zastupitelstvo"] == "Liberec"), False)) for y in (2014, 2018, 2022)]})

    data = {
        "lists": lists,
        "results": results,
        "pruzkumy": pruzkumy,
        "kontext": kontext,
        "hlasovani": rekey_votes(load("hlasovani_klicova.json"), k26) if load("hlasovani_klicova.json") else None,
        "hlasovani_summary": load("hlasovani_summary.json"),
        "hlasovani_agg": load("hlasovani_agg.json"),
        "kalkulacka": load("kalkulacka.json"),
        "toky": flows,
        "built": "2026-10-08",
    }
    tpl = (ROOT / "scripts/template.html").read_text(encoding="utf-8")
    js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out = ROOT / "site/volby-liberec-2026.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(tpl.replace("/*__DATA__*/null", js), encoding="utf-8")
    print("wrote", out, f"{out.stat().st_size/1024:.0f} KB; party analyses:", sorted(strany))


if __name__ == "__main__":
    main()
