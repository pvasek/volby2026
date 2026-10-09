# Schema: data/processed/strany/<cislo>.json   (all text in Czech, neutral tone, no marketing)
{
  "cislo": 11, "nazev": "...", "zkratka": "...",
  "slozeni": "které strany/hnutí tvoří kandidátku (+ NK = nezávislí)",
  "web": "url", "program_url": "url (or null)", "program_local": "data/raw/programy/<slug>/<file>",
  "shrnuti": "2–3 věty: kdo to je a na co se zaměřují",
  "zamereni": ["3–6 krátkých klíčových slov"],
  "zkusenost_skore": 0-100,           # zkušenost subjektu + lídrů s (komunální) politikou a správou města
  "zkusenost_zduvodneni": "1–2 věty",
  "temata_pct": { "doprava_parkovani": 0, "bydleni": 0, "rozvoj_uzemni_plan_vystavba": 0,
      "zivotni_prostredi_zelen": 0, "socialni_zdravotnictvi_seniori": 0, "skolstvi_deti_rodina": 0,
      "kultura_sport_volny_cas": 0, "bezpecnost_poradek": 0, "finance_hospodareni_dane": 0,
      "sprava_transparentnost_digitalizace": 0, "ekonomika_podnikani_cestovni_ruch": 0, "ostatni": 0 },
      # integers summing to 100 = approx. share of the PROGRAMME CONTENT devoted to each theme (count concrete points)
  "program_body": [ {"tema": "<key from temata_pct>", "bod": "konkrétní věc, kterou chtějí udělat (bez omáčky)", "konkretni": true/false } ],
      # 8–25 points, merge duplicates, flag vague ones konkretni=false
  "hodnoceni": { "silne_stranky": ["..."], "slabe_stranky_rizika": ["..."], "kontroverze": [{"text":"...", "zdroj":"<source id>"}] },
  "povolebni_signaly": "s kým chtějí/nechtějí spolupracovat, pokud řekli (+zdroj)",
  "kandidati": [   # exactly top 5 of the list, in ballot order
    { "poradi": 1, "jmeno": "...", "vek": 0, "povolani_dle_listiny": "...", "prislusnost": "...",
      "shrnuti": "2–3 věty",
      "politicka_kariera": [ {"funkce": "zastupitel SML / radní / náměstek / krajský zastupitel / poslanec / člen strany X / starosta obvodu ...", "od": 2018, "do": 2022 or null, "zdroj": "<id>"} ],
      "roky_v_politice": 0,           # years holding elected office or salaried political/party role (not just candidacies)
      "zkusenost_skore": 0-100,
      "soucasna_prace": "co dělá teď (uvolněný politik? civilní práce?)",
      "posledni_nepoliticka_prace": {"co": "...", "kdy": "např. 'souběžně dosud' / 'do 2018' / 'neznámé'"},
      "pozitivni": [ {"text": "co mluví v jeho/její prospěch (konkrétní činy, odbornost)", "zdroj": "<id>"} ],
      "negativni": [ {"text": "kritika, kauzy, přeběhlictví, střet zájmů, kontroverzní výroky", "zdroj": "<id>"} ],
      "nejiste": "co se nepodařilo ověřit" }
  ],
  "zdroje": [ {"id": "s1", "url": "...", "nazev": "...", "datum_stazeni": "2026-10-08", "local": "data/raw/...", "obsah": "co v něm je (1 věta)"} ]
}
