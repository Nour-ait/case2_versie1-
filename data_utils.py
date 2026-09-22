"""
data_utils.py
=============

Alle dataverwerving en data-samenvoeging voor het dashboard.

Databronnen (allemaal opgehaald via een openbare bron/API in dit script,
NIET handmatig gedownload, zodat het volledig reproduceerbaar is):

1. OWID CO2-data
   https://github.com/owid/co2-data
   -> CO2-uitstoot (totaal, per capita, groei) per land per jaar.

2. OWID Energy-data
   https://github.com/owid/energy-data
   -> Aandeel hernieuwbare energie, GDP en bevolking per land per jaar.

3. World Bank API (echte JSON REST-API)
   https://api.worldbank.org/v2/country
   -> Inkomensclassificatie per land (High income / Upper middle income /
      Lower middle income / Low income), nodig om rijke, opkomende en
      arme landen te kunnen vergelijken.

Join-logica
-----------
Stap 1: CO2-data + Energy-data worden samengevoegd op de sleutel
        (iso_code, year). Dit zijn twee losse bestanden/bronnen, dus dit
        voldoet aan de eis "twee tabellen die niet uit hetzelfde bestand
        komen".
Stap 2: Het resultaat wordt verrijkt met de inkomensclassificatie van de
        Wereldbank op sleutel iso_code.

Bij elke join wordt gelogd hoeveel rijen er voor en na de join zijn, zoals
de opdracht vraagt.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import requests
import streamlit as st

CO2_URL = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
ENERGY_URL = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
WB_COUNTRY_API = "https://api.worldbank.org/v2/country?format=json&per_page=400"

CO2_COLUMNS = [
    "country",
    "iso_code",
    "year",
    "co2",                 # totale CO2-uitstoot, miljoen ton
    "co2_per_capita",      # ton per persoon
    "cumulative_co2",
    "co2_growth_prct",
    "share_global_co2",
]

ENERGY_COLUMNS = [
    "country",
    "iso_code",
    "year",
    "population",
    "gdp",
    "renewables_share_energy",
    "renewables_share_elec",
    "fossil_share_energy",
    "low_carbon_share_energy",
    "energy_per_capita",
]

# OWID gebruikt "OWID_XXX"-codes voor werelddelen/aggregaten (bv. OWID_WRL
# voor "World"). Die hebben geen echte ISO3-code en horen niet in een
# landenvergelijking thuis.
def _is_real_country(iso_code: pd.Series) -> pd.Series:
    return iso_code.notna() & ~iso_code.astype(str).str.startswith("OWID_")


@st.cache_data(ttl=60 * 60 * 24, show_spinner="CO2-data ophalen bij Our World in Data...")
def fetch_co2_data() -> pd.DataFrame:
    df = pd.read_csv(CO2_URL, usecols=lambda c: c in CO2_COLUMNS)
    df = df[_is_real_country(df["iso_code"])].copy()
    return df


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Energiedata ophalen bij Our World in Data...")
def fetch_energy_data() -> pd.DataFrame:
    df = pd.read_csv(ENERGY_URL, usecols=lambda c: c in ENERGY_COLUMNS)
    df = df[_is_real_country(df["iso_code"])].copy()
    return df


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Inkomensclassificatie ophalen bij de Wereldbank...")
def fetch_income_classification() -> pd.DataFrame:
    resp = requests.get(WB_COUNTRY_API, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    records = []
    for c in payload[1]:
        if c.get("region", {}).get("value") == "Aggregates":
            continue  # regio's/werelddeel-aggregaten overslaan, alleen landen
        income_group = c.get("incomeLevel", {}).get("value")
        if income_group in (None, "Aggregates", "Not classified"):
            continue
        records.append(
            {
                "iso_code": c["id"],  # World Bank 'id' = ISO3-code
                "region_wb": c.get("region", {}).get("value"),
                "income_group": income_group,
            }
        )
    return pd.DataFrame(records)


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Datasets combineren...")
def build_merged_dataset() -> tuple[pd.DataFrame, dict]:
    """Haalt alle bronnen op, voegt ze samen en geeft (data, join_log) terug.

    join_log bevat de rij-aantallen voor/na elke join, zodat dit in het
    dashboard (tab "Data & methode") getoond kan worden -- zoals de
    opdracht vraagt.
    """
    co2 = fetch_co2_data()
    energy = fetch_energy_data()
    income = fetch_income_classification()

    join_log = {
        "co2_rows_before": len(co2),
        "energy_rows_before": len(energy),
    }

    merged = pd.merge(
        co2,
        energy,
        on=["iso_code", "year"],
        how="inner",
        suffixes=("_co2", "_energy"),
    )
    join_log["merged_after_co2_energy"] = len(merged)

    # Kolomnamen opschonen na de merge (country komt in beide bronnen voor)
    merged["country"] = merged["country_co2"].combine_first(merged["country_energy"])
    merged = merged.drop(columns=["country_co2", "country_energy"])

    before_income = len(merged)
    merged = merged.merge(income, on="iso_code", how="left")
    join_log["rows_after_income_join"] = len(merged)
    join_log["rows_missing_income_group"] = int(merged["income_group"].isna().sum())
    assert before_income == len(merged), "Left join op iso_code mag geen rijen dupliceren"

    # Afgeleide variabelen
    merged["gdp_per_capita"] = merged["gdp"] / merged["population"]
    merged["gdp_per_capita"] = merged["gdp_per_capita"].replace([np.inf, -np.inf], np.nan)

    # Onmogelijke/onbetrouwbare waarden eruit filteren (dataverkenning-eis)
    merged.loc[merged["renewables_share_energy"] < 0, "renewables_share_energy"] = np.nan
    merged.loc[merged["renewables_share_energy"] > 100, "renewables_share_energy"] = np.nan
    merged.loc[merged["co2_per_capita"] < 0, "co2_per_capita"] = np.nan
    merged.loc[merged["gdp_per_capita"] <= 0, "gdp_per_capita"] = np.nan

    merged["income_group"] = merged["income_group"].fillna("Onbekend")

    return merged, join_log


def compute_decoupling_table(df: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    """Voor elk land: verandering in renewable-aandeel vs. verandering in
    CO2 per capita tussen start_year en end_year. Gebruikt om te bepalen
    welke landen echt "walk the talk" zijn en welke vooral "talk" blijven.
    """
    cols = ["iso_code", "country", "year", "renewables_share_energy", "co2_per_capita", "income_group"]
    sub = df[cols].dropna(subset=["renewables_share_energy", "co2_per_capita"])

    start = sub[sub["year"] == start_year].set_index("iso_code")
    end = sub[sub["year"] == end_year].set_index("iso_code")

    common = start.index.intersection(end.index)
    result = pd.DataFrame(
        {
            "country": start.loc[common, "country"],
            "income_group": start.loc[common, "income_group"],
            "renewables_share_start": start.loc[common, "renewables_share_energy"],
            "renewables_share_end": end.loc[common, "renewables_share_energy"],
            "co2_per_capita_start": start.loc[common, "co2_per_capita"],
            "co2_per_capita_end": end.loc[common, "co2_per_capita"],
        }
    )
    result["delta_renewables_pp"] = result["renewables_share_end"] - result["renewables_share_start"]
    result["delta_co2_per_capita"] = result["co2_per_capita_end"] - result["co2_per_capita_start"]

    def classify(row):
        if row["delta_renewables_pp"] > 1 and row["delta_co2_per_capita"] < 0:
            return "Walk (ontkoppeling)"
        if row["delta_renewables_pp"] > 1 and row["delta_co2_per_capita"] >= 0:
            return "Talk (beleid zonder resultaat)"
        if row["delta_renewables_pp"] <= 1 and row["delta_co2_per_capita"] < 0:
            return "Daling zonder renewable-groei"
        return "Geen verandering / stilstand"

    result["categorie"] = result.apply(classify, axis=1)
    return result.reset_index().rename(columns={"iso_code": "iso_code"})
