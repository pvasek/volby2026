"""Index „Praxe“ (0–100): vzdělání podle titulů (0–30) + kariéra mimo politiku (0–70).

Vzdělání se počítá automaticky z titulů na kandidátní listině ČSÚ. Kariéru hodnotíme ručně podle
stupnice níže, z profilů v data/processed/strany/<n>.json (soucasna_prace, posledni_nepoliticka_prace, shrnuti)
a povolání uvedeného na listině. Placené politické funkce (primátor, náměstek, asistent radní…) se do kariéry nepočítají.

Stupnice kariéry:
  60–70  vrcholové vedení velké organizace, profesor / docent vedoucí katedry, šéf uměleckého souboru
  45–59  vedoucí pozice nebo zavedený odborník s dlouhou praxí (ředitel pobočky, jednatel výrobní firmy,
         daňový poradce, právník, architekt, vrchní sestra, projektant s vlastní firmou)
  30–44  kvalifikovaná odborná praxe (učitel, IT, projektový manažer, účetní, zdravotní sestra, úředník)
  15–29  krátká praxe, nekvalifikovaná práce nebo o civilní práci skoro nic nevíme
   0–14  student, nezaměstnaný, nic nevíme

Out: data/processed/praxe.json
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "data/processed"

KARIERA = {  # (cislo, poradi): (body 0–70, zdůvodnění)
    (1, 1): (30, "ekolog, zaměstnavatel neověřen"),
    (1, 2): (22, "stavební technik, 29 let"),
    (1, 3): (25, "úředník, terénní koordinátor, technik; od 2020 důchodce"),
    (1, 4): (32, "stavební technik, podnikatel"),
    (1, 5): (30, "podnikatelka v gastronomii, dříve provozní"),
    (2, 1): (55, "jednatel a technický ředitel výrobní firmy METALO, jednatel dalších firem"),
    (2, 2): (52, "ředitel regionální kanceláře CzechInvestu"),
    (2, 3): (58, "dirigent, 18 let šéf opery Divadla F. X. Šaldy"),
    (2, 4): (38, "instrumentářka na operačním sále KNL"),
    (2, 5): (5, "student TUL"),
    (3, 1): (30, "manažerka bytového poradenství, seniorská ombudsmanka; nyní stranická funkce"),
    (3, 2): (42, "auditor (další informace chybí)"),
    (3, 3): (15, "vedoucí marketingu strany; civilní práce neznámá"),
    (3, 4): (32, "IT specialista, programátor; důchodce"),
    (3, 5): (35, "pedagožka"),
    (4, 1): (40, "vedoucí útvaru v Centru pro regionální rozvoj, dříve magistrát a ministerstva"),
    (4, 2): (35, "vedoucí oddělení územního plánování magistrátu (do 2022)"),
    (4, 3): (45, "podnikatel v realitách a odhadce nemovitostí, firmy od 2007"),
    (4, 4): (50, "daňový poradce, OSVČ od 1992"),
    (4, 5): (28, "vedoucí pracovník TSML, jednatel malé firmy; 29 let"),
    (5, 1): (38, "živnostník, projektant elektro"),
    (5, 2): (40, "podnikatelka, ekonomka, jednatelka společnosti (neověřeno)"),
    (5, 3): (35, "manažer obchodu, OSVČ v energetice a stavebnictví; důchodce"),
    (5, 4): (35, "učitelka ZŠ"),
    (5, 5): (38, "podnikatel v IT"),
    (6, 1): (30, "copywriter, online marketér"),
    (6, 2): (45, "olympionička, mistryně světa, komentátorka ČT, dříve učitelka"),
    (6, 3): (45, "právník, pořizování územních plánů"),
    (6, 4): (42, "přírodovědkyně, výzkum a projekty v ochraně životního prostředí"),
    (6, 5): (68, "profesor a vedoucí katedry chemie TUL"),
    (7, 1): (0, "nezaměstnaný, 19 let"),
    (7, 2): (3, "student"),
    (7, 3): (32, "účetní"),
    (7, 4): (42, "projektový manažer, dříve manažer odboru v ČD Telematice"),
    (8, 1): (42, "právnička"),
    (8, 2): (3, "student TUL"),
    (8, 3): (12, "recepční, 22 let"),
    (8, 4): (25, "podnikatelka, obor neuveden"),
    (8, 5): (10, "důchodce, předchozí práce neznámá"),
    (9, 1): (32, "sociální pracovnice, vedoucí pracovnice ve veřejné správě"),
    (9, 2): (15, "od 2008 starosta obvodu; předchozí civilní práce neznámá"),
    (9, 3): (38, "vedoucí oddělení magistrátu, dříve projektový manažer"),
    (9, 4): (32, "projektový manažer, předseda krajského svazu házené"),
    (9, 5): (45, "stavební inženýr, projektant"),
    (10, 1): (65, "generální ředitel Krajské nemocnice Liberec (2011–13), ředitel DPMLJ, ředitel sportovní firmy"),
    (10, 2): (38, "oblastní manažer realitní kanceláře"),
    (10, 3): (20, "asistentka krajské radní (politický aparát), dříve koordinátorka v sociální oblasti"),
    (10, 4): (45, "vrchní sestra (Senevida, dříve urologie KNL)"),
    (10, 5): (45, "projektant a podnikatel, prezident florbalového klubu"),
    (11, 1): (42, "odborný asistent na Univerzitě Karlově, dříve analytik ČT"),
    (11, 2): (55, "25 let tajemník a jednatel Euroregionu Nisa"),
    (11, 3): (38, "odbornice Agentury ochrany přírody a krajiny"),
    (11, 4): (55, "architekt, spoluzakladatel ateliéru ATAKARCHITEKTI, vedoucí Kanceláře architektury města"),
    (11, 5): (60, "docent a vedoucí katedry filozofie TUL"),
}


def vzdelani(jmeno, povolani):
    t = jmeno.replace(",", " ")
    has = lambda rx: re.search(rx, t) is not None
    masters = len(re.findall(r"\b(Ing|Mgr|MUDr|MVDr|JUDr|PhDr|RNDr|PaedDr)\.", t)) + (1 if "arch." in t else 0) * 0
    if has(r"\bprof\."):
        b, d = 30, "profesor"
    elif has(r"\bdoc\."):
        b, d = 29, "docent"
    elif has(r"Ph\.\s?D|CSc\."):
        b, d = 27, "doktorát (Ph.D./CSc.)"
    elif masters:
        b, d = 22, "magisterské / inženýrské"
    elif has(r"\bBc\."):
        b, d = 15, "bakalářské"
    elif "student" in (povolani or "").lower():
        b, d = 8, "studuje VŠ"
    else:
        b, d = 5, "bez titulu na listině"
    extra = (masters >= 2) + has(r"\bMBA\b") + (has(r"\bBc\.") and masters >= 1)
    if extra and b < 30:
        b = min(30, b + 2)
        d += " + další titul"
    return b, d


def main():
    k26 = json.load(open(P / "kandidati_2026.json", encoding="utf-8"))
    out = {}
    for l in k26:
        for c in l["kandidati"][:5]:
            kb, kz = KARIERA[(l["cislo"], c["poradi"])]
            vb, vd = vzdelani(c["jmeno"], c["povolani"])
            out[f'{l["cislo"]}|{c["poradi"]}'] = {"vzdelani_body": vb, "vzdelani": vd, "kariera_body": kb, "kariera": kz, "index": vb + kb}
    (P / "praxe.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in out.items():
        print(k, v["index"], v["vzdelani_body"], v["kariera_body"], v["vzdelani"])


if __name__ == "__main__":
    main()
