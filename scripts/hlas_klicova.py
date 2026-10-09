"""Build hlasovani_summary.json and hlasovani_klicova.json from hlasovani_long.csv.
usage: python3 -I hlas_klicova.py LONG_CSV QA_JSON ZAPIS_CSV INDEX_JSON OUT_SUMMARY OUT_KLICOVA"""
import csv, json, sys
from collections import Counter, OrderedDict, defaultdict

long_csv, qa_json, zap_csv, index_json, out_sum, out_key = sys.argv[1:7]
rows = list(csv.DictReader(open(long_csv)))
qa = json.load(open(qa_json))
zap = list(csv.DictReader(open(zap_csv)))
idx = json.load(open(index_json))

votes = OrderedDict()
for r in rows:
    votes.setdefault((r["zasedani"], r["zdroj_url"], r["hlasovani_c"]), []).append(r)

# ------------------------------------------------------------------ key votes
# (datum, číslo hlasování dle zápisu, téma, popis, kontextový zdroj)
SEL = [
    ("2016-12-15", 23, "hazard", "Hlasování o protinávrhu „nulová tolerance hazardu“ v bodu Regulace provozování hazardních her na území města (usn. 289/2016); protinávrh byl přijat.", ""),
    ("2017-01-26", 4, "rozpočet", "Schválení rozpočtu města na rok 2017 ve znění pozměňovacích návrhů (usn. 3/2017), za primátora T. Batthyányho.", ""),
    ("2017-03-02", 15, "symbolická gesta", "Připojení města ke kampani „Vlajka pro Tibet“ (vyvěšení tibetské vlajky 10. března) – usn. 35/2017.", ""),
    ("2017-04-27", 16, "doprava / tramvaj", "Souhlas se zahájením projekční a investiční přípravy novostavby tramvajové trati Liberec – dolní centrum Dopravním podnikem (DPMLJ) a s finančním příspěvkem do 7 mil. Kč (usn. 102/2017).", ""),
    ("2017-06-29", 40, "spory ve vedení města 2017", "Primátor T. Batthyány pozastavil výkon usnesení rady města o změně organizačního řádu magistrátu a věc předložil zastupitelstvu; hlasování o návrhu usnesení k tomuto pozastavení (usn. 164/2017).", ""),
    ("2018-02-01", 13, "teplárenství", "Mimořádné zasedání: schválení prováděcího ujednání s MVV Energie CZ a Teplárnou Liberec (budoucnost dodávek tepla, projekt GreenNet, korporátní změny) – usn. 28/2018.", "https://oenergetice.cz/teplarenstvi/liberec-se-zacal-pripravovat-na-mozny-prodej-podilu-v-teplarne"),
    ("2018-03-29", 22, "majetek / autobusové nádraží", "Odkup budov autobusového nádraží ve Vaňurově ulici městem (usn. 80/2018).", ""),
    ("2018-03-29", 29, "hazard", "Obecně závazná vyhláška o regulaci provozování hazardních her na území města (usn. 87/2018).", ""),
    ("2018-09-06", 29, "Ještěd", "Řešení finanční situace městské společnosti Sportovní areál Ještěd, a. s. (upravený návrh usnesení, usn. 200/2018).", ""),
    ("2018-11-20", 4, "ustavující zasedání 2018", "Ustavující zasedání po volbách 2018: stanovení počtu členů Rady města na 11 (usn. 249/2018). Volba primátora a radních byla tajná a jmenovitě se nezaznamenává.", "https://www.e15.cz/domaci/liberec-povede-koalice-slk-ano-a-ods-1353047"),
    ("2019-02-28", 28, "rozpočet", "Schválení rozpočtu města na rok 2019 (první rozpočet koalice SLK–ANO–ODS, usn. 57/2019).", ""),
    ("2019-10-24", 11, "Ještěd / sport", "Modernizace skokanských můstků ve sportovním areálu Ještěd – upravený návrh usnesení o přípravě projektu a žádosti o dotaci (usn. 311/2019).", "https://www.kraj-lbc.cz/aktuality/case:detailPdf/itemId:534079/cgId:15623"),
    ("2019-12-12", 20, "rozpočet", "Schválení rozpočtu města na rok 2020 (původní návrh, usn. 364/2019).", ""),
    ("2020-05-07", 11, "Ještěd", "Mimořádné zasedání: uzavření dodatku č. 1 ke koncesní smlouvě na provozování Sportovního areálu Ještěd (usn. 87/2020).", ""),
    ("2020-12-10", 11, "majetek / developeři", "Směna nemovitostí se společností SYNER Group, a. s. (město získává pozemky u Papírového náměstí, Syner pozemky v Kunraticích; doplněno o plánovací smlouvu se školkou) – usn. 301/2020.", "https://www.seznamzpravy.cz/clanek/liberec-smeni-pozemky-s-firmou-syner-doplati-za-ne-23-milionu-kc-133326"),
    ("2020-12-10", 19, "rozpočet", "Schválení upraveného návrhu rozpočtu města na rok 2021 (usn. 304/2020).", ""),
    ("2021-06-24", 59, "sport / bazén", "Založení městské společnosti BAZÉN LIBEREC, s.r.o. pro provoz městského plaveckého bazénu (usn. 196/2021).", ""),
    ("2021-11-25", 20, "ZOO / kraj", "Darování ZOO Liberec a Botanické zahrady Libereckému kraji a přijetí daru domovů seniorů od kraje (usn. 279/2021).", "https://www.kraj-lbc.cz/aktuality/case:detailPdf/itemId:548141/cgId:15623"),
    ("2021-12-16", 14, "rozpočet / opozice", "Oddělené hlasování o protinávrhu opozice (prof. Šedlbauer, LOL) k rozpočtu 2022 – bod a): přesun 10 mil. Kč z provozu plaveckého bazénu do fondu pro rekonstrukci městského bazénu; nepřijato.", ""),
    ("2021-12-16", 25, "rozpočet", "Schválení rozpočtu města na rok 2022 (usn. 309/2021).", ""),
    ("2022-02-24", 24, "územní plán", "Vydání nového územního plánu Liberec (usn. 72/2022), připravovaného téměř 15 let.", "https://ct24.ceskatelevize.cz/clanek/regiony/liberec-ma-schvaleny-novy-uzemni-plan-jeho-priprava-trvala-skoro-patnact-let-22965"),
    ("2022-02-24", 46, "spory / byty", "Souhlas se zpětvzetím odvolání v soudním sporu mezi městem a společností Interma Byty, a. s. (kauza bytových domů SBD A+G Stadion) – usn. 70/2022.", ""),
    ("2022-06-30", 39, "územní plán / Textilana", "Pořízení změny územního plánu zkráceným postupem Z1_A Textilana (usn. 191/2022).", ""),
    ("2022-10-18", 4, "ustavující zasedání 2022", "Ustavující zasedání po volbách 2022: stanovení počtu členů Rady města na 11 (usn. 266/2022). Primátor J. Zámečník byl zvolen tajnou volbou (29 hlasů), jmenovitě se nezaznamenává.", "https://www.ceskenoviny.cz/zpravy/2271134"),
    ("2022-12-15", 4, "rozpočet", "Schválení rozpočtu města na rok 2023 s úpravou (přesun 9 mil. Kč ze sportovního fondu) – usn. 308/2022.", ""),
    ("2023-06-29", 34, "investice / průmysl", "Záměr uzavření smlouvy o investičním příspěvku se společností Hengst Filtration (podpora investice firmy v Liberci) – usn. 172/2023. Pozn.: protokol uvádí 23 pro / 7 proti / 3 zdrž. (33 přítomných), zápis uvádí 27 pro – pravděpodobně překlep v zápisu.", ""),
    ("2023-09-07", 29, "bydlení", "Přijetí dotace pro projekt Liberecká nájemní agentura (usn. 215/2023).", ""),
    ("2023-12-14", 9, "rozpočet", "Schválení rozpočtu města na rok 2024 s pozměňovacím návrhem (usn. 316/2023).", ""),
    ("2024-04-25", 9, "změna koalice 2024", "Po odchodu ODS z koalice (obvinění náměstka P. Židka) volba Ing. Vojtěcha Prachaře (ANO) náměstkem primátora pro energetiku a Smart City aklamací (usn. 63/2024).", "https://cnn.iprima.cz/namestek-primatora-liberce-za-ods-zidek-rezignoval-na-sve-funkce-je-obvineny-v-korupcni-kauze-434294"),
    ("2024-06-13", 3, "energetika / EPC", "Mimořádné zasedání: vyhodnocení nadlimitní veřejné zakázky „Energetické úspory metodou EPC pro statutární město Liberec – dotační část“ (usn. 134/2024).", ""),
    ("2024-06-27", 48, "investice / průmysl", "Smlouva o investičním příspěvku se společností Hengst Filtration, s. r. o. (usn. 172/2024).", ""),
    ("2024-10-31", 9, "finance / dluh", "Přijetí kontokorentních úvěrů do limitu 1 500 mil. Kč (jedním hlasováním o obou kontokorentech, usn. 242/2024).", ""),
    ("2024-11-28", 6, "rozpočet", "Schválení rozpočtu města na rok 2025 (usn. 265/2024).", ""),
    ("2025-05-19", 3, "odvolání náměstka 2025", "Mimořádné zasedání k odvolání náměstka Mgr. Jiřího Šolce (obviněného z korupce): hlasování o tom, zda odvolání proběhne veřejně aklamací; nepřijato, odvolání pak proběhlo tajně (27 hlasů pro odvolání).", "https://ct24.ceskatelevize.cz/clanek/regiony/zastupitele-liberce-odvolali-solce-z-funkce-namestka-primatora-361125"),
    ("2025-05-19", 4, "odvolání náměstka 2025", "Tamtéž: hlasování o volbě nového člena Rady města (navržen Ing. Jan Majzner, ANO) veřejně aklamací; nepřijato, volba proběhla tajně.", "https://ct24.ceskatelevize.cz/clanek/regiony/zastupitele-liberce-odvolali-solce-z-funkce-namestka-primatora-361125"),
    ("2025-10-30", 6, "bydlení", "Schválení Koncepce udržitelnosti a rozvoje bydlení SML 2025+ (usn. 259/2025).", ""),
    ("2025-11-27", 6, "rozpočet", "Schválení rozpočtu města na rok 2026 (původní návrh, usn. 289/2025); předtím neprošel protinávrh opozice týkající se Linserky.", ""),
    ("2025-12-11", 30, "sociální začleňování", "Schválení Desegregačního plánu statutárního města Liberec (lokality Františkov a Jeřáb; spolupráce s Agenturou pro sociální začleňování) – usn. 343/2025.", "https://mmr.gov.cz/getattachment/Microsites/Socialni-zaclenovani/Dokumenty-o-nas/Desegregacni-plan-Statutarniho-mesta-Liberec/29_Desegregacni-plan-Statutarniho-mesta-Liberec.pdf.aspx"),
    ("2026-02-26", 5, "veřejný pořádek", "Obecně závazná vyhláška o zákazu odpalování pyrotechniky (ohňostrojů) na území města (usn. 24/2026).", ""),
    ("2026-09-24", 33, "energetika / teplárenství", "Poslední zasedání volebního období: smlouva o poskytnutí peněžitého příplatku mimo základní kapitál městské společnosti Energetika Liberec, s. r. o., v upravené podobě (usn. 196/2026).", ""),
]

