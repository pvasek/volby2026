"""Stáhne originální zdroje (stránky, PDF, registry ČSÚ) do data/raw/ podle manifestu data/sources_manifest.json.

Kopie zdrojů nejsou v repozitáři (autorská práva, velikost) – repozitář obsahuje jen odkazy.

  python scripts/fetch_sources.py                 # stáhne vše, co chybí
  python scripts/fetch_sources.py --only hlasovani,volby_gov
  python scripts/fetch_sources.py --force         # stáhne znovu i existující soubory
  python scripts/fetch_sources.py --verify        # stáhne originály do dočasné složky a porovná je s otisky (sha256)
  python scripts/fetch_sources.py --verify-local  # porovná už stažené kopie v data/raw/ s otisky
  python scripts/fetch_sources.py --build-manifest   # (údržba) sestaví manifest ze zpracovaných dat a našich kopií

Ověření: manifest obsahuje pro každý soubor URL, otisk SHA-256, velikost a datum, kdy jsme ho stáhli.
Shodný otisk = máte přesně stejný soubor, ze kterého analýza vychází. Webové stránky se v čase mění
(reklamy, komentáře, úpravy článku), u nich proto rozdílný otisk neznamená chybu – porovnejte obsah
nebo použijte archiv (https://web.archive.org/web/2026*/<url>). PDF a registry ČSÚ by měly sedět přesně.

Druhy zdrojů: profily, programy, kontext, pruzkumy (stránky a dokumenty), hlasovani (PDF protokoly a zápisy
z podklady.liberec.cz, ~1,2 GB), volby_gov (otevřená data ČSÚ, ~300 MB po rozbalení).
"""
import argparse, hashlib, json, pathlib, sys, time, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data/sources_manifest.json"
UA = "Mozilla/5.0 (volby2026 source fetcher; personal research)"

VOLBY_GOV = [  # (adresář, soubor, rozbalit do)
    ("kv2026", "KV2026reg20261002_csv.zip", "reg"), ("kv2026", "KV2026ciselniky20261002_csv.zip", "cis"),
    ("kv2022", "KV2022reg20260328_csv.zip", "reg"), ("kv2022", "KV2022ciselniky20260328_csv.zip", "cis"),
    ("kv2018", "KV2018_reg_20230224_csv.zip", "reg"), ("kv2018", "KV2018_cisel_20230224_csv.zip", "cis"),
    ("kv2014", "KV2014_reg_20230224_csv.zip", "reg"), ("kv2014", "KV2014_cisel_20230224_csv.zip", "cis"),
    ("kz2016", "KZ2016_reg_20230223_csv.zip", "reg"), ("kz2016", "KZ2016_cisel_20230223_csv.zip", "cis"),
    ("kz2020", "KZ2020reg20201004a_csv.zip", "reg"), ("kz2020", "KZ2020ciselniky20200918_csv.zip", "cis"),
    ("kz2024", "KZ2024reg20240922_csv.zip", "reg"), ("kz2024", "KZ2024ciselniky20240922_csv.zip", "cis"),
    ("ps2021", "PS2021reg20211111_csv.zip", "reg"), ("ps2021", "PS2021ciselniky20211006_csv.zip", "cis"),
    ("ps2025", "PS2025reg20251005_csv.zip", "reg"), ("ps2025", "PS2025ciselniky20251005_csv.zip", "cis"),
]


