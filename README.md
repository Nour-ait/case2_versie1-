# Klimaatbeleid vs. werkelijkheid

Interactief Streamlit-dashboard over de relatie tussen CO₂-uitstoot, hernieuwbare
energie en economische welvaart per land (2000–2022).

**Onderzoeksvraag:** In hoeverre komt de transitie naar hernieuwbare energie
daadwerkelijk tot uiting in dalende CO₂-uitstoot, en hoe verhoudt dit zich tot
het inkomensniveau van landen?

## Databronnen

Alleen de twee aangeleverde bestanden worden gebruikt:

| Bestand | Bron | Gebruikt voor |
|---|---|---|
| `data/annual-co2-emissions-per-country.csv` | Our World in Data / Global Carbon Project | CO₂-uitstoot per land per jaar |
| `data/renewable_energy_share_2000_2025.csv` | Our World in Data / Ember | Aandeel hernieuwbare energie, GDP, bevolking |

Inkomensgroep (rijk / opkomend / arm) wordt zelf berekend uit GDP per capita
met de standaard Wereldbank-drempels — hier géén losse API voor nodig.

### Hoe dit aan de "openbare API"-eis voldoet

De opdracht eist: *"Haal de data in je script op, niet met de hand
gedownload, zodat iemand anders je dataset kan reproduceren."* Dit dashboard
lost dat zo op:

1. De twee CSV's staan in de map `data/` in deze repo.
2. In `data_utils.py` vul je `RAW_BASE_URL` in met de raw-GitHub-link naar
   jouw eigen, gepushte repo, bijvoorbeeld:
   ```python
   RAW_BASE_URL = "https://raw.githubusercontent.com/<gebruikersnaam>/<repo>/main/data"
   ```
3. Het script probeert dan bij elke run eerst die publieke URL op te halen
   (`requests.get`). Dat maakt het reproduceerbaar: wie de repo kloont en
   `streamlit run app.py` doet, krijgt automatisch dezelfde data — zonder dat
   ze iets handmatig hoeven te downloaden. Lukt het ophalen niet (bijv. tijdens
   lokaal ontwikkelen vóórdat je gepusht hebt), dan valt het script terug op
   het lokale bestand in `data/`.

⚠️ **Let op:** dit is een CSV-bestand via een publieke URL, geen "echte"
REST/JSON-API zoals de Wereldbank-API die er eerder in zat. Voor puur
CSV-bronnen is dit in de praktijk gangbaar, maar controleer bij je docent
(Jerome Mies) of dit voor jullie cursus als "openbare API" telt, of dat er
een JSON-API vereist is. Zo niet, dan is de eenvoudigste fix om er een
tweede, JSON-gebaseerde bron bij te zoeken (bijv. de Wereldbank-API voor
inkomensclassificatie) — laat het weten en ik zet die er zo weer bij.

## Waarom de data bij 2022 stopt

`annual-co2-emissions-per-country.csv` loopt tot en met **2022** — de laatste
jaargang die het Global Carbon Project publiceert. Het renewable-bestand
loopt door tot 2025, maar de `gdp`-kolom daarin stopt óók al bij 2022. Omdat
CO₂ en renewables op jaartal worden samengevoegd (inner join), valt alles na
2022 automatisch weg. Dit is geen fout — het is de laatst beschikbare
jaargang waarin beide databronnen overlappen. Zie het tabblad
**"Data & methode"** in het dashboard voor de exacte jaartallen en
rij-aantallen.

## Join-logica

De twee bestanden worden samengevoegd op sleutel **(iso_code, year)** met een
inner join. Rij-aantallen voor en na de join, en de laatste beschikbare
jaartallen per bestand, worden gelogd en getoond in het tabblad
"Data & methode" — zoals de opdracht vraagt.

## Lokaal draaien

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

De app opent op `http://localhost:8501`.

## Publiceren op GitHub + Streamlit Community Cloud

