from . import DATA_DIR
import csv
import pandas as pd

CO2_FUELS = DATA_DIR / "fuel_co2_emission_factor.txt"
LHV_FUELS = DATA_DIR / "fuels_lower_heating_value.txt"
CLINKER_RATIO_ECOINVENT_36 = DATA_DIR / "cement" / "clinker_ratio_ecoinvent_36.csv"
CLINKER_RATIO_ECOINVENT_35 = DATA_DIR / "cement" / "clinker_ratio_ecoinvent_35.csv"
CLINKER_RATIO_REMIND = DATA_DIR / "cement" / "clinker_ratios.csv"

REMIND_TO_FUELS = DATA_DIR / "steel" / "remind_fuels_correspondance.txt"
EFFICIENCY_RATIO_SOLAR_PV = DATA_DIR / "renewables" / "efficiency_solar_PV.csv"

def eidb_label(model, scenario, year):
    return "ecoinvent_" + model + "_" + scenario + "_" + str(year)

def get_correspondance_remind_to_fuels():
    """
    Return a dictionary with REMIND fuels as keys and ecoinvent activity names and reference products as values.
    :return: dict
    :rtype: dict
    """
    d = {}
    with open(REMIND_TO_FUELS) as f:
        r = csv.reader(f, delimiter=";")
        for row in r:
            d[row[0]] = {"fuel name": row[1], "activity name": row[2], "reference product": row[3]}
    return d

def get_fuel_co2_emission_factors():
    """
    Return a dictionary with fuel names as keys and, as values:
    * CO_2 emission factor, in kg CO2 per MJ of lower heating value
    * share of biogenic CO2

    Source: https://www.plateformeco2.ch/portal/documents/10279/16917/IPCC+(2006),%20Guidelines+for+National+Greenhouse+Gas+Inventories.pdf/a3838a98-5ad6-4da5-82f3-c9430007a158

    :return: dict
    """
    d = {}
    with open(CO2_FUELS) as f:
        r = csv.reader(f, delimiter=";")
        for row in r:
            d[row[0]] = {"co2": float(row[1]), "bio_share": float(row[2])}

    return d

def get_lower_heating_values():
    """
    Loads a csv file into a dictionary. This dictionary contains lower heating values for a number of fuel types.
    Mostly taken from: https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html

    :return: dictionary that contains lower heating values
    :rtype: dict
    """
    with open(LHV_FUELS) as f:
        d = dict(filter(None, csv.reader(f, delimiter=";")))
        d = {k: float(v) for k, v in d.items()}
        return d

def get_efficiency_ratio_solar_PV(year, power):
    """
    Return a dictionary with years as keys and efficiency ratios as values
    :return: dict
    """

    df = pd.read_csv(
        EFFICIENCY_RATIO_SOLAR_PV)

    return df.groupby(["power", "year"]) \
        .mean()["value"] \
        .to_xarray() \
        .interp(year=year, power=power, kwargs={"fill_value": "extrapolate"})

def get_clinker_ratio_ecoinvent(version):
    """
    Return a dictionary with (cement names, location) as keys and clinker-to-cement ratios as values,
    as found in ecoinvent.
    :return: dict
    """
    if version == 3.5:
        fp = CLINKER_RATIO_ECOINVENT_35
    else:
        fp = CLINKER_RATIO_ECOINVENT_36

    with open(fp) as f:
        d = {}
        for val in csv.reader(f):
            d[(val[0], val[1])] = float(val[2])
    return d

def get_clinker_ratio_remind(year):
    """
    Return an array with the average clinker-to-cement ratio per year and per region, as given by REMIND.
    :return: xarray
    :return:
    """
    df = pd.read_csv(
        CLINKER_RATIO_REMIND)

    return df.groupby(["region", "year"]) \
        .mean()["value"] \
        .to_xarray() \
        .interp(year=year)
