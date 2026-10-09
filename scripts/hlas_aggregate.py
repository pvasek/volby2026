"""Aggregate council roll-call votes: per-candidate stats and club-to-club agreement.
In:  data/processed/hlasovani_long.csv, data/processed/kandidati_2026.json
Out: data/processed/hlasovani_agg.json"""
import collections, csv, json, pathlib, re, sys, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"
TITLES = r"\b(ing|mgr|bc|phdr|rndr|mudr|mvdr|judr|doc|prof|paeddr|arch|csc|ph\.?d|mba|mpa|ll\.?m|m\.?a)\b\.?"


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(TITLES, " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    return " ".join(s.split())


TERMS = [("2014–2018", "2014-11-01", "2018-10-31"), ("2018–2022", "2018-11-01", "2022-10-31"), ("2022–2026", "2022-11-01", "2026-12-31")]
CLUB_ALIAS = {"ZpL": "Změna pro Liberec", "TOP09": "TOP 09", "BEZ ZK": "bez klubu"}


def term_of(d):
    return next((t for t, a, b in TERMS if a <= d <= b), None)


def main():
    rows = list(csv.DictReader(open(P / "hlasovani_long.csv", encoding="utf-8")))
    k26 = json.load(open(P / "kandidati_2026.json", encoding="utf-8"))
    hist = json.load(open(P / "historie_kandidatu.json", encoding="utf-8"))
    def was_councillor(l, c):  # namesakes (e.g. two Tibor Batthyány on one list): prefer the one elected to the city council
        h = next((v for k, v in hist.items() if k.endswith(f'|{l["cislo"]}|{c["poradi"]}')), [])
        return any(x["volby"] == "komunální" and x["zastupitelstvo"] == "Liberec" and x["zvolen"] for x in h)
    cand = {}
    for l in k26:
        for c in l["kandidati"]:
            n = norm(c["jmeno"])
            if n not in cand or (was_councillor(l, c) and not was_councillor(*cand[n])):
                cand[n] = (l, c)

    by_vote = collections.defaultdict(list)
    for r in rows:
        by_vote[(r["zasedani"], r["hlasovani_c"])].append(r)

    # club position per vote = plurality among members present & voting (A/N/Z)
    club_pos = {}
    contested = set()
    for key, rs in by_vote.items():
        pro = sum(r["hlas_raw"] == "PRO" for r in rs)
        opp = sum(r["hlas_raw"] in ("PROTI", "ZDRŽEL SE") for r in rs)
        if opp >= 3 and pro >= 3:
            contested.add(key)
        clubs = collections.defaultdict(collections.Counter)
        for r in rs:
            h = {"PRO": "A", "PROTI": "N", "ZDRŽEL SE": "Z"}.get(r["hlas_raw"])
            if h and r["klub_strana"]:
                clubs[CLUB_ALIAS.get(r["klub_strana"], r["klub_strana"])][h] += 1
        club_pos[key] = {c: cnt.most_common(1)[0][0] for c, cnt in clubs.items() if sum(cnt.values()) >= 1}

    # per person
    st = collections.defaultdict(lambda: collections.Counter())
    span = {}
    clubs_of = collections.defaultdict(set)
    for r in rows:
        n = norm(r["jmeno_norm"] or r["zastupitel"])
        if n not in cand:
            continue
        s = st[n]
        s["n"] += 1
        s[r["hlas_raw"] or "?"] += 1
        d = r["datum"]
        span[n] = (min(span.get(n, (d, d))[0], d), max(span.get(n, (d, d))[1], d))
        club = CLUB_ALIAS.get(r["klub_strana"], r["klub_strana"])
        if club:
            clubs_of[n].add(club)
        key = (r["zasedani"], r["hlasovani_c"])
        h = {"PRO": "A", "PROTI": "N", "ZDRŽEL SE": "Z"}.get(r["hlas_raw"])
        if h and club and club in club_pos[key] and key in contested:
            s["contested_voted"] += 1
            if h != club_pos[key][club]:
                s["rebel"] += 1

    osoby = []
    for n, s in st.items():
        l, c = cand[n]
        present = s["n"] - s["NEPŘÍTOMEN"]
        voted = s["PRO"] + s["PROTI"] + s["ZDRŽEL SE"]
        pct = lambda a, b: round(100 * a / b, 1) if b else None
        osoby.append({
            "jmeno": c["jmeno"], "cislo": l["cislo"], "poradi": c["poradi"],
            "od": span[n][0], "do": span[n][1], "kluby": sorted(clubs_of[n]),
            "hlasovani": s["n"], "ucast_pct": pct(present, s["n"]),
            "pro_pct": pct(s["PRO"], voted), "proti_pct": pct(s["PROTI"], voted), "zdrzel_pct": pct(s["ZDRŽEL SE"], voted),
            "nehlasoval_pct": pct(s["NEHLASOVAL"], present),
            "odchylka_od_klubu_pct": pct(s["rebel"], s["contested_voted"]), "spornych": s["contested_voted"],
        })
    osoby.sort(key=lambda o: (o["cislo"], o["poradi"]))

    # club agreement per term on contested votes
    kluby = {}
    for t, a, b in TERMS:
        keys = [k for k in contested if a <= by_vote[k][0]["datum"] <= b]
        agree, tot = collections.Counter(), collections.Counter()
        names = collections.Counter()
        for k in keys:
            pos = club_pos[k]
            for c in pos:
                names[c] += 1
            for c1 in pos:
                for c2 in pos:
                    tot[(c1, c2)] += 1
                    agree[(c1, c2)] += pos[c1] == pos[c2]
        cl = [c for c, n in names.most_common() if n >= 0.3 * len(keys) and c != "bez klubu"]
        if not keys or not cl:
            continue
        kluby[t] = {"kluby": cl, "spornych": len(keys),
                    "shoda": [[round(100 * agree[(x, y)] / tot[(x, y)]) if tot[(x, y)] else None for y in cl] for x in cl]}

    out = {
        "osoby": osoby, "kluby": kluby,
        "metodika": "Sporné hlasování = alespoň 3 hlasy pro a alespoň 3 proti nebo zdržel se. Pozice klubu = nejčastější volba "
                    "(pro / proti / zdržel se) přítomných hlasujících členů klubu. Odchylka od klubu = podíl sporných hlasování, "
                    "kde zastupitel hlasoval jinak než většina jeho klubu. Účast = podíl hlasování, kdy nebyl veden jako nepřítomný.",
        "celkem_hlasovani": len(by_vote), "spornych_celkem": len(contested),
    }
    (P / "hlasovani_agg.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(osoby), "candidates with votes;", len(contested), "contested of", len(by_vote))
    for o in osoby:
        print(f'{o["cislo"]:>2}.{o["poradi"]:<2} {o["jmeno"][:28]:<28} {o["od"]}–{o["do"]} n={o["hlasovani"]:>5} účast={o["ucast_pct"]} pro={o["pro_pct"]} proti={o["proti_pct"]} zdr={o["zdrzel_pct"]} odch={o["odchylka_od_klubu_pct"]} {o["kluby"]}')
    for t, v in kluby.items():
        print(t, v["spornych"], v["kluby"])
        for c, r in zip(v["kluby"], v["shoda"]):
            print(f"   {c[:12]:<12}", r)


if __name__ == "__main__":
    main()
