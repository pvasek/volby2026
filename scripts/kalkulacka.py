"""Volební kalkulačka: teze, postoje kandidátek (s doložením z programu) a navázaná hlasování zastupitelstva.

Postoj: 1 = pro, 0.5 = spíš pro / podmíněně, 0 = neutrální, -0.5 = spíš proti, -1 = proti.
Kandidátka, která se k tezi nevyjádřila, v seznamu chybí (počítá se jako bez postoje).
Důkazy jsou zkrácené programové body z data/processed/strany/<n>.json (pole program_body / povolebni_signaly).
Hlasování: id z data/processed/hlasovani_klicova.json; "smer" = 1, když hlas PRO znamená souhlas s tezí, -1 opak.

Out: data/processed/kalkulacka.json
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

TEZE = [
    {"id": "zony", "tema": "Doprava", "text": "Na sídlištích by se měly zavést rezidentní (modré) parkovací zóny.",
     "postoje": {1: (1, "Zavést rezidentní parkování zvýhodňující obyvatele s trvalým pobytem."),
                 2: (0.5, "Modré zóny na sídlištích až po navýšení kapacity parkování."),
                 3: (-1, "Odmítá modré zóny na sídlištích jako „zpoplatnění nedostatku“."),
                 4: (-0.5, "Placené zóny na sídlištích zatím neplánuje, koncepce parkování až do konce 2027."),
                 6: (0, "Zóny jen se souhlasem místních, parkování podle celoměstské koncepce."),
                 8: (0.5, "Zóny rezidentního či placeného stání nařízením obce (odpověď ČRo)."),
                 9: (-0.5, "Placené zóny spíše jen v centru."),
                 10: (0, "Rezidentní parkování s předností pro obyvatele, plošné placené zóny ale nepovažuje za optimální.")}},
    {"id": "okruh", "tema": "Doprava", "text": "Město by mělo dostavět vnitřní městský okruh a silnice k průmyslovým zónám.",
     "postoje": {2: (1, "Přímé napojení průmyslové zóny Sever na I/35, tlačit na kraj kvůli zóně Jih."),
                 4: (1, "Dostavět vnitřní okruh a silnice k průmyslovým zónám Sever a Jih."),
                 5: (1, "Prověřit projekty a začít realizovat vnitřní městský okruh.")}},
    {"id": "centrum", "tema": "Doprava", "text": "Centrum by se mělo zklidnit a omezit v něm průjezd aut.",
     "postoje": {5: (-1, "Centrum ponechat průjezdné."),
                 6: (1, "Zklidňovat centrum podle Plánu udržitelné mobility."),
                 9: (0, "Zklidnit dopravu jen tam, kde to nepřesune problém jinam."),
                 10: (-0.5, "Nesnižovat počet parkovacích míst v centru bez náhrady.")}},
    {"id": "cyklo", "tema": "Doprava", "text": "V hlavních ulicích by měly vzniknout oddělené cyklostezky, i když uberou místo autům.",
     "postoje": {2: (0, "Místo cyklopruhů na rušných silnicích stavět oddělené cyklostezky mimo ně."),
                 5: (-1, "Cyklisty směrovat na cyklostezky místo vyhrazených pruhů v ulicích."),
                 6: (1, "Oddělené cyklopruhy při rekonstrukcích ulic (např. 1. máje)."),
                 11: (1, "Oddělené cyklostezky v ulicích 1. máje a Milady Horákové.")}},
    {"id": "mhd", "tema": "Doprava", "text": "MHD by měla být zdarma pro děti do 15 let.",
     "postoje": {4: (1, "MHD zdarma pro děti do 15 let."), 6: (1, "Jízdné zdarma pro děti do 15 let."),
                 11: (1, "MHD zdarma pro děti do 15 let.")}},
    {"id": "lanovka", "tema": "Investice", "text": "Nová lanovka na Ještěd by měla být pro město prioritou.",
     "postoje": {2: (0.5, "Lanovku chce, ale ne předraženou a ne jen z peněz města (test racionality)."),
                 4: (1, "Urychlit stavbu lanovky, ideálně se soukromým investorem."),
                 11: (1, "Nová lanovka na Ještěd do roku 2030.")}},
    {"id": "stadion", "tema": "Investice", "text": "Město by mělo prodat stadion U Nisy klubu FC Slovan (se zárukou sportovního využití).",
     "postoje": {1: (1, "Prodat stadion klubu se smluvními zárukami a za cenu podle posudku."),
                 3: (0, "O prodeji jednat se všemi stranami, v programu není."),
                 4: (0.5, "Prodej zvážit, pokud bude zajištěno užívání pro fotbal a předkupní právo města."),
                 5: (0.5, "Prodej podpořit s podmínkami (peníze na halu, veřejné parkoviště)."),
                 6: (0.5, "Lídr: podpořit prodej se zárukami, že klub o stadion nepřijde."),
                 8: (0, "Prodat jen za cenu obvyklou, veřejné vlastnictví považuje za legitimní."),
                 9: (0.5, "Prodej jen s podmínkami (sportovní využití, výnos do dalších sportovišť)."),
                 10: (0.5, "Prodej jen za tržní cenu podle posudku a s garancí sportovního využití."),
                 11: (1, "Jednat o prodeji klubu, z výnosu by podle lídra mohla být lanovka.")}},
    {"id": "vapenka", "tema": "Investice", "text": "Město by mělo koupit nebo pronajmout koupaliště Vápenka a obnovit ho.",
     "postoje": {4: (-1, "Vápenku nevykupovat, postavit nové koupaliště u Home Credit Areny."),
                 5: (-0.5, "Postavit bazén s koupalištěm u Home Credit Areny."),
                 6: (0.5, "Lídr: Vápenka zůstane koupalištěm."),
                 8: (1, "Řešit koupi nebo pronájem Vápenky a její rekonstrukci."),
                 10: (-0.5, "Nové městské koupaliště v areálu Vesec.")}},
    {"id": "dluh", "tema": "Finance", "text": "Město by si nemělo dál půjčovat, i kdyby muselo odložit investice.",
     "postoje": {1: (1, "Odmítnout další zadlužování města."),
                 2: (1, "Zastavit růst dluhu, některé plánované akce odložit či zrušit."),
                 4: (1, "Nezadlužovat město více."),
                 5: (1, "Nezvyšovat zadlužení, dotace jen po analýze provozních nákladů."),
                 6: (0.5, "Zastavit růst dluhu, úvěry jen na návratné nebo vynucené investice."),
                 9: (0.5, "Upřednostnit levná řešení před drahými projekty."),
                 10: (0, "Zadlužení jen u smysluplných dlouhodobých investic."),
                 11: (-0.5, "Investovat do 2030 přes 3 mld. Kč, dluh držet v poměru k příjmům na úrovni 2026.")},
     "hlasovani": [("LBC-ZM-2024-10-31-9", -1)]},
    {"id": "dan", "tema": "Finance", "text": "Daň z nemovitosti by se neměla zvyšovat.",
     "postoje": {4: (1, "Nezvyšovat daň z nemovitosti."), 5: (0.5, "Přehodnotit výši daně z nemovitosti."),
                 11: (-0.5, "Zvýšit daň z nemovitosti pro dlouhodobě neobydlené a chátrající domy.")}},
    {"id": "developeri", "tema": "Rozvoj", "text": "Developeři by měli městu přispívat na školky, silnice a další infrastrukturu.",
     "postoje": {5: (-1, "Zrušit nebo změnit netransparentní požadavky na příspěvky investorů."),
                 6: (1, "Po developerech chtít podíl bytů s regulovaným nájmem a občanskou vybavenost."),
                 8: (1, "U velkých projektů požadovat řešení dopravy, chodníků, zeleně, škol a služeb."),
                 10: (-1, "Zrušit nebo výrazně upravit příspěvky investorů na infrastrukturu („výpalné“).")}},
    {"id": "investori", "tema": "Rozvoj", "text": "Město by mělo finančně podporovat příchod velkých firem (investiční příspěvky).",
     "postoje": {4: (0.5, "Hledat nového velkého zaměstnavatele z oblasti průmyslu 4.0.")},
     "hlasovani": [("LBC-ZM-2023-06-29-34", 1), ("LBC-ZM-2024-06-27-48", 1)]},
    {"id": "byty", "tema": "Bydlení", "text": "Město by mělo samo stavět nové městské byty.",
     "postoje": {2: (1, "Zvýšit počet městských bytů, rozšířit nájemní agenturu."),
                 4: (1, "Zvýšit počet městských bytů a zřídit městské bytové družstvo."),
                 6: (1, "Postavit 220 městských bytů a opravou domů získat dalších 90."),
                 8: (1, "Podporovat výstavbu dostupného městského a sociálního bydlení."),
                 9: (0.5, "Podpořit výstavbu nových bytů, bez čísel a harmonogramu."),
                 10: (1, "Dlouhodobý program systematické výstavby městských bytů."),
                 11: (1, "Zahájit výstavbu 150 bytů na Papírovém náměstí a 70 Na Žižkově.")},
     "hlasovani": [("LBC-ZM-2023-09-07-29", 1), ("LBC-ZM-2025-10-30-6", 1)]},
    {"id": "fugnerka", "tema": "Bezpečnost", "text": "Na terminálu Fügnerova by měla být nonstop služebna nebo stálá hlídka městské policie.",
     "postoje": {1: (0.5, "Více strážníků v ulicích a u terminálu Fügnerova."),
                 2: (1, "Obnovit služebnu městské policie na terminálu Fügnerova."),
                 4: (1, "Nonstop služebna městské policie na terminálu po rekonstrukci."),
                 5: (0.5, "Městská policie viditelná v terénu."),
                 6: (1, "Lídr: na Fügnerce stálá dvoučlenná hlídka a služebna."),
                 8: (0.5, "Lepší osvětlení a dohled v okolí terminálu."),
                 9: (0.5, "Více strážníků v problémových lokalitách."),
                 11: (1, "Stálá hlídka městské policie 24/7 na terminálu.")}},
    {"id": "hazard", "tema": "Bezpečnost", "text": "Herny a kasina by měly být v Liberci úplně zakázané.",
     "postoje": {11: (1, "Zavřít herny a kasina na celém území města.")},
     "hlasovani": [("LBC-ZM-2016-12-15-23", 1), ("LBC-ZM-2018-03-29-29", 1)]},
    {"id": "ohnostroje", "tema": "Bezpečnost", "text": "Odpalování ohňostrojů by mělo být ve městě zakázané.",
     "postoje": {}, "hlasovani": [("LBC-ZM-2026-02-26-5", 1)]},
    {"id": "bezdomovci", "tema": "Sociální", "text": "Město by mělo zřídit azylový dům nebo celoroční zařízení pro lidi bez domova.",
     "postoje": {5: (1, "Celoroční „stacionář“ pro lidi bez domova, podmíněný střízlivostí."),
                 6: (1, "Zřídit azylový dům, prevence bezdomovectví."),
                 11: (1, "Usilovat o azylový dům nebo noclehárnu.")}},
    {"id": "desegregace", "tema": "Sociální", "text": "Město by mělo aktivně řešit sociálně vyloučené lokality a segregaci ve školách.",
     "postoje": {2: (0.5, "Terénní asistence pro děti ze znevýhodněných rodin.")},
     "hlasovani": [("LBC-ZM-2025-12-11-30", 1)]},
    {"id": "divadlo", "tema": "Kultura", "text": "Město by mělo udržet třísouborové Divadlo F. X. Šaldy (činohra, opera, balet).",
     "postoje": {2: (1, "Zachovat třísouborové divadlo a vyjednat vyšší podíl kraje."),
                 6: (1, "Udržet třísouborové divadlo, vyjednat vyšší příspěvek kraje."),
                 11: (0.5, "Připravit rekonstrukci zázemí divadla.")}},
    {"id": "participace", "tema": "Správa", "text": "O části rozpočtu by měli přímo rozhodovat obyvatelé čtvrtí (participativní rozpočet, místní komise).",
     "postoje": {2: (1, "Posílit pravomoci místních komisí, o poldru v Machníně místní referendum."),
                 6: (1, "Participativní rozpočet 10 mil. Kč ročně a 100 mil. Kč čtvrtím podle místních komisí."),
                 8: (0.5, "U významných investic umožnit obyvatelům včasné vyjádření."),
                 9: (0.5, "Rozhodovat o investicích podle potřeb jednotlivých čtvrtí."),
                 11: (0.5, "Posílit místní komise online portálem.")}},
]


def main():
    out = []
    for t in TEZE:
        out.append({"id": t["id"], "tema": t["tema"], "text": t["text"],
                    "postoje": {str(k): {"p": v[0], "proc": v[1]} for k, v in t["postoje"].items()},
                    "hlasovani": [{"id": i, "smer": s} for i, s in t.get("hlasovani", [])]})
    ids = {v["id"] for v in json.load(open(ROOT / "data/processed/hlasovani_klicova.json", encoding="utf-8"))["hlasovani"]}
    missing = [h["id"] for t in out for h in t["hlasovani"] if h["id"] not in ids]
    assert not missing, missing
    (ROOT / "data/processed/kalkulacka.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(out), "tezí,", sum(len(t["hlasovani"]) > 0 for t in out), "s hlasováním")


if __name__ == "__main__":
    main()
