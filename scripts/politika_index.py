"""Index „Politika“ (0–100) spočítaný z doložených funkcí v profilech kandidátů (data/processed/strany/<n>.json → politicka_kariera).

Politika = min(100, 3 × R + F)
  R = počet let ve volených nebo výkonných funkcích (sjednocení období; kandidatury, členství ve straně,
      výbory, komise, dozorčí rady a stranické funkce se nepočítají; probíhající funkce do roku 2026)
  F = body za nejvyšší dosaženou funkci (viz FUNKCE)
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"
NOW = 2026

def classify(funkce):
    """Vrátí [(body, název)] pro volenou/výkonnou funkci, jinak []. Rozhoduje text před první závorkou."""
    f = funkce.lower()
    if re.search(r"kandid|nezvolen|nevolen|nečlen", f):
        return []
    head = f.split("(")[0]
    if re.match(r"\s*(člen|členka|lídr|předsed|místopředsed|asistent|vedoucí|zakladatel|seniorsk)", head) or \
       re.search(r"výbor|komis|dozorčí|představenstv|statutárního orgánu", head):
        return []
    hits = []
    if re.search(r"náměst(ek|kyně)", head):
        hits.append((22, "náměstek primátora / hejtmana"))
    elif re.search(r"\bprimátor", head):
        hits.append((30, "primátor"))
    if re.search(r"poslan|senátor", head):
        hits.append((22, "poslanec / senátor"))
    if re.search(r"\bradní", head):
        hits.append((16, "radní"))
    if re.search(r"(?<!místo)starost(a|ka)\b", head):
        hits.append((16, "starosta městského obvodu"))
    if re.search(r"místostarost", head):
        hits.append((5, "místostarosta obvodu"))
    if re.search(r"krajsk\w* zastupitel|zastupitel\w* (libereckého )?kraje|\bzlk\b", head):
        hits.append((10, "krajský zastupitel"))
    elif re.search(r"zastupitel\w* (mo\b|obvodu|městského obvodu)|zastupitel\w* .*vratislav", head):
        hits.append((5, "zastupitel městského obvodu"))
    elif re.search(r"zastupitel", head):
        hits.append((8, "zastupitel města"))
    return hits


def politika(kariera):
    years, best = set(), (0, "žádná volená funkce")
    used = []
    for k in kariera or []:
        hits = classify(k.get("funkce", ""))
        if not hits:
            continue
        od, do = k.get("od"), k.get("do")
        if not isinstance(od, int):
            # bez roku začátku: jen body za funkci, roky nepočítáme
            od = do = None
        else:
            do = do if isinstance(do, int) else NOW
            years.update(range(od, max(do, od + 1)))
        b = max(hits)
        if b[0] > best[0]:
            best = b
        used.append({"funkce": k["funkce"], "od": k.get("od"), "do": k.get("do"), "body": b[0], "typ": b[1]})
    R = len(years)
    return {"index": min(100, 3 * R + best[0]), "roky": R, "funkce_body": best[0], "funkce": best[1], "zapocteno": used}


def main():
    out = {}
    for f in sorted((P / "strany").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for k in d["kandidati"]:
            out[f'{d["cislo"]}|{k["poradi"]}'] = politika(k.get("politicka_kariera"))
    (P / "politika.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    res = main()
    old = {}
    for f in sorted((P / "strany").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for k in d["kandidati"]:
            old[f'{d["cislo"]}|{k["poradi"]}'] = (k.get("zkusenost_skore"), k.get("jmeno"))
    for key, v in sorted(res.items(), key=lambda kv: (int(kv[0].split("|")[0]), int(kv[0].split("|")[1]))):
        print(f'{key:>5} {old[key][1][:28]:<28} old={old[key][0]!s:>3} new={v["index"]:>3} = 3×{v["roky"]} + {v["funkce_body"]} ({v["funkce"]})')
