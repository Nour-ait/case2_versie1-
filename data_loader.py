"""
data_loader.py
================
Alle dataverzameling voor het dashboard. GEEN enkele CSV wordt met de hand
gedownload: alles wordt in dit script opgehaald bij de bron, zodat de dataset
voor iedereen reproduceerbaar is (zie opdracht-eis: "Haal de data in je
script op, niet met de hand gedownload.").

Bron 1 - CO2-uitstoot per land per jaar (1750-heden)
    Our World in Data "Chart / Data API" (officieel, publiek, gedocumenteerd:
    https://docs.owid.io / https://ourworldindata.org/faqs#grapher-api).
    Elke grapher-chart op ourworldindata.org is met ".csv" erachter direct als
    API-endpoint te bevragen, inclusief query-parameters (v, csvType, ...).
    Endpoint hieronder = exact de chart-slug "annual-co2-emissions-per-country".

Bron 2 - Energiemix, hernieuwbaar-aandeel, bevolking & GDP per land per jaar
    Het "OWID Energy dataset", de brontabel die Our World in Data zelf
    publiceert en onderhoudt op GitHub (CC BY 4.0, publiek, machine-
    leesbaar, wordt dagelijks automatisch herbouwd uit hun ETL-pipeline):
    https://github.com/owid/energy-data
    Dit bestand heeft exact dezelfde kolommen als de Kaggle-dataset die als
    voorbeeld is gebruikt (renewables_share_energy, gdp, population, ...),
    omdat die Kaggle-dataset er simpelweg een gefilterde kopie van is.

Beide bronnen worden hier dus via een URL/HTTP-request in code opgehaald
(nooit met de hand gedownload), en het zijn twee volledig aparte bestanden/
tabellen -> dat voldoet aan de eis "je voegt twee tabellen samen die niet uit
hetzelfde bestand komen".
"""

import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Bronnen
# ---------------------------------------------------------------------------
CO2_API_URL = (
    "https://ourworldindata.org/grapher/annual-co2-emissions-per-country.csv"
    "?v=1&csvType=full&useColumnShortNames=true"
)
ENERGY_DATA_URL = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"

# Onze eigen "User-Agent"-header: OWID vraagt hier expliciet om in hun
# API-documentatie, zodat automatische requests herkenbaar zijn.
_HTTP_HEADERS = {"User-Agent": "VA-IDS-dashboard/1.0 (student project)"}

# Kolommen die we uit de energie-bron nodig hebben (die tabel heeft er >100)
ENERGY_COLUMNS = [
    "country",
    "year",
    "iso_code",
    "population",
    "gdp",
    "primary_energy_consumption",
    "electricity_generation",
    "renewables_share_energy",
    "fossil_share_energy",
    "low_carbon_share_energy",
    "renewables_share_elec",
    "fossil_share_elec",
    "solar_share_elec",
    "wind_share_elec",
    "hydro_share_elec",
    "nuclear_share_elec",
    "coal_share_elec",
    "gas_share_elec",
    "energy_per_capita",
]


def _is_real_country(code) -> bool:
    """OWID gebruikt voor regio's/inkomensgroepen (bv. 'Africa', 'High-income
    countries', 'World') geen (of een niet-ISO3) landcode. Door alleen rijen
    met een geldige 3-letter ISO-code te houden, isoleren we losse landen van
    dat soort aggregaten."""
    return isinstance(code, str) and len(code) == 3 and code != "OWID_WRL"


# ---------------------------------------------------------------------------
# Ophalen (elk 24 uur gecached, zodat de app snel blijft en niet omvalt als
# de bron traag/tijdelijk onbereikbaar is)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60 * 60 * 24, show_spinner="CO2-data ophalen bij Our World in Data (API)...")
def fetch_co2_raw() -> pd.DataFrame:
    df = pd.read_csv(CO2_API_URL, storage_options={"User-Agent": _HTTP_HEADERS["User-Agent"]})
    df = df.rename(columns={"Entity": "country", "Code": "iso_code", "Year": "year"})
    # De naam van de waarde-kolom hangt af van de OWID-versie/instellingen; pak 'm dynamisch
    # (de eerste kolom die niet country/iso_code/year is).
    value_col = [c for c in df.columns if c not in ("country", "iso_code", "year")][0]
    df = df.rename(columns={value_col: "co2_tonnes"})
    return df[["country", "iso_code", "year", "co2_tonnes"]]


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Energie- en welvaartdata ophalen bij Our World in Data (GitHub)...")
def fetch_energy_raw() -> pd.DataFrame:
    df = pd.read_csv(
        ENERGY_DATA_URL,
        usecols=lambda c: c in ENERGY_COLUMNS,
        storage_options={"User-Agent": _HTTP_HEADERS["User-Agent"]},
    )
    return df


