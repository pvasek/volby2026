# Oficiální volební data – ČSÚ (volby.gov.cz, dříve volby.cz)
Staženo: 2026-10-08. Licence: podmínky ČSÚ pro využívání statistických údajů.

| Volby | URL (balík) | Lokálně | Obsah |
|---|---|---|---|
| Komunální 2026 | https://volby.gov.cz/opendata/kv2026/KV2026reg20261002_csv.zip | kv2026/reg/ | Registr kandidátních listin (kvros.csv) a kandidátů (kvrk.csv), stav k 2.10.2026 |
| Komunální 2026 | https://volby.gov.cz/opendata/kv2026/KV2026ciselniky20261002_csv.zip | kv2026/cis/ | Číselníky stran (cvs, cpp, cns) |
| Komunální 2022 | https://volby.gov.cz/opendata/kv2022/KV2022reg20260328_csv.zip (+ciselniky) | kv2022/ | Kandidáti vč. hlasů a mandátů |
| Komunální 2018 | https://volby.gov.cz/opendata/kv2018/KV2018_reg_20230224_csv.zip (+cisel) | kv2018/ | dtto |
| Komunální 2014 | https://volby.gov.cz/opendata/kv2014/KV2014_reg_20230224_csv.zip (+cisel) | kv2014/ | dtto |
| Krajské 2016/2020/2024 | https://volby.gov.cz/opendata/kz20XX/… (reg + číselníky csv) | kz2016/ kz2020/ kz2024/ | Kandidáti do zastupitelstev krajů (filtrováno na Liberecký kraj, KRZAST=6) |
| Sněmovní 2021/2025 | https://volby.gov.cz/opendata/ps20XX/… (reg + číselníky csv) | ps2021/ ps2025/ | Kandidáti do PSP (filtrováno na Liberecký volební kraj, VOLKRAJ=7) |
| Sněmovní 2017 | registr vrací 404 | – | nepoužito |

Zastupitelstvo statutárního města Liberec = KODZASTUP 563889.
Zpracování: `scripts/extract_candidates.py` → `data/processed/kandidati_<rok>.json`,
`scripts/cross_reference.py` → `data/processed/historie_kandidatu.json`
(shoda jméno+příjmení a rok narození ±1; může obsahovat vzácné shody jmenovců).
