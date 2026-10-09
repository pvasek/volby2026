"""Parse OCR'd H.E.R. voting printouts (Liberec ZM) into long CSV.
usage: python3 -I hlas_parse.py OCRDIR RAWDIR OUT_CSV OUT_QA_JSON [ZAPIS_VOTES_CSV]
OCRDIR/<session>/<pdfstem>/page-NNN.txt ; RAWDIR/downloads.json gives source URLs."""
import csv, json, os, re, sys, unicodedata, difflib
from collections import Counter, defaultdict, OrderedDict

ocrdir, rawdir, out_csv, out_qa = sys.argv[1:5]
manifest = json.load(open(os.path.join(rawdir, "downloads.json")))
url_by_key = {}
for dest, m in manifest.items():
    url_by_key[(m["session"], os.path.splitext(m["name"])[0])] = m["url"]


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()


VOTE_PATTERNS = [  # (regex on folded tail, raw label, code)
    (re.compile(r"(PROTI|PR0TI|PROT1|PROTL)\W*$"), "PROTI", "N"),
    (re.compile(r"(Z\s?D\s?R\w{0,2}\s?E\s?L\w?(\s+S\s?E)?|ZDR\w*\s+SE)\W*$"), "ZDRŽEL SE", "Z"),
    (re.compile(r"(NE\s?HLAS\w*|NEHL\w+)\W*$"), "NEHLASOVAL", "X"),
    (re.compile(r"(NEP\w{0,3}TOM\w*|NEPRIT\w*|NEPR\w*TOMEN|NEPRITOMNA)\W*$"), "NEPŘÍTOMEN", "X"),
    (re.compile(r"(PRO|PR0|PRQ)\W*$"), "PRO", "A"),
]
TITLES = {"BC", "MGR", "ING", "MUDR", "PHDR", "RNDR", "JUDR", "MVDR", "DOC", "PROF", "PAEDDR", "PHMR", "MGA", "ING.ARCH", "DIS", "MBA"}
ROW_RE = re.compile(r"^\W{0,3}(\d{1,2}|[Il|]{1,2})[\.\s,|]+(\S{1,3})[\s|©®.]+(.*)$")


def parse_vote_line(line):
    for _ in range(2):  # drop trailing OCR junk like " o", " ©", " |"
        m = re.search(r"\s+(\S{1,2})\s*$", line)
        if m and fold(m.group(1)).upper() != "SE":
            line = line[: m.start()]
    f = fold(line).rstrip()
    if len(f) < 8:
        return None
    for rx, lab, code in VOTE_PATTERNS:
        m = rx.search(f)
        if m:
            # cut the same number of chars from the original line
            body = line.rstrip()[: len(line.rstrip()) - (len(f) - m.start())].rstrip()
            toks = body.split()
            lead = []
            while toks and len(lead) < 3 and not re.search(r"[A-Za-zÀ-ž]{3}", toks[0]) and \
                    fold(toks[0]).strip(".,") not in TITLES:
                lead.append(toks.pop(0))
            if not lead:
                return None
            row = lead[0]; card = lead[1] if len(lead) > 1 else ""
            rest = " ".join(toks).strip(" |©®.")
            if len(rest) < 2 or not re.search(r"[A-Za-zÁ-ž]{2}", rest):
                return None
            return {"row": row, "card": card, "rest": rest, "raw": lab, "code": code}
    return None


TOT_RE = {
    "pritomnych": re.compile(r"P\w?I?TOMN\w*\W+(\d+)"),
    "nepritomnych": re.compile(r"NEP\w{0,4}TOMN\w*\W+(\d+)"),
    "pro": re.compile(r"(?<![A-Z])PRO\W{1,3}(\d+)"),
    "proti": re.compile(r"PROTI\W+(\d+)"),
    "zdrzelo": re.compile(r"ZDR\w*\s?O?\s?SE\W+(\d+)"),
    "nehlasovalo": re.compile(r"NEHLAS\w*\W+(\d+)"),
    "clenu": re.compile(r"CLEN\w*\s+ZASTUP\w*\W+(\d+)"),
}

HEAD_RE = re.compile(r"HLAS\w*\s*(?:(?:C|E|Č)\.?\s*(\d+))?\s*[-–—]?\s*BOD\s*\w?\.?\s*([0-9A-Za-z\.\-/ ]{1,12}?)\s*[-–—]\s*(.*)$")
SESS_RE = re.compile(r"Zased\w*\s*\S*\s*(\d{6})\s*[-–—]\s*(.*?)\s*Dne\W*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*(\d{1,2}:\d{2})?")