key_out, missing = [], []
for i, (d, zno, tema, popis, news) in enumerate(SEL, 1):
    cand = [(k, rs) for k, rs in votes.items() if rs[0]["datum"] == d and rs[0].get("zapis_hlasovani_c") == str(zno)
            and rs[0]["zapis_shoda"] in ("ano", "ano_posun_cisla", "ne")]
    if len(cand) != 1:
        missing.append((d, zno, len(cand)))
        continue
    k, rs = cand[0]
    r0 = rs[0]
    hl = OrderedDict((r["zastupitel"], r["hlas"] or "?") for r in rs)
    raw = OrderedDict((r["zastupitel"], r["hlas_raw"]) for r in rs)
    kl = OrderedDict((r["zastupitel"], r["klub_strana"]) for r in rs)
    by_party = defaultdict(Counter)
    for r in rs:
        by_party[r["klub_strana"] or "(neuvedeno)"][r["hlas_raw"] or "?"] += 1
    key_out.append(OrderedDict([
        ("id", f"LBC-ZM-{d}-{r0['hlasovani_c']}"), ("datum", d), ("zasedani", r0["zasedani"]),
        ("hlasovani_c", int(r0["hlasovani_c"])), ("bod", r0["bod"]), ("usneseni", r0.get("usneseni", "")),
        ("nazev", r0["nazev"]), ("popis", popis), ("tema", tema), ("vysledek", r0["vysledek"]),
        ("souhrn", {"pro": r0["pro"], "proti": r0["proti"], "zdrzelo": r0["zdrzelo"], "nehlasovalo": r0["nehlasovalo"], "nepritomno": r0["nepritomno"]}),
        ("hlasy", hl), ("hlasy_detail", raw), ("klub_strana", kl),
        ("podle_klubu", {p: dict(c) for p, c in by_party.items()}),
        ("kontrola_ocr", r0["kontrola"]), ("shoda_se_zapisem", r0["zapis_shoda"]),
        ("zdroj_url", r0["zdroj_url"]), ("zapis_url", r0.get("zapis_url", "")), ("strana_pdf", int(r0["strana_pdf"])),
        ("kontext_url", news),
    ]))
