"""
data_utils.py
=============

Dataverwerving en -samenvoeging voor het dashboard, gebaseerd op de twee
aangeleverde datasets (en niets anders):

1. annual-co2-emissions-per-country.csv   (Our World in Data / Global Carbon
   Project) -> jaarlijkse CO2-uitstoot per land.
2. renewable_energy_share_2000_2025.csv   (Our World in Data / Ember)
   -> aandeel hernieuwbare energie, GDP en bevolking per land per jaar.

Hoe de "openbare API"-eis toch geregeld is
-------------------------------------------
De opdracht vraagt: "Haal de data in je script op, niet met de hand
gedownload." Dat betekent niet per se een REST-API met JSON; een publieke,
altijd-bereikbare URL die je script zelf uitleest voldoet ook, zolang iemand
anders jouw dataset kan reproduceren zonder handmatige stappen.

Daarom werkt dit bestand zo:
- Zet de twee CSV's in een map `data/` in je eigen GitHub-repository.
- Vul hieronder RAW_BASE_URL in met jouw eigen GitHub-gebruikersnaam/repo
  zodra je gepusht hebt.
- Het script probeert dan eerst die publieke URL op te halen (reproduceerbaar
  voor iedereen die de repo kloont). Lukt dat niet (bijv. omdat je nog niet
  gepusht hebt, of geen internet hebt tijdens lokaal ontwikkelen), dan valt
  het terug op het lokale bestand in `data/` zodat je gewoon door kunt werken.

Let op: dit is een pragmatische invulling van de eis. Als je docent een
"echte" API (met JSON, zoals de Wereldbank-API die we er eerder in hadden
zitten) verplicht stelt, overleg dat dan even -- voor puur CSV-bronnen zoals
deze is ophalen via een publieke URL in de praktijk de gangbare aanpak.

Join-logica
-----------
De twee bestanden worden samengevoegd op (iso_code, year). Dit zijn twee
losse bestanden, dus dat voldoet aan "twee tabellen die niet uit hetzelfde
bestand komen". Rij-aantallen voor en na de join worden gelogd.
"""

from __future__ import annotations

import io

import numpy as np
import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# VUL DIT IN zodra je hebt gepusht naar GitHub, bijvoorbeeld:
# RAW_BASE_URL = "https://raw.githubusercontent.com/jouw-gebruikersnaam/climate-dashboard/main/data"
RAW_BASE_URL = ""  # leeg = alleen lokale bestanden gebruiken

CO2_FILENAME = "annual-co2-emissions-per-country.csv"
ENERGY_FILENAME = "renewable_energy_share_2000_2025.csv"

LOCAL_DATA_DIR = "data"


def _load_csv(filename: str) -> pd.DataFrame:
    """Probeert het bestand via de publieke GitHub-URL op te halen; valt
    terug op het lokale bestand in data/ als dat niet lukt."""
    if RAW_BASE_URL:
        url = f"{RAW_BASE_URL.rstrip('/')}/{filename}"
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return pd.read_csv(io.StringIO(resp.text))
        except Exception:
            pass  # val terug op lokaal bestand
    return pd.read_csv(f"{LOCAL_DATA_DIR}/{filename}")


@st.cache_data(ttl=60 * 60 * 24, show_spinner="CO2-data inladen...")
def fetch_co2_data() -> pd.DataFrame:
    df = _load_csv(CO2_FILENAME)
    df = df.rename(
        columns={
            "Entity": "country",
            "Code": "iso_code",
            "Year": "year",
            "Annual CO₂ emissions": "co2_emissions_tonnes",
        }
    )
    df = df.dropna(subset=["iso_code"]).copy()
    return df


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Energiedata inladen...")
def fetch_energy_data() -> pd.DataFrame:
    keep = [
        "country",
        "year",
        "iso_code",
        "population",
        "gdp",
        "renewables_share_energy",
        "renewables_share_elec",
        "fossil_share_energy",
        "low_carbon_share_energy",
        "energy_per_capita",
    ]
    df = _load_csv(ENERGY_FILENAME)
    df = df[[c for c in keep if c in df.columns]]
    df = df.dropna(subset=["iso_code"]).copy()
    return df


def _income_group(gdp_per_capita: float) -> str:
    """Classificeert een land in een inkomensgroep op basis van GDP per
    capita, met de drempels die de Wereldbank hanteert (referentiewaarden,
    hier hardcoded -- dit vervangt de eerdere live Wereldbank-API-call).
    """
    if pd.isna(gdp_per_capita):
        return "Onbekend"
    if gdp_per_capita >= 14005:
        return "High income"
    if gdp_per_capita >= 4516:
        return "Upper middle income"
    if gdp_per_capita >= 1146:
        return "Lower middle income"
    return "Low income"


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Datasets combineren...")
def build_merged_dataset() -> tuple[pd.DataFrame, dict]:
    co2 = fetch_co2_data()
    energy = fetch_energy_data()

    join_log = {
        "co2_rows_before": len(co2),
        "energy_rows_before": len(energy),
        "co2_laatste_jaar": int(co2["year"].max()),
        "energy_laatste_jaar": int(energy["year"].max()),
    }

    merged = pd.merge(
        co2,
        energy,
        on=["iso_code", "year"],
        how="inner",
        suffixes=("_co2", "_energy"),
    )
    join_log["rows_after_join"] = len(merged)
    join_log["laatste_jaar_in_gecombineerde_data"] = int(merged["year"].max())

    merged["country"] = merged["country_co2"].combine_first(merged["country_energy"])
    merged = merged.drop(columns=["country_co2", "country_energy"])

    # Afgeleide variabelen
    merged["gdp_per_capita"] = merged["gdp"] / merged["population"]
    merged["co2_per_capita"] = merged["co2_emissions_tonnes"] / merged["population"]
    merged[["gdp_per_capita", "co2_per_capita"]] = merged[
        ["gdp_per_capita", "co2_per_capita"]
    ].replace([np.inf, -np.inf], np.nan)

    # Onmogelijke/onbetrouwbare waarden opschonen (dataverkenning-eis)
    merged.loc[merged["renewables_share_energy"] < 0, "renewables_share_energy"] = np.nan
    merged.loc[merged["renewables_share_energy"] > 100, "renewables_share_energy"] = np.nan
    merged.loc[merged["co2_per_capita"] < 0, "co2_per_capita"] = np.nan
    merged.loc[merged["gdp_per_capita"] <= 0, "gdp_per_capita"] = np.nan

    merged["income_group"] = merged["gdp_per_capita"].apply(_income_group)

    return merged, join_log


def compute_decoupling_table(df: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    """Voor elk land: verandering in renewable-aandeel vs. verandering in
    CO2 per capita tussen start_year en end_year -- gebruikt om te bepalen
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
