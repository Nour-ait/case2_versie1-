Hier is een zeer uitgebreide, academische en gedetailleerde documentatie van het project. Dit document kun je rechtstreeks overnemen als **`DOCUMENTATIE.md`** op GitHub, opnemen in een projectverslag of gebruiken als volledige voorbereiding op het eindgesprek/presentatie.

---

# Uitgebreide Projectdocumentatie: Klimaatbeleid vs. Realiteit

**Vakken:** Introduction to Data Science (IDS) & Visual Analytics (VA)

**Bestand:** `app.py`

**Technologieën:** Python, Streamlit, Pandas, Plotly Express

---

## 1. Projectomschrijving & Onderzoeksvragen

### 1.1 Context

In het wereldwijde klimaatdebat staat de energietransitie centraal. Landen investeren op grote schaal in hernieuwbare energiebronnen (zoals zon en wind) met als hoofddoel het terugdringen van de CO₂-uitstoot. Echter verschilt de impact van dit beleid sterk per land, mede afhankelijk van de economische welvaart (GDP) en bevolkingsomvang.

### 1.2 Hoofdvraag

> *In hoeverre leidt een toename in het aandeel hernieuwbare energie tot een daadwerkelijke reductie van de CO₂-uitstoot per inwoner, en welke rol speelt de economische welvaart (GDP per inwoner) hierin?*

### 1.3 Deelvragen

1. Is er sprake van een **Environmental Kuznets Curve** (ontkoppeling van economische groei en uitstoot)?
2. Welke landen laten tussen het begin- en eindjaar een 'groene daling' zien (stijging hernieuwbaar + daling CO₂), en welke niet?
3. Hoe heeft het aandeel hernieuwbare energie zich geografisch en door de tijd heen ontwikkeld, met name rond scharnierpunten zoals het **Klimaatakkoord van Parijs (2015)**?

---

## 2. Rubric & Vakvereisten Matchen

Hieronder staat hoe elke eis uit het beoordelingsmodel is vertaald naar specifieke functionaliteiten in de Python-code:

| Categorie | Vereiste uit Rubric | Implementatie in `app.py` | Academische / Technische Verantwoording |
| --- | --- | --- | --- |
| **IDS** | **Data Cleaning** | Filtering op `str.len() == 3` & `notna()` | Verwijdert aggregaatrijen (zoals *World*, *Europe*) om dubbeltellingen te voorkomen. |
| **IDS** | **Data Integration** | `pd.merge(..., on=['iso_code', 'year'], how='inner')` | Combineert twee onafhankelijke bronnen op landniveau en tijdstempel. |
| **IDS** | **Join-verantwoording** | Teller-variabelen + Tab 4 kwantitatieve overzichten | Maakt rijenuitval volledig transparant (eisen datakwaliteit). |
| **IDS** | **Feature Engineering** | Berekent `gdp_per_capita` & `co2_per_capita` | Corrigeert voor bevolkingsomvang voor eerlijke vergelijkingen tussen landen. |
| **IDS** | **Performance Optimization** | Decorator `@st.cache_data` | Voorkomt dat zware herberekeningen opnieuw draaien bij elke gebruikersinteractie. |
| **VA** | **Interactiviteit (>= 3 Controls)** | Slider (Jaar), Dropdown (Inkomen), Checkbox (Log-schaal) | Biedt de gebruiker direct de mogelijkheid om hypotheses op deelverzamelingen te testen. |
| **VA** | **Visual Storytelling** | `st.tabs([...])` verdeeld in 4 stappen | Gidst de lezer van macro-analyse (global) naar micro-analyse (per land) tot verantwoording. |
| **VA** | **Referentiepunten & Annotatie** | `add_hline()`, `add_vline()`, Kleurcategorieën | Geeft contextuele betekenis aan data (bijv. Parijs-akkoord 2015, grenslijnen bij 0% en 5%-punt). |
| **VA** | **Geografische & Tijdweergave** | Choropleth Map & Multi-line Time Series | Combineert ruimtelijke patronen met temporele trends. |

---

## 3. Data Pipeline & Architectuur

```
[ annual-co2-emissions-per-country.csv ] ──┐
                                           ├──> Filter ISO3 (3-letter) ──> Inner Join (iso_code, year) ──> Feature Engineering ──> Dashboard UI
[ renewable_energy_share_2000_2025.csv ] ──┘

```

### Data-opschoning & Relational Join

