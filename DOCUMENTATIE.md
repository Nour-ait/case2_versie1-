

# Documentatie & Toelichting Streamlit Dashboard: Klimaatbeleid vs. Realiteit

## 1. Introductie & Koppeling met de Opdracht

Dit Dashboard is gebouwd in Python met behulp van **Streamlit**, **Pandas** en **Plotly Express**. Het doel is om data van CO₂-uitstoot te combineren met gegevens over hernieuwbare energie om te onderzoeken of de klimaattransitie daadwerkelijk leidt tot lagere emissies, en welke rol economische welvaart hierin speelt.

### Sluiting aan op de Onderzoeksvragen:

* **Hoofdvraag:** *"In hoeverre komt de transitie naar hernieuwbare energie daadwerkelijk tot uiting in dalende CO₂-uitstoot, en hoe verhoudt dit zich tot het inkomensniveau van landen?"*
$\rightarrow$ **Oplossing in app:** De gebruiker kan via de zijbalk jaartallen en inkomensniveaus filteren, terwijl KPI-kaarten en visualisaties direct inzicht geven in deze dynamiek.
* **Deelvraag 1 ("Walk vs. Talk"):** *"Welke landen laten een reële ontkoppeling zien en welke blijven steken?"*
$\rightarrow$ **Oplossing in app:** Tabblad 2 berekent de verandering over de gehele periode en deelt landen in 4 duidelijke categorieën in op een scatterplot met scheidingslijnen.
* **Deelvraag 2 & 3 (Environmental Kuznets Curve & Inkomensgroepen):** *"Is er bewijs voor een Environmental Kuznets Curve en hoe verschilt dit per inkomensgroep?"*
$\rightarrow$ **Oplossing in app:** Tabblad 1 plot het GDP per inwoner tegen de CO₂-uitstoot per inwoner, waarbij landen gekleurd zijn op basis van hun gefabriceerde inkomensgroep (`income_group`).

---

## 2. Stap-voor-Stap Code-Uitleg

### Stap 1: Imports & Pagina-instellingen

```python
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Klimaatbeleid vs. Realiteit", 
    layout="wide"
)

```

* **Wat gebeurt hier?**
De benodigde bibliotheken worden geladen. `st.set_page_config` zet de titel van het tabblad in de browser en stelt de lay-out in op `wide` (volledige breedte van het scherm), wat prettig werkt voor dashboards met meerdere kolommen en grote grafieken.

---

### Stap 2: Data Inladen, Opschonen en Feature Engineering

```python
@st.cache_data
def load_data():
    ...

```

* **Wat gebeurt hier?**
1. **Caching (`@st.cache_data`):** Zorgt ervoor dat Pandas de CSV-bestanden slechts één keer inleest in het geheugen. Dit maakt de app ontzettend snel bij het toepassen van filters.
2. **Kolomhernoeming:** Kolomnamen in de CO₂-dataset worden gestandaardiseerd (`Entity` $\rightarrow$ `country_co2`, `Code` $\rightarrow$ `iso_code`, etc.) zodat ze matchen met de structuur van de energie-dataset.
3. **Opschonen (ISO3 Filtering):** Met `df['iso_code'].str.len() == 3` worden alleen rijen met een geldige 3-letterige landcode (zoals `NLD`, `USA`) behouden. Regio's, werelddelen en totalen (zoals *World* of *Europe*) worden hiermee gefilterd om dubbeltellingen te voorkomen.
4. **Inner Join:** De datasets worden samengevoegd op basis van de unieke sleutel `[iso_code, year]`.
5. **Feature Engineering (Nieuwe variabelen):**
* `gdp_per_capita` = Bruto Binnenlands Product per inwoner.
* `co2_per_capita` = CO₂-uitstoot per inwoner.
* `income_group` = Landen worden automatisch ingedeeld in drie klassen met `pd.cut()`:
* *Lage inkomens* (< $5.000)
* *Opkomende inkomens* ($5.000 - $20.000)
* *Hoge inkomens* (> $20.000)




6. **Relationale Statistieken:** Aantallen rijen voor en na het opschonen worden opgeslagen in `stats` voor verantwoording in Tabblad 4.



---

### Stap 3: Zijbalk & Dynamische Filters

```python
st.sidebar.header("Filters")
selected_year = st.sidebar.slider("Selecteer een jaar", min_value=min_jaar, max_value=max_jaar, value=max_jaar)
selected_income = st.sidebar.selectbox("Filter op inkomensniveau", income_options)
use_log_scale = st.sidebar.checkbox("Logaritmische schaal voor GDP", value=True)

```

* **Wat gebeurt hier?**
De zijbalk bevat drie interactieve elementen:
* Een **jaar-slider** die zich automatisch aanpast aan het minimale en maximale jaar uit de dataset.
* Een **dropdown** om specifiek in te zoomen op een inkomensgroep.
* Een **checkbox** om de X-as van de Kuznets Curve op logaritmische schaal te zetten (zodat grote verschillen tussen arme en rijkere landen overzichtelijk zichtbaar blijven).



