"""OCR one scanned voting PDF page by page (pdftoppm 200dpi gray + tesseract ces psm6).
usage: python3 -I hlas_ocr.py PDF OUTDIR   -> OUTDIR/page-NNN.txt"""
import os, subprocess, sys, tempfile, re
pdf, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
n = int(re.search(r"Pages:\s+(\d+)", info).group(1))
env = dict(os.environ, OMP_THREAD_LIMIT="1")
with tempfile.TemporaryDirectory() as td:
    for p in range(1, n + 1):
        dest = os.path.join(out, f"page-{p:03d}.txt")
        if os.path.exists(dest): continue
        base = os.path.join(td, "img")
        subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-r", "200", "-gray", "-singlefile", pdf, base], check=True)
        r = subprocess.run(["tesseract", base + ".pgm", "stdout", "-l", "ces", "--psm", "6"], capture_output=True, text=True, env=env)
        open(dest + ".tmp", "w").write(r.stdout); os.replace(dest + ".tmp", dest)
        os.remove(base + ".pgm")
print("done", pdf, n)