def build_manifest():
    P = ROOT / "data/processed"
    items = {}

    def add(local, url, kind, desc=""):
        if not local or not url or not str(local).startswith("data/raw/") or not str(url).startswith("http"):
            return
        items.setdefault(local, {"local": local, "url": url, "kind": kind, "desc": desc})

    for f in sorted((P / "strany").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for z in d.get("zdroje", []):
            loc = z.get("local") or ""
            add(loc, z.get("url"), "programy" if "/programy/" in loc else "profily", f'{d.get("zkratka")}: {z.get("nazev", "")}')
    k = json.loads((P / "kontext.json").read_text(encoding="utf-8"))
    for z in k.get("zdroje", []):
        add(z.get("local_file"), z.get("url"), "kontext")
    pr = json.loads((P / "pruzkumy.json").read_text(encoding="utf-8"))
    for sec in ("pruzkumy", "souvisejici_starsi_pruzkumy", "proxy_vysledky"):
        for z in pr.get(sec, []):
            add(z.get("local_file"), z.get("url"), "pruzkumy", z.get("volby") or z.get("agentura") or "")
    dl = json.loads((ROOT / "data/raw/hlasovani/downloads.json").read_text(encoding="utf-8"))
    for loc, z in dl.items():
        add(loc, z["url"], "hlasovani", z.get("name", ""))
        items[loc].update({"sha256": z.get("sha256"), "bytes": z.get("bytes")})
    for d, f, sub in VOLBY_GOV:
        loc = f"data/raw/volby_gov/{d}/{f}"
        add(loc, f"https://volby.gov.cz/opendata/{d}/{f}", "volby_gov", "registr ČSÚ")
        items[loc]["unzip"] = f"data/raw/volby_gov/{d}/{sub}"
    for it in items.values():
        f = ROOT / it["local"]
        if f.exists():
            it["sha256"] = it.get("sha256") or hashlib.sha256(f.read_bytes()).hexdigest()
            it["bytes"] = it.get("bytes") or f.stat().st_size
        it.setdefault("fetched", "2026-10-08")
    out = sorted(items.values(), key=lambda x: (x["kind"], x["local"]))
    MANIFEST.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print("manifest:", len(out), "souborů", dict(Counter(x["kind"] for x in out)))


def fetch(item, force=False):
    dest = ROOT / item["local"]
    if dest.exists() and not force:
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(item["url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest.with_suffix(dest.suffix + ".part"), "wb") as fh:
                h = hashlib.sha256()
                while chunk := r.read(1 << 16):
                    fh.write(chunk); h.update(chunk)
            if item.get("sha256") and h.hexdigest() != item["sha256"]:
                print(f"  ! jiný obsah než při původním stažení (sha256): {item['local']}")
            dest.with_suffix(dest.suffix + ".part").replace(dest)
            if item.get("unzip"):
                zipfile.ZipFile(dest).extractall(ROOT / item["unzip"])
            return "ok"
        except Exception as e:  # noqa: BLE001 – report and retry
            last = e
            time.sleep(2 ** (attempt + 1))
    print(f"  ! nepodařilo se: {item['url']} ({last})")
    return "fail"


def sha_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 16):
            h.update(chunk)
    return h.hexdigest()


def verify(items, online):
    import tempfile
    res = {"shodné": [], "změněné": [], "chybí / nedostupné": []}
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="volby2026_verify_"))
    for i, it in enumerate(items, 1):
        if online:
            dest = tmp / f"{i}"
            try:
                req = urllib.request.Request(it["url"], headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=120) as r:
                    dest.write_bytes(r.read())
                time.sleep(0.5)
            except Exception as e:  # noqa: BLE001
                res["chybí / nedostupné"].append((it["local"], str(e)[:80])); continue
        else:
            dest = ROOT / it["local"]
            if not dest.exists():
                res["chybí / nedostupné"].append((it["local"], "není staženo")); continue
        key = "shodné" if sha_of(dest) == it.get("sha256") else "změněné"
        res[key].append((it["local"], it["url"]))
    for k, v in res.items():
        print(f"{k}: {len(v)}")
    for k in ("změněné", "chybí / nedostupné"):
        for loc, info in res[k][:200]:
            print(f"  [{k}] {loc} – {info}")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="čárkou oddělené druhy: profily,programy,kontext,pruzkumy,hlasovani,volby_gov")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--build-manifest", action="store_true")
    ap.add_argument("--verify", action="store_true", help="stáhnout znovu a porovnat otisky")
    ap.add_argument("--verify-local", action="store_true", help="porovnat lokální kopie s otisky")
    a = ap.parse_args()
    if a.build_manifest:
        build_manifest()
        return
    items = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if a.only:
        kinds = set(a.only.split(","))
        items = [x for x in items if x["kind"] in kinds]
    if a.verify or a.verify_local:
        verify(items, online=a.verify)
        return
    stats = {"ok": 0, "skip": 0, "fail": 0}
    for i, it in enumerate(items, 1):
        res = fetch(it, a.force)
        stats[res] += 1
        if res == "ok":
            print(f"[{i}/{len(items)}] {it['local']}")
            time.sleep(0.5)  # šetrně k serverům
    print(stats)
    sys.exit(1 if stats["fail"] else 0)


if __name__ == "__main__":
    main()
