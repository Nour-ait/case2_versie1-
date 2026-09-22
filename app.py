# ==============================================================================
# CASE 2: DASHBOARD KLIMAATBELEID VS. REALITEIT
# Bronvermelding code:
# - Streamlit Layout & State: https://docs.streamlit.io/
# - Plotly Express Scatter & Choropleth: https://plotly.com/python/plotly-express/
# - Pandas Data Transformation & Merging: https://pandas.pydata.org/docs/
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration (Bron: Streamlit API Reference)
st.set_page_config(
    page_title="Klimaatbeleid vs. Realiteit", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# 1. DATA VERKENNING, BEWERKING & CACHING (IDS Eisen)
# ------------------------------------------------------------------------------
@st.cache_data
def load_and_process_data():
    """
    Laadt de CSV bestanden (met toestemming i.p.v. openbare API),
    schoont de data op en voert een Inner Join uit.
    """
    # Bron data 1: Our World in Data (CO2 Emissions)
    df_co2 = pd.read_csv('data/annual-co2-emissions-per-country.csv')
    
    # Bron data 2: Renewable Energy Share Dataset (Ember / World Bank)
    df_ren = pd.read_csv('data/renewable_energy_share_2000_2025.csv')
    
    # Herbenoemen van kolommen voor consistentie
    df_co2.rename(columns={
        'Entity': 'country_co2', 
        'Code': 'iso_code', 
        'Year': 'year', 
        'Annual CO₂ emissions': 'co2_emissions'
    }, inplace=True)
    
    # Statistieken voor join-verantwoording
    raw_co2_rows = len(df_co2)
    raw_ren_rows = len(df_ren)
    
    # Dataverkenning & Schoonmaken: Filteren op geldige 3-letterige ISO-landcodes
    # Dit verwijdert geaggregeerde regio's zoals 'World', 'Europe', etc.
    df_co2_clean = df_co2[df_co2['iso_code'].notna() & (df_co2['iso_code'].str.len() == 3)].copy()
    df_ren_clean = df_ren[df_ren['iso_code'].notna() & (df_ren['iso_code'].str.len() == 3)].copy()
    
    # Inner Join op Unieke Sleutel: [iso_code, year]
    merged = pd.merge(
        df_co2_clean, 
        df_ren_clean, 
        on=['iso_code', 'year'], 
        how='inner'
    )
    
    # Afgeleide Variabelen (Feature Engineering)
    merged['gdp_per_capita'] = merged['gdp'] / merged['population']
    merged['co2_per_capita'] = merged['co2_emissions'] / merged['population'] # ton CO2 p.p.
    
    stats = {
        'raw_co2': raw_co2_rows,
        'raw_ren': raw_ren_rows,
        'clean_co2': len(df_co2_clean),
        'clean_ren': len(df_ren_clean),
        'merged': len(merged)
    }
    
    return merged, stats

# Data inladen met error handeling
try:
    df, stats = load_and_process_data()
except Exception as e:
    st.error(f"Fout bij het inladen van de data uit de data/ map: {e}")
    st.stop()

# ------------------------------------------------------------------------------
# 2. HEADER & ONDERZOEKSVRAAG
# ------------------------------------------------------------------------------
st.title("🌱 Klimaatbeleid vs. Werkelijkheid")
st.markdown("""
**Hoofdvraag:** *In hoeverre komt de transitie naar hernieuwbare energie daadwerkelijk tot uiting in een daling van de CO₂-uitstoot per capita, en welke rol speelt het inkomensniveau (GDP per capita) van een land hierin?*
""")

# ------------------------------------------------------------------------------
# 3. INTERACTIEVE SIDEBAR (Verplichte Controls: Slider, Dropdown, Checkbox)
# ------------------------------------------------------------------------------
st.sidebar.header("🎛️ Dashboard Filters")

# CONTROL 1: SLIDER (Verplicht)
selected_year = st.sidebar.slider(
    "Selecteer Jaar", 
    min_value=int(df['year'].min()), 
    max_value=int(df['year'].max()), 
    value=2021
)

# CONTROL 2: DROPDOWN / SELECTBOX (Verplicht)
income_groups = [
    "Alle Inkomensniveaus", 
    "Hoge Inkomens (> $20.000)", 
    "Midden Inkomens ($5.000 - $20.000)", 
    "Lage Inkomens (< $5.000)"
]
selected_income = st.sidebar.selectbox("Filter op Inkomensniveau", income_groups)

# CONTROL 3: CHECKBOX (Verplicht)
log_scale = st.sidebar.checkbox("Logaritmische Schaal op GDP-as", value=True)
show_annotations = st.sidebar.checkbox("Toon Visual Annotaties op Grafieken", value=True)

# Data filteren op basis van gekozen controls
df_year = df[df['year'] == selected_year].copy()

if selected_income == "Hoge Inkomens (> $20.000)":
    df_year = df_year[df_year['gdp_per_capita'] > 20000]
elif selected_income == "Midden Inkomens ($5.000 - $20.000)":
    df_year = df_year[(df_year['gdp_per_capita'] >= 5000) & (df_year['gdp_per_capita'] <= 20000)]
elif selected_income == "Lage Inkomens (< $5.000)":
    df_year = df_year[df_year['gdp_per_capita'] < 5000]

# KPIs bovenaan
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Aantal Landen in Filter", len(df_year))
kpi2.metric("Gem. Hernieuwbare Stroom", f"{df_year['renewables_share_elec'].mean():.1f}%")
kpi3.metric("Gem. CO₂ per capita", f"{df_year['co2_per_capita'].mean():.2f} ton")
kpi4.metric("Gem. GDP per capita", f"${df_year['gdp_per_capita'].mean():,.0f}" if not df_year['gdp_per_capita'].isna().all() else "N/B")

st.divider()

# ------------------------------------------------------------------------------
# 4. HOOFDSTRUCTURE TABS (Visual Analytics Storytelling)
# ------------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📉 Environmental Kuznets Curve", 
    "🏃 Walk vs. Talk Analyser", 
    "🗺️ Wereldkaart & Landen", 
    "📋 Data, Join & Bronnen"
])

