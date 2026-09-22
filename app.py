import streamlit as st
import pandas as pd
import plotly.express as px

# Pagina-instellingen
st.set_page_config(page_title="Klimaatbeleid vs. Realiteit", layout="wide")

# Data inladen en opschonen
@st.cache_data
def load_data():
    df_co2 = pd.read_csv('data/annual-co2-emissions-per-country.csv')
    df_ren = pd.read_csv('data/renewable_energy_share_2000_2025.csv')
    
    # Kolommen hernoemen
    df_co2.rename(columns={
        'Entity': 'country_co2', 
        'Code': 'iso_code', 
        'Year': 'year', 
        'Annual CO₂ emissions': 'co2_emissions'
    }, inplace=True)
    
    # Aantallen bewaren voor de verantwoording
    raw_co2_count = len(df_co2)
    raw_ren_count = len(df_ren)
    
    # Filteren op geldige ISO3-landcodes (3 letters)
    df_co2_clean = df_co2[df_co2['iso_code'].notna() & (df_co2['iso_code'].str.len() == 3)].copy()
    df_ren_clean = df_ren[df_ren['iso_code'].notna() & (df_ren['iso_code'].str.len() == 3)].copy()
    
    # Samenvoegen op landcode en jaar
    merged = pd.merge(df_co2_clean, df_ren_clean, on=['iso_code', 'year'], how='inner')
    
    # Extra variabelen berekenen
    merged['gdp_per_capita'] = merged['gdp'] / merged['population']
    merged['co2_per_capita'] = merged['co2_emissions'] / merged['population']
    
    stats = {
        'raw_co2': raw_co2_count,
        'raw_ren': raw_ren_count,
        'clean_co2': len(df_co2_clean),
        'clean_ren': len(df_ren_clean),
        'merged': len(merged)
    }
    
    return merged, stats

# Data laden
try:
    df, stats = load_data()
except Exception as e:
    st.error(f"Fout bij het laden van de bestanden: {e}")
    st.stop()

# Dynamisch berekenen van het eerste en laatste jaar uit de dataset
min_jaar = int(df['year'].min())
max_jaar = int(df['year'].max())

# Titel en korte toelichting
st.title("Klimaatbeleid vs. Realiteit")
st.write(
    "In dit dashboard onderzoeken we in hoeverre de overstap naar hernieuwbare energie "
    "leidt tot een lagere CO₂-uitstoot per inwoner, en wat de rol is van de welvaart van een land."
)

# Zijbalk met filters (Slider, Dropdown, Checkbox)
st.sidebar.header("Filters")

# 1. Slider (Jaar - dynamisch gekoppeld aan de dataset)
selected_year = st.sidebar.slider("Selecteer een jaar", min_value=min_jaar, max_value=max_jaar, value=max_jaar)

# 2. Dropdown (Inkomensniveau)
income_options = [
    "Alle landen", 
    "Hoge inkomens (> $20.000)", 
    "Midden inkomens ($5.000 - $20.000)", 
    "Lage inkomens (< $5.000)"
]
selected_income = st.sidebar.selectbox("Filter op inkomensniveau", income_options)

# 3. Checkbox (Logaritmische schaal)
use_log_scale = st.sidebar.checkbox("Logaritmische schaal voor GDP", value=True)

# Filteren op basis van de zijbalk
df_year = df[df['year'] == selected_year].copy()

if selected_income == "Hoge inkomens (> $20.000)":
    df_year = df_year[df_year['gdp_per_capita'] > 20000]
elif selected_income == "Midden inkomens ($5.000 - $20.000)":
    df_year = df_year[(df_year['gdp_per_capita'] >= 5000) & (df_year['gdp_per_capita'] <= 20000)]
elif selected_income == "Lage inkomens (< $5.000)":
    df_year = df_year[df_year['gdp_per_capita'] < 5000]

# Kerncijfers
col1, col2, col3, col4 = st.columns(4)
col1.metric("Aantal landen", len(df_year))
col2.metric("Gem. hernieuwbare stroom", f"{df_year['renewables_share_elec'].mean():.1f}%")
col3.metric("Gem. CO₂ per inwoner", f"{df_year['co2_per_capita'].mean():.2f} ton")
col4.metric("Gem. GDP per inwoner", f"${df_year['gdp_per_capita'].mean():,.0f}" if not df_year['gdp_per_capita'].isna().all() else "N/B")

st.divider()

# Tabbladen
tab1, tab2, tab3, tab4 = st.tabs([
    "GDP vs. CO₂ Uitstoot", 
    f"Verandering {min_jaar}-{max_jaar}", 
    "Landen & Wereldkaart", 
    "Data & Verantwoording"
])

# Tab 1: GDP vs CO2
with tab1:
    st.subheader(f"Relatie tussen GDP en CO₂-uitstoot ({selected_year})")
    
    fig_ekc = px.scatter(
        df_year,
        x="gdp_per_capita",
        y="co2_per_capita",
        size="population",
        color="renewables_share_elec",
        hover_name="country",
        log_x=use_log_scale,
        labels={
            "gdp_per_capita": "GDP per inwoner (USD)",
            "co2_per_capita": "CO₂ per inwoner (ton)",
            "renewables_share_elec": "% Hernieuwbare stroom"
        }
    )
    st.plotly_chart(fig_ekc, use_container_width=True)
    
    st.write("Toelichting: In deze grafiek is te zien hoe rijkere landen zich verhouden tot ontwikkelingslanden. Veel welvarende landen laten zien dat de CO₂-uitstoot per inwoner afneemt naarmate het aandeel hernieuwbare energie stijgt.")