def parse_page(text):
    lines = [l for l in text.splitlines()]
    res = {"votes": [], "title": None, "vote_no": None, "bod": None, "poznamka": None,
           "sess_code": None, "sess_name": None, "date": None, "time": None, "tot": {}}
    hi = None
    for i, l in enumerate(lines):
        fl = fold(l)
        if hi is None and ("BOD" in fl or re.search(r"HLASOV\w*\s*C\.?\s*\d", fl)) and ("HLAS" in fl or "VYSLED" in fl or "SLEDEK" in fl):
            m = HEAD_RE.search(fl)
            # work on original line for title (keep diacritics)
            mo = re.search(r"BOD\s*\S?\.?\s*([0-9A-Za-z\.\-/ ]{1,12}?)\s*[-–—]\s*(.*)$", l)
            vn = re.search(r"(?:č|c|Č|e|é)\.?\s*(\d{1,3})\s*[-–—]?\s*BOD", l)
            if not mo:
                mo = re.search(r"(?:č|c|Č|e|é)\.?\s*(\d{1,3})\s*[-–—]\s*(.*)$", l)
                if mo:
                    mo = type("M", (), {"group": (lambda self, k, _m=mo: ("?" if k == 1 else _m.group(2)))})()
            if mo:
                hi = i
                res["bod"] = mo.group(1).strip(" .")
                title = [mo.group(2).strip()]
                for j in range(i + 1, min(i + 4, len(lines))):
                    if re.search(r"Pozn|Zased|^\s*\(", lines[j]):
                        break
                    if lines[j].strip():
                        title.append(lines[j].strip())
                res["title"] = " ".join(title).strip()
                res["vote_no"] = int(vn.group(1)) if vn else None
        if "POZN" in fl and res["poznamka"] is None:
            m = re.search(r"Pozn\w*\W*(.*?)\)?\s*$", l)
            res["poznamka"] = m.group(1).strip(" ()") if m else None
        m = SESS_RE.search(l) or SESS_RE.search(fold(l).replace("ZASED", "Zased"))
        if m and res["date"] is None:
            res["sess_code"], res["sess_name"] = m.group(1), m.group(2)
            res["date"] = f"{m.group(5)}-{int(m.group(4)):02d}-{int(m.group(3)):02d}"
            res["time"] = m.group(6)
        fl2 = re.sub(r"(?<=[A-Z]) (?=[A-Z]{2,}\W*:)|(?<=T[O0]) (?=[A-Z])|(?<=PRIT) (?=O)|(?<=PRI) (?=TOM)", "", fl)
        if "TOMN" in fl2 and re.search(r"\d", fl2):
            mm = re.search(r"TOMN\w*\W+(\d+)", fl2)
            if mm:
                key = "nepritomnych" if re.match(r"\W*NE", fl2) else "pritomnych"
                res["tot"].setdefault(key, int(mm.group(1)))
        for k in ("pro", "proti", "zdrzelo", "nehlasovalo", "clenu"):
            if k in res["tot"]:
                continue
            mm = TOT_RE[k].search(fl)
            if mm and ("TOMN" in fl2 or "CLEN" in fl or "ZASTUPITELSTVA" in fl or "NEHLASOVALO" in fl or "ZDRZELO" in fl.replace(" ", "")):
                res["tot"][k] = int(mm.group(1))
        if hi is not None:
            v = parse_vote_line(l)
            if v and not re.search(r"PRITOMN|ZASTUPITELSTVA:|CLENU", fl):
                res["votes"].append(v)
    return res