json.dump({"popis": "Vybraná politicky významná / sporná jmenovitá hlasování ZM Liberec 2016–2026. hlas: A=pro, N=proti, Z=zdržel se, X=nehlasoval nebo nepřítomen (rozlišení v hlasy_detail). Zdroj: OCR skenů protokolů hlasovacího zařízení, ověřeno součty a zápisem.",
           "hlasovani": key_out}, open(out_key, "w"), ensure_ascii=False, indent=1)

# ------------------------------------------------------------------ summary
sess = sorted({r["zasedani"].split(" (")[0] for r in rows})
dates = sorted({r["datum"] for r in rows})
st = Counter(rs[0]["kontrola"] for rs in votes.values())
zs = Counter(rs[0]["zapis_shoda"] for rs in votes.values())
vs = Counter(rs[0]["vysledek_zdroj"] for rs in votes.values())
per_year = Counter(k[0][:4] for k in votes)
persons = sorted({r["jmeno_norm"] for r in rows if not r["jmeno_norm"].startswith("(")})
all_sess = sorted(s["session"] for s in idx)
no_data = [s for s in all_sess if s not in sess]
zap_votes = len(zap)
unanimous = sum(1 for rs in votes.values() if rs[0]["proti"] in ("0", "") and rs[0]["zdrzelo"] in ("0", ""))
summary = OrderedDict([
    ("instituce", "Zastupitelstvo statutárního města Liberec (39 členů)"),
    ("zdroj", "https://podklady.liberec.cz/ (agenda ZM) – skeny „Výsledky hlasování“ (protokoly H.E.R. Systém) + textové „Zápisy“"),
    ("datum_zpracovani", "2026-10-08"),
    ("rozsah_dat", {"od": dates[0], "do": dates[-1]}),
    ("pocet_zasedani_v_archivu_2016_2026", len(all_sess)),
    ("pocet_zasedani_s_jmenovitymi_daty", len(sess)),
    ("pocet_hlasovani", len(votes)),
    ("pocet_radku_long_csv", len(rows)),
    ("pocet_zastupitelu_unikatnich", len(persons)),
    ("zastupitele", persons),
    ("hlasovani_podle_roku", dict(sorted(per_year.items()))),
    ("jednomyslna_nebo_bez_proti_a_zdrzeni", unanimous),
    ("kvalita", OrderedDict([
        ("metoda", "Skeny PDF (bez textové vrstvy) → pdftoppm 200 dpi → tesseract 5 (ces, psm 6) → parser; jména sjednocena v rámci zasedání (modus pozic), hlasy kontrolovány proti součtům na protokolu."),
        ("kontrola_souctu_na_protokolu", dict(st)),
        ("vysvetlivky_kontrola", {"OK": "všech 39 (resp. M) řádků přečteno a součty PRO/PROTI/ZDRŽEL/NEHLASOVAL/NEPŘÍTOMEN sedí",
                                   "OK_DOPLNENO_ZE_SOUCTU": "1 nepřečtený řádek doplněn jednoznačně ze součtů",
                                   "NEUPLNE": "některé řádky nepřečteny (hlas prázdný)",
                                   "NESOULAD_SOUCTU": "přečtené hlasy nesedí se součty (možná chyba OCR)"}),
        ("shoda_se_zapisem", dict(zs)),
        ("vysvetlivky_shoda", {"ano": "číslo hlasování i součty pro/proti/zdržel se shodné se zápisem",
                                "ano_posun_cisla": "součty shodné se zápisem, číslo hlasování v zápisu se liší o 1–2 (číslování protokolu vs. zápisu)",
                                "ne": "stejné číslo v zápisu, ale jiné součty (chyba OCR, nebo nepřesnost zápisu)",
                                "nenalezeno": "hlasování v zápisu nenalezeno (zápis jej neuvádí ve standardním tvaru)"}),
        ("pocet_hlasovani_v_zapisech", zap_votes),
        ("zdroj_vysledku", dict(vs)),
        ("nazev", "Sloupec nazev = název bodu z hlavičky protokolu (OCR, drobné chyby možné). Protokol neuvádí, o jakém návrhu (pozměňovací/protinávrh/procedurální) se hlasovalo – to bývá jen ručně dopsáno na skenu; proto sloupec popis_ze_zapisu (úryvek zápisu před hlasováním) a usneseni."),
        ("jmena", "zastupitel = jméno z protokolu (OCR, s tituly; tituly se v čase mění); jmeno_norm = jméno bez titulů se sjednocenými OCR variantami – použijte pro agregace."),
        ("hlas", "A=PRO, N=PROTI, Z=ZDRŽEL SE, X=NEHLASOVAL nebo NEPŘÍTOMEN (rozlišeno ve sloupci hlas_raw); prázdné = nepřečteno."),
        ("vysledek", "Ze zápisu („návrh byl/nebyl přijat“), jinak dopočteno: PRO > polovina všech členů (vysledek_zdroj)."),
    ])),
    ("mezery", [
        "Zasedání bez jmenovitých dat: " + ", ".join(no_data) + " (2016-05-27 ZM 5P: jen zvukový záznam; 2018-03-05 ZM 0-2: zveřejněna jen pozvánka a usnesení).",
        "Tajné volby (primátor, náměstci, radní, odvolávání – např. odvolání J. Šolce 19. 5. 2025, volba primátora 20. 11. 2018 a 18. 10. 2022) se jmenovitě nezaznamenávají; v datech jsou jen procedurální hlasování (např. o volbě aklamací).",
        "Období před 2016 (2007–2015 jsou na docs.liberec.cz) nebylo zpracováno.",
        "Na některých stranách skenů jsou jen ručně psané poznámky/usnesení (nejde o hlasování) – ignorovány.",
    ]),
    ("nesouhlasici_vyber_klicovych", missing),
    ("soubory", {"long": "data/processed/hlasovani_long.csv", "hlasovani_1_radek_na_hlasovani": "data/processed/hlasovani_votes.csv", "klicova": "data/processed/hlasovani_klicova.json",
                 "zapis_hlasovani": "data/processed/hlasovani_zapis_votes.csv", "qa_pdf": "data/processed/hlasovani_qa.json",
                 "ocr_text": "data/processed/hlasovani_ocr/<zasedani>/<pdf>/page-NNN.txt", "raw": "data/raw/hlasovani/<YYYY-MM-DD ZM N>/",
                 "zdroje": "data/raw/hlasovani/SOURCES.md"}),
])
json.dump(summary, open(out_sum, "w"), ensure_ascii=False, indent=1)
print("key votes", len(key_out), "missing", missing, file=sys.stderr)
