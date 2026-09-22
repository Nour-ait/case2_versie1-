import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration
st.set_page_config(page_title="Klimaatbeleid vs. Realiteit", layout="wide", initial_sidebar_state="expanded")

# Cache data loading for optimal performance
@st.cache_data
def load_and_process_data():
    # Read files from data/ directory
    df_co2 = pd.read_csv('data/annual-co2-emissions-per-country.csv')
    df_ren = pd.read_csv('data/renewable_energy_share_2000_2025.csv')
    
    # Rename CO2 dataset columns
    df_co2.rename(columns={
        'Entity': 'country_co2', 
        'Code': 'iso_code', 
        'Year': 'year', 
        'Annual CO₂ emissions': 'co2_emissions'
    }, inplace=True)
    
    # Filter for valid 3-letter ISO country codes
    df_co2_clean = df_co2[df_co2['iso_code'].notna() & (df_co2['iso_code'].str.len() == 3)].copy()
    df_ren_clean = df_ren[df_ren['iso_code'].notna() & (df_ren['iso_code'].str.len() == 3)].copy()
    
    # Inner join on iso_code and year
    merged = pd.merge(df_co2_clean, df_ren_clean, on=['iso_code', 'year'], how='inner')
    
    # Feature Engineering (Derived Variables)
    merged['gdp_per_capita'] = merged['gdp'] / merged['population']
    merged['co2_per_capita'] = merged['co2_emissions'] / merged['population'] # ton per capita
    
    return merged, len(df_co2_clean), len(df_ren_clean), len(merged)

# Load data with exception handling
try:
    df, co2_count, ren_count, merged_count = load_and_process_data()
except Exception as e:
    st.error(f"Fout bij inladen van bestanden uit data/: {e}")
    st.stop()

# Header Section
st.title("🌱 Klimaatbeleid vs. Werkelijkheid")
st.markdown("""
**Onderzoeksvraag:** *In hoeverre komt de transitie naar hernieuwbare energie daadwerkelijk tot uiting in dalende CO₂-uitstoot, en hoe verhoudt dit zich tot het inkomensniveau van landen?*
""")

# ---------------------------------------------------------
# SIDEBAR CONTROLS (Eisen: Slider, Checkbox, Dropdown)
# ---------------------------------------------------------
st.sidebar.header("🎛️ Dashboard Filters")

# 1. SLIDER (Required Control 1)
selected_year = st.sidebar.slider("Selecteer Jaar", min_value=2000, max_value=2022, value=2021)

# 2. DROPDOWN / SELECTBOX (Required Control 2)
income_groups = ["Alle Inkomensniveaus", "Hoge Inkomens (> $20.000)", "Midden Inkomens ($5.000 - $20.000)", "Lage Inkomens (< $5.000)"]
selected_income = st.sidebar.selectbox("Filter op Inkomensniveau", income_groups)

# 3. CHECKBOX (Required Control 3)
log_scale = st.sidebar.checkbox("Logaritmische Schaal op GDP-as", value=True)

# Data filtering based on controls
df_year = df[df['year'] == selected_year].copy()

if selected_income == "Hoge Inkomens (> $20.000)":
    df_year = df_year[df_year['gdp_per_capita'] > 20000]
elif selected_income == "Midden Inkomens ($5.000 - $20.000)":
    df_year = df_year[(df_year['gdp_per_capita'] >= 5000) & (df_year['gdp_per_capita'] <= 20000)]
elif selected_income == "Lage Inkomens (< $5.000)":
    df_year = df_year[df_year['gdp_per_capita'] < 5000]

# Key Performance Indicators (KPIs)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Aantal Landen in Filter", len(df_year))
m2.metric("Gem. Hernieuwbare Stroom", f"{df_year['renewables_share_elec'].mean():.1f}%")
m3.metric("Gem. CO₂ per capita", f"{df_year['co2_per_capita'].mean():.2f} ton")
m4.metric("Gem. GDP per capita", f"${df_year['gdp_per_capita'].mean():,.0f}" if not df_year['gdp_per_capita'].isna().all() else "N/B")

st.divider()

