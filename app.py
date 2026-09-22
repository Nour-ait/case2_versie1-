import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as bg

# 1. Pagina configuratie
st.set_page_config(
    page_title="Klimaatbeleid vs. Werkelijkheid",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Klimaatbeleid vs. Werkelijkheid")
st.subheader("De relatie tussen CO₂-uitstoot, hernieuwbare energie en economische welvaart per land")

# 2. Data ophalen en caching (API / Directe URL-download voor reproduceerbaarheid)
@st.cache_data
def load_data():
    # Via openbare Our World in Data / GitHub URLs (API-style data fetching)
    co2_url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
    energy_url = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
    
    # Als fallback lezen we de meegestuurde bestanden
    try:
        df_co2 = pd.read_csv(co2_url)
    except Exception:
        df_co2 = pd.read_csv("annual-co2-emissions-per-country.csv")
        
    try:
        df_energy = pd.read_csv(energy_url)
    except Exception:
        df_energy = pd.read_csv("renewable_energy_share_2000_2025.csv")
    
    return df_co2, df_energy

df_co2_raw, df_energy_raw = load_data()

# 3. Data-opschoning en Merging
# Normaliseren van kolomnamen
if 'Entity' in df_co2_raw.columns:
    df_co2_raw = df_co2_raw.rename(columns={'Entity': 'country', 'Code': 'iso_code', 'Year': 'year', 'Annual CO₂ emissions': 'co2'})

# Filter op geldige ISO-codes (landen, geen aggregaten/regio's)
df_co2_clean = df_co2_raw[df_co2_raw['iso_code'].notna() & (df_co2_raw['iso_code'].str.len() == 3)].copy()
df_energy_clean = df_energy_raw[df_energy_raw['iso_code'].notna() & (df_energy_raw['iso_code'].str.len() == 3)].copy()

rows_co2_before = len(df_co2_clean)
rows_energy_before = len(df_energy_clean)

# Merge op iso_code en year
df_merged = pd.merge(
    df_co2_clean,
    df_energy_clean,
    on=['iso_code', 'year'],
    how='inner',
    suffixes=('_co2', '_energy')
)

rows_after = len(df_merged)

# Afgeleide variabelen
if 'gdp' in df_merged.columns and 'population' in df_merged.columns:
    df_merged['gdp_per_capita'] = df_merged['gdp'] / df_merged['population']

if 'co2' in df_merged.columns and 'population' in df_merged.columns:
    df_merged['co2_per_capita'] = (df_merged['co2'] * 1000) / df_merged['population'] # in tonnen per persoon

# 4. Sidebar / Interactieve besturingselementen (EISEM)
st.sidebar.header("📊 Filteropties")

# REQUIREMENT 1: Slider
min_year = int(df_merged['year'].min())
max_year = int(df_merged['year'].max())
selected_year = st.sidebar.slider("Selecteer Jaar", min_value=2000, max_value=2023, value=2020)

# REQUIREMENT 2: Dropdown (Selectbox / Multiselect)
available_countries = sorted(df_merged['country_co2'].dropna().unique().tolist())
default_countries = [c for c in ['Netherlands', 'Germany', 'China', 'United States', 'Brazil', 'India'] if c in available_countries]
selected_countries = st.sidebar.multiselect("Selecteer Landen voor Vergelijking", available_countries, default=default_countries)

# REQUIREMENT 3: Checkbox
show_merge_info = st.sidebar.checkbox("Toon Merge & Dataverkenning Details", value=False)
log_scale = st.sidebar.checkbox("Gebruik Logaritmische Schaal voor BBP", value=True)

# 5. Dataverkenning sectie (indien aangevinkt)
if show_merge_info:
    st.info(f"""
    **Data Merge Informatie:**
    - Aantal rijen CO₂ dataset voor merge: `{rows_co2_before}`
    - Aantal rijen Energie dataset voor merge: `{rows_energy_before}`
    - Aantal rijen na `inner join` op `ISO3-code` + `Jaar`: `{rows_after}`
    """)

# Data filteren op basis van selectie
df_year = df_merged[df_merged['year'] == selected_year]
df_filtered_countries = df_merged[df_merged['country_co2'].isin(selected_countries)]

# 6. Tabs voor Hoofdanalyse (Aansluitend op je deelvragen)
tab1, tab2, tab3 = st.tabs(["🌍 Kuznets Curve (BBP vs CO₂)", "🔄 Energietransitie (Renewables vs CO₂)", "📈 Tijdreeks & Vergelijking"])

with tab1:
    st.header("1. Environmental Kuznets Curve")
    st.markdown("Onderzoek of CO₂-uitstoot per capita eerst stijgt met BBP per capita en daarna afvlakt of daalt.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        fig_kuznets = px.scatter(
            df_year.dropna(subset=['gdp_per_capita', 'co2_per_capita']),
            x='gdp_per_capita',
            y='co2_per_capita',
            size='population',
            color='country_co2',
            hover_name='country_co2',
            log_x=log_scale,
            title=f"BBP per Capita vs CO₂ per Capita ({selected_year})",
            labels={'gdp_per_capita': 'BBP per capita (USD)', 'co2_per_capita': 'CO₂ per capita (ton)'}
        )
        st.plotly_chart(fig_kuznets, use_container_width=True)
    
    with col2:
        st.write("**Inzicht:**")
        st.write("Rijke landen laten vaak een stabilisatie of daling zien in CO₂ per capita, terwijl snelgroeiende opkomende economieën een stijging vertonen.")

with tab2:
    st.header("2. Walk vs. Talk: Hernieuwbare Energie vs. Uitstoot")
    st.markdown("Verhouding tussen het aandeel hernieuwbare energie en CO₂-uitstoot.")
    
    ren_col = 'renewables_share_energy' if 'renewables_share_energy' in df_year.columns else 'renewables_share_elec'
    
    if ren_col in df_year.columns:
        fig_ren = px.scatter(
            df_year.dropna(subset=[ren_col, 'co2_per_capita']),
            x=ren_col,
            y='co2_per_capita',
            size='population',
            hover_name='country_co2',
            title=f"Aandeel Hernieuwbare Energie vs CO₂ per Capita ({selected_year})",
            labels={ren_col: 'Aandeel Hernieuwbare Energie (%)', 'co2_per_capita': 'CO₂ per capita (ton)'}
        )
        st.plotly_chart(fig_ren, use_container_width=True)

with tab3:
    st.header("3. Tijdreeksvergelijking gekozen landen")
    
    if len(selected_countries) > 0:
        fig_time = px.line(
            df_filtered_countries,
            x='year',
            y='co2_per_capita',
            color='country_co2',
            title="Verloop CO₂-uitstoot per capita over de tijd",
            labels={'co2_per_capita': 'CO₂ per capita (ton)', 'year': 'Jaar'}
        )
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.warning("Selecteer minimaal één land in de sidebar.")

# Bronvermelding volgens richtlijnen
st.caption("Bronvermelding code & data: Data afkomstig van Our World in Data (OWID) / Ember / Energy Institute via GitHub openbare datasets.")