from . import DATA_DIR, INVENTORY_DIR
from .clean_datasets import DatabaseCleaner
from .data_collection import RemindDataCollection
from .electricity import Electricity
from .inventory_imports import CarmaCCSInventory, \
    BiofuelInventory, \
    HydrogenInventory, \
    BiogasInventory, \
    SynfuelInventory, \
    SyngasInventory, \
    HydrogenCoalInventory, \
    HydrogenWoodyInventory, \
    GeothermalInventory, \
    SyngasCoalInventory, \
    SynfuelCoalInventory, \
    LPGInventory, \
    CarculatorInventory
from .cement import Cement
from .steel import Steel
from .cars import Cars
from .heat import Heat

from .export import Export
from .utils import eidb_label
import wurst
import wurst.searching as ws
from pathlib import Path

FILEPATH_CARMA_INVENTORIES = (INVENTORY_DIR / "lci-Carma-CCS.xlsx")
FILEPATH_BIOFUEL_INVENTORIES = (INVENTORY_DIR / "lci-biofuels.xlsx")
FILEPATH_BIOGAS_INVENTORIES = (INVENTORY_DIR / "lci-biogas.xlsx")
FILEPATH_HYDROGEN_INVENTORIES = (INVENTORY_DIR / "lci-hydrogen-electrolysis.xlsx")
FILEPATH_HYDROGEN_BIOGAS_INVENTORIES = (INVENTORY_DIR / "lci-hydrogen-smr-atr-biogas.xlsx")
FILEPATH_HYDROGEN_NATGAS_INVENTORIES = (INVENTORY_DIR / "lci-hydrogen-smr-atr-natgas.xlsx")
FILEPATH_HYDROGEN_WOODY_INVENTORIES = (INVENTORY_DIR / "lci-hydrogen-wood-gasification.xlsx")
FILEPATH_SYNFUEL_INVENTORIES = (INVENTORY_DIR / "lci-synfuels-from-FT.xlsx")
FILEPATH_SYNGAS_INVENTORIES = (INVENTORY_DIR / "lci-syngas.xlsx")
FILEPATH_HYDROGEN_COAL_GASIFICATION_INVENTORIES = (INVENTORY_DIR / "lci-hydrogen-coal-gasification.xlsx")
FILEPATH_GEOTHERMAL_HEAT_INVENTORIES = (INVENTORY_DIR / "lci-geothermal.xlsx")
FILEPATH_SYNGAS_FROM_COAL_INVENTORIES = (INVENTORY_DIR / "lci-syngas-from-coal.xlsx")
FILEPATH_SYNFUEL_FROM_COAL_INVENTORIES = (INVENTORY_DIR / "lci-synfuel-from-coal.xlsx")
FILEPATH_METHANOL_FUELS_INVENTORIES = (INVENTORY_DIR / "lci-synfuels-from-methanol.xlsx")