def norm_name(s):
    s = fold(s)
    s = re.sub(r"[^A-Z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


rows_out, qa = [], {"pdfs": []}
for sess in sorted(os.listdir(ocrdir)):
    sd = os.path.join(ocrdir, sess)
    if not os.path.isdir(sd):
        continue
    for stem in sorted(os.listdir(sd)):
        pd = os.path.join(sd, stem)
        pages = sorted(p for p in os.listdir(pd) if p.endswith(".txt"))
        parsed = [(p, parse_page(open(os.path.join(pd, p)).read())) for p in pages]
        vp = [(p, r) for p, r in parsed if r["title"] is not None and len(r["votes"]) >= 10]
        info = {"session": sess, "pdf": stem, "pages": len(pages), "vote_pages": len(vp), "issues": []}
        if not vp:
            info["issues"].append("no vote pages parsed")
            qa["pdfs"].append(info)
            continue
        # roster: positional mode over pages with modal line-count
        cnt = Counter(len(r["votes"]) for _, r in vp)
        M = cnt.most_common(1)[0][0]
        clenu = Counter(r["tot"].get("clenu") for _, r in vp if r["tot"].get("clenu")).most_common(1)
        clenu = clenu[0][0] if clenu else 39
        pos = defaultdict(Counter)
        for _, r in vp:
            if len(r["votes"]) == M:
                for k, v in enumerate(r["votes"]):
                    pos[k][re.sub(r"\s+", " ", v["rest"])] += 1
        roster = [pos[k].most_common(1)[0][0] for k in range(M)]
        roster_n = [norm_name(x) for x in roster]
        info["roster_size"] = M
        info["clenu"] = clenu
        # date fallback
        dates = Counter(r["date"] for _, r in vp if r["date"])
        sdate = dates.most_common(1)[0][0] if dates else sess[:10]
        codes = Counter(r["sess_code"] for _, r in vp if r["sess_code"])
        scode = codes.most_common(1)[0][0] if codes else ""
        url = url_by_key.get((sess, stem), "")
        prev_no = 0
        bad = 0
        for p, r in vp:
            no = r["vote_no"]
            if no is None or no <= prev_no or no > prev_no + 5:
                no_src = "inferred"
                no = prev_no + 1 if (r["vote_no"] is None or r["vote_no"] <= prev_no) else r["vote_no"]
            prev_no = no
            assigned = {}
            for k, v in enumerate(r["votes"]):
                n = norm_name(v["rest"])
                if len(r["votes"]) == M and difflib.SequenceMatcher(None, n, roster_n[k]).ratio() > 0.6:
                    idx = k
                else:
                    sc = [difflib.SequenceMatcher(None, n, rn).ratio() for rn in roster_n]
                    idx = max(range(M), key=lambda j: sc[j])
                    if sc[idx] < 0.55:
                        continue
                if idx in assigned:
                    continue
                assigned[idx] = v
            t = dict(r["tot"])
            KEYS = (("pro", "PRO", "A"), ("proti", "PROTI", "N"), ("zdrzelo", "ZDRŽEL SE", "Z"), ("nehlasovalo", "NEHLASOVAL", "X"))
            # absent count: derive from members minus the other four when OCR'd absent total is inconsistent
            if all(k in t for k, _, _ in KEYS):
                derived = clenu - sum(t[k] for k, _, _ in KEYS)
                if t.get("nepritomnych") != derived and t.get("pritomnych") == clenu - derived:
                    t["nepritomnych"] = derived
                elif "nepritomnych" not in t:
                    t["nepritomnych"] = derived
            KEYS = KEYS + (("nepritomnych", "NEPŘÍTOMEN", "X"),)
            imputed = False
            c = Counter(v["raw"] for v in assigned.values())
            if len(assigned) == M - 1 and all(k in t for k, _, _ in KEYS):
                deficit = [(lab, code) for k, lab, code in KEYS if t[k] - c.get(lab, 0) == 1]
                others_ok = sum(1 for k, lab, _ in KEYS if t[k] == c.get(lab, 0)) == len(KEYS) - 1
                if len(deficit) == 1 and others_ok:
                    miss = [j for j in range(M) if j not in assigned][0]
                    assigned[miss] = {"raw": deficit[0][0], "code": deficit[0][1]}
                    imputed = True
                    c = Counter(v["raw"] for v in assigned.values())
            chk = [t[k] == c.get(lab, 0) for k, lab, _ in KEYS if k in t]
            ok = (len(assigned) == M and len(chk) >= 4 and all(chk))
            if len(assigned) == M and len(chk) >= 3 and all(chk):
                ok = True
                for k, lab, _ in KEYS:
                    t.setdefault(k, c.get(lab, 0))
            status = ("OK_DOPLNENO_ZE_SOUCTU" if imputed else "OK") if ok else ("NEUPLNE" if len(assigned) < M else "NESOULAD_SOUCTU")
            if not ok:
                bad += 1
            pro_tot = t.get("pro", c.get("PRO", 0))
            vysl = "přijato" if pro_tot > clenu / 2 else "nepřijato"
            date = r["date"] or sdate
            zas = sess if date == sess[:10] else f"{sess} (jednání {date})"
            for idx in range(M):
                person = roster[idx]
                v = assigned.get(idx)
                rows_out.append({
                    "datum": date, "zasedani": zas, "zasedani_kod": r["sess_code"] or scode,
                    "bod": r["bod"], "nazev": r["title"], "hlasovani_c": no,
                    "zastupitel_raw": person, "hlas": v["code"] if v else "", "hlas_raw": v["raw"] if v else "",
                    "vysledek": vysl, "pro": t.get("pro"), "proti": t.get("proti"), "zdrzelo": t.get("zdrzelo"),
                    "nehlasovalo": t.get("nehlasovalo"), "nepritomno": t.get("nepritomnych"),
                    "kontrola": status, "zdroj_url": url, "strana_pdf": int(p[5:8]), "poznamka": r["poznamka"],
                })
        info["pages_not_ok"] = bad
        qa["pdfs"].append(info)
        print(sess, stem[:40], "pages", len(pages), "votes", len(vp), "M", M, "bad", bad, file=sys.stderr)

# split zastupitel_raw into name + party using known party suffixes
PARTIES = ["Změna pro Liberec", "Starostové pro Liberecký kraj", "ANO 2011", "ANO", "SLK", "ODS", "ČSSD", "TOP09", "TOP 09", "KSČM",
           "LOL", "ZpL", "SPD", "Piráti", "BEZ ZK", "Pro Liberec", "PRO Liberec", "Nezávislí", "nez.", "BEZPP", "Bez PP", "STAN",
           "KDU-ČSL", "Liberec otevřený lidem", "Zelení", "SZ", "PRO 2016", "SPOLU", "BEZ KLUBU", "NK", "Nezař.", "Nezávislá", "BPP", "BEZ"]
PF = sorted(((fold(p), p) for p in PARTIES), key=lambda x: -len(x[0]))


def split_party(s):
    fs = fold(s).rstrip(" .|")
    for fp, p in PF:
        if fs.endswith(" " + fp) or fs.endswith(fp) and len(fs) > len(fp) + 3 and not fs[-len(fp) - 1].isalpha():
            return s[: len(s.rstrip(" .|")) - len(fp)].strip(" |,"), p
    # fuzzy: last 1-3 tokens
    toks = s.split()
    for n in (3, 2, 1):
        tail = fold(" ".join(toks[-n:]))
        for fp, p in PF:
            if difflib.SequenceMatcher(None, tail, fp).ratio() >= 0.8 and len(toks) > n + 1:
                return " ".join(toks[:-n]), p
    return s, ""


TIT = re.compile(r"\b(Bc|Ing\.arch\.Ing|Ing\.arch\.ing|Ing\.arch|Ing|Mgr|MUDr|PhDr|RNDr|JUDr|MVDr|doc|prof|Ph\.\s?D|PhD|CSc|MBA|M\.A|LL\.M|MPA|Dipl\.\s?Kfm|DiS)\b\.?,?", re.I)
ALIAS = {"Jindřich Feleman": "Jindřich Felcman", "Jindřich Felecman": "Jindřich Felcman", "Marek Várvra": "Marek Vávra",
         "Jiří Šole": "Jiří Šolc", "Jan Meči": "Jan Mečl", "Vit Kyzlink": "Vít Kyzlink", "Pavla Hnyková Haidlová": "Pavla Haidlová",
         "Radka Loučková-Kotasová": "Radka Loučková Kotasová", "Petr Židek ops": "Petr Židek", "Zora Machartová BPP": "Zora Machartová",
         "Ivan Langr BEZ": "Ivan Langr"}


def norm_person(n):
    if n.startswith("("):
        return n
    x = TIT.sub(" ", n)
    x = re.sub(r"[,\.]", " ", x)
    x = re.sub(r"\s+", " ", x).strip()
    return ALIAS.get(x, x)


cache = {}
for r in rows_out:
    k = r["zastupitel_raw"]
    if k not in cache:
        cache[k] = split_party(k)
    r["zastupitel"], r["klub_strana"] = cache[k]
    if len(re.sub(r"[^A-Za-zÀ-ž]", "", r["zastupitel"])) < 4 or fold(r["zastupitel"]).strip() == fold(r["klub_strana"]).strip():
        r["zastupitel"] = "(mandát bez jména na protokolu – neobsazený)"
    r["jmeno_norm"] = norm_person(r["zastupitel"])

# ---- join with minutes (zápis) per-vote records -------------------------------------------
zap_csv = sys.argv[5] if len(sys.argv) > 5 else None
if zap_csv:
    zap = list(csv.DictReader(open(zap_csv)))
    by_sess = defaultdict(list)
    for z in zap:
        z["_n"] = int(z["hlasovani_c"])
        by_sess[z["zasedani"]].append(z)
    sess_sorted = sorted(by_sess)
    KW = ("nahrad", "pokrac")

    def pool_for(sess, pdfstem):
        zs = by_sess.get(sess)
        if not zs:  # e.g. 2016-06-09 ZM 5N: minutes filed in the previous session folder
            prev = [x for x in sess_sorted if x < sess]
            zs = by_sess.get(prev[-1], []) if prev else []
        files = sorted({z["zapis_soubor"] for z in zs})
        fp = fold(pdfstem).lower()
        pref = [f for f in files if any(kw in fp and kw in fold(f).lower() for kw in KW)]
        if not pref:
            pref = [f for f in files if not any(kw in fold(f).lower() for kw in KW)] or files
        return [z for z in zs if z["zapis_soubor"] in pref] + [z for z in zs if z["zapis_soubor"] not in pref]
    stem_of = {u: stem for (sess, stem), u in url_by_key.items()}
    votes = OrderedDict()
    for r in rows_out:
        votes.setdefault((r["zasedani"], r["zdroj_url"], r["hlasovani_c"]), []).append(r)
    used = set()
    for (zas, url, no), rs in votes.items():  # pass 1: exact number + counts
        r0 = rs[0]
        key = tuple(str(r0[k]) if r0[k] not in (None, "") else None for k in ("pro", "proti", "zdrzelo"))
        for z in pool_for(zas.split(" (")[0], stem_of.get(url, "")):
            if z["_n"] == int(no) and all(a is None or a == z[k] for a, k in zip(key, ("pro", "proti", "zdrzelo"))):
                used.add(id(z))
                break
    for (zas, url, no), rs in votes.items():
        r0 = rs[0]
        pool = pool_for(zas.split(" (")[0], stem_of.get(url, ""))
        key = tuple(str(r0[k]) if r0[k] not in (None, "") else None for k in ("pro", "proti", "zdrzelo"))
        same_no = [z for z in pool if z["_n"] == int(no)]
        cm = lambda z: all(a is None or a == z[k] for a, k in zip(key, ("pro", "proti", "zdrzelo")))
        hit = [z for z in same_no if cm(z)]
        status = "ano"
        if hit:
            z = hit[0]
        else:
            near = [z for z in pool if abs(z["_n"] - int(no)) <= 2 and cm(z) and id(z) not in used]
            if len(near) == 1:
                z, status = near[0], "ano_posun_cisla"
            elif same_no:
                z, status = same_no[0], "ne"
            else:
                z, status = None, ("nenalezeno" if pool else "zapis_chybi")
        for r in rs:
            r["zapis_shoda"] = status
            if z is None:
                continue
            r["zapis_hlasovani_c"] = z["_n"]
            r["usneseni"] = z["usneseni"]
            r["popis_ze_zapisu"] = (z["o_cem"] + " | " if z["o_cem"] else "") + z["kontext"][-300:]
            r["zapis_url"] = z["zdroj_url"]
            if status != "ne" and z["vysledek"] in ("přijato", "nepřijato"):
                r["vysledek"] = z["vysledek"]
                r["vysledek_zdroj"] = "zápis"
    for r in rows_out:
        r.setdefault("vysledek_zdroj", "dopočteno (PRO > polovina členů)")
    print("zapis join", Counter(r["zapis_shoda"] for r in rows_out), file=sys.stderr)

cols = ["datum", "zasedani", "zasedani_kod", "bod", "nazev", "hlasovani_c", "zastupitel", "jmeno_norm", "klub_strana", "hlas", "hlas_raw",
        "vysledek", "vysledek_zdroj", "pro", "proti", "zdrzelo", "nehlasovalo", "nepritomno", "kontrola", "zapis_shoda", "zapis_hlasovani_c",
        "usneseni", "strana_pdf", "zdroj_url"]
vcols = ["datum", "zasedani", "zasedani_kod", "bod", "nazev", "hlasovani_c", "vysledek", "vysledek_zdroj", "pro", "proti", "zdrzelo",
         "nehlasovalo", "nepritomno", "kontrola", "zapis_shoda", "zapis_hlasovani_c", "usneseni", "poznamka", "popis_ze_zapisu",
         "strana_pdf", "zdroj_url", "zapis_url"]
seen = set()
with open(re.sub(r"_long\.csv$", "_votes.csv", out_csv) if out_csv.endswith("_long.csv") else out_csv + ".votes.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=vcols, extrasaction="ignore")
    w.writeheader()
    for r in rows_out:
        k = (r["zasedani"], r["zdroj_url"], r["hlasovani_c"])
        if k not in seen:
            seen.add(k)
            w.writerow(r)
with open(out_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows_out)
json.dump(qa, open(out_qa, "w"), ensure_ascii=False, indent=1)
print("rows", len(rows_out), file=sys.stderr)
