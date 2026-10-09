"""Enumerate podklady.liberec.cz ZM (zastupitelstvo) tree; write JSON index of sessions+files.
usage: python3 -I hlas_enumerate.py OUT.json [years...]"""
import json, sys, time, urllib.request, urllib.parse
BASE = "https://podklady.liberec.cz/?controller=open&action="
def post(action, data):
    body = "&".join(f"{k}={v}" for k, v in data.items()).encode()  # path already urlencoded
    for i in range(5):
        try:
            req = urllib.request.Request(BASE + action, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("retry", action, data, e, file=sys.stderr); time.sleep(3)
    raise RuntimeError("failed")
out = sys.argv[1]
years = sys.argv[2:] or [str(y) for y in range(2016, 2027)]
res = []
for y in years:
    sess = post("loadtree", {"agend": "zm", "path": y})
    for s in sess:
        c = post("loadcontent", {"agend": "zm", "path": s["path"]})
        items = list(c.values()) if isinstance(c, dict) else c
        files = []
        for it in items:
            if it.get("file"):
                files.append({"name": it["name"], "path": it["path"], "size": it.get("size"), "strtime": it.get("strtime")})
            elif it.get("name") == "Dle bodů":
                sub = post("loadcontent", {"agend": "zm", "path": it["path"]})
                subitems = list(sub.values()) if isinstance(sub, dict) else sub
                for si in subitems:
                    if si.get("file"):
                        files.append({"name": "Dle bodů/" + si["name"], "path": si["path"], "size": si.get("size"), "strtime": si.get("strtime")})
            else:
                files.append({"name": it["name"], "link": it["path"].strip(), "dir": True})
        res.append({"year": y, "session": s["name"], "path": s["path"], "files": files})
        print(y, s["name"], len(files), file=sys.stderr)
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
