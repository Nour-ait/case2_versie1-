# Zorg dat gdp_per_capita en co2_per_capita altijd worden aangemaakt
if 'gdp' in df_merged.columns and 'population' in df_merged.columns:
    df_merged['gdp_per_capita'] = df_merged['gdp'] / df_merged['population']
else:
    df_merged['gdp_per_capita'] = None

if 'co2' in df_merged.columns and 'population' in df_merged.columns:
    df_merged['co2_per_capita'] = (df_merged['co2'] * 1000) / df_merged['population']
else:
    df_merged['co2_per_capita'] = None