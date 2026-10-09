"""Extract per-vote records from text-based ZM minutes (Zápis) PDFs.
usage: python3 -I hlas_zapis.py RAWDIR OUT_CSV
For each 'Hlasování č. N ... pro – a, proti – b, zdržel se – c, návrh (ne)byl přijat' in the minutes,
record session, part (pdf), vote no, counts, result, agenda item (last 'K bodu č.'), resolution no., and
the preceding text (context) so the vote subject can be read."""
import csv, json, os, re, subprocess, sys, unicodedata

rawdir, out = sys.argv[1:3]
manifest = json.load(open(os.path.join(rawdir, "downloads.json")))
url_of = {os.path.basename(k): v["url"] for k, v in manifest.items()}


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


D = r"\s*[–—-]\s*"
VOTE = re.compile(r"[Hh]lasování\s+č\.\s*(\d+)\s*(.{0,400}?)\bpro" + D + r"(\d+)\s*,?\s*proti" + D + r"(\d+)\s*,?\s*zdržel[a-z]*\s+se" + D + r"(\d+)\s*,?\s*(.{0,60}?)(?:\.|$)", re.S)
BOD = re.compile(r"K\s+bodu\s+č\.\s*([0-9A-Za-z/\.]+)\s*\n\s*(.{3,300}?)\n", re.S)
USN = re.compile(r"usnesení\s+č\.\s*(\d+\s*/\s*\d{4})")
rows = []
for sess in sorted(os.listdir(rawdir)):
    sd = os.path.join(rawdir, sess)
    if not os.path.isdir(sd):
        continue
    for fn in sorted(os.listdir(sd)):
        if not fold(fn).startswith("zapis") or not fn.lower().endswith(".pdf"):
            continue
        txt = subprocess.run(["pdftotext", os.path.join(sd, fn), "-"], capture_output=True, text=True).stdout
        txt = txt.replace("\f", "\n")
        bods = [(m.start(), m.group(1).strip(". "), re.sub(r"\s+", " ", m.group(2)).strip()) for m in BOD.finditer(txt)]
        prev_end = 0
        ms = list(VOTE.finditer(txt))
        for i, m in enumerate(ms):
            no = int(m.group(1))
            bod = [b for b in bods if b[0] < m.start()]
            bod_no, bod_title = (bod[-1][1], bod[-1][2]) if bod else ("", "")
            start = max(prev_end, bod[-1][0] if bod else 0)
            ctx = re.sub(r"\s+", " ", txt[start:m.start()]).strip()
            ctx = ctx[-500:]
            tail = txt[m.end(): m.end() + 200]
            nxt = ms[i + 1].start() - m.end() if i + 1 < len(ms) else 200
            u = USN.search(tail[: max(0, min(200, nxt))])
            res = fold(m.group(6))
            vysl = "nepřijato" if "nebyl" in res or "neprijat" in res else ("přijato" if "prijat" in res else m.group(6).strip())
            rows.append({"zasedani": sess, "zapis_soubor": fn, "hlasovani_c": no,
                         "o_cem": re.sub(r"\s+", " ", m.group(2)).strip(" –-,"),
                         "pro": int(m.group(3)), "proti": int(m.group(4)), "zdrzelo": int(m.group(5)),
                         "vysledek": vysl, "bod": bod_no, "bod_nazev": bod_title,
                         "usneseni": re.sub(r"\s", "", u.group(1)) if u else "", "kontext": ctx,
                         "zdroj_url": url_of.get(fn, "")})
            prev_end = m.end()
        print(sess, fn[:50], len(ms), file=sys.stderr)
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("votes", len(rows), file=sys.stderr)
