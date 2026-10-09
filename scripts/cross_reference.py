"""Cross-reference 2026 Liberec candidates against earlier election registries (CSU open data).
Match: same first+last name AND birth year consistent (election year - age, +-1)."""
import csv, json, sys, pathlib, io

G = pathlib.Path(sys.argv[1])          # data/raw/volby_gov
OUT = pathlib.Path(sys.argv[2])

def rd(p):
    raw = p.read_bytes()
    try: txt = raw.decode("utf-8")
    except UnicodeDecodeError: txt = raw.decode("cp1250")
    delim = ";" if txt.split("\n", 1)[0].count(";") > txt.split("\n", 1)[0].count(",") else ","
    return list(csv.DictReader(io.StringIO(txt), delimiter=delim))

def find(d, name):
    for sub in ("reg/csv_od", "reg", "reg/csv", "cis/csv_od", "cis", "cis/csv"):
        p = G / d / sub / name
        if p.exists(): return p

ELECTIONS = [  # (dir, year, kind, candidates file, lists file, list-key fields)
    ("kv2014", 2014, "komunální"), ("kv2018", 2018, "komunální"), ("kv2022", 2022, "komunální"),
    ("kz2016", 2016, "krajské"), ("kz2020", 2020, "krajské"), ("kz2024", 2024, "krajské"),
    ("ps2021", 2021, "sněmovní"), ("ps2025", 2025, "sněmovní"),
]
c26 = rd(find("kv2026", "kvrk.csv")); c26 = [c for c in c26 if c["KODZASTUP"] == "563889"]
key = lambda j, p: (j.strip().lower(), p.strip().lower())
targets = {}
for c in c26:
    targets.setdefault(key(c["JMENO"], c["PRIJMENI"]), []).append(c)

hist = {}
for d, year, kind in ELECTIONS:
    if kind == "komunální":
        rk = rd(find(d, "kvrk.csv")); ros = {(r["KODZASTUP"], r["COBVODU"], r["POR_STR_HL"]): r for r in rd(find(d, "kvros.csv"))}
        zast = {r["KODZASTUP"]: r["NAZEVZAST"] for r in rd(find(d, "kvros.csv"))}
    elif kind == "krajské":
        rk = rd(find(d, "kzrk.csv")); ros = {(r["KRZAST"], r["KSTRANA"]): r for r in rd(find(d, "kzrkl.csv"))}
    else:
        rk = rd(find(d, "psrk.csv")); ros = {r["KSTRANA"]: r for r in rd(find(d, "psrkl.csv"))}
    for r in rk:
        k = key(r["JMENO"], r["PRIJMENI"])
        if k not in targets: continue
        by = year - int(r["VEK"] or 0)
        for t in targets[k]:
            if abs((2026 - int(t["VEK"])) - by) > 1: continue
            if kind == "komunální":
                l = ros.get((r["KODZASTUP"], r["COBVODU"], r["POR_STR_HL"]), {}); kde = zast.get(r["KODZASTUP"], r["KODZASTUP"])
                if kde != "Liberec" and "Liberec" not in (r["BYDLISTEN"] or "") and kde not in (t["BYDLISTEN"],): continue
            elif kind == "krajské":
                l = ros.get((r["KRZAST"], r["KSTRANA"]), {}); kde = "Liberecký kraj"
                if r["KRZAST"] != "6": continue   # 6 = Liberecký kraj (kzciskr.csv)
            else:
                if r["VOLKRAJ"] != "7": continue   # 7 = Liberecký volební kraj
                l = ros.get(r["KSTRANA"], {}); kde = "Liberecký kraj (PS)"
            ident = f'{t["JMENO"]} {t["PRIJMENI"]}|{t["POR_STR_HL"]}|{t["PORCISLO"]}'
            hist.setdefault(ident, []).append({
                "rok": year, "volby": kind, "zastupitelstvo": kde,
                "strana": l.get("ZKRATKAO30") or l.get("ZKRATKAK30") or l.get("NAZEVCELK", ""),
                "poradi": int(r["PORCISLO"]), "povolani": r["POVOLANI"], "hlasy": r.get("POCHLASU"),
                "zvolen": r.get("MANDAT") == "A",
            })
for v in hist.values(): v.sort(key=lambda x: x["rok"])
OUT.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(hist), "candidates with history")
