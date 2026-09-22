import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    # Relatieve paden naar de data-map
    df_co2 = pd.read_csv('data/annual-co2-emissions-per-country.csv')
    df_ren = pd.read_csv('data/renewable_energy_share_2000_2025.csv')
    
    # Kolomhernoeming voor CO2 dataset
    df_co2.rename(columns={
        'Entity': 'country_co2', 
        'Code': 'iso_code', 
        'Year': 'year', 
        'Annual CO₂ emissions': 'co2_emissions'
    }, inplace=True)
    
    # Filteren op geldige ISO3-landcodes (3 letters)
    df_co2_clean = df_co2[df_co2['iso_code'].notna() & (df_co2['iso_code'].str.len() == 3)]
    df_ren_clean = df_ren[df_ren['iso_code'].notna() & (df_ren['iso_code'].str.len() == 3)]
    
    # Join/Merge op iso_code en year
    df = pd.merge(df_co2_clean, df_ren_clean, on=['iso_code', 'year'], how='inner')
    
    # Afgeleide variabelen
    df['gdp_per_capita'] = df['gdp'] / df['population']
    df['co2_per_capita'] = df['co2_emissions'] / df['population']
    
    return df

df = load_data()