from . import DATA_DIR
import csv

REMIND_TO_ECOINVENT_EMISSION_FILEPATH = (DATA_DIR / "ecoinvent_to_gains_emission_mappping.csv")


class InventorySet:
    """
    Hosts different filter sets to for ecoinvent activities and exchanges.

    It stores:
    * material_filters: filters for activities related to materials.
    * powerplant_filters: filters for activities related to power generation technologies.
    * emissions_map: REMIND emission labels as keys, ecoinvent emission labels as values

    The functions :func:`generate_material_map` and :func:`generate_powerplant_map` can
    be used to extract the actual activity objects as dictionaries.
    These functions return the result of applying :func:`act_fltr` to the filter dictionaries.
    """

    material_filters = {
        "steel, primary": {"fltr": "steel production, converter", "mask": "hot rolled"},
        "steel, secondary": {"fltr": "steel production, electric", "mask": "hot rolled"},
        "concrete": {"fltr": "market for concrete,"},
        "copper": {"fltr": "market for copper", "filter_exact": True},
        "aluminium": {
            "fltr": ["market for aluminium, primary", "market for aluminium alloy,"]
        },
        "electricity": {"fltr": "market for electricity"},
        "gas": {"fltr": "market for natural gas,", "mask": ["network", "burned"]},
        "diesel": {"fltr": "market for diesel", "mask": ["burned", "electric"]},
        "petrol": {"fltr": "market for petrol,", "mask": "burned"},
        "freight": {"fltr": "market for transport, freight"},
        "cement": {"fltr": "market for cement,"},
        "heat": {"fltr": "market for heat,"},
    }

    fuel_filters = {
        "gas": {"fltr": "market for natural gas,", "mask": ["network", "burned"]},
        "diesel": {"fltr": "market for diesel", "mask": ["burned", "electric"]},
        "petrol": {"fltr": "market for petrol,", "mask": "burned"},
        "hard coal": {"fltr": 'market for hard coal', 'mask': ['factory', 'plant', 'briquettes', 'ash']},
        "lignite": {"fltr": 'market for lignite', 'mask': ['factory', 'plant', 'briquettes', 'ash']},
        "petroleum coke": {"fltr": 'market for petroleum coke'},
        "wood pellet": {"fltr": 'market for wood pellet', 'mask': ['factory']},
        "natural gas, high pressure": {"fltr": 'market for natural gas, high pressure'},
        "natural gas, low pressure": {"fltr": 'market for natural gas, low pressure'},
        "heavy fuel oil": {"fltr": 'market for heavy fuel oil', 'mask': ['burned']},
        "light fuel oil": {"fltr": 'market for light fuel oil'},
        "biogas": {"fltr": 'biogas', 'mask': ['burned']},
        "waste": {"fltr": {'reference product': ['waste plastic, mixture']},
                  'mask': ['market for', 'treatment', 'market group']},
        "syngas": {"fltr": 'methane, from electrochemical methanation'},
        "synfuel": {"fltr": 'Diesel production, Fischer Tropsch process'},
        "hydrogen": {"fltr": 'Hydrogen, gaseous'},
        "bioethanol": {"fltr": 'Ethanol from'},
        "liquified petroleum gas": {"fltr": 'Liquefied petroleum gas production, from methanol-to-gas process'}
    }

    powerplant_filters = {
        "Biomass IGCC CCS": {
            "fltr": [
                "electricity production, from CC plant, 100% SNG, truck 25km, post, pipeline 200km, storage 1000m",
                "electricity production, at wood burning power plant 20 MW, truck 25km, post, pipeline 200km, storage 1000m",
                "electricity production, at BIGCC power plant 450MW, pre, pipeline 200km, storage 1000m",
            ]
        },
        "Biomass IGCC": {
            "fltr": "electricity production, at BIGCC power plant 450MW, no CCS"
        },
        "Coal IGCC": {
            "fltr": [
                "electricity production, at power plant/hard coal, IGCC, no CCS",
                "electricity production, at power plant/lignite, IGCC, no CCS",
            ]
        },
        "Coal IGCC CCS": {
            "fltr": [
                "electricity production, at power plant/hard coal, pre, pipeline 200km, storage 1000m",
                "electricity production, at power plant/lignite, pre, pipeline 200km, storage 1000m",
            ]
        },
        "Coal PC CCS": {
            "fltr": [
                "electricity production, at power plant/hard coal, post, pipeline 200km, storage 1000m",
                "electricity production, at power plant/lignite, post, pipeline 200km, storage 1000m",
            ]
        },
        "Gas CCS": {
            "fltr": [
                "electricity production, at power plant/natural gas, pre, pipeline 200km, storage 1000m",
                "electricity production, at power plant/natural gas, post, pipeline 200km, storage 1000m",
            ]
        },
        "Biomass CHP": {
            "fltr": [
                    "heat and power co-generation, wood chips",
                    "heat and power co-generation, biogas",
            ],
            "mask":{"reference product": "heat"}
        },
        "Coal PC": {
            "fltr": [
                "electricity production, hard coal",
                "electricity production, lignite",
            ],
            "mask": "mine",
        },
        "Coal CHP": {
            "fltr": [
                    "heat and power co-generation, hard coal",
                    "heat and power co-generation, lignite",
            ],
            "mask":{"reference product":"heat"}

        },
        "Gas OC": {
            "fltr": "electricity production, natural gas, conventional power plant"
        },
        "Gas CC": {
            "fltr": "electricity production, natural gas, combined cycle power plant"
        },
        "Gas CHP": {
            "fltr": [
                    "heat and power co-generation, natural gas, combined cycle power plant, 400MW electrical",
                    "heat and power co-generation, natural gas, conventional power plant, 100MW electrical",
            ],
            "mask":{"reference product":"heat"}
        },
        "Geothermal": {"fltr": "electricity production, deep geothermal"},
        "Hydro": {
            "fltr": [
                "electricity production, hydro, reservoir",
                "electricity production, hydro, run-of-river",
            ]
        },
        "Nuclear": {"fltr": "electricity production, nuclear", "mask": "aluminium"},
        "Oil": {
            "fltr": [
                    "electricity production, oil",
                    "heat and power co-generation, oil",
            ],
            "mask": {"name":"aluminium", "reference product":"heat"}
        },
        "Solar CSP": {
            "fltr": [
                "electricity production, solar thermal parabolic trough, 50 MW",
                "electricity production, solar tower power plant, 20 MW",
            ]
        },
        "Solar PV": {"fltr": "electricity production, photovoltaic"},
        "Wind": {"fltr": "electricity production, wind"},
    }
    
    heatplant_filters = {
        "Biomass": {
            "fltr": [
                    "heat production, wood chips from industry, at furnace 1000kW",
            ]
        },
        "Biomass CHP": {
            "fltr": [
                    "heat and power co-generation, wood chips",
                    "heat and power co-generation, biogas",
            ],
            "mask":{"reference product": "electricity"}
        },
        "Coal": {
            "fltr": [
                    "heat production, at hard coal industrial furnace 1-10MW",
                    "heat production, hard coal coke, stove 5-15kW",
            ]
        },
        "Coal CHP": {
            "fltr": [
                    "heat and power co-generation, hard coal",
                    "heat and power co-generation, lignite",
            ],
            "mask":{"reference product":"electricity"}
        },
        "Gas": {
            "fltr": [
                    "heat production, natural gas, at boiler modulating >100kW",
                    "heat production, natural gas, at industrial furnace >100kW",
            ]
        },
        "Gas CHP": {
            "fltr": [
                    "heat and power co-generation, natural gas, combined cycle power plant, 400MW electrical",
                    "heat and power co-generation, natural gas, conventional power plant, 100MW electrical",
            ],
            "mask":{"reference product":"electricity"}
        },
        "Geothermal": {"fltr": "heat production, deep geothermal"},
    }

    def __init__(self, db):
        self.db = db

    def generate_material_map(self):
        """
        Filter ecoinvent processes related to different material demands.

        :return: dictionary with materials as keys (see below) and
            sets of related ecoinvent activities as values.
        :rtype: dict

        """

        return self.generate_sets_from_filters(self.material_filters)

    def generate_powerplant_map(self):
        """
        Filter ecoinvent processes related to electricity production.

        :return: dictionary with el. prod. techs as keys (see below) and
            sets of related ecoinvent activities as values.
        :rtype: dict

        """
        return self.generate_sets_from_filters(self.powerplant_filters)
        
    def generate_heatplant_map(self):
        """
        Filter ecoinvent processes related to heat production.

        :return: dictionary with heat prod. techs as keys (see below) and
            sets of related ecoinvent activities as values.
        :rtype: dict

        """
        return self.generate_sets_from_filters(self.heatplant_filters)

    def generate_fuel_map(self):
        """
        Filter ecoinvent processes related to fuel supply.

        :return: dictionary with fuel names as keys (see below) and
            sets of related ecoinvent activities as values.
        :rtype: dict

        """
        return self.generate_sets_from_filters(self.fuel_filters)

    @staticmethod
    def get_remind_to_ecoinvent_emissions():
        """
        Retrieve the correspondence between REMIND and ecoinvent emission labels.
        :return: REMIND emission labels as keys and ecoinvent emission labels as values
        :rtype: dict
        """

        if not REMIND_TO_ECOINVENT_EMISSION_FILEPATH.is_file():
            raise FileNotFoundError(
                "The dictionary of emission labels correspondences could not be found."
            )

        csv_dict = {}

        with open(REMIND_TO_ECOINVENT_EMISSION_FILEPATH) as f:
            input_dict = csv.reader(f, delimiter=";")
            for row in input_dict:
                csv_dict[row[0]] = row[1]

        return csv_dict

    @staticmethod
    def act_fltr(db, fltr=None, mask=None, filter_exact=False, mask_exact=False):
        """Filter `db` for activities matching field contents given by `fltr` excluding strings in `mask`.
        `fltr`: string, list of strings or dictionary.
        If a string is provided, it is used to match the name field from the start (*startswith*).
        If a list is provided, all strings in the lists are used and results are joined (*or*).
        A dict can be given in the form <fieldname>: <str> to filter for <str> in <fieldname>.
        `mask`: used in the same way as `fltr`, but filters add up with each other (*and*).
        `filter_exact` and `mask_exact`: boolean, set `True` to only allow for exact matches.

        :param db: A lice cycle inventory database
        :type db: brightway2 database object
        :param fltr: value(s) to filter with.
        :type fltr: Union[str, lst, dict]
        :param mask: value(s) to filter with.
        :type mask: Union[str, lst, dict]
        :param filter_exact: requires exact match when true.
        :type filter_exact: bool
        :param mask_exact: requires exact match when true.
        :type mask_exact: bool
        :return: list of activity data set names
        :rtype: list

        """
        if fltr is None:
            fltr = {}
        if mask is None:
            mask = {}
        result = []

        # default field is name
        if type(fltr) == list or type(fltr) == str:
            fltr = {"name": fltr}
        if type(mask) == list or type(mask) == str:
            mask = {"name": mask}

        def like(a, b):
            if filter_exact:
                return a == b
            else:
                return a.startswith(b)

        def notlike(a, b):
            if mask_exact:
                return a != b
            else:
                return b not in a

        assert len(fltr) > 0, "Filter dict must not be empty."
        for field in fltr:
            condition = fltr[field]
            if type(condition) == list:
                for el in condition:
                    # this is effectively connecting the statements by *or*
                    result.extend([act for act in db if like(act[field], el)])
            else:
                result.extend([act for act in db if like(act[field], condition)])

        for field in mask:
            condition = mask[field]
            if type(condition) == list:
                for el in condition:
                    # this is effectively connecting the statements by *and*
                    result = [act for act in result if notlike(act[field], el)]
            else:
                result = [act for act in result if notlike(act[field], condition)]
        return result

    def generate_sets_from_filters(self, filtr):
        """
        Generate a dictionary with sets of activity names for
        technologies from the filter specifications.

            :param filtr:
            :func:`activity_maps.InventorySet.act_fltr`.
        :return: dictionary with the same keys as provided in filter
            and a set of activity data set names as values.
        :rtype: dict
        """
        techs = {tech: self.act_fltr(self.db, **fltr) for tech, fltr in filtr.items()}
        return {
            tech: set([act["name"] for act in actlst]) for tech, actlst in techs.items()
        }
