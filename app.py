import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================================
# 1. PAGINA CONFIGURATIE
# ==========================================
st.set_page_config(
    page_title="Klimaatbeleid vs. Werkelijkheid",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Klimaatbeleid vs. Werkelijkheid")
st.subheader("De relatie tussen CO₂-uitstoot, hernieuwbare energie en economische welvaart per land")

# ==========================================
# 2. DATA OPHALEN EN CACHING (@st.cache_data)
# ==========================================
@st.cache_data
def load_and_preprocess_data():
    # 1. CO2 Dataset inladen (met fallback)
    co2_path_local = "annual-co2-emissions-per-country.csv"
    co2_path_online = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
    
    if os.path.exists(co2_path_local):
        df_co2 = pd.read_csv(co2_path_local)
    else:
        df_co2 = pd.read_csv(co2_path_online)

    # 2. Renewable Energy Dataset inladen (met fallback)
    energy_path_local = "renewable_energy_share_2000_2025.csv"
    energy_path_online = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
    
    if os.path.exists(energy_path_local):
        df_energy = pd.read_csv(energy_path_local)
    else:
        df_energy = pd.read_csv(energy_path_online)

    # 3. Kolomnamen hernoemen naar een uniforme structuur
    df_co2 = df_co2.rename(columns={
        'Entity': 'country',
        'Code': 'iso_code',
        'Year': 'year',
        'Annual CO₂ emissions': 'co2'
    })

    # 4. Filteren op geldige landcodes (ISO3-codes van exact 3 letters opschonen)
    df_co2_clean = df_co2[df_co2['iso_code'].notna() & (df_co2['iso_code'].str.len() == 3)].copy()
    df_energy_clean = df_energy[df_energy['iso_code'].notna() & (df_energy['iso_code'].str.len() == 3)].copy()

    rows_co2_before = len(df_co2_clean)
    rows_energy_before = len(df_energy_clean)

    # 5. DATA MERGE: Inner join op iso_code + year
    df_merged = pd.merge(
        df_co2_clean,
        df_energy_clean,
        on=['iso_code', 'year'],
        how='inner',
        suffixes=('_co2', '_energy')
    )

    rows_after = len(df_merged)

    # 6. Afgeleide variabelen berekenen (met robuuste checks tegen NaNs en missende kolommen)
    # BBP per capita
    if 'gdp' in df_merged.columns and 'population' in df_merged.columns:
        df_merged['gdp_per_capita'] = df_merged['gdp'] / df_merged['population']
    else:
        df_merged['gdp_per_capita'] = None

    # CO2 per capita (in tonnen per persoon)
    if 'co2' in df_merged.columns and 'population' in df_merged.columns:
        df_merged['co2_per_capita'] = (df_merged['co2'] * 1000) / df_merged['population']
    elif 'co2_per_capita' not in df_merged.columns:
        df_merged['co2_per_capita'] = None

    merge_stats = {
        'rows_co2_before': rows_co2_before,
        'rows_energy_before': rows_energy_before,
        'rows_after': rows_after
    }

    return df_merged, merge_stats

# Laad de verwerkte dataset en statistieken
df_merged, merge_stats = load_and_preprocess_data()

# ==========================================
# 3. SIDEBAR / INTERACTIEVE CONTROLS (EISEM)
# ==========================================
st.sidebar.header("📊 Filteropties")

# REQUIREMENT 1: SLIDER (Jaar selecteren)
available_years = sorted(df_merged['year'].dropna().unique().astype(int).tolist())
min_yr, max_yr = min(available_years), max(available_years)
selected_year = st.sidebar.slider("Selecteer Jaar", min_value=min_yr, max_value=max_yr, value=2020)

# REQUIREMENT 2: DROPDOWN / MULTISELECT (Landen selecteren)
available_countries = sorted(df_merged['country_co2'].dropna().unique().tolist())
default_selection = [c for c in ['Netherlands', 'Germany', 'China', 'United States', 'Brazil', 'India'] if c in available_countries]
selected_countries = st.sidebar.multiselect("Selecteer Landen voor Vergelijking", available_countries, default=default_selection)

# REQUIREMENT 3: CHECKBOXEN (Verkenning & Logaritmische Schaal)
show_merge_info = st.sidebar.checkbox("Toon Merge & Dataverkenning Details", value=True)
log_scale_gdp = st.sidebar.checkbox("Gebruik Logaritmische Schaal voor BBP", value=True)

# Filter datasets op basis van gemaakte keuzes
df_year = df_merged[df_merged['year'] == selected_year].copy()
df_countries = df_merged[df_merged['country_co2'].isin(selected_countries)].copy()

# ==========================================
# 4. DATAVERKENNING & MERGE INFO SECTIE
# ==========================================
if show_merge_info:
    st.info(f"""
    **🔍 Data Merge & Verkenning Verantwoording:**
    - **Aantal rijen CO₂ Dataset (voor merge):** `{merge_stats['rows_co2_before']:,}`
    - **Aantal rijen Energie Dataset (voor merge):** `{merge_stats['rows_energy_before']:,}`
    - **Sleutel voor samenvoegen:** `iso_code` (ISO3-landcode) + `year` (Jaar)
    - **Aantal rijen na Inner Join:** `{merge_stats['rows_after']:,}`
    - **Aantal unieke landen in samengevoegde set:** `{df_merged['country_co2'].nunique()}`
    """)

# ==========================================
# 5. HOOFDANALYSE (TABS MET VISUALISATIES)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🌍 Kuznets Curve (BBP vs CO₂)", 
    "🔄 Energietransitie (Renewables vs CO₂)", 
    "📈 Tijdreeks per Land",
    "📋 Datatabel"
])

