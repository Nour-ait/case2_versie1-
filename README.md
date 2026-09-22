# Klimaatbeleid vs. werkelijkheid 🌍

Streamlit-dashboard voor de case *Analytics* (Introduction to Data Science / Visual Analytics).

**Onderzoeksvraag:** In hoeverre komt de transitie naar hernieuwbare energie daadwerkelijk tot
uiting in dalende CO2-uitstoot, en hoe verhoudt dit zich tot het inkomensniveau van landen?

**Deelvragen:**
- Welke landen laten een reële ontkoppeling zien tussen groei in hernieuwbare energie en
  daling van CO2-uitstoot ("walk"), en welke blijven vooral bij beleidsintenties ("talk")?
- Is er bewijs voor een *Environmental Kuznets Curve* (CO2 stijgt mee met GDP per capita tot
  een bepaald niveau, en vlakt daarna af of daalt)?
- Hoe verschilt dit patroon tussen rijke, opkomende en arme landen?

## Databronnen (opgehaald via een openbare API/bron, niet met de hand gedownload)

| # | Data | Bron | Endpoint |
|---|------|------|----------|
| 1 | CO2-uitstoot per land per jaar | Our World in Data **Chart API** (officiële, gedocumenteerde publieke API — voeg `.csv` toe aan elke grapher-URL) | `https://ourworldindata.org/grapher/annual-co2-emissions-per-country.csv` |
| 2 | Hernieuwbaar-aandeel, GDP, bevolking | OWID **Energy dataset** (publiek, CC BY 4.0, dagelijks automatisch bijgewerkt) op GitHub | `https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv` |

> ⚠️ **Belangrijk voor de beoordeling:** de opdracht eist expliicit dat je de data ophaalt via
> een **openbare API**, niet met de hand gedownload bestanden. Kaggle-CSV's die je zelf
> download (zoals de twee bestanden die als vertrekpunt zijn gebruikt om deze case te
> verkennen) voldoen daar **niet** aan. Dit dashboard haalt daarom bij het opstarten dezelfde
> data live op bij de oorspronkelijke bron (Our World in Data) via de URL's hierboven — de
> inhoud is (op de laatste bijgewerkte jaren na) identiek aan de Kaggle-bestanden, omdat die
> daar simpelweg een kopie van zijn. Zie `data_loader.py` voor de details en bronvermelding.

Beide bronnen zijn **twee volledig gescheiden bestanden**, samengevoegd op de sleutel
`iso_code` (landcode) + `year` — dat voldoet aan de eis "je voegt twee tabellen samen die niet
uit hetzelfde bestand komen".

### Join-verantwoording (rijaantallen voor/na)

Wordt live getoond in het tabblad **"📥 Data & methode"** van het dashboard zelf (met exacte
aantallen), inclusief:
- hoeveel rijen wegvallen omdat het aggregaten/regio's zijn (bv. "Africa", "World") in plaats
  van losse landen;
- hoe de jaartallen van beide bronnen automatisch gelijk worden getrokken (de CO2-reeks stopt
  eerder dan de energiereeks — de app neemt dynamisch de overlap, in plaats van een hard
  gecodeerd jaartal);
- hoeveel rijen overblijven na de merge, en hoeveel % van GDP/hernieuwbaar-aandeel ontbreekt.

## Structuur van dit project

```
.
├── app.py                  # Streamlit-app (UI, tabs, interactie)
├── data_loader.py           # Ophalen bij de bron + samenvoegen + opschonen
├── analysis.py               # Walk-vs-talk classificatie + EKC-regressie
├── requirements.txt
├── .streamlit/config.toml    # Kleurthema
└── README.md
```

## Lokaal draaien

```bash
git clone <jouw-repo-url>
cd <repo-map>
python3 -m venv .venv && source .venv/bin/activate   # optioneel
pip install -r requirements.txt
streamlit run app.py
```