# ------------------------------------------------------------------------------
# TAB 1: KUZNETS CURVE (Analyse & Annotaties)
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("1. Environmental Kuznets Curve (EKC)")
    st.write("Onderzoekt of de CO₂-uitstoot per capita eerst stijgt met economische welvaart (GDP) en na een omslagpunt afvlakt of daalt.")
    
    fig_ekc = px.scatter(
        df_year,
        x="gdp_per_capita",
        y="co2_per_capita",
        size="population",
        color="renewables_share_elec",
        hover_name="country",
        log_x=log_scale,
        color_continuous_scale=px.colors.sequential.Viridis,
        labels={
            "gdp_per_capita": "GDP per Capita (USD)", 
            "co2_per_capita": "CO₂ per Capita (ton)", 
            "renewables_share_elec": "% Hernieuwbare Stroom"
        },
        title=f"Relatie GDP per Capita vs. CO₂ per Capita ({selected_year})"
    )
    
    # Annotaties toevoegen (VA Rubric: Vergelijken en annoteren)
    if show_annotations and not df_year.empty:
        # Zoek hoogste uitstoter voor annotatie
        top_emitter = df_year.loc[df_year['co2_per_capita'].idxmax()]
        fig_ekc.add_annotation(
            x=top_emitter['gdp_per_capita'],
            y=top_emitter['co2_per_capita'],
            text=f"Hoogste uitstoot: {top_emitter['country']}",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red"
        )

    st.plotly_chart(fig_ekc, use_container_width=True)
    st.info("💡 **Inzicht:** Welvarende landen laten een geleidelijke ontkoppeling zien: hoge GDP-waarden combineren met een afnemende CO₂-voetafdruk door investeringen in hernieuwbare stroom.")

