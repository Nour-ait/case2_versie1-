"""
app.py
======
Klimaatbeleid vs. werkelijkheid: CO2-uitstoot, hernieuwbare energie en
economische welvaart per land.

Start lokaal met:
    streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_utils import build_merged_dataset, compute_decoupling_table

st.set_page_config(
    page_title="Klimaatbeleid vs. werkelijkheid",
    page_icon="🌍",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Data laden (gecachet in data_utils, dus dit is snel na de eerste keer)
# ---------------------------------------------------------------------------
with st.spinner("Data laden..."):
    data, join_log = build_merged_dataset()

MIN_YEAR = int(data["year"].min())
MAX_YEAR = int(data["year"].max())
INCOME_ORDER = ["High income", "Upper middle income", "Lower middle income", "Low income", "Onbekend"]
INCOME_COLORS = {
    "High income": "#2E7D32",
    "Upper middle income": "#F9A825",
    "Lower middle income": "#EF6C00",
    "Low income": "#C62828",
    "Onbekend": "#9E9E9E",
}

st.title("🌍 Klimaatbeleid vs. werkelijkheid")
st.markdown(
    "In hoeverre komt de transitie naar hernieuwbare energie daadwerkelijk tot uiting in "
    "dalende CO₂-uitstoot, en hoe verhoudt dit zich tot het inkomensniveau van landen?"
)

tab_map, tab_series, tab_ekc, tab_decouple, tab_data = st.tabs(
    ["🗺️ Wereldkaart", "📈 Land over tijd", "💰 GDP vs CO₂", "🚶 Walk vs Talk", "🔍 Data & methode"]
)

# ---------------------------------------------------------------------------
# TAB 1: Wereldkaart
# ---------------------------------------------------------------------------
with tab_map:
    st.subheader("Wereldkaart per jaar")

    col_a, col_b = st.columns([1, 3])
    with col_a:
        map_metric = st.selectbox(  # dropdown
            "Indicator",
            options=["co2_per_capita", "renewables_share_energy", "gdp_per_capita"],
            format_func=lambda x: {
                "co2_per_capita": "CO₂-uitstoot per capita (ton)",
                "renewables_share_energy": "Aandeel hernieuwbare energie (%)",
                "gdp_per_capita": "GDP per capita ($)",
            }[x],
            key="map_metric",
        )
        map_year = st.slider("Jaar", MIN_YEAR, MAX_YEAR, value=MAX_YEAR, key="map_year")  # slider

    map_df = data[data["year"] == map_year].dropna(subset=[map_metric])
    fig_map = px.choropleth(
        map_df,
        locations="iso_code",
        color=map_metric,
        hover_name="country",
        color_continuous_scale="RdYlGn_r" if map_metric != "renewables_share_energy" else "RdYlGn",
        projection="natural earth",
        title=f"{map_year}",
    )
    fig_map.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=520)
    st.plotly_chart(fig_map, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 2: Tijdreeks per land
# ---------------------------------------------------------------------------
with tab_series:
    st.subheader("CO₂-uitstoot en hernieuwbare energie door de tijd")

    countries_sorted = sorted(data["country"].dropna().unique())
    default_idx = countries_sorted.index("Netherlands") if "Netherlands" in countries_sorted else 0

    col_a, col_b = st.columns([1, 1])
    with col_a:
        country = st.selectbox("Land", countries_sorted, index=default_idx, key="series_country")  # dropdown
    with col_b:
        log_scale = st.checkbox("Logaritmische schaal voor CO₂", value=False, key="series_log")  # checkbox

    year_range = st.slider(  # slider
        "Periode", MIN_YEAR, MAX_YEAR, value=(max(MIN_YEAR, 2000), MAX_YEAR), key="series_years"
    )

    c_df = data[(data["country"] == country) & data["year"].between(*year_range)].sort_values("year")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=c_df["year"], y=c_df["co2_per_capita"], name="CO₂ per capita (ton)",
            line=dict(color="#C62828"), yaxis="y1",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=c_df["year"], y=c_df["renewables_share_energy"], name="Aandeel hernieuwbaar (%)",
            line=dict(color="#2E7D32"), yaxis="y2",
        )
    )
    fig.update_layout(
        title=f"{country}: CO₂ per capita vs. aandeel hernieuwbare energie",
        xaxis=dict(title="Jaar"),
        yaxis=dict(title="CO₂ per capita (ton)", type="log" if log_scale else "linear"),
        yaxis2=dict(title="Aandeel hernieuwbaar (%)", overlaying="y", side="right", range=[0, 100]),
        legend=dict(orientation="h", y=1.12),
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

    if c_df.empty:
        st.info("Geen data voor dit land in deze periode.")

# ---------------------------------------------------------------------------
# TAB 3: GDP vs CO2 (Environmental Kuznets Curve)
# ---------------------------------------------------------------------------
with tab_ekc:
    st.subheader("Environmental Kuznets Curve: GDP per capita vs. CO₂ per capita")

    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        ekc_year = st.slider("Jaar", MIN_YEAR, MAX_YEAR, value=MAX_YEAR, key="ekc_year")  # slider
    with col_b:
        income_filter = st.multiselect(
            "Inkomensgroep", options=INCOME_ORDER, default=INCOME_ORDER, key="ekc_income"
        )
    with col_c:
        log_x = st.checkbox("Logaritmische x-as (GDP)", value=True, key="ekc_logx")  # checkbox

    ekc_df = data[
        (data["year"] == ekc_year)
        & data["income_group"].isin(income_filter)
    ].dropna(subset=["gdp_per_capita", "co2_per_capita", "population"])

    fig_ekc = px.scatter(
        ekc_df,
        x="gdp_per_capita",
        y="co2_per_capita",
        size="population",
        color="income_group",
        color_discrete_map=INCOME_COLORS,
        hover_name="country",
        log_x=log_x,
        size_max=45,
        labels={"gdp_per_capita": "GDP per capita ($)", "co2_per_capita": "CO₂ per capita (ton)"},
        title=f"GDP per capita vs. CO₂ per capita ({ekc_year})",
    )

    # Kwadratische trendlijn (proxy voor een Kuznets-curve) over alle punten
    fit_df = ekc_df.dropna(subset=["gdp_per_capita", "co2_per_capita"])
    if len(fit_df) > 10:
        x = np.log10(fit_df["gdp_per_capita"]) if log_x else fit_df["gdp_per_capita"]
        coeffs = np.polyfit(x, fit_df["co2_per_capita"], 2)
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = np.polyval(coeffs, x_line)
        x_line_plot = 10 ** x_line if log_x else x_line
        fig_ekc.add_trace(
            go.Scatter(
                x=x_line_plot, y=y_line, mode="lines", name="Kwadratisch fit (EKC-proxy)",
                line=dict(color="black", dash="dash"),
            )
        )
    fig_ekc.update_layout(height=550)
    st.plotly_chart(fig_ekc, use_container_width=True)
    st.caption(
        "De stippellijn is een kwadratische regressie door de data, als indicatieve proxy voor "
        "een Environmental Kuznets Curve (stijging gevolgd door afvlakking/daling). "
        "Bolgrootte = bevolkingsomvang."
    )

# ---------------------------------------------------------------------------
# TAB 4: Walk vs Talk
# ---------------------------------------------------------------------------
with tab_decouple:
    st.subheader("Welke landen laten écht ontkoppeling zien?")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        d_start, d_end = st.slider(  # slider
            "Vergelijk periode", MIN_YEAR, MAX_YEAR, value=(2010, min(2023, MAX_YEAR)), key="decouple_years"
        )
    with col_b:
        only_growing_renewables = st.checkbox(  # checkbox
            "Toon alleen landen met groeiend aandeel hernieuwbaar", value=False, key="decouple_filter"
        )

    decouple_df = compute_decoupling_table(data, d_start, d_end)
    if only_growing_renewables:
        decouple_df = decouple_df[decouple_df["delta_renewables_pp"] > 0]

    fig_dec = px.scatter(
        decouple_df,
        x="delta_renewables_pp",
        y="delta_co2_per_capita",
        color="categorie",
        hover_name="country",
        labels={
            "delta_renewables_pp": "Verandering aandeel hernieuwbaar (procentpunt)",
            "delta_co2_per_capita": "Verandering CO₂ per capita (ton)",
        },
        title=f"Verandering {d_start}–{d_end}: hernieuwbaar-aandeel vs. CO₂ per capita",
    )
    fig_dec.add_hline(y=0, line_dash="dot", line_color="gray")
    fig_dec.add_vline(x=0, line_dash="dot", line_color="gray")
    fig_dec.update_layout(height=520)
    st.plotly_chart(fig_dec, use_container_width=True)

    st.markdown("**Ranking — grootste dalers in CO₂ per capita mét renewable-groei ('walk the talk'):**")
    walkers = decouple_df[decouple_df["categorie"] == "Walk (ontkoppeling)"].sort_values("delta_co2_per_capita")
    st.dataframe(
        walkers[["country", "income_group", "delta_renewables_pp", "delta_co2_per_capita"]].head(15),
        use_container_width=True,
        hide_index=True,
    )

# ---------------------------------------------------------------------------
# TAB 5: Data & methode
# ---------------------------------------------------------------------------
with tab_data:
    st.subheader("Dataverkenning en methodeverantwoording")

    st.markdown("### Bronnen")
    st.markdown(
        "- **CO2-uitstoot per land** — `annual-co2-emissions-per-country.csv` (Our World in Data / "
        "Global Carbon Project), opgehaald via een publieke URL met `requests`/`pandas.read_csv`.\n"
        "- **Hernieuwbare energie, GDP en bevolking** — `renewable_energy_share_2000_2025.csv` "
        "(Our World in Data / Ember), opgehaald via dezelfde methode.\n"
        "- **Inkomensgroep** wordt zelf berekend uit GDP per capita met de Wereldbank-drempels "
        "(High / Upper middle / Lower middle / Low income) — geen aparte API nodig hiervoor."
    )

    st.markdown("### Join-logging")
    st.json(join_log)
    st.caption(
        "De twee bestanden zijn samengevoegd op sleutel (iso_code, year) met een inner join. "
        "Het CO2-bestand loopt tot en met "
        f"{join_log['co2_laatste_jaar']}, dus de samengevoegde data stopt automatisch bij "
        f"{join_log['laatste_jaar_in_gecombineerde_data']} — ook al bevat het energie-bestand "
        f"nieuwere jaren tot {join_log['energy_laatste_jaar']}."
    )

    st.markdown("### Ontbrekende waarden (na opschonen)")
    missing = data[["co2_per_capita", "renewables_share_energy", "gdp_per_capita", "income_group"]].isna().mean() * 100
    st.dataframe(missing.round(1).rename("% ontbrekend").to_frame(), use_container_width=True)

    st.markdown("### Beschrijvende statistiek")
    st.dataframe(
        data[["co2_per_capita", "renewables_share_energy", "gdp_per_capita"]].describe().round(2),
        use_container_width=True,
    )

    st.markdown("### Wat we hebben opgeschoond")
    st.markdown(
        "- Regio's/werelddeel-aggregaten zonder landcode (zoals 'World', 'Africa', 'European Union', "
        "'High-income countries') zijn verwijderd uit beide bestanden — dit zijn geen landen en zouden "
        "de landenvergelijking vervuilen (dubbeltellingen).\n"
        "- `renewables_share_energy` buiten het bereik 0–100% is als ontbrekend gemarkeerd (onmogelijke waarde).\n"
        "- Negatieve `co2_per_capita` en `gdp_per_capita` (of nul/negatieve GDP) zijn als ontbrekend gemarkeerd.\n"
        "- De dataset stopt bij het laatste jaar waarin *beide* bestanden data hebben "
        f"({join_log['laatste_jaar_in_gecombineerde_data']}) — recentere renewable-cijfers zonder "
        "bijbehorende CO2-cijfers worden dus niet getoond, om geen appels met peren te vergelijken."
    )

    with st.expander("Voorbeeld van de samengevoegde data"):
        st.dataframe(data.sample(min(20, len(data))), use_container_width=True)
