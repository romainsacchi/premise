import os
from . import DATA_DIR
from .activity_maps import InventorySet
from .geomap import Geomap
from wurst import searching as ws
from wurst.ecoinvent import filters
import csv
import numpy as np
import uuid
import wurst
from datetime import date

# PRODUCTION_PER_TECH = (
    # DATA_DIR / "electricity" / "electricity_production_volumes_per_tech.csv"
# )
# LOSS_PER_COUNTRY = DATA_DIR / "electricity" / "losses_per_country.csv"
LHV_FUELS = DATA_DIR / "fuels_lower_heating_value.txt"


class Heat:
    """
    Class that modifies heat markets in ecoinvent based on REMIND output data.

    :ivar scenario: name of a Remind scenario
    :vartype scenario: str

    """

    def __init__(self, db, rmd, scenario, year):
        self.db = db
        self.rmd = rmd
        self.geo = Geomap()
        #self.production_per_tech = self.get_production_per_tech_dict()
        #self.losses = self.get_losses_per_country_dict()
        self.scenario = scenario
        self.year = year
        self.fuels_lhv = self.get_lower_heating_values()
        mapping = InventorySet(self.db)
        self.emissions_map = mapping.get_remind_to_ecoinvent_emissions()
        self.heatplant_map = mapping.generate_heatplant_map()

    @staticmethod
    def get_lower_heating_values():
        """
        Loads a csv file into a dictionary. This dictionary contains lower heating values for a number of fuel types.
        Taken from: https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html

        :return: dictionary that contains lower heating values
        :rtype: dict
        """
        with open(LHV_FUELS) as f:
            return dict(filter(None, csv.reader(f, delimiter=";")))

    def get_suppliers_of_a_region(self, ecoinvent_regions, ecoinvent_technologies):
        """
        Return a list of electricity-producing datasets which location and name correspond to the region and name given,
        respectively.

        :param ecoinvent_regions: an ecoinvent region
        :type ecoinvent_regions: list
        :param ecoinvent_technologies: name of ecoinvent dataset
        :type ecoinvent_technologies: str
        :return: list of wurst datasets
        :rtype: list
        """

        return ws.get_many(
            self.db,
            *[
                ws.either(
                    *[
                        ws.equals("name", supplier)
                        for supplier in ecoinvent_technologies
                    ]
                ),
                ws.either(*[ws.equals("location", loc) for loc in ecoinvent_regions]),
                ws.equals("unit", "kilowatt hour"),
            ]
        )

    # @staticmethod
    # def get_losses_per_country_dict():
        # """
        # Create a dictionary with ISO country codes as keys and loss ratios as values.
        # :return: ISO country code to loss ratio dictionary
        # :rtype: dict
        # """

        # if not LOSS_PER_COUNTRY.is_file():
            # raise FileNotFoundError(
                # "The production per country dictionary file could not be found."
            # )

        # with open(LOSS_PER_COUNTRY) as f:
            # csv_list = [[val.strip() for val in r.split(";")] for r in f.readlines()]

        # (_, *header), *data = csv_list
        # csv_dict = {}
        # for row in data:
            # key, *values = row
            # csv_dict[key] = {key: float(value) for key, value in zip(header, values)}

        # return csv_dict

    # @staticmethod
    # def get_production_per_tech_dict():
        # """
        # Create a dictionary with tuples (technology, country) as keys and production volumes as values.
        # :return: technology to production volume dictionary
        # :rtype: dict
        # """

        # if not PRODUCTION_PER_TECH.is_file():
            # raise FileNotFoundError(
                # "The production per technology dictionary file could not be found."
            # )
        # csv_dict = {}
        # with open(PRODUCTION_PER_TECH) as f:
            # input_dict = csv.reader(f, delimiter=";")
            # for row in input_dict:
                # csv_dict[(row[0], row[1])] = row[2]

        # return csv_dict

    def get_production_weighted_share(self, supplier, suppliers):
        """
        Return the share of production of an electricity-producing dataset in a specific location,
        relative to the summed production of similar technologies in locations contained in the same REMIND region.

        :param supplier: electricity-producing dataset
        :type supplier: wurst dataset
        :param suppliers: list of electricity-producing datasets
        :type suppliers: list of wurst datasets
        :return: share of production relative to the total population
        :rtype: float
        """

        # Fetch the production volume of the supplier
        loc_production = float(
            self.production_per_tech.get((supplier["name"], supplier["location"]), 0)
        )

        # Fetch the total production volume of similar technologies in other locations
        # contained within the REMIND region.

        total_production = 0
        for loc in suppliers:
            total_production += float(
                self.production_per_tech.get((loc["name"], loc["location"]), 0)
            )

        # If a corresponding production volume is found.
        if total_production != 0:
            return loc_production / total_production
        else:
            # If not, we allocate an equal share of supply
            return 1 / len(suppliers)

    def get_production_weighted_losses(self, voltage, remind_region):
        """
        Return the transformation, transmission and distribution losses at a given voltage level for a given location.
        A weighted average is made of the locations contained in the REMIND region.

        :param voltage: voltage level (high, medium or low)
        :type voltage: str
        :param remind_region: Remind region
        :type remind_region: str
        :return: tuple that contains transformation and distribution losses
        :rtype: tuple
        """

        # Fetch locations contained in REMIND region
        locations = self.geo.remind_to_ecoinvent_location(remind_region)

        if voltage == "high":

            cumul_prod, transf_loss = 0, 0
            for loc in locations:
                dict_loss = self.losses.get(
                    loc,
                    {"Transformation loss, high voltage": 0, "Production volume": 0},
                )

                transf_loss += (
                    dict_loss["Transformation loss, high voltage"]
                    * dict_loss["Production volume"]
                )
                cumul_prod += dict_loss["Production volume"]
            transf_loss /= cumul_prod
            return transf_loss

        if voltage == "medium":

            cumul_prod, transf_loss, distr_loss = 0, 0, 0
            for loc in locations:
                dict_loss = self.losses.get(
                    loc,
                    {
                        "Transformation loss, medium voltage": 0,
                        "Transmission loss to medium voltage": 0,
                        "Production volume": 0,
                    },
                )
                transf_loss += (
                    dict_loss["Transformation loss, medium voltage"]
                    * dict_loss["Production volume"]
                )
                distr_loss += (
                    dict_loss["Transmission loss to medium voltage"]
                    * dict_loss["Production volume"]
                )
                cumul_prod += dict_loss["Production volume"]
            transf_loss /= cumul_prod
            distr_loss /= cumul_prod
            return transf_loss, distr_loss

        if voltage == "low":

            cumul_prod, transf_loss, distr_loss = 0, 0, 0

            for loc in locations:
                dict_loss = self.losses.get(
                    loc,
                    {
                        "Transformation loss, low voltage": 0,
                        "Transmission loss to low voltage": 0,
                        "Production volume": 0,
                    },
                )
                transf_loss += (
                    dict_loss["Transformation loss, low voltage"]
                    * dict_loss["Production volume"]
                )
                distr_loss += (
                    dict_loss["Transmission loss to low voltage"]
                    * dict_loss["Production volume"]
                )
                cumul_prod += dict_loss["Production volume"]
            transf_loss /= cumul_prod
            distr_loss /= cumul_prod
            return transf_loss, distr_loss


    def create_new_heat_markets(self):
        """
        Create market groups for heat, based on heat mixes given by REMIND.
        Does not return anything. Modifies the database in place.
        """
        # Loop through REMIND regions
        gen_region = (
            region for region in self.rmd.heat_markets.coords["region"].values
        )
        gen_tech = list(
            (
                tech for tech in self.rmd.heat_markets.coords["variables"].values
            )
        )

        created_markets = []

        for region in gen_region:

            # Fetch ecoinvent regions contained in the REMIND region
            ecoinvent_regions = self.geo.remind_to_ecoinvent_location(region)

            # Create an empty dataset
            new_dataset = {
                "location": region,
                "name": ("market group for heat"),
                "reference product": "heat",
                "unit": "kilowatt hour",
                "database": self.db[1]["database"],
                "code": str(uuid.uuid4().hex),
                "comment": "Dataset produced from REMIND scenario output results",
            }

            new_exchanges = [
                {
                    "uncertainty type": 0,
                    "loc": 1,
                    "amount": 1,
                    "type": "production",
                    "production volume": 0,
                    "product": "heat",
                    "name": "market group for heat",
                    "unit": "kilowatt hour",
                    "location": region,
                }
            ]

            # First, add the reference product exchange

            # Second, add transformation loss
            transf_loss = self.get_production_weighted_losses("high", region)
            new_exchanges.append(
                {
                    "uncertainty type": 0,
                    "loc": 1,
                    "amount": transf_loss,
                    "type": "technosphere",
                    "production volume": 0,
                    "product": "heat",
                    "name": "market group for heat",
                    "unit": "kilowatt hour",
                    "location": region,
                }
            )

            # Loop through the REMIND technologies
            for technology in gen_tech:

                # If the given technology contributes to the mix
                if self.rmd.heat_markets.loc[region, technology] != 0.0:

                    # Contribution in supply
                    amount = self.rmd.heat_markets.loc[region, technology].values

                    # Get the possible names of ecoinvent datasets
                    ecoinvent_technologies = self.powerplant_map[
                        self.rmd.rev_heat_market_labels[technology]
                    ]

                    # Fetch heat-producing technologies contained in the REMIND region
                    suppliers = list(
                        self.get_suppliers_of_a_region(
                            ecoinvent_regions, ecoinvent_technologies
                        )
                    )

                    suppliers = self.check_for_production_volume(suppliers)

                    # If no technology is available for the REMIND region
                    if len(suppliers) == 0:
                        # We fetch European technologies instead
                        suppliers = list(
                            self.get_suppliers_of_a_region(
                                ["RER"], ecoinvent_technologies
                            )
                        )

                    suppliers = self.check_for_production_volume(suppliers)

                    # If, after looking for European technologies, no technology is available
                    if len(suppliers) == 0:
                        # We fetch RoW technologies instead
                        suppliers = list(
                            self.get_suppliers_of_a_region(
                                ["RoW"], ecoinvent_technologies
                            )
                        )

                    suppliers = self.check_for_production_volume(suppliers)

                    if len(suppliers) == 0:
                        print(
                            "no suppliers for {} in {} with ecoinvent names {}".format(
                                technology, region, ecoinvent_technologies
                            )
                        )

                    for supplier in suppliers:
                        share = self.get_production_weighted_share(supplier, suppliers)

                        new_exchanges.append(
                            {
                                "uncertainty type": 0,
                                "loc": (amount * share) / (1 - solar_amount),
                                "amount": (amount * share) / (1 - solar_amount),
                                "type": "technosphere",
                                "production volume": 0,
                                "product": supplier["reference product"],
                                "name": supplier["name"],
                                "unit": supplier["unit"],
                                "location": supplier["location"],
                            }
                        )

                        created_markets.append(
                            [
                                "high voltage, "
                                + self.scenario
                                + ", "
                                + str(self.year),
                                technology,
                                region,
                                transf_loss,
                                0.0,
                                supplier["name"],
                                supplier["location"],
                                share,
                                (amount * share) / (1 - solar_amount),
                            ]
                        )
            new_dataset["exchanges"] = new_exchanges

            self.db.append(new_dataset)

        # Writing log of created markets

        with open(
            DATA_DIR
            / "logs/log created markets {} {}-{}.csv".format(
                self.scenario, self.year, date.today()
            ),
            "w",
        ) as csv_file:
            writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")
            writer.writerow(
                [
                    "dataset name",
                    "energy type",
                    "REMIND location",
                    "Transformation loss",
                    "Distr./Transmission loss",
                    "Supplier name",
                    "Supplier location",
                    "Contribution within energy type",
                    "Final contribution",
                ]
            )
            for line in created_markets:
                writer.writerow(line)

    def check_for_production_volume(self, suppliers):

        # Remove suppliers that do not have a production volume
        return [
            supplier
            for supplier in suppliers
            if self.get_production_weighted_share(supplier, suppliers) != 0
        ]

    def relink_activities_to_new_markets(self):
        """
        Links heat input exchanges to new datasets with the appropriate REMIND location:
        * "market for electricity, high voltage" --> "market group for electricity, high voltage"
        * "market for electricity, medium voltage" --> "market group for electricity, medium voltage"
        * "market for electricity, low voltage" --> "market group for electricity, low voltage"
        Does not return anything.
        """

        # Filter all activities that consume high voltage electricity

        for ds in ws.get_many(
            self.db, ws.exclude(ws.contains("name", "market group for heat"))
        ):

            for exc in ws.get_many(
                ds["exchanges"],
                *[
                    ws.either(
                        *[
                            ws.contains("name", "market for heat"),
                            ws.contains("name", "market group for heat"),
                        ]
                    )
                ]
            ):
                if exc["type"] != "production" and exc["unit"] == "kilowatt hour":
                    if "high" in exc["product"]:
                        exc["name"] = "market group for heat"
                        exc["product"] = "heat, high voltage"
                        exc["location"] = self.geo.ecoinvent_to_remind_location(
                            exc["location"]
                        )
                if "input" in exc:
                    exc.pop("input")

    def find_ecoinvent_fuel_efficiency(self, ds, fuel_filters):
        """
        This method calculates the efficiency value set initially, in case it is not specified in the parameter
        field of the dataset. In Carma datasets, fuel inputs are expressed in megajoules instead of kilograms.

        :param ds: a wurst dataset of an heat-producing technology
        :param fuel_filters: wurst filter to to filter fuel input exchanges
        :return: the efficiency value set by ecoinvent
        """

        def calculate_input_energy(fuel_name, fuel_amount, fuel_unit):


            if fuel_unit == 'kilogram' or fuel_unit == 'cubic meter':

                lhv = [self.fuels_lhv[k] for k in self.fuels_lhv if k in fuel_name.lower()][
                    0
                ]
                return float(lhv) * fuel_amount / 3.6

            if fuel_unit == 'megajoule':
                return fuel_amount / 3.6

        not_allowed = ["thermal"]
        key = list()
        if "parameters" in ds:
            key = list(
                key
                for key in ds["parameters"]
                if "efficiency" in key and not any(item in key for item in not_allowed)
            )
        if len(key) > 0:
            return ds["parameters"][key[0]]

        else:

            energy_input = np.sum(
                np.sum(
                    np.asarray(
                        [
                            calculate_input_energy(exc["name"], exc["amount"], exc['unit'])
                            for exc in ws.technosphere(ds, *fuel_filters)
                        ]
                    )
                )
            )

            current_efficiency = (
                float(ws.reference_product(ds)["amount"]) / energy_input
            )

            if "paramters" in ds:
                ds["parameters"]["efficiency"] = current_efficiency
            else:
                ds["parameters"] = {"efficiency": current_efficiency}

            return current_efficiency

    def find_fuel_efficiency_scaling_factor(self, ds, fuel_filters, technology):
        """
        This method calculates a scaling factor to change the process efficiency set by ecoinvent
        to the efficiency given by REMIND.

        :param ds: wurst dataset of an electricity-producing technology
        :param fuel_filters: wurst filter to filter the fuel input exchanges
        :param technology: label of an electricity-producing technology
        :return: a rescale factor to change from ecoinvent efficiency to REMIND efficiency
        :rtype: float
        """

        ecoinvent_eff = self.find_ecoinvent_fuel_efficiency(ds, fuel_filters)

        # If the current efficiency is too high, there's an issue, and teh dataset is skipped.
        if ecoinvent_eff > 1.1:
            print("The current efficiency factor for the dataset {} has not been found. Its current efficiency will remain".format(ds["name"]))
            return 1

        remind_locations = self.geo.ecoinvent_to_remind_location(ds["location"])
        remind_eff = (
            self.rmd.electricity_efficiencies.loc[
                dict(
                    variables=self.rmd.electricity_efficiency_labels[technology],
                    region=remind_locations,
                )
            ]
            .mean()
            .values
        )

        with open(
            DATA_DIR
            / "logs/log efficiencies change {} {}-{}.csv".format(
                self.scenario, self.year, date.today()
            ),
            "a",
        ) as csv_file:
            writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")

            writer.writerow([ds["name"], ds["location"], ecoinvent_eff, remind_eff])

        return ecoinvent_eff / remind_eff

    @staticmethod
    def update_ecoinvent_efficiency_parameter(ds, scaling_factor):
        """
        Update the old efficiency value in the ecoinvent dataset by the newly calculated one.
        :param ds: dataset
        :type ds: dict
        :param scaling_factor: scaling factor (new efficiency / old efficiency)
        :type scaling_factor: float
        """
        parameters = ds["parameters"]
        possibles = ["efficiency", "efficiency_oil_country", "efficiency_electrical"]

        for key in possibles:
            if key in parameters:
                ds["parameters"][key] /= scaling_factor

    def get_remind_mapping(self):
        """
        Define filter functions that decide which wurst datasets to modify.
        :return: dictionary that contains filters and functions
        :rtype: dict
        """
        generic_excludes = [
            ws.exclude(ws.contains("name", "aluminium industry")),
            ws.exclude(ws.contains("name", "carbon capture and storage")),
            ws.exclude(ws.contains("name", "market")),
            ws.exclude(ws.contains("name", "treatment")),
        ]
        no_imports = [ws.exclude(ws.contains("name", "import"))]

        gas_open_cycle_electricity = [
            ws.equals(
                "name", "electricity production, natural gas, conventional power plant"
            )
        ]

        biomass_chp_electricity = [
            ws.either(ws.contains("name", " wood"), ws.contains("name", "bio")),
            ws.equals("unit", "kilowatt hour"),
            ws.contains("name", "heat and power co-generation"),
        ]

        coal_IGCC = [
            ws.either(ws.contains("name", "coal"), ws.contains("name", "lignite")),
            ws.contains("name", "IGCC"),
            ws.contains("name", "no CCS"),
            ws.equals("unit", "kilowatt hour"),
        ]

        coal_IGCC_CCS = [
            ws.either(ws.contains("name", "coal"), ws.contains("name", "lignite")),
            ws.contains("name", "storage"),
            ws.contains("name", "pre"),
            ws.equals("unit", "kilowatt hour"),
        ]

        coal_PC_CCS = [
            ws.either(ws.contains("name", "coal"), ws.contains("name", "lignite")),
            ws.contains("name", "storage"),
            ws.equals("unit", "kilowatt hour"),
        ]

        coal_PC = [
            ws.either(ws.contains("name", "coal"), ws.contains("name", "lignite")),
            ws.exclude(ws.contains("name", "storage")),
            ws.exclude(ws.contains("name", "heat")),
            ws.exclude(ws.contains("name", "IGCC")),
            ws.equals("unit", "kilowatt hour"),
        ]

        gas_CCS = [
            ws.contains("name", "natural gas"),
            ws.either(ws.contains("name", "post"), ws.contains("name", "pre")),
            ws.contains("name", "storage"),
            ws.equals("unit", "kilowatt hour"),
        ]

        biomass_IGCC_CCS = [
            ws.either(
                ws.contains("name", "SNG"),
                ws.contains("name", "wood"),
                ws.contains("name", "BIGCC"),
            ),
            ws.contains("name", "storage"),
            ws.equals("unit", "kilowatt hour"),
        ]

        biomass_IGCC = [
            ws.contains("name", "BIGCC"),
            ws.contains("name", "no CCS"),
            ws.equals("unit", "kilowatt hour"),
        ]

        return {
            "Coal IGCC": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": coal_IGCC,
                "fuel filters": [
                    ws.either(
                        ws.contains("name", "Hard coal"), ws.contains("name", "Lignite")
                    ),
                    ws.equals("unit", "megajoule"),
                ],
                "technosphere excludes": [],
            },
            "Coal IGCC CCS": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": coal_IGCC_CCS,
                "fuel filters": [
                    ws.either(
                        ws.contains("name", "Hard coal"), ws.contains("name", "Lignite")
                    ),
                    ws.equals("unit", "megajoule"),
                ],
                "technosphere excludes": [],
            },
            "Coal PC": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": coal_PC + generic_excludes,
                "fuel filters": [
                    ws.either(
                        ws.contains("name", "hard coal"),
                        ws.contains("name", "Hard coal"),
                        ws.contains("name", "lignite"),
                        ws.contains("name", "Lignite")
                    ),
                    ws.doesnt_contain_any("name", ("ash", "SOx")),
                    ws.either(ws.equals("unit", "kilogram"),ws.equals("unit", "megajoule")),
                ],
                "technosphere excludes": [],
            },
            "Coal PC CCS": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": coal_PC_CCS,
                "fuel filters": [
                    ws.either(
                        ws.contains("name", "Hard coal"), ws.contains("name", "Lignite")
                    ),
                    ws.equals("unit", "megajoule"),
                ],
                "technosphere excludes": [],
            },
            "Coal CHP": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": filters.coal_chp_electricity + generic_excludes,
                "fuel filters": [
                    ws.either(
                        ws.contains("name", "hard coal"), ws.contains("name", "lignite")
                    ),
                    ws.doesnt_contain_any("name", ("ash", "SOx")),
                    ws.equals("unit", "kilogram"),
                ],
                "technosphere excludes": [],
            },
            "Gas OC": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": gas_open_cycle_electricity
                + generic_excludes
                + no_imports,
                "fuel filters": [
                    ws.either(
                        ws.contains("name", "natural gas, low pressure"),
                        ws.contains("name", "natural gas, high pressure"),
                    ),
                    ws.equals("unit", "cubic meter"),
                ],
                "technosphere excludes": [],
            },
            "Gas CC": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": filters.gas_combined_cycle_electricity
                + generic_excludes
                + no_imports,
                "fuel filters": [
                    ws.either(
                        ws.contains("name", "natural gas, low pressure"),
                        ws.contains("name", "natural gas, high pressure"),
                    ),
                    ws.equals("unit", "cubic meter"),
                ],
                "technosphere excludes": [],
            },
            "Gas CHP": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": filters.gas_chp_electricity
                + generic_excludes
                + no_imports,
                "fuel filters": [
                    ws.either(
                        ws.contains("name", "natural gas, low pressure"),
                        ws.contains("name", "natural gas, high pressure"),
                    ),
                    ws.equals("unit", "cubic meter"),
                ],
                "technosphere excludes": [],
            },
            "Gas CCS": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": gas_CCS,
                "fuel filters": [
                    ws.contains("name", "Natural gas"),
                    ws.equals("unit", "megajoule"),
                ],
                "technosphere excludes": [],
            },
            "Oil": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": (
                    filters.oil_open_cycle_electricity
                    + generic_excludes
                    + [ws.exclude(ws.contains("name", "nuclear"))]
                ),
                "fuel filters": [
                    ws.contains("name", "heavy fuel oil"),
                    ws.equals("unit", "kilogram"),
                ],
                "technosphere excludes": [],
            },
            "Biomass CHP": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": biomass_chp_electricity + generic_excludes,
                "fuel filters": [
                    ws.either(
                        ws.contains("name", "wood pellet"),
                        ws.contains("name", "biogas"),
                    ),
                    ws.either(
                        ws.equals("unit", "kilogram"), ws.equals("unit", "cubic meter")
                    ),
                ],
                "technosphere excludes": [],
            },
            "Biomass IGCC CCS": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": biomass_IGCC_CCS,
                "fuel filters": [
                    ws.either(
                        ws.contains("name", "100% SNG, burned in CC plant"),
                        ws.contains("name", "Wood chips"),
                        ws.contains("name", "Hydrogen"),
                    ),
                    ws.either(
                        ws.equals("unit", "megajoule"), ws.equals("unit", "kilogram"),
                    ),
                ],
                "technosphere excludes": [],
            },
            "Biomass IGCC": {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": biomass_IGCC,
                "fuel filters": [
                    ws.contains("name", "Hydrogen"),
                    ws.either(
                        ws.equals("unit", "kilogram"),
                        ws.equals("unit", "megajoule"),
                    ),

                ],
                "technosphere excludes": [],
            },
        }

    def update_heat_efficiency(self):
        """
        This method modifies each ecoinvent coal, gas,
        geothermal and biomass dataset using data from the REMIND model.
        Return a wurst database with modified datasets.

        :return: a wurst database, with rescaled heat-producing datasets.
        :rtype: list
        """

        technologies_map = self.get_remind_mapping()

        if not os.path.exists(DATA_DIR / "logs"):
            os.makedirs(DATA_DIR / "logs")

        with open(
            DATA_DIR
            / "logs/log efficiencies change {} {}-{}.csv".format(
                self.scenario, self.year, date.today()
            ),
            "w",
        ) as csv_file:
            writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")
            writer.writerow(
                ["dataset name", "location", "original efficiency", "new efficiency"]
            )

        print(
            "Log of changes in power plants efficiencies saved in {}".format(
                DATA_DIR / "logs"
            )
        )

        for remind_technology in technologies_map:
            dict_technology = technologies_map[remind_technology]
            print("Rescale inventories and emissions for", remind_technology)

            datsets = list(ws.get_many(self.db, *dict_technology["technology filters"]))

            # no activities found? Check filters!
            assert len(datsets) > 0, "No dataset found for {}".format(remind_technology)
            for ds in datsets:
                # Modify using remind efficiency values:
                scaling_factor = dict_technology["eff_func"](
                    ds, dict_technology["fuel filters"], remind_technology
                )
                self.update_ecoinvent_efficiency_parameter(ds, scaling_factor)

                # Rescale all the technosphere exchanges according to REMIND efficiency values
                wurst.change_exchanges_by_constant_factor(
                    ds,
                    float(scaling_factor),
                    dict_technology["technosphere excludes"],
                    [ws.doesnt_contain_any("name", self.emissions_map)],
                )

                # Update biosphere exchanges according to GAINS emission values
                for exc in ws.biosphere(
                    ds, ws.either(*[ws.contains("name", x) for x in self.emissions_map])
                ):
                    remind_emission_label = self.emissions_map[exc["name"]]

                    remind_emission = self.rmd.electricity_emissions.loc[
                        dict(
                            region=self.geo.ecoinvent_to_remind_location(
                                ds["location"]
                            ),
                            pollutant=remind_emission_label,
                            sector=self.rmd.electricity_emission_labels[
                                remind_technology
                            ],
                        )
                    ].values.item(0)

                    if exc["amount"] == 0:
                        wurst.rescale_exchange(
                            exc, remind_emission / 1, remove_uncertainty=True
                        )
                    else:
                        wurst.rescale_exchange(exc, remind_emission / exc["amount"])

        return self.db

    def update_heat_markets(self):
        """
        Delete existing heat markets. Create new markets for heat.
        Link heat-consuming datasets to newly created market groups for heat.
        Return a wurst database with modified datasets.

        :return: a wurst database with new market groups for heat
        :rtype: list
        """
        # We first need to delete 'market for heat' and 'market group for heat' datasets
        print("Remove old markets datasets")
        list_to_remove = [
            "market for heat,",
            "market group for heat,",
        ]

        # Writing log of deleted markets
        markets_to_delete = [
            [i["name"], i["location"]]
            for i in self.db
            if any(stop in i["name"] for stop in list_to_remove)
        ]

        if not os.path.exists(DATA_DIR / "logs"):
            os.makedirs(DATA_DIR / "logs")

        with open(
            DATA_DIR
            / "logs/log deleted markets {} {}-{}.csv".format(
                self.scenario, self.year, date.today()
            ),
            "w",
        ) as csv_file:
            writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")
            writer.writerow(["dataset name", "location"])
            for line in markets_to_delete:
                writer.writerow(line)

        self.db = [
            i for i in self.db if not any(stop in i["name"] for stop in list_to_remove)
        ]

        # We then need to create high voltage REMIND electricity markets
        print("Create heat markets.")
        self.create_new_heat_markets()

        # Finally, we need to relink all electricity-consuming activities to the new electricity markets
        print("Link activities to new electricity markets.")
        self.relink_activities_to_new_markets()

        print(
            "Log of deleted electricity markets saved in {}".format(DATA_DIR / "logs")
        )
        print(
            "Log of created electricity markets saved in {}".format(DATA_DIR / "logs")
        )

        return self.db