# --- TAB 1: ENVIRONMENTAL KUZNETS CURVE ---
with tab1:
    st.header("1. Environmental Kuznets Curve (EKC)")
    st.markdown("""
    *Onderzoeksvraag-focus:* Stijgt de CO₂-uitstoot per capita mee met de economische groei (BBP) tot een bepaald welvaartsniveau, om daarna af te vlakken of te dalen?
    """)
    
    # Check of de nodige kolommen data bevatten
    df_kuznets = df_year.dropna(subset=['gdp_per_capita', 'co2_per_capita'])
    
    if not df_kuznets.empty:
        col1, col2 = st.columns([3, 1])
        with col1:
            fig_kuznets = px.scatter(
                df_kuznets,
                x='gdp_per_capita',
                y='co2_per_capita',
                size='population' if 'population' in df_kuznets.columns else None,
                color='country_co2',
                hover_name='country_co2',
                log_x=log_scale_gdp,
                title=f"BBP per Capita vs CO₂ per Capita ({selected_year})",
                labels={
                    'gdp_per_capita': 'BBP per Capita (USD)',
                    'co2_per_capita': 'CO₂ per Capita (Ton/persoon)',
                    'country_co2': 'Land'
                }
            )
            fig_kuznets.update_layout(showlegend=False)
            st.plotly_chart(fig_kuznets, use_container_width=True)
            
        with col2:
            st.markdown("### 💡 Inzichten")
            st.write("""
            - **Armere en opkomende landen** vertonen vaak een stijging in CO₂ bij economische groei.
            - **Ontwikkelde economieën** (hoge BBP per capita) laten in veel gevallen een stabilisatie of daling zien. Dit ondersteunt het idee van een Environmental Kuznets Curve.
            """)
    else:
        st.warning(f"Geen gekoppelde BBP- en CO₂-data beschikbaar voor het gekozen jaar ({selected_year}). Probeer een ander jaar op de slider.")

# --- TAB 2: RENEWABLES VS CO2 ---
with tab2:
    st.header("2. Walk vs. Talk: Hernieuwbare Energie vs. Uitstoot")
    st.markdown("""
    *Onderzoeksvraag-focus:* Leidt een hoger aandeel hernieuwbare energie direct tot een lagere CO₂-uitstoot per persoon?
    """)
    
    # Bepaal welke hernieuwbare energie-kolom beschikbaar is
    ren_col = None
    if 'renewables_share_energy' in df_year.columns and df_year['renewables_share_energy'].notna().sum() > 0:
        ren_col = 'renewables_share_energy'
        label_ren = 'Aandeel Hernieuwbare Energie in Totale Energiemix (%)'
    elif 'renewables_share_elec' in df_year.columns and df_year['renewables_share_elec'].notna().sum() > 0:
        ren_col = 'renewables_share_elec'
        label_ren = 'Aandeel Hernieuwbare Elektriciteit (%)'

    if ren_col:
        df_ren = df_year.dropna(subset=[ren_col, 'co2_per_capita'])
        
        if not df_ren.empty:
            fig_ren = px.scatter(
                df_ren,
                x=ren_col,
                y='co2_per_capita',
                size='population' if 'population' in df_ren.columns else None,
                color='country_co2',
                hover_name='country_co2',
                title=f"Hernieuwbaar Aandeel vs. CO₂ per Capita ({selected_year})",
                labels={
                    ren_col: label_ren,
                    'co2_per_capita': 'CO₂ per Capita (Ton/persoon)',
                    'country_co2': 'Land'
                }
            )
            fig_ren.update_layout(showlegend=False)
            st.plotly_chart(fig_ren, use_container_width=True)
        else:
            st.warning(f"Geen data over hernieuwbare energie en CO₂ gevonden voor {selected_year}.")
    else:
        st.error("Geen geschikte hernieuwbare energie-kolom gevonden in de dataset.")

# --- TAB 3: TIJDREEKSVERGELIJKING ---
with tab3:
    st.header("3. Tijdreeksvergelijking van Selectie")
    st.markdown("Vergelijk de ontwikkeling van CO₂-uitstoot per capita over de tijd voor de geselecteerde landen.")
    
    if len(selected_countries) > 0:
        df_time = df_countries.dropna(subset=['co2_per_capita'])
        
        fig_time = px.line(
            df_time,
            x='year',
            y='co2_per_capita',
            color='country_co2',
            markers=True,
            title="Verloop CO₂-uitstoot per capita (2000 - Heden)",
            labels={
                'co2_per_capita': 'CO₂ per Capita (Ton/persoon)',
                'year': 'Jaar',
                'country_co2': 'Land'
            }
        )
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.warning("⚠️ Selecteer minimaal één land in het linkermenu (multiselect) om de tijdreeks te bekijken.")

# --- TAB 4: RAW DATA & EXPORT ---
with tab4:
    st.header("4. Gefilterde Datatabel")
    st.markdown("Bekijk de werkelijke cijfers achter de grafieken voor het geselecteerde jaar.")
    
    display_cols = [c for c in ['country_co2', 'iso_code', 'year', 'co2', 'gdp_per_capita', 'co2_per_capita', 'renewables_share_energy', 'renewables_share_elec'] if c in df_year.columns]
    st.dataframe(df_year[display_cols], use_container_width=True)

# ==========================================
# 6. BRONVERMELDING & FOOTER
# ==========================================
st.markdown("---")
st.caption("""
**Bronvermelding:**  
- CO₂ Dataset: *Our World in Data (OWID)*  
- Renewable Energy Dataset: *Our World in Data / Ember / Energy Institute*  
- Dashboard framework: *Streamlit & Plotly Express*
""")
