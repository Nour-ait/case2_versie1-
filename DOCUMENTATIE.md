Hier is een uitgebreide en heldere uitleg van de code. Je kunt deze tekst kopiëren en opslaan als een **`DOCUMENTATIE.md`** bestand op GitHub, of gebruiken als voorbereiding op je presentatie.

Het document is opgebouwd in twee delen:

1. **Match met de Opdracht**: Welke eis uit de rubric hoort bij welk onderdeel.
2. **Code-uitleg van regel tot regel**: Precies wat de Python-code stap voor stap doet in begrijpelijke taal.

---

# Documentatie & Code-Toelichting: Klimaatbeleid vs. Realiteit

Dit document legt uit hoe het Streamlit-dashboard `app.py` is opgebouwd, welke data-analystappen zijn toegepast en hoe de code precies voldoet aan de eisen uit de beoordelingsrubric van **Introduction to Data Science (IDS)** en **Visual Analytics (VA)**.

---

## Deel 1: Koppeling met de Opdrachteisen & Rubric

| Opdrachteis / Rubric Criterium | Waar dit in de code zit | Wat het precies doet |
| --- | --- | --- |
| **1. Verplichte Controls (IDS/VA)** | Zijbalk (`st.sidebar`) | Bevat **minimaal 3 interactieve elementen**: <br>

<br>• **Slider**: Selecteren van een jaar (`st.sidebar.slider`) <br>

<br>• **Dropdown**: Filteren op inkomensniveau (`st.sidebar.selectbox`) <br>

<br>• **Checkbox**: Logaritmische schaal aan/uit (`st.sidebar.checkbox`) |
| **2. Twee datasets samengevoegd (IDS)** | Functie `load_data()` | Combineert twee losse CSV-bestanden via een **Inner Join** op de unieke combinatie `['iso_code', 'year']`. |
| **3. Join-verantwoording (IDS)** | Tab 4 ("Data & Verantwoording") | Berekent en toont het aantal rijen vóór en ná de join (`stats['raw_co2']`, `stats['clean_co2']`, `stats['merged']`) om rijenuitval transparant te verantwoorden. |
| **4. Dataverkenning & Opschoning (IDS)** | Functie `load_data()` | Filtert via `str.len() == 3` alle geaggregeerde regio's (zoals *World* of *Europe*) eruit, zodat alleen soevereine landen overblijven. |
| **5. Feature Engineering (IDS)** | Functie `load_data()` | Berekent nieuwe afgeleide variabelen die niet in de ruwe data zaten: <br>

<br>• `gdp_per_capita` (`gdp` / `population`) <br>

<br>• `co2_per_capita` (`co2_emissions` / `population`) |
| **6. Caching van Data (IDS)** | Decorator `@st.cache_data` | Zorgt ervoor dat de data slechts één keer wordt ingeladen en verwerkt. Hierdoor blijft het dashboard erg snel bij het verschuiven van de filters. |
| **7. Verhaallijn & Structuur (VA)** | `st.tabs([...])` | Verdeelt het dashboard in **4 logische stappen**: <br>

<br>1. *Kuznets Curve* (Macro-relatie tussen rijkdom en uitstoot) <br>

<br>2. *Verandering* (Gedrag van landen tussen start- en eindjaar) <br>

<br>3. *Landen & Kaart* (Geografische verdeling en historische trend) <br>

<br>4. *Verantwoording* (Data-transparantie en bronnen) |
| **8. Vergelijken & Annoteren (VA)** | Tab 2 & Tab 3 | Bevat referentielijnen (nul-lijnen bij verandering en een stippellijn bij het **Klimaatakkoord van Parijs 2015**). |
| **9. Bronvermelding (Verplicht)** | Tab 4 | Vermeldt de herkomst van de datasets (Our World in Data & Ember) en de gebruikte Python-bibliotheken. |

---

## Deel 2: Stap-voor-Stap Code Uitleg

### 1. Inladen van bibliotheken & Pagina-instellingen

```python
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Klimaatbeleid vs. Realiteit", layout="wide")

```

* **Wat gebeurt hier?** We importeren Streamlit (voor de web-interface), Pandas (voor het bewerken van data) en Plotly Express (voor de grafieken).
* `layout="wide"` zorgt ervoor dat het dashboard het hele scherm gebruikt.

---

### 2. Data inladen, opschonen en samenvoegen (`load_data`)

```python
@st.cache_data
def load_data():
    df_co2 = pd.read_csv('data/annual-co2-emissions-per-country.csv')
    df_ren = pd.read_csv('data/renewable_energy_share_2000_2025.csv')

```

* **`@st.cache_data`**: Zorgt dat Python de bestanden in het geheugen opslaat, zodat de app sneller laadt.
* `pd.read_csv(...)`: Leest de twee CSV-bestanden uit de map `data/` in als gegevenstabellen (DataFrames).

```python
    df_co2.rename(columns={
        'Entity': 'country_co2', 
        'Code': 'iso_code', 
        'Year': 'year', 
        'Annual CO₂ emissions': 'co2_emissions'
    }, inplace=True)

```