# ------------------------------------------------------------------------------
# TAB 2: WALK VS TALK CLASSIFICATIE
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("2. 'Walk' vs. 'Talk' Classificatie (2000 - 2021)")
    st.write("Analyseert welk deel van de landen daadwerkelijk CO₂-reductie realiseert ('Walk') versus landen waar groene energiegroei teniet wordt gedaan door economische uitbreiding ('Talk').")
    
    # Vergelijking 2000 vs 2021
    df_2000 = df[df['year'] == 2000][['iso_code', 'country', 'co2_per_capita', 'renewables_share_elec']]
    df_2021 = df[df['year'] == 2021][['iso_code', 'co2_per_capita', 'renewables_share_elec']]
    df_change = pd.merge(df_2000, df_2021, on='iso_code', suffixes=('_2000', '_2021'))
    
    df_change['co2_pct_change'] = ((df_change['co2_per_capita_2021'] - df_change['co2_per_capita_2000']) / df_change['co2_per_capita_2000']) * 100
    df_change['ren_diff'] = df_change['renewables_share_elec_2021'] - df_change['renewables_share_elec_2000']
    
    def classify_country(row):
        if row['ren_diff'] > 5 and row['co2_pct_change'] < 0:
            return 'Walk (Echte ontkoppeling)'
        elif row['ren_diff'] > 5 and row['co2_pct_change'] >= 0:
            return 'Talk (Groei overstijgt transitie)'
        elif row['ren_diff'] <= 5 and row['co2_pct_change'] < 0:
            return 'Passieve CO₂-daling'
        else:
            return 'Stagnatie / Stijging'

    df_change['Categorie'] = df_change.apply(classify_country, axis=1)
    
    fig_walk = px.scatter(
        df_change,
        x="ren_diff",
        y="co2_pct_change",
        color="Categorie",
        hover_name="country",
        labels={
            "ren_diff": "Toename Hernieuwbare Stroom (%-punt)", 
            "co2_pct_change": "Verandering CO₂ per Capita (%)"
        },
        title="Ontwikkeling Hernieuwbare Energie vs. CO₂-Daling (2000 vs 2021)"
    )
    
    # Referentielijnen en annotaties
    fig_walk.add_hline(y=0, line_dash="dash", line_color="red")
    fig_walk.add_vline(x=5, line_dash="dash", line_color="gray")
    
    if show_annotations:
        fig_walk.add_annotation(
            x=20, y=-40,
            text="Quadrant 'Walk': Stijging hernieuwbaar & daling CO₂",
            showarrow=False,
            font=dict(size=10, color="green")
        )

    st.plotly_chart(fig_walk, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 3: WERELDKAART & HISTORISCHE TREND
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("3. Geografische Spreiding & Landen Trend")
    
    fig_map = px.choropleth(
        df_year,
        locations="iso_code",
        color="renewables_share_elec",
        hover_name="country",
        color_continuous_scale=px.colors.sequential.Greens,
        title=f"Aandeel Hernieuwbare Elektriciteit per Land ({selected_year})"
    )
    st.plotly_chart(fig_map, use_container_width=True)
    
    st.divider()
    
    st.subheader("Historische Trend (2000 - 2022)")
    all_countries = sorted(df['country'].unique())
    default_index = all_countries.index("Netherlands") if "Netherlands" in all_countries else 0
    selected_country = st.selectbox("Selecteer een land voor de trendanalyse", all_countries, index=default_index)
    
    df_country = df[df['country'] == selected_country].sort_values("year")
    
    fig_line = px.line(
        df_country,
        x="year",
        y=["renewables_share_elec", "co2_per_capita"],
        title=f"Trendontwikkeling in {selected_country}",
        labels={"value": "Waarde", "year": "Jaar", "variable": "Variabele"}
    )
    
    if show_annotations:
        # Parijs Akkoord annotatie (2015)
        fig_line.add_vline(x=2015, line_dash="dot", line_color="blue")
        fig_line.add_annotation(
            x=2015, y=df_country['renewables_share_elec'].max() if not df_country.empty else 0,
            text="Klimaatakkoord van Parijs (2015)",
            showarrow=True,
            arrowhead=1
        )

    st.plotly_chart(fig_line, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 4: DATASET TRANSFORMATIE, JOIN VERANTWOORDING & BRONNEN
# ------------------------------------------------------------------------------
with tab4:
    st.subheader("4. Datatransformatie & Join Verantwoording")
    st.markdown("""
    **Toestemming Dataverzameling:**  
    *Er is expliciete toestemming verleend om de onderstaande gereinigde CSV-bestanden te gebruiken voor deze case in plaats van een live API-koppeling.*
    """)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        ### 📊 Dataverkenning & Join Statistieken
        * **CO₂ Dataset (Ruaw)**: `{stats['raw_co2']:,}` rijen
        * **CO₂ Dataset (Na ISO3 filter)**: `{stats['clean_co2']:,}` rijen
        * **Renewables Dataset (Ruw)**: `{stats['raw_ren']:,}` rijen
        * **Renewables Dataset (Na ISO3 filter)**: `{stats['clean_ren']:,}` rijen
        * **Koppelsleutel (Join Keys)**: `iso_code` + `year`
        * **Resultaat na Inner Join**: **`{stats['merged']:,}` rijen**
        """)
    
    with col_b:
        st.markdown("""
        ### 🔍 Valkuilcontrole
        Rijen die zijn afgevallen betreffen voornamelijk **geaggregeerde continenten en regio's** (zoals *World*, *European Union*, *OECD*) die geen officiële 3-letterige ISO3-code hebben. Dit voorkomt dubbeltelling in landelijke analyses.
        """)
        
    st.divider()
    
    st.subheader("📚 Bronvermelding (Verplicht)")
    st.markdown("""
    * **CO₂ Uitstoot Data**: Our World in Data (OWID) - *Annual CO₂ Emissions per country*.
    * **Hernieuwbare Energie Data**: Ember Climate / World Bank Development Indicators.
    * **Code Libraries**:
        * Streamlit (Dashboard UI) — [docs.streamlit.io](https://docs.streamlit.io)
        * Plotly Express (Visualisaties) — [plotly.com/python/plotly-express](https://plotly.com/python/plotly-express/)
        * Pandas (Data manipulatie) — [pandas.pydata.org](https://pandas.pydata.org/)
    """)
    
    st.subheader("Preview Samengevoegde Dataset")
    st.dataframe(df_year[['iso_code', 'country', 'year', 'co2_emissions', 'co2_per_capita', 'renewables_share_elec', 'gdp_per_capita']].head(25))