# ---------------------------------------------------------
# MAIN CONTENT TABS
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📉 Environmental Kuznets Curve", 
    "🏃 Walk vs. Talk Analyser", 
    "🗺️ Wereldkaart & Landen", 
    "📋 Data & Join Verantwoording"
])

# TAB 1: Kuznets Curve
with tab1:
    st.subheader("1. Environmental Kuznets Curve (EKC)")
    st.write("Onderzoekt of de CO₂-uitstoot per capita eerst stijgt met economische welvaart (GDP) en na een omslagpunt daalt bij hogere inkomens.")
    
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
            "co2_per_capita": "CO₂ per capita (ton)", 
            "renewables_share_elec": "% Hernieuwbare Stroom"
        },
        title=f"GDP per capita vs. CO₂ per capita ({selected_year})"
    )
    st.plotly_chart(fig_ekc, use_container_width=True)
    
    st.info("💡 **Inzicht:** Rijke landen vertonen een ontkoppeling: ze behouden een hoog GDP per capita maar dringen hun CO₂-uitstoot terug door een hoger aandeel hernieuwbare energie.")

# TAB 2: Walk vs Talk
with tab2:
    st.subheader("2. 'Walk' vs. 'Talk' (Ontwikkeling 2000 - 2021)")
    st.write("Vergelijkt de procentuele verandering in CO₂ per capita t.o.v. de toename van het aandeel hernieuwbare energie.")
    
    # Calculate baseline change 2000 -> 2021
    df_2000 = df[df['year'] == 2000][['iso_code', 'country', 'co2_per_capita', 'renewables_share_elec', 'gdp_per_capita']]
    df_2021 = df[df['year'] == 2021][['iso_code', 'co2_per_capita', 'renewables_share_elec', 'gdp_per_capita']]
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
            "co2_pct_change": "Verandering CO₂ per capita (%)"
        },
        title="Verandering tussen 2000 en 2021 per land"
    )
    fig_walk.add_hline(y=0, line_dash="dash", line_color="red")
    fig_walk.add_vline(x=5, line_dash="dash", line_color="gray")
    st.plotly_chart(fig_walk, use_container_width=True)

# TAB 3: Map & Time-Series
with tab3:
    st.subheader("3. Geografische Spreiding & Landen Trend")
    
    fig_map = px.choropleth(
        df_year,
        locations="iso_code",
        color="renewables_share_elec",
        hover_name="country",
        color_continuous_scale=px.colors.sequential.Greens,
        title=f"Aandeel hernieuwbare elektriciteit per land ({selected_year})"
    )
    st.plotly_chart(fig_map, use_container_width=True)
    
    st.divider()
    
    # Land specifieke tijdreeks
    st.subheader("Tijdreeks per Land (2000 - 2022)")
    all_countries = sorted(df['country'].unique())
    selected_country = st.selectbox("Selecteer een land voor de historische trend", all_countries, index=all_countries.index("Netherlands") if "Netherlands" in all_countries else 0)
    
    df_country = df[df['country'] == selected_country].sort_values("year")
    
    fig_line = px.line(
        df_country,
        x="year",
        y=["renewables_share_elec", "co2_per_capita"],
        title=f"Trendontwikkeling in {selected_country}",
        labels={"value": "Waarde", "year": "Jaar", "variable": "Variabele"}
    )
    st.plotly_chart(fig_line, use_container_width=True)

# TAB 4: Data & Join documentation
with tab4:
    st.subheader("4. Datatransformatie & Join Verantwoording")
    st.markdown(f"""
    Om reproduceerbaarheid en datakwaliteit te garanderen, is er een **Inner Join** uitgevoerd op de ISO3-landcode en het Jaar:
    
    * **CO₂ Emissions Dataset**: {co2_count:,} rijen (gefilterd op soevereine landen).
    * **Renewables Share Dataset**: {ren_count:,} rijen (gefilterd op soevereine landen).
    * **Resultaat ná Join**: **{merged_count:,} rijen** over de periode **2000 t/m 2022**.
    """)
    
    st.dataframe(df_year[['iso_code', 'country', 'year', 'co2_emissions', 'co2_per_capita', 'renewables_share_elec', 'gdp_per_capita']].head(20))