* **Hernoemen**: We maken de kolomnamen van de CO₂-dataset gelijk aan die van de hernieuwbare energie-dataset, zodat het samenvoegen straks vlekkeloos verloopt.

```python
    df_co2_clean = df_co2[df_co2['iso_code'].notna() & (df_co2['iso_code'].str.len() == 3)].copy()
    df_ren_clean = df_ren[df_ren['iso_code'].notna() & (df_ren['iso_code'].str.len() == 3)].copy()

```

* **Opschonen**: Officiële landcodes (ISO3) bestaan altijd uit exact 3 letters (bijv. `NLD`, `DEU`, `USA`). Geaggregeerde regio's zoals 'World' of 'Europe' hebben dit niet. Door hierop te filteren, voorkomen we dubbeltellingen.

```python
    merged = pd.merge(df_co2_clean, df_ren_clean, on=['iso_code', 'year'], how='inner')
    
    merged['gdp_per_capita'] = merged['gdp'] / merged['population']
    merged['co2_per_capita'] = merged['co2_emissions'] / merged['population']

```

* **Inner Join**: We voegen de twee schoner gemaakte tabellen samen op basis van twee sleutels: de landcode (`iso_code`) én het jaar (`year`).
* **Afgeleide variabelen**: We delen de totale CO₂-uitstoot en het totale GDP door de bevolking (`population`) om eerlijke waarden per inwoner te krijgen.

---

### 3. Dynamische Jaarbepaling & Zijbalk (Filters)

```python
min_jaar = int(df['year'].min())
max_jaar = int(df['year'].max())

selected_year = st.sidebar.slider("Selecteer een jaar", min_value=min_jaar, max_value=max_jaar, value=max_jaar)

```

* **Dynamische Slider**: De slider kijkt automatisch wat het laagste en hoogste jaar in de dataset is (bijv. 2000 tot 2022) en past de schaal daarop aan.

```python
selected_income = st.sidebar.selectbox("Filter op inkomensniveau", income_options)
use_log_scale = st.sidebar.checkbox("Logaritmische schaal voor GDP", value=True)

```

* **Dropdown & Checkbox**: De gebruiker kan landen filteren op welvaartsklasse en de assen van de grafiek aanpassen.

---

### 4. Kenniscijfers (Metrics)

```python
col1, col2, col3, col4 = st.columns(4)
col1.metric("Aantal landen", len(df_year))
col2.metric("Gem. hernieuwbare stroom", f"{df_year['renewables_share_elec'].mean():.1f}%")

```

* **KPI Kaarten**: Bovenaan het dashboard tonen 4 kolommen direct de gemiddelden van de gekozen selectie (aantal landen, % groene stroom, CO₂ per inwoner en gemiddeld GDP).

---

### 5. Tabbladen & Visualisaties

#### Tab 1: GDP vs. CO₂ Uitstoot (Kuznets Curve)

```python
fig_ekc = px.scatter(
    df_year,
    x="gdp_per_capita",
    y="co2_per_capita",
    size="population",
    color="renewables_share_elec",
    hover_name="country",
    log_x=use_log_scale
)
st.plotly_chart(fig_ekc, use_container_width=True)

```

* **Puntenwolk (Scatterplot)**: Elks stipje is een land. De grootte van de stip geeft de bevolkingsomvang aan en de kleur toont het aandeel hernieuwbare energie.

#### Tab 2: Verandering tussen Start- en Eindjaar

```python
df_change['co2_pct_change'] = ((df_change[f'co2_per_capita_{max_jaar}'] - df_change[f'co2_per_capita_{min_jaar}']) / df_change[f'co2_per_capita_{min_jaar}']) * 100
df_change['ren_diff'] = df_change[f'renewables_share_elec_{max_jaar}'] - df_change[f'renewables_share_elec_{min_jaar}']

```

* **Verandering berekenen**: Berekent per land hoeveel % de CO₂-uitstoot is gestegen of gedaald tussen het eerste en het laatste jaar, en hoeveel procentpunt groene energie erbij is gekomen.
* **Categorisering**: Met een functie delen we landen in categorieën in (bijv. *Groene daling* als CO₂ daalt én groene stroom stijgt).

#### Tab 3: Wereldkaart & Landentrend

```python
fig_map = px.choropleth(df_year, locations="iso_code", color="renewables_share_elec", color_continuous_scale="Greens")

```

* **Choropleth (Wereldkaart)**: Kleurt de landen op de wereldkaart in op basis van hun aandeel hernieuwbare stroom.
* **Tijdreeks met Annotatie**: Bevat een iline-chart voor één gekozen land met een **blauwe stippellijn op het jaar 2015** (het Klimaatakkoord van Parijs) om beleidseffecten te evalueren.

#### Tab 4: Data & Verantwoording

```python
st.write(f"- CO₂-dataset (ruw): {stats['raw_co2']:,} rijen")
st.write(f"- Uiteindelijke samengevoegde dataset: {stats['merged']:,} rijen")

```

* **Transparantie**: Rapporteert exact het effect van de data-opschoning en de join. Dit geeft de docent direct inzicht in de datakwaliteit en voorkomt aftrekpunten voor onduidelijke gegevensbewerking.