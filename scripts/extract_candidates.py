"""Extract Liberec (KODZASTUP 563889) lists + candidates from the official CSU registry CSVs."""
import csv, json, sys, pathlib

ROOT = pathlib.Path(sys.argv[1])  # e.g. data/raw/volby_gov/kv2026
OUT = pathlib.Path(sys.argv[2])
KOD = "563889"

def rd(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))

cpp = {r["PSTRANA"]: r for r in rd(ROOT / "cis/csv_od/cpp.csv")}
cns = {r["NSTRANA"]: r for r in rd(ROOT / "cis/csv_od/cns.csv")}
lists = [r for r in rd(ROOT / "reg/csv_od/kvros.csv") if r["KODZASTUP"] == KOD]
cands = [r for r in rd(ROOT / "reg/csv_od/kvrk.csv") if r["KODZASTUP"] == KOD]
out = []
for l in sorted(lists, key=lambda r: int(r["POR_STR_HL"])):
    cs = sorted([c for c in cands if c["POR_STR_HL"] == l["POR_STR_HL"]], key=lambda c: int(c["PORCISLO"]))
    out.append({
        "cislo": int(l["POR_STR_HL"]), "nazev": l["NAZEVCELK"], "zkratka": l["ZKRATKAO8"],
        "slozeni": l["SLOZENI"], "hlasy": l.get("HLASY_STR"), "procenta": l.get("PROCHLSTR"), "mandaty": l.get("MAND_STR"),
        "kandidati": [{
            "poradi": int(c["PORCISLO"]),
            "jmeno": " ".join(x for x in [c["TITULPRED"], c["JMENO"], c["PRIJMENI"], c["TITULZA"]] if x),
            "vek": int(c["VEK"]), "povolani": c["POVOLANI"], "bydliste": c["BYDLISTEN"],
            "prislusnost": cpp.get(c["PSTRANA"], {}).get("ZKRATKAP8", c["PSTRANA"]),  # PSTRANA = politická příslušnost (KV2026regPopis)
            "navrhujici_strana": cns.get(c["NSTRANA"], {}).get("ZKRATKAN8", c["NSTRANA"]),  # NSTRANA = navrhující strana
            "platnost": c["PLATNOST"], "hlasy": c.get("POCHLASU"), "mandat": c.get("MANDAT"),
        } for c in cs],
    })
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for l in out:
    print(f'{l["cislo"]:>2} {l["zkratka"]:<16} {l["nazev"][:50]:<50} n={len(l["kandidati"])}')
    for c in l["kandidati"][:5]:
        print(f'     {c["poradi"]}. {c["jmeno"]} ({c["vek"]}) {c["povolani"]} | {c["navrhujici_strana"]}/{c["prislusnost"]}')
