"""Download 'Výsledky hlasování' PDFs (and optionally Usnesení) listed in podklady_index.json.
usage: python3 -I hlas_download.py INDEX.json OUTDIR [--usneseni] [--zapis] [--only-extra]
Files saved as OUTDIR/<YYYY-MM-DD ZM N>/<original filename>. Writes OUTDIR/downloads.json manifest."""
import json, os, sys, time, urllib.request, unicodedata, hashlib, datetime
idx = json.load(open(sys.argv[1])); outdir = sys.argv[2]
want_usn = "--usneseni" in sys.argv
want_zap = "--zapis" in sys.argv
only_extra = "--only-extra" in sys.argv
DL = "https://podklady.liberec.cz/?controller=open&action=download&agend=zm&path="
manifest_p = os.path.join(outdir, "downloads.json")
manifest = json.load(open(manifest_p)) if os.path.exists(manifest_p) else {}
def is_vote(n):
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower()
    return n.startswith("vysledky hlasovani") or n.startswith("vysledek hlasovani")
def is_zap(n):
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower()
    return n.startswith("zapis")
def is_usn(n):
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower()
    return n.startswith("usneseni")
for s in idx:
    for f in s["files"]:
        if f.get("dir") or "/" in f["name"]:
            continue
        if not (((not only_extra) and is_vote(f["name"])) or (want_usn and is_usn(f["name"])) or (want_zap and is_zap(f["name"]))):
            continue
        d = os.path.join(outdir, s["session"]); os.makedirs(d, exist_ok=True)
        dest = os.path.join(d, f["name"])
        url = DL + f["path"]
        if os.path.exists(dest) and os.path.getsize(dest) > 1000 and dest in manifest:
            continue
        for i in range(6):
            try:
                with urllib.request.urlopen(url, timeout=300) as r, open(dest + ".part", "wb") as o:
                    ct = r.headers.get("Content-Type")
                    while True:
                        b = r.read(1 << 20)
                        if not b: break
                        o.write(b)
                os.replace(dest + ".part", dest)
                break
            except Exception as e:
                print("retry", f["name"], e, file=sys.stderr); time.sleep(5)
        else:
            print("FAILED", url, file=sys.stderr); continue
        h = hashlib.sha256(open(dest, "rb").read()).hexdigest()
        manifest[dest] = {"url": url, "session": s["session"], "name": f["name"], "listed_size": f.get("size"),
                          "listed_time": f.get("strtime"), "bytes": os.path.getsize(dest), "sha256": h, "content_type": ct,
                          "fetched": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
        json.dump(manifest, open(manifest_p, "w"), ensure_ascii=False, indent=1)
        print("ok", s["session"], f["name"], os.path.getsize(dest), file=sys.stderr)
