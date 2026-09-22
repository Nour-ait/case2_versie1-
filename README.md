# Klimaatbeleid vs. werkelijkheid

Interactief Streamlit-dashboard over de relatie tussen CO₂-uitstoot, hernieuwbare
energie en economische welvaart per land (1990–heden).

**Onderzoeksvraag:** In hoeverre komt de transitie naar hernieuwbare energie
daadwerkelijk tot uiting in dalende CO₂-uitstoot, en hoe verhoudt dit zich tot
het inkomensniveau van landen?

## Databronnen (opgehaald in het script, niet handmatig)

| Bron | Ophaalmethode | Gebruikt voor |
|---|---|---|
| [OWID CO2-data](https://github.com/owid/co2-data) | `pandas.read_csv(url)` | CO₂-uitstoot, CO₂ per capita |
| [OWID Energy-data](https://github.com/owid/energy-data) | `pandas.read_csv(url)` | Aandeel hernieuwbare energie, GDP, bevolking |
| [World Bank API](https://api.worldbank.org/v2/country) | `requests.get()` (JSON) | Inkomensclassificatie per land |

Join-sleutel: `(iso_code, year)` voor CO2 ↔ Energy, daarna `iso_code` voor de
inkomensclassificatie. Zie het tabblad **"Data & methode"** in het dashboard
voor de rij-aantallen voor en na elke join.

## Lokaal draaien

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

De app opent op `http://localhost:8501`. De eerste keer duurt het laden iets
langer omdat de data wordt opgehaald; daarna wordt alles 24 uur gecachet
(`@st.cache_data`).

## Publiceren op GitHub + Streamlit Community Cloud

1. Maak een nieuwe **publieke** GitHub-repository aan en zet deze map erin:
   ```bash
   git init
   git add .
   git commit -m "Eerste versie dashboard"
   git branch -M main
   git remote add origin https://github.com/<jouw-gebruikersnaam>/<repo-naam>.git
   git push -u origin main
   ```
2. Ga naar [share.streamlit.io](https://share.streamlit.io) en log in met je
   GitHub-account.
3. Klik **New app**, kies je repository, branch `main` en bestand `app.py`.
4. Klik **Deploy**. Na een paar minuten krijg je een publieke link
   (`https://<naam>.streamlit.app`).
5. Test daarna of een **schone clone** van de repo zonder handmatige stappen
   werkt — dit is een harde eis van de opdracht.

## Projectstructuur

```
climate-dashboard/
├── app.py              # Streamlit-app (5 tabbladen)
├── data_utils.py        # Data ophalen, opschonen en samenvoegen
├── requirements.txt
├── .streamlit/
│   └── config.toml       # Kleurthema
└── README.md
```

## Widgets per tabblad (eis: minimaal 1 slider, 1 checkbox, 1 dropdown)

- **Wereldkaart** — dropdown (indicator) + slider (jaar)
- **Land over tijd** — dropdown (land) + checkbox (log-schaal) + slider (periode)
- **GDP vs CO₂** — slider (jaar) + multiselect + checkbox (log-x-as)
- **Walk vs Talk** — slider (periode) + checkbox (filter)

## Nog te doen voor jouw inlevering

- [ ] Deelvragen expliciet beantwoorden in de presentatie aan de hand van de
      tabbladen "GDP vs CO₂" (Kuznets-curve) en "Walk vs Talk" (ontkoppeling).
- [ ] Eigen toelichting/interpretatie van de resultaten toevoegen (tekst in
      het dashboard of in de presentatie) — de cijfers/analyse zijn nu klaar,
      de duiding is aan jou.
- [ ] Dataset-keuze uiterlijk woensdag week 3 melden bij Jerome Mies via Teams.
- [ ] Broncode die je overneemt (bv. van Streamlit-documentatie) van een
      bronvermelding voorzien.