# Tab 2: Verandering over de tijd
with tab2:
    st.subheader(f"Verandering in CO₂ en hernieuwbare energie ({min_jaar} vs. {max_jaar})")
    
    df_start = df[df['year'] == min_jaar][['iso_code', 'co2_per_capita', 'renewables_share_elec']]
    df_recent = df[df['year'] == max_jaar][['iso_code', 'country', 'co2_per_capita', 'renewables_share_elec']]
    df_change = pd.merge(df_start, df_recent, on='iso_code', suffixes=(f'_{min_jaar}', f'_{max_jaar}'))
    
    df_change['co2_pct_change'] = ((df_change[f'co2_per_capita_{max_jaar}'] - df_change[f'co2_per_capita_{min_jaar}']) / df_change[f'co2_per_capita_{min_jaar}']) * 100
    df_change['ren_diff'] = df_change[f'renewables_share_elec_{max_jaar}'] - df_change[f'renewables_share_elec_{min_jaar}']
    
    def categoriseer(row):
        if row['ren_diff'] > 5 and row['co2_pct_change'] < 0:
            return 'Groene daling (CO₂ daalt, groen stijgt)'
        elif row['ren_diff'] > 5 and row['co2_pct_change'] >= 0:
            return 'Stijging ondanks meer groene energie'
        elif row['ren_diff'] <= 5 and row['co2_pct_change'] < 0:
            return 'Daling zonder grote groene groei'
        else:
            return 'Beperkte verandering of stijging'

    df_change['Categorie'] = df_change.apply(categoriseer, axis=1)
    
    fig_walk = px.scatter(
        df_change,
        x="ren_diff",
        y="co2_pct_change",
        color="Categorie",
        hover_name="country",
        labels={
            "ren_diff": "Toename hernieuwbare stroom (%-punt)",
            "co2_pct_change": "Verandering CO₂ per inwoner (%)"
        }
    )
    fig_walk.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_walk.add_vline(x=5, line_dash="dash", line_color="gray")
    st.plotly_chart(fig_walk, use_container_width=True)

# Tab 3: Wereldkaart en Tijdreeks
with tab3:
    st.subheader(f"Aandeel hernieuwbare stroom per land ({selected_year})")
    
    fig_map = px.choropleth(
        df_year,
        locations="iso_code",
        color="renewables_share_elec",
        hover_name="country",
        color_continuous_scale="Greens",
        labels={"renewables_share_elec": "% Hernieuwbaar"}
    )
    st.plotly_chart(fig_map, use_container_width=True)
    
    st.divider()
    
    st.subheader("Verloop per land over de tijd")
    landen_lijst = sorted(df['country'].unique())
    gekozen_land = st.selectbox("Selecteer een land", landen_lijst, index=landen_lijst.index("Netherlands") if "Netherlands" in landen_lijst else 0)
    
    df_land = df[df['country'] == gekozen_land].sort_values("year")
    
    fig_line = px.line(
        df_land,
        x="year",
        y=["renewables_share_elec", "co2_per_capita"],
        labels={"value": "Waarde", "year": "Jaar", "variable": "Variabele"},
        title=f"Ontwikkeling in {gekozen_land}"
    )
    # Markering voor het Klimaatakkoord van Parijs
    fig_line.add_vline(x=2015, line_dash="dot", line_color="blue", annotation_text="Parijs-akkoord (2015)")
    st.plotly_chart(fig_line, use_container_width=True)

# Tab 4: Data & Verantwoording
with tab4:
    st.subheader("Dataverantwoording")
    st.write(
        "Voor dit dashboard zijn twee losse datasets gecombineerd via een **inner join** "
        "op de combinatie van landcode (ISO3) en het betreffende jaar."
    )
    
    st.write("**Aantallen rijen voor en na het samenvoegen:**")
    st.write(f"- CO₂-dataset (ruw): {stats['raw_co2']:,} rijen")
    st.write(f"- CO₂-dataset (na filteren op landcodes): {stats['clean_co2']:,} rijen")
    st.write(f"- Hernieuwbare energie dataset (ruw): {stats['raw_ren']:,} rijen")
    st.write(f"- Hernieuwbare energie dataset (na filteren op landcodes): {stats['clean_ren']:,} rijen")
    st.write(f"- **Uiteindelijke samengevoegde dataset:** {stats['merged']:,} rijen")
    
    st.write(
        "Toelichting uitval: Continenten en regio's (zoals 'World' of 'Europe') "
        "zijn gefilterd omdat deze geen landcode hebben. Zo voorkomen we dubbeltellingen."
    )
    
    st.divider()
    
    st.subheader("Bronvermelding")
    st.write("- **CO₂-gegevens:** Our World in Data (Annual CO₂ emissions)")
    st.write("- **Hernieuwbare energie:** Ember Climate / World Bank Indicators")
    st.write("- **Software:** Python, Streamlit, Pandas, Plotly Express")
    st.write("- *Noot: De CSV-bestanden zijn lokaal ingelezen vanuit de data/ map met toestemming van de docent.*")
    
    st.write("**Preview van de samengevoegde data:**")
    st.dataframe(df_year[['iso_code', 'country', 'year', 'co2_emissions', 'co2_per_capita', 'renewables_share_elec', 'gdp_per_capita']].head(15))
