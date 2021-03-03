# content of test_activity_maps.py
import pytest
from premise.inventory_imports import \
    BaseInventoryImport, CarmaCCSInventory,\
    BiofuelInventory, CarculatorInventory
from pathlib import Path
from premise import INVENTORY_DIR, DATA_DIR


FILEPATH_CARMA_INVENTORIES = (INVENTORY_DIR / "lci-Carma-CCS.xls")
FILEPATH_BIOFUEL_INVENTORIES = (INVENTORY_DIR / "lci-biofuels.xls")
FILEPATH_BIOGAS_INVENTORIES = (INVENTORY_DIR / "lci-biogas.xls")
FILEPATH_HYDROGEN_INVENTORIES = (INVENTORY_DIR / "lci-hydrogen.xls")
FILEPATH_SYNFUEL_INVENTORIES = (INVENTORY_DIR / "lci-synfuel.xls")
FILEPATH_SYNGAS_INVENTORIES = (INVENTORY_DIR / "lci-syngas.xls")
FILEPATH_HYDROGEN_COAL_GASIFICATION_INVENTORIES = (INVENTORY_DIR / "lci-hydrogen-coal-gasification.xls")


def get_db():
    db = [{
        'code':'argsthyfujgyftdgr',
        'name': 'fake activity',
        'reference product': 'fake product',
        'location': 'IAI Area, Africa',
        'unit': 'kilogram',
        'exchanges': [
            {'name': 'fake activity',
             'product': 'fake product',
             'amount': 1,
             'type': 'production',
             'unit': 'kilogram',
             'input': ('dummy_db', '6543541'), },
            {'name': '1,4-Butanediol',
             'categories': ('air', 'urban air close to ground'),
             'amount': 1,
             'type': 'biosphere',
             'unit': 'kilogram',
             'input': ('dummy_bio', '123'),
             },
        ]
    }]
    version = 3.5
    return db, version

def test_file_exists():
    db, version = get_db()
    with pytest.raises(FileNotFoundError) as wrapped_error:
        BaseInventoryImport(db, version, "testfile")
    assert wrapped_error.type == FileNotFoundError

def test_biosphere_dict():
    db, version = get_db()
    testpath = Path("testfile")
    open(testpath, "w")
    dbc = BaseInventoryImport(db, version, testpath)
    assert dbc.biosphere_dict[
               (
                   '1,4-Butanediol',
                   'air',
                   'urban air close to ground',
                   'kilogram'
               )] == '38a622c6-f086-4763-a952-7c6b3b1c42ba'

    testpath.unlink()

def test_biosphere_dict_2():
    db, version = get_db()
    testpath = Path("testfile")
    open(testpath, "w")
    dbc = BaseInventoryImport(db, version, testpath)

    for act in dbc.db:
        for exc in act['exchanges']:
            if exc['type'] == 'biosphere':
                assert dbc.biosphere_dict[(
                    exc['name'],
                    exc['categories'][0],
                    exc['categories'][1],
                    exc['unit']
                )] == '38a622c6-f086-4763-a952-7c6b3b1c42ba'

    testpath.unlink()

def test_load_carma():
    db, version = get_db()
    carma = CarmaCCSInventory(db, version, FILEPATH_CARMA_INVENTORIES)
    assert len(carma.import_db.data) == 148


def test_load_biofuel():
    db, version = get_db()
    bio = BiofuelInventory(db, version, FILEPATH_BIOFUEL_INVENTORIES)
    assert len(bio.import_db.data) == 36


def test_load_carculator():
    db, version = get_db()
<<<<<<< HEAD
    carc = CarculatorInventory(db, 2015, "3.7", ["EUR"])
    assert len(carc.import_db.data) == 335
=======
    carc = CarculatorInventory(database=db,
                               version=3.7,
                               model="remind",
                               path=Path(""),
                               scenario="SSP2-Base",
                               year=2015,
                               regions=["EUR"],
                               vehicles={"source file": (DATA_DIR / "iam_output_files")}
                               )
    assert len(carc.import_db.data) >= 335

>>>>>>> fa9f44a36360457b501a363a2bda40e06b058380