1. **Sleutelidentificatie:** Omdat landennamen per dataset kunnen verschillen (bijv. *"USA"* vs *"United States"*), gebruiken we de officiële ISO 3166-1 alpha-3 landcodes (`iso_code`).
2. **Aggregaatfiltering:** Niet-landen (regio's, continenten) hebben in de ruwe dataset vaak geen ISO-code of een afwijkende lengte. Door strikt te filteren op `len(code) == 3`, houden we uitsluitend individuele soevereine staten over.
3. **Inner Join:** We voegen de datasets samen als een matrix op de samengestelde sleutel `(iso_code, year)`. Alleen jaren en landen die in *beide* bestanden voorkomen blijven behouden.

---

## 4. Regel-voor-Regel Code-Analyse

Hieronder wordt de code uit `app.py` per logisch blok gedetailleerd uitgelegd.

### Blok 1: Bibliotheken en Pagina-instellingen

```python
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Klimaatbeleid vs. Realiteit", layout="wide")

```

* **`import streamlit as st`**: Laadt het Streamlit-framework voor het bouwen van de web-app.
* **`import pandas as pd`**: Laadt Pandas voor gegevensbewerking en dataframes.
* **`import plotly.express as px`**: Laadt Plotly Express voor interactieve en responsieve grafieken.
* **`st.set_page_config(...)`**: Stel de browsertab-titel in en dwingt een breed schermformaat af (`layout="wide"`), wat noodzakelijk is voor een overzichtelijk dashboard met meerdere kolommen.

---

### Blok 2: ETL-functie (Extract, Transform, Load) & Caching

```python
@st.cache_data
def load_data():
    df_co2 = pd.read_csv('data/annual-co2-emissions-per-country.csv')
    df_ren = pd.read_csv('data/renewable_energy_share_2000_2025.csv')

```

* **`@st.cache_data`**: Een Streamlit-decorator. Dit zorgt ervoor dat Python de uitkomst van deze functie opslaat in het geheugen. Bij het veranderen van een filter wordt de data niet opnieuw van de schijf ingelezen, wat de prestaties enorm verhoogt.
* **`pd.read_csv(...)`**: Leest de CSV-bestanden in vanuit de lokale projectmap `data/`.

```python
    df_co2.rename(columns={
        'Entity': 'country_co2', 
        'Code': 'iso_code', 
        'Year': 'year', 
        'Annual CO₂ emissions': 'co2_emissions'
    }, inplace=True)

```

* **`rename(...)`**: Normaliseert de kolomnamen van de CO₂-dataset, zodat deze naadloos aansluiten bij de sleutelnamen in de dataset voor hernieuwbare energie.

```python
    raw_co2_count = len(df_co2)
    raw_ren_count = len(df_ren)
    
    df_co2_clean = df_co2[df_co2['iso_code'].notna() & (df_co2['iso_code'].str.len() == 3)].copy()
    df_ren_clean = df_ren[df_ren['iso_code'].notna() & (df_ren['iso_code'].str.len() == 3)].copy()

```

* **`raw_co2_count` / `raw_ren_count**`: Bewaart het exacte aantal rijen uit de ruwe bestanden ten behoeve van de dataverantwoording in Tab 4.
* **`notna() & str.len() == 3`**: Opschoningsregel. ISO3-codes bestaan exact uit 3 letters. Regio's zoals *World*, *OECD*, of *Europe* vallen hierdoor automatisch af.

```python
    merged = pd.merge(df_co2_clean, df_ren_clean, on=['iso_code', 'year'], how='inner')
    
    merged['gdp_per_capita'] = merged['gdp'] / merged['population']
    merged['co2_per_capita'] = merged['co2_emissions'] / merged['population']

```

* **`pd.merge(..., how='inner')`**: Combineert de geschoonde dataframes. Enkel de rijen waar zowel CO₂-gegevens als hernieuwbare energiegegevens voor hetzelfde land én jaar bestaan, blijven behouden.
* **Feature Engineering**: Berekent twee relatieve indicatoren (`gdp_per_capita` en `co2_per_capita`). Dit is essentieel omdat absolute cijfers (zoals de totale uitstoot van China vs. Luxemburg) een vertekenend beeld geven.

---

### Blok 3: Dynamische Initialisatie & Zijbalk (Controls)

```python
try:
    df, stats = load_data()
except Exception as e:
    st.error(f"Fout bij het laden van de bestanden: {e}")
    st.stop()

min_jaar = int(df['year'].min())
max_jaar = int(df['year'].max())

```

* **Foutafhandeling (`try-except`)**: Vangt eventuele ontbrekende bestanden op en toont een heldere foutmelding in plaats van een harde Python-crash.
* **Dynamische Datumbepaling**: Kijkt via `.min()` en `.max()` naar het bereik in de gecombineerde dataset. Mocht de dataset later worden uitgebreid (bijv. tot 2025/2026), dan past de gehele applicatie zich automatisch aan.

```python
st.sidebar.header("Filters")
selected_year = st.sidebar.slider("Selecteer een jaar", min_value=min_jaar, max_value=max_jaar, value=max_jaar)

income_options = [
    "Alle landen", 
    "Hoge inkomens (> $20.000)", 
    "Midden inkomens ($5.000 - $20.000)", 
    "Lage inkomens (< $5.000)"
]
selected_income = st.sidebar.selectbox("Filter op inkomensniveau", income_options)
use_log_scale = st.sidebar.checkbox("Logaritmische schaal voor GDP", value=True)

```

* **Interactiviteit (Verplicht onderdeel)**:
1. **`st.sidebar.slider`**: Bepaalt de tijdssnede voor de analyse.
2. **`st.sidebar.selectbox`**: Maakt het mogelijk om specifieke economische klassen te isoleren.
3. **`st.sidebar.checkbox`**: Schakelt tussen een lineaire en logaritmische as voor GDP (cruciaal voor het visualiseren van inkomensverschillen over meerdere grootteordes).



---

### Blok 4: Data Filtering op Basis van Gebruikersinvoer

```python
df_year = df[df['year'] == selected_year].copy()

if selected_income == "Hoge inkomens (> $20.000)":
    df_year = df_year[df_year['gdp_per_capita'] > 20000]
elif selected_income == "Midden inkomens ($5.000 - $20.000)":
    df_year = df_year[(df_year['gdp_per_capita'] >= 5000) & (df_year['gdp_per_capita'] <= 20000)]
elif selected_income == "Lage inkomens (< $5.000)":
    df_year = df_year[df_year['gdp_per_capita'] < 5000]

```

* **Subsetting**: Maakt een gefilterde kopie (`df_year`) aan die exact overeenkomt met de door de gebruiker gekozen instellingen in de zijbalk.

---

### Blok 5: Kerncijfers (KPI Metrics)

```python
col1, col2, col3, col4 = st.columns(4)
col1.metric("Aantal landen", len(df_year))
col2.metric("Gem. hernieuwbare stroom", f"{df_year['renewables_share_elec'].mean():.1f}%")
col3.metric("Gem. CO₂ per inwoner", f"{df_year['co2_per_capita'].mean():.2f} ton")
col4.metric("Gem. GDP per inwoner", f"${df_year['gdp_per_capita'].mean():,.0f}" if not df_year['gdp_per_capita'].isna().all() else "N/B")

```

* **`st.columns(4)`**: Telt de pagina op in 4 even grote kolommen.
* **`st.metric`**: Berekent dynamisch de aggregaten (gemiddelden en aantallen) over de gefilterde set, wat de gebruiker direct context geeft bij het veranderen van een filter.

---

### Blok 6: Tabbladen & Visualisaties

#### Tab 1: Kuznets Curve (Scatterplot)

```python
with tab1:
    fig_ekc = px.scatter(
        df_year,
        x="gdp_per_capita",
        y="co2_per_capita",
        size="population",
        color="renewables_share_elec",
        hover_name="country",
        log_x=use_log_scale,
        labels={...}
    )
    st.plotly_chart(fig_ekc, use_container_width=True)

```

* **Multidimensionale Visualisatie**:
* **X-as:** Welvaart (`gdp_per_capita`)
* **Y-as:** Uitstoot (`co2_per_capita`)
* **Bolgrootte (`size`):** Bevolkingsomvang (`population`)
* **Kleur (`color`):** Aandeel hernieuwbare stroom (`renewables_share_elec`)


* **`log_x=use_log_scale`**: Maakt de exponentiële spreiding van GDP inzichtelijk.

#### Tab 2: Veranderingsanalyse over de Tijd

```python
with tab2:
    df_start = df[df['year'] == min_jaar][['iso_code', 'co2_per_capita', 'renewables_share_elec']]
    df_recent = df[df['year'] == max_jaar][['iso_code', 'country', 'co2_per_capita', 'renewables_share_elec']]
    df_change = pd.merge(df_start, df_recent, on='iso_code', suffixes=(f'_{min_jaar}', f'_{max_jaar}'))

```

* **Pivoting via Merge**: Combineert het allereerste jaar in de data met het meest recente jaar per land.

```python
    df_change['co2_pct_change'] = ((df_change[f'co2_per_capita_{max_jaar}'] - df_change[f'co2_per_capita_{min_jaar}']) / df_change[f'co2_per_capita_{min_jaar}']) * 100
    df_change['ren_diff'] = df_change[f'renewables_share_elec_{max_jaar}'] - df_change[f'renewables_share_elec_{min_jaar}']

```

* **Procentuele en Absolute Verandering**: Berekent de relatieve CO₂-mutatie (%) en de absolute toename in duurzame stroom (procentpunten).

```python
    def categoriseer(row):
        if row['ren_diff'] > 5 and row['co2_pct_change'] < 0:
            return 'Groene daling (CO₂ daalt, groen stijgt)'
        ...

```

* **Business Logic / Regelgebaseerde Categorisering**: Deelt landen op basis van hun voortgang in 4 kwadranten in.

```python
    fig_walk.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_walk.add_vline(x=5, line_dash="dash", line_color="gray")

```

* **Referentielijnen**: Hulplijnen die het snijpunt aangeven tussen daling/stijging en betekenisvolle groei in duurzame stroom.

#### Tab 3: Geografische Spreiding & Tijdreeks per Land

```python
with tab3:
    fig_map = px.choropleth(
        df_year,
        locations="iso_code",
        color="renewables_share_elec",
        color_continuous_scale="Greens"
    )

```

* **`px.choropleth`**: Visualiseert de data geografisch op een wereldkaart, gekleurd in groentinten om het aandeel hernieuwbare energie intuïtief weer te geven.

```python
    fig_line = px.line(df_land, x="year", y=["renewables_share_elec", "co2_per_capita"])
    fig_line.add_vline(x=2015, line_dash="dot", line_color="blue", annotation_text="Parijs-akkoord (2015)")

```

* **Annotatie**: Plaatst een stippellijn op het jaar 2015. Dit helpt de gebruiker te analyseren of de trend van een specifiek land versnelde na het Klimaatakkoord van Parijs.

#### Tab 4: Data & Verantwoording

```python
with tab4:
    st.write(f"- CO₂-dataset (ruw): {stats['raw_co2']:,} rijen")
    st.write(f"- Uiteindelijke samengevoegde dataset: {stats['merged']:,} rijen")

```

* **Datatransparantie**: Toont exact hoeveel rijen uit de bronbestanden afkomstig zijn en hoeveel rijen overblijven na het schonen en koppelen. Dit onderbouwt de betrouwbaarheid van het dashboard.

---

## 5. Designbeslissingen & Visual Analytics Principes

1. **Cognitieve Belasting Beperken:** Door de opdeling in tabs wordt de gebruiker niet overspoeld met informatie. Elk tabblad beantwoordt één specifieke deelvraag.
2. **Visual Encoding (Kleur & Formaat):**
* **Groentinten:** Worden consequent gebruikt voor hernieuwbare energie.
* **Grootte van stippen:** Representeert bevolkingsomvang, zodat grote landen (zoals India of de VS) visueel meer gewicht krijgen dan kleine eilandstaten.


3. **Logaritmische Schaal:** Welvaart (GDP per inwoner) kent extreem grote verschillen (bijv. $500 vs $100.000). Een lineaire schaal zou 90% van de landen op een kluitje links in de grafiek drukken. Een logaritmische schaal maakt patronen in alle inkomensklassen zichtbaar.

---

## 6. Beperkingen & Mogelijkheden voor Vervolgonderzoek

* **Data-beschikbaarheid:** Verschillende ontwikkelingslanden hebben onvolledige historische gegevens over hernieuwbare energie, waardoor zij uit de gecombineerde set vallen.
* **Eelektriciteit vs. Totale Energie:** De metriek `renewables_share_elec` kijkt naar het aandeel hernieuwbare *elektriciteit*. Transport en zware industrie (die vaak op olie/gas draaien) zijn hierin niet direct vertegenwoordigd, wat verklaart waarom een land met veel groene stroom soms toch een hoge CO₂-uitstoot behoudt.
