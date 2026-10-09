# Volby Liberec 2026

Osobní, nezávislý přehled komunálních voleb do Zastupitelstva statutárního města Liberec (9.–10. 10. 2026):
11 kandidátek, programy, profily prvních pěti kandidátů, volební kalkulačka a jak zastupitelé hlasovali 2016–2026.
Nejde o oficiální ani stranický materiál.

Web: https://pvasek.github.io/volby2026/ (sestavuje se automaticky po každém pushi, viz `.github/workflows/pages.yml`).

## Zdroje a jejich ověření

Repozitář neobsahuje kopie cizích stránek ani dokumentů, jen odkazy na ně.

- `data/sources_manifest.json`: všech 529 použitých souborů s URL, datem stažení, velikostí a otiskem SHA-256
  (stránky a dokumenty k profilům a programům, kontext kampaně, 255 protokolů a zápisů z jednání zastupitelstva,
  otevřená data ČSÚ).
- `python scripts/fetch_sources.py` stáhne originály do `data/raw/` (protokoly hlasování mají ~1,2 GB,
  jen část: `--only profily,programy,kontext,pruzkumy`).
- `python scripts/fetch_sources.py --verify` stáhne originály znovu a porovná otisky s manifestem;
  `--verify-local` porovná už stažené kopie. PDF a data ČSÚ mají sedět přesně. Webové stránky se v čase mění,
  u nich použijte https://web.archive.org/.

## Jak se data zpracovávají

| Krok | Skript | Výstup |
|---|---|---|
| Kandidátní listiny a výsledky (ČSÚ) | `scripts/extract_candidates.py` | `data/processed/kandidati_<rok>.json` |
| Dřívější kandidatury (komunální, krajské, sněmovní) | `scripts/cross_reference.py` | `data/processed/historie_kandidatu.json` |
| Hlasování zastupitelstva (OCR protokolů) | `scripts/hlas_*.py` | `data/processed/hlasovani_*.{csv,json}` |
| Souhrny hlasování (účast, odchylka od klubu, shoda klubů) | `scripts/hlas_aggregate.py` | `data/processed/hlasovani_agg.json` |
| Index Politika (z doložených funkcí) | `scripts/politika_index.py` | `data/processed/politika.json` |
| Index Praxe (vzdělání + kariéra) | `scripts/praxe_index.py` | `data/processed/praxe.json` |
| Teze kalkulačky a postoje kandidátek | `scripts/kalkulacka.py` | `data/processed/kalkulacka.json` |
| Web | `scripts/build_site.py` | `_site/index.html` |

Analýzy kandidátek (`data/processed/strany/<číslo>.json`) obsahují ke každému tvrzení identifikátor zdroje.
Všechny vzorce jsou popsané na webu v sekci „Zdroje a metodika“.

## Sestavení lokálně

```
python scripts/build_site.py _site      # vyžaduje jen Python 3.10+, žádné balíčky
```