# ---------------------------------------------------------------------------
# Combineren + opschonen + afgeleide variabelen
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60 * 60 * 24, show_spinner="Datasets samenvoegen en opschonen...")
def build_dataset():
    """Haalt beide bronnen op, merged ze en levert (df, join_log) terug.
    join_log bevat de rij-aantallen voor/na de merge, zoals de opdracht vraagt."""
    co2_raw = fetch_co2_raw()
    energy_raw = fetch_energy_raw()

    join_log = {
        "co2_rows_raw": len(co2_raw),
        "energy_rows_raw": len(energy_raw),
    }

    # 1) Alleen echte landen (aggregaten/regio's eruit) voor de hoofdanalyse.
    co2 = co2_raw[co2_raw.iso_code.apply(_is_real_country)].copy()
    energy = energy_raw[energy_raw.iso_code.apply(_is_real_country)].copy()
    join_log["co2_rows_countries_only"] = len(co2)
    join_log["energy_rows_countries_only"] = len(energy)

    # 2) Jaartallen gelijktrekken: de CO2-reeks stopt bij het laatste jaar
    #    waarvoor OWID CO2-cijfers heeft; de energie-reeks loopt vaak een paar
    #    jaar verder door (voorlopige cijfers). We nemen daarom automatisch de
    #    OVERLAP van beide bronnen, in plaats van een jaartal hard te coderen.
    start_year = max(co2.year.min(), energy.year.min())
    end_year = min(co2.year.max(), energy.year.max())
    co2 = co2[(co2.year >= start_year) & (co2.year <= end_year)]
    energy = energy[(energy.year >= start_year) & (energy.year <= end_year)]
    join_log["common_year_range"] = (int(start_year), int(end_year))
    join_log["co2_rows_after_year_align"] = len(co2)
    join_log["energy_rows_after_year_align"] = len(energy)

    # 3) Merge op de sleutel iso_code + year (landcode + jaar).
    merged = pd.merge(
        co2, energy, on=["iso_code", "year"], how="inner", suffixes=("_co2", "_energy")
    )
    join_log["merged_rows"] = len(merged)
    merged = merged.rename(columns={"country_co2": "country"}).drop(columns=["country_energy"])

    # 4) Afgeleide variabelen (nieuwe kolommen die we zelf berekenen)
    merged["co2_per_capita_t"] = merged["co2_tonnes"] / merged["population"]
    merged["gdp_per_capita"] = merged["gdp"] / merged["population"]
    merged["renewables_share_energy_pct"] = merged["renewables_share_energy"]  # al in %

    # Inkomensgroep: eigen, transparante kwartiel-indeling op basis van de
    # gemiddelde GDP per capita van elk land over de hele periode (dus geen
    # officiële Wereldbank-indeling, maar zelf afgeleid en reproduceerbaar).
    avg_gdp_pc = merged.groupby("country")["gdp_per_capita"].mean()
    valid = avg_gdp_pc.dropna()
    labels = ["Laag inkomen", "Lager-midden inkomen", "Hoger-midden inkomen", "Hoog inkomen"]
    income_group = pd.qcut(valid, q=4, labels=labels)
    income_map = income_group.to_dict()
    merged["income_group"] = merged["country"].map(income_map)

    join_log["rows_missing_gdp_pct"] = float(merged["gdp_per_capita"].isna().mean())
    join_log["rows_missing_renewables_pct"] = float(merged["renewables_share_energy"].isna().mean())

    return merged, join_log
