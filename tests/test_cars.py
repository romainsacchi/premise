from rmnd_lca import DATA_DIR
from rmnd_lca import NewDatabase
from rmnd_lca import RemindDataCollection
from rmnd_lca.cars import Cars

import os
import pytest
import wurst
import brightway2 as bw
import pandas as pd
import numpy as np

REGION_MAPPING_FILEPATH = (DATA_DIR / "regionmappingH12.csv")

# for local test runs
remind_output_folder = "/home/alois/remind/testruns/lca_paper/"
BW_PROJECT = "transport_lca_Budg1100_Conv"
scenario = "Budg1100_Conv"
year = 2035
remind_regions = ['LAM', 'OAS', 'SSA', 'EUR',
                  'NEU', 'MEA', 'REF', 'CAZ',
                  'CHA', 'IND', 'JPN', 'USA']
ecoinvent_version = 3.7


def get_db():
    db = [
        {
            'name': 'fake activity',
            'reference product': 'fake product',
            'location': 'IAI Area, Africa',
            'unit': 'kilogram',
            'exchanges': [
            {
                'name': 'fake activity',
                'product': 'fake product',
                'amount': 1,
                'type': 'production',
                'unit': 'kilogram',
                'input': ('dummy_db', '6543541'), },
            {
                'name': '1,4-Butanediol',
                'categories': ('air', 'urban air close to ground'),
                'amount': 1,
                'type': 'biosphere',
                'unit': 'kilogram',
                'input': ('dummy_bio', '123'),
            }]
        },
        {
            'name': 'electricity supply for electric vehicles',
            'reference product': 'electricity, low voltage',
            'location': 'RER',
            'unit': 'kilowatt hour',
            'exchanges': [
                {
                    'name': 'electricity supply for electric vehicles',
                    'product': 'fake product',
                    'amount': 1,
                    'type': 'production',
                    'unit': 'kilogram',
                    'input': ('dummy_db', '6543541')},
                {
                    'name': '1,4-Butanediol',
                    'categories': ('air', 'urban air close to ground'),
                    'amount': 1,
                    'type': 'biosphere',
                    'unit': 'kilogram',
                    'input': ('dummy_bio', '123'),
                },
            ]
        },
        {
            'name': 'BEV,',
            'reference product': 'car',
            'location': 'RER',
            'unit': 'car',
            'exchanges': [
                {
                    'name': 'BEV,',
                    'product': 'fake product',
                    'amount': 1,
                    'type': 'production',
                    'unit': 'kilogram',
                    'input': ('dummy_db', '6543541')},
                {
                    'name': 'electricity supply for electric vehicles',
                    'product': 'fake product',
                    'amount': 1,
                    'type': 'technosphere',
                    'unit': 'kilogram',
                    'input': ('dummy_db', '6543541')},
            ]
        },
        *[{
            'name': 'market group for electricity, low voltage',
            'reference product': 'electricity, low voltage',
            'location': region,
            'unit': 'kilowatt hour'
        } for region in remind_regions
        ]
    ]
    version = ecoinvent_version
    return db, version

def setup_db():
    bw.projects.set_current(BW_PROJECT)
    return NewDatabase(
        scenario=scenario,
        year=year,
        source_db='ecoinvent {} cutoff'.format(ecoinvent_version),
        source_version=ecoinvent_version,
        add_vehicles={
            "fleet file": os.path.join(
                remind_output_folder, scenario + "_vintcomp.csv")
        },
        filepath_to_remind_files=remind_output_folder)


@pytest.mark.ecoinvent
def test_link_local_electricity_supply():
    ndb = setup_db()

    ndb.update_electricity_to_remind_data()
    Cars(ndb.db, ndb.rdc, scenario, year).link_local_electricity_supply()


@pytest.mark.ecoinvent
def test_link_local_liquid_fuel_markets():
    bw.projects.set_current(BW_PROJECT)

    ndb = setup_db()

    ndb.update_electricity_to_remind_data()
    Cars(ndb.db, ndb.rdc, scenario, year).link_local_liquid_fuel_markets()


@pytest.mark.ecoinvent
def test_full_import():
    bw.projects.set_current(BW_PROJECT)

    ndb = setup_db()

    ndb.update_electricity_to_remind_data()
    ndb.update_cars()
    dbname = "test_carculator_complete"
    if dbname in bw.databases:
        del bw.databases[dbname]
    wurst.write_brightway2_database(ndb.db, dbname)
    del bw.databases[dbname]


def test_get_fuel_mix():
    from rmnd_lca import DATA_DIR

    rdc = RemindDataCollection(scenario, year, remind_output_folder)
    data = rdc.get_remind_fuel_mix_for_ldvs()
    assert data.shape == (13, 3)
    np.testing.assert_allclose(data.sum(dim="variables"), 1.)