class NewDatabase:
    """
    Class that represents a new wurst inventory database, modified according to IAM data.

    :ivar scenario: name of the REMIND scenario, e.g., 'BAU', 'SCP26'.
    :vartype scenario: str
    :ivar year: year of the REMIND scenario to consider, between 2005 and 2150.
    :vartype year: int
    :ivar source_db: name of the ecoinvent source database
    :vartype source_db: str
    :ivar source_version: version of the ecoinvent source database. Currently works with ecoinvent 3.5 and 3.6.
    :vartype source_version: float
    :ivar filepath_to_remind_files: Filepath to the directory that contains REMIND output files.
    :vartype filepath_to_remind_file: pathlib.Path

    """

    def __init__(self, year, source_db, scenario=None,
                 source_version=3.5,
                 source_type='brightway',
                 source_file_path=None,
                 filepath_to_remind_files=None,
                 add_vehicles=None):

        if filepath_to_remind_files is None:
            if scenario not in [
                "SSP2-Base",
                "SSP2-NDC",
                "SSP2-NPi",
                "SSP2-PkBudg900",
                "SSP2-PkBudg1100",
                "SSP2-PkBudg1300",
            ]:
                print(('Warning: The scenario chosen is not any of '
                       '"SSP2-Base", "SSP2-NDC", "SSP2-NPi", "SSP2-PkBudg900", '
                       '"SSP2-PkBudg1100", "SSP2-PkBudg1300".'))


        # If we produce fleet average vehicles, fleet compositions and electricity mixes must be provided
        if add_vehicles:
            if "fleet file" not in add_vehicles:
                print("No fleet composition file is provided, hence fleet average vehicles inventories will not be produced.")
            if "source file" not in add_vehicles:
                add_vehicles["source file"] = (filepath_to_remind_files or DATA_DIR / "remind_output_files")

        if scenario is None:
            raise ValueError("Missing scenario name.")
        else:
            self.scenario = scenario

        self.year = year
        self.source = source_db
        self.version = source_version
        self.source_type = source_type
        self.source_file_path = source_file_path
        self.filepath_to_remind_files = Path(filepath_to_remind_files or DATA_DIR / "remind_output_files")
        self.add_vehicles = add_vehicles

        if not self.filepath_to_remind_files.is_dir():
            raise FileNotFoundError(
                "The REMIND output directory could not be found."
            )
        self.rdc = RemindDataCollection(self.scenario, self.year, self.filepath_to_remind_files)

        self.db = self.clean_database()
        self.import_inventories()


    def clean_database(self):
        return DatabaseCleaner(
            self.source,
            self.source_type,
            self.source_file_path
        ).prepare_datasets()

    def import_inventories(self):

        # Add Carma CCS inventories
        print("Add Carma CCS inventories")
        carma = CarmaCCSInventory(self.db, self.version, FILEPATH_CARMA_INVENTORIES)
        carma.merge_inventory()

        print("Add Biogas inventories")
        biogas = BiogasInventory(self.db, self.version, FILEPATH_BIOGAS_INVENTORIES)
        biogas.merge_inventory()

        print("Add Electrolysis Hydrogen inventories")
        hydro = HydrogenInventory(self.db, self.version, FILEPATH_HYDROGEN_INVENTORIES)
        hydro.merge_inventory()

        print("Add Natural Gas SMR and ATR Hydrogen inventories")
        hydro = HydrogenInventory(self.db, self.version, FILEPATH_HYDROGEN_NATGAS_INVENTORIES)
        hydro.merge_inventory()

        print("Add Biogas SMR and ATR Hydrogen inventories")
        hydro = HydrogenInventory(self.db, self.version, FILEPATH_HYDROGEN_BIOGAS_INVENTORIES)
        hydro.merge_inventory()

        print("Add Woody biomass gasification Hydrogen inventories")
        hydro = HydrogenWoodyInventory(self.db, self.version, FILEPATH_HYDROGEN_WOODY_INVENTORIES)
        hydro.merge_inventory()

        print("Add Synthetic gas inventories")
        syngas = SyngasInventory(self.db, self.version, FILEPATH_SYNGAS_INVENTORIES)
        syngas.merge_inventory()

        print("Add Biofuel inventories")
        bio = BiofuelInventory(self.db, self.version, FILEPATH_BIOFUEL_INVENTORIES)
        bio.merge_inventory()

        print("Add Fischer-Tropsh-based synthetic fuels inventories")
        synfuel = SynfuelInventory(self.db, self.version, FILEPATH_SYNFUEL_INVENTORIES)
        synfuel.merge_inventory()

        print("Add Hydrogen from coal gasification inventories")
        hydrogen_coal = HydrogenCoalInventory(self.db, self.version, FILEPATH_HYDROGEN_COAL_GASIFICATION_INVENTORIES)
        hydrogen_coal.merge_inventory()

        print("Add Geothermal heat inventories")
        geo_heat = GeothermalInventory(self.db, self.version, FILEPATH_GEOTHERMAL_HEAT_INVENTORIES)
        geo_heat.merge_inventory()

        print("Add Syngas from coal gasification inventories")
        syngas_coal = SyngasCoalInventory(self.db, self.version, FILEPATH_SYNGAS_FROM_COAL_INVENTORIES)
        syngas_coal.merge_inventory()

        print("Add Synfuel from coal gasification inventories")
        synfuel_coal = SynfuelCoalInventory(self.db, self.version, FILEPATH_SYNFUEL_FROM_COAL_INVENTORIES)
        synfuel_coal.merge_inventory()

        print("Add methanol-based synthetic fuel inventories")
        lpg = LPGInventory(self.db, self.version, FILEPATH_METHANOL_FUELS_INVENTORIES)
        lpg.merge_inventory()

        # Import `carculator` inventories if wanted
        if self.add_vehicles:
            print("Add Carculator inventories")
            cars = CarculatorInventory(self.db, self.year, self.version, self.rdc.regions,
                                       self.add_vehicles, self.scenario)
            cars.merge_inventory()

    def update_electricity_to_remind_data(self):
        electricity = Electricity(self.db, self.rdc, self.scenario, self.year)
        self.db = electricity.update_electricity_markets()
        self.db = electricity.update_electricity_efficiency()
        
    def update_heat_to_remind_data(self):
        heat = Heat(self.db, self.rdc, self.scenario, self.year)
        self.db = heat.update_heat_markets()
        self.db = heat.update_heat_efficiency()

    def update_cement_to_remind_data(self):
        if len([v for v in self.rdc.data.variables.values
                if "cement" in v.lower() and "production" in v.lower()])>0:
            cement = Cement(self.db, self.rdc, self.year, self.version)
            self.db = cement.add_datasets_to_database()
        else:
            print("The REMIND scenario chosen does not contain any data related to the cement sector."
                  "Transformations related to the cement sector will be skipped.")

    def update_steel_to_remind_data(self):
        if len([v for v in self.rdc.data.variables.values
                if "steel" in v.lower() and "production" in v.lower()])>0:
            steel = Steel(self.db, self.rdc, self.year)
            self.db = steel.generate_activities()
        else:
            print("The REMIND scenario chosen does not contain any data related to the steel sector."
                  "Transformations related to the steel sector will be skipped.")

    def update_cars(self):
        try:
            next(ws.get_many(
                self.db,
                ws.equals("name", "market group for electricity, low voltage")))
            crs = Cars(self.db, self.rdc, self.scenario, self.year)
            crs.update_cars()
        except StopIteration as e:
            print(("No updated electricity markets found. Please update "
                   "electricity markets before updating upstream fuel "
                   "inventories for electricity powered vehicles"))

    def update_all(self):
        self.update_electricity_to_remind_data()
        self.update_heat_to_remind_data()
        self.update_cement_to_remind_data()
        self.update_steel_to_remind_data()
        if self.add_vehicles:
            self.update_cars()

    def write_db_to_brightway(self):
        print('Write new database to Brightway2.')
        wurst.write_brightway2_database(self.db, eidb_label(self.scenario, self.year))

    def write_db_to_matrices(self):
        print("Write new database to matrix.")
        Export(self.db, self.scenario, self.year).export_db_to_matrices()