---

### Stap 4: Top-level Kerncijfers (KPI metrics)

```python
col1, col2, col3, col4 = st.columns(4)
col1.metric("Aantal analyseerde landen", len(df_year))
col2.metric("Gem. hernieuwbare stroom", f"{df_year['renewables_share_elec'].mean():.1f}%" ...)
...

```

* **Wat gebeurt hier?**
Bovenaan het dashboard worden 4 samenvattende kaarten getoond. Deze rekenen dynamisch mee met het geselecteerde jaar en de gekozen inkomensgroep.

---

### Stap 5: Tabblad 1 – Environmental Kuznets Curve (Deelvraag 2 & 3)

```python
fig_ekc = px.scatter(
    df_year,
    x="gdp_per_capita",
    y="co2_per_capita",
    size="population",
    color="income_group",
    ...
)

```

* **Wat gebeurt hier?**
Een interactieve scatterplot toont het verband tussen welvaart ($X$-as) en CO₂-uitstoot ($Y$-as).
* **Bolgrootte (`size`):** Representeert de populatiegrootte van een land.
* **Kleur (`color`):** Geeft de inkomensgroep aan.
* **Doel:** Zichtbaar maken of rijkere landen na verloop van tijd minder uitstoten per inwoner (ontkoppeling / Kuznets-curve).



---

### Stap 6: Tabblad 2 – "Walk vs. Talk" Categorieën (Deelvraag 1)

```python
df_change['co2_pct_change'] = ((df_change[f'co2_per_capita_{max_jaar}'] - ...) / ...) * 100
df_change['ren_diff'] = df_change[f'renewables_share_elec_{max_jaar}'] - df_change[...]

def categoriseer(row):
    if row['ren_diff'] > 5 and row['co2_pct_change'] < 0:
        return 'Walk: Groene daling (Meer hernieuwbaar & minder CO₂)'
    ...

```

* **Wat gebeurt hier?**
Het script vergelijkt de situatie van het eerste jaar (`min_jaar`) met het meest recente jaar (`max_jaar`) per land.
* **Berekening:** Hoeveel procentuele CO₂-verandering is er geweest en hoeveel procentpunt toename in hernieuwbare energie?
* **Categorisering:** Landen worden via de Python-functie `categoriseer()` ingedeeld in vier kwadranten (bijv. 'Walk' vs 'Talk/Lag').
* **Visualisatie:** Een Plotly scatterplot met referentielijnen (`add_hline` op 0% en `add_vline` op 5 percentagepunten) scheidt de categorieën visueel van elkaar.



---

### Stap 7: Tabblad 3 – Geografische Kaart & Tijdreeks

```python
fig_map = px.choropleth(df_year, locations="iso_code", color="renewables_share_elec", ...)
...
fig_line = px.line(df_land, x="year", y=["renewables_share_elec", "co2_per_capita"], ...)
fig_line.add_vline(x=2015, line_dash="dot", line_color="blue", annotation_text="Parijs-akkoord (2015)")

```

* **Wat gebeurt hier?**
1. **Wereldkaart (`choropleth`):** Geeft landen op de wereldkaart een groene kleur op basis van hun aandeel hernieuwbare energie in het gekozen jaar.
2. **Tijdreeks per land:** Een selectiebox laat de gebruiker één specifiek land kiezen (standaard ingesteld op Nederland). Een lijngrafiek toont de verandering door de jaren heen.
3. **Parijs-akkoord annotatie:** Er is een verticale stippellijn op het jaar **2015** geplaatst om te beoordelen of er een versnelling plaatsvond na de klimaatconferentie van Parijs.



---

### Stap 8: Tabblad 4 – Data & Methodologie (Verantwoording)

```python
st.write(f"- CO₂-dataset (ruw): {stats['raw_co2']:,} rijen")
...
st.dataframe(df_year[...].head(15))

```

* **Wat gebeurt hier?**
Dit tabblad biedt transparantie. Het toont hoeveel rijen er in de ruwe data zaten, hoeveel er zijn overgebleven na opschoning en hoe de uiteindelijke tabel er in het geheugen uitziet via `st.dataframe()`.

---

## 3. Samenvatting van de Technische Werking

| Component | Gebruikte Technologie | Functie in de App |
| --- | --- | --- |
| **Data Structuur** | `pandas.DataFrame` | Opschonen, joins, berekeningen (`gdp_per_capita`, `income_group`). |
| **Performance** | `@st.cache_data` | Voorkomt herhaaldelijk inlezen van bestanden. |
| **Interactiviteit** | `st.sidebar`, `st.slider`, `st.selectbox` | Dynamisch filteren van de gegevens. |
| **Visualisatie** | `plotly.express` (Scatter, Line, Choropleth) | Interactieve en zoom bare grafieken en wereldkaarten. |
| **Structuur** | `st.tabs`, `st.columns`, `st.metric` | Overzichtelijke en nette presentatie van de resultaten. |