De app heeft een internetverbinding nodig (om de data bij Our World in Data op te halen) maar
verder geen extra configuratie, API-key of handmatige stap.

## Live publiceren via Streamlit Community Cloud

1. Push deze map naar een **publieke GitHub-repository**.
2. Ga naar [share.streamlit.io](https://share.streamlit.io) en log in met je GitHub-account.
3. Klik op **"New app"**, kies je repo/branch en zet **Main file path** op `app.py`.
4. Klik op **Deploy**. Na een paar minuten is de app publiek bereikbaar via een `*.streamlit.app`-link.
5. Zet die link (en je repo-link) in je Teams-melding / presentatie.

Een schone `git clone` + de bovenstaande stappen zijn voldoende — er is geen los databestand
nodig, want alles wordt in `data_loader.py` bij de bron opgehaald.

## Interactieve elementen in het dashboard

| Element | Locatie | Koppeling |
|---|---|---|
| **Slider** — analyseperiode | Sidebar | Filtert alle tabs |
| **Slider** — jaar op de kaart | Wereldkaart | Bepaalt welk jaar de choropleth toont |
| **Slider** — walk/talk-drempel | Walk vs. Talk | Bepaalt de classificatie-grens |
| **Checkbox** — CO2 per capita aan/uit | Sidebar | Wisselt de metric in alle grafieken |
| **Checkbox** — EKC-fit tonen | Kuznets-curve | Toont/verbergt de kwadratische regressielijn |
| **Dropdown** — land highlighten | Sidebar | Accentueert een land in de scatter/tijdreeks-grafieken |
| **Dropdown** — kaart-variabele | Wereldkaart | Wisselt tussen CO2, hernieuwbaar-aandeel, GDP |
| **Dropdown** — inkomensgroep-filter | Kuznets-curve | Filtert de scatterplot op inkomensgroep |
| **Multiselect** — landen vergelijken | Landen vergelijken | Kiest welke landen in de tijdreeksen staan |

## Analyse / afgeleide variabelen

- `co2_per_capita_t` = CO2-uitstoot ÷ bevolking
- `gdp_per_capita` = GDP ÷ bevolking
- `income_group` = eigen kwartiel-indeling (Laag / Lager-midden / Hoger-midden / Hoog inkomen)
  op basis van gemiddelde GDP per capita per land — **geen** officiële Wereldbank-classificatie,
  wat expliciet zo benoemd wordt in de app.
- Walk-vs-talk classificatie: vergelijkt de verandering in hernieuwbaar-aandeel met de
  verandering in CO2 tussen begin- en eindjaar van de gekozen periode (`analysis.py`).
- Kwadratische regressie (`numpy.polyfit`, graad 2) van CO2 per capita op GDP per capita, als
  eenvoudig model om de Environmental Kuznets Curve te toetsen.

## Bronvermelding overgenomen code

- Plotly Express choropleth-opzet: aangepast van het officiële voorbeeld op
  [plotly.com/python/choropleth-maps](https://plotly.com/python/choropleth-maps/).
- `st.cache_data`-gebruik: volgens het cachingpatroon uit de
  [Streamlit-documentatie](https://docs.streamlit.io/library/advanced-features/caching).
- OWID Chart-API-aanroep (parameters `v`, `csvType`, `useColumnShortNames`): overgenomen van de
  officiële [OWID Chart API-documentatie](https://docs.owid.io/projects/etl/api/chart-api/).

## Beperkingen / wat (nog) niet mogelijk is

- Correlatie ≠ causaliteit: het dashboard laat samenhang en trends zien, geen bewijs dat beleid
  X uitstoot Y heeft veroorzaakt.
- GDP-cijfers ontbreken voor de laatste jaren (rapportagevertraging) en voor een aantal kleine
  (eiland)staten — dit vermindert het aantal landen in de Kuznets-curve-analyse.
- De inkomensgroep-indeling is zelf afgeleid en niet gelijk aan officiële Wereldbank-groepen.
