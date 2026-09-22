import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Klimaatbeleid vs. Realiteit", layout="wide")

st.title("🌱 Klimaatbeleid vs. Werkelijkheid")

@st.cache_data
def load_data():
    # Inlezen vanuit de data/ map
    df_co2 = pd.read_csv('data/annual-co2-emissions-per-country.csv')
    df_ren = pd.read_csv('data/renewable_energy_share_2000_2025.csv')
    
    # Kolommen hernoemen
    df_co2.rename(columns={
        'Entity': 'country_co2', 
        'Code': 'iso_code', 
        'Year': 'year', 
        'Annual CO₂ emissions': 'co2_emissions'
    }, inplace=True)
    
    # Filteren op geldige ISO3 codes (3 letters)
    df_co2_clean = df_co2[df_co2['iso_code'].notna() & (df_co2['iso_code'].str.len() == 3)]
    df_ren_clean = df_ren[df_ren['iso_code'].notna() & (df_ren['iso_code'].str.len() == 3)]
    
    # Samenvoegen op iso_code en jaar
    merged = pd.merge(df_co2_clean, df_ren_clean, on=['iso_code', 'year'], how='inner')
    
    # Afgeleide variabelen
    merged['gdp_per_capita'] = merged['gdp'] / merged['population']
    merged['co2_per_capita'] = merged['co2_emissions'] / merged['population']
    
    return merged

try:
    df = load_data()
    st.success("✅ Data succesvol ingeladen!")
    
    # Interatieve filters (Eisen uit de opdracht)
    st.sidebar.header("Filters")
    selected_year = st.sidebar.slider("Selecteer Jaar", min_value=2000, max_value=2022, value=2021)
    log_scale = st.sidebar.checkbox("Logaritmische Schaal op GDP", value=True)
    
    df_year = df[df['year'] == selected_year]
    
    # Visualisatie
    st.subheader(f"Relatie GDP per capita vs CO₂ per capita ({selected_year})")
    fig = px.scatter(
        df_year,
        x="gdp_per_capita",
        y="co2_per_capita",
        size="population",
        color="renewables_share_elec",
        hover_name="country",
        log_x=log_scale,
        labels={"gdp_per_capita": "GDP per Capita (USD)", "co2_per_capita": "CO₂ per capita (ton)"}
    )
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Er is een fout opgetreden bij het laden van de data: {e}")
