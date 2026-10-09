# Zdroje – průzkumy a náhradní ukazatele (Liberec, komunální volby 2026)

Datum stažení všech souborů: 2026-10-08 (curl, `-A "Mozilla/5.0"`, u nasliberec.cz plný UA prohlížeče).

Závěr rešerše: pro komunální volby 2026 v Liberci nebyl nalezen žádný zveřejněný volební průzkum (viz `data/processed/pruzkumy.json`, pole `poznamka`).

| URL | Lokální soubor | Obsah |
|---|---|---|
| https://www.volby.cz/appdata/ps2025/odata/vysledky_krajmesta.xml | ps2025_vysledky_krajmesta.xml | ČSÚ open data: výsledky voleb do PS 2025 v krajských městech (vč. Liberce, obec 563889). Názvy stran z `data/raw/volby_gov/ps2025/reg/csv_od/psrkl.csv`. |
| https://www.volby.cz/appdata/kz2024/odata/vysledky_krajmesta.xml | kz2024_vysledky_krajmesta.xml | ČSÚ open data: výsledky krajských voleb 2024 v krajských městech (vč. Liberce). Názvy z `data/raw/volby_gov/kz2024/reg/csv_od/kzrkl.csv`. |
| https://www.volby.cz/pls/kv2022/vysledky_obec?datumvoleb=20220923&cislo_obce=563889 | kv2022_vysledky_obec_563889.xml | ČSÚ open data: výsledky komunálních voleb 2022 v Liberci (hlasy, mandáty, zvolení). |
| https://liberecka.drbna.cz/politika/37001-nejvyssi-volebni-potencial-ma-v-libereckem-kraji-ano-tesne-nasledovane-starosty.html | drbna_kantar_potencial_kraj_2024.html | Kantar pro ČT, volební potenciál v Libereckém kraji před krajskými volbami 2024 (6.–27. 8. 2024, n=687). Kraj, ne město. |
| https://zpravy.kurzy.cz/638909-sanep-volebni-preference-stran-hnuti-a-koalic-v-krajskych-mestech-cr/ | sanep_krajska_mesta_kurzy.html | SANEP, preference v krajských městech, březen 2022 (historické, před volbami 2022; kódování cp1250). |
| https://www.parlamentnilisty.cz/zpravy/tiskovezpravy/SANEP-Komunalni-volby-volebni-preference-v-peti-nejvetsich-mestech-CR-712150 | sanep_5_mest_pl.html | SANEP, 5 největších měst (starší, Liberec obsažen jen okrajově/v navigaci). Neobsahuje data pro 2026. |
| https://nasliberec.cz/?s=pr%C5%AFzkum | nasliberec_hledani_pruzkum.html | Fulltextové hledání „průzkum“ na Náš Liberec – žádný volební průzkum; zmínka o průzkumu STEM/MARK pro město (MA21, 800 respondentů, nevolební). |