1. Maak een nieuwe **publieke** GitHub-repository en zet deze hele map erin
   (inclusief de `data/`-map met de twee CSV's):
   ```bash
   git init
   git add .
   git commit -m "Eerste versie dashboard"
   git branch -M main
   git remote add origin https://github.com/<jouw-gebruikersnaam>/<repo-naam>.git
   git push -u origin main
   ```
2. Vul daarna `RAW_BASE_URL` in `data_utils.py` in met je eigen repo-link
   (zie hierboven) en commit die wijziging.
3. Ga naar [share.streamlit.io](https://share.streamlit.io), log in met je
   GitHub-account, klik **New app**, kies je repo/branch/`app.py` en klik
   **Deploy**.
4. Test daarna of een **schone clone** van de repo zonder handmatige stappen
   werkt — dit is een harde eis van de opdracht.

## Projectstructuur

```
climate-dashboard/
├── app.py                  # Streamlit-app (5 tabbladen)
├── data_utils.py            # Data ophalen, opschonen en samenvoegen
├── data/
│   ├── annual-co2-emissions-per-country.csv
│   └── renewable_energy_share_2000_2025.csv
├── requirements.txt
├── .streamlit/
│   └── config.toml           # Kleurthema
└── README.md
```

## Widgets per tabblad (eis: minimaal 1 slider, 1 checkbox, 1 dropdown)

- **Wereldkaart** — dropdown (indicator) + slider (jaar)
- **Land over tijd** — dropdown (land) + checkbox (log-schaal) + slider (periode)
- **GDP vs CO₂** — slider (jaar) + multiselect + checkbox (log-x-as)
- **Walk vs Talk** — slider (periode) + checkbox (filter)

## Hoe dit aan de rubric voldoet

**Introduction to Data Science**
- *Dataverzameling*: twee losse bronnen, opgehaald via een publieke URL in het
  script (zie hierboven), samengevoegd op `(iso_code, year)`.
- *Data verkenning*: tabblad "Data & methode" toont join-logging, % missende
  waarden, beschrijvende statistiek en welke opschoonstappen zijn toegepast
  en waarom (regio-aggregaten, onmogelijke percentages, ontbrekend GDP).
- *Analyse*: afgeleide variabelen (CO₂ per capita, GDP per capita), een
  kwadratische regressie als EKC-proxy, en een zelfgemaakte decoupling-
  classificatie per land (Walk/Talk).

**Visual Analytics**
- *Opbouw en verhaallijn*: de tabbladen volgen de opbouw van je
  onderzoeksvraag naar je drie deelvragen (wereldbeeld → per land →
  GDP-relatie → walk-vs-talk-ranking).
- *Interactiviteit*: dropdowns, sliders, checkboxes en een multiselect,
  allemaal gekoppeld aan een visualisatie.
- *Vergelijken en annoteren*: kleurcodering op inkomensgroep, referentielijnen
  op nul in de walk/talk-scatter, EKC-trendlijn.
- *Dashboardontwerp*: consistente kleuren, duidelijke titels en assen,
  tooltips via Plotly.

## Nog te doen voor jouw inlevering

- [ ] `RAW_BASE_URL` invullen zodra je gepusht hebt (zie hierboven).
- [ ] Nagaan bij je docent of ophalen-via-publieke-CSV-URL voldoet aan de
      "openbare API"-eis, of dat een JSON-API verplicht is.
- [ ] Deelvragen expliciet beantwoorden in de presentatie aan de hand van de
      tabbladen "GDP vs CO₂" (Kuznets-curve) en "Walk vs Talk" (ontkoppeling).
- [ ] Eigen interpretatie van de resultaten toevoegen — de cijfers/analyse
      staan klaar, de duiding is aan jou.
- [ ] Dataset-keuze uiterlijk woensdag week 3 melden bij Jerome Mies via Teams.
- [ ] Overgenomen code (bv. van Streamlit-documentatie) van bronvermelding voorzien.
