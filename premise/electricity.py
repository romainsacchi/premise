import os
from . import DATA_DIR
from .activity_maps import InventorySet
from .geomap import Geomap
from wurst import searching as ws
import csv
import numpy as np
import uuid
import wurst
from .utils import get_lower_heating_values
from datetime import date

PRODUCTION_PER_TECH = (
    DATA_DIR / "electricity" / "electricity_production_volumes_per_tech.csv"
)
LOSS_PER_COUNTRY = DATA_DIR / "electricity" / "losses_per_country.csv"
LHV_FUELS = DATA_DIR / "fuels_lower_heating_value.txt"


class Electricity:
    """
    Class that modifies electricity markets in ecoinvent based on IAM output data.

    :ivar scenario: name of an IAM scenario
    :vartype scenario: str

    """

    def __init__(self, db, rmd, model, scenario, year):
        self.db = db
        self.rmd = rmd
        self.model = model
        self.geo = Geomap(model=model)
        self.production_per_tech = self.get_production_per_tech_dict()
        self.losses = self.get_losses_per_country_dict()
        self.scenario = scenario
        self.year = year
        self.fuels_lhv = get_lower_heating_values()
        mapping = InventorySet(self.db)
        self.emissions_map = mapping.get_remind_to_ecoinvent_emissions()
        self.powerplant_map = mapping.generate_powerplant_map()
        self.powerplant_fuels_map = mapping.generate_powerplant_fuels_map()

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

    @staticmethod
    def get_losses_per_country_dict():
        """
        Create a dictionary with ISO country codes as keys and loss ratios as values.
        :return: ISO country code to loss ratio dictionary
        :rtype: dict
        """

        if not LOSS_PER_COUNTRY.is_file():
            raise FileNotFoundError(
                "The production per country dictionary file could not be found."
            )

        with open(LOSS_PER_COUNTRY) as f:
            csv_list = [[val.strip() for val in r.split(";")] for r in f.readlines()]

        (_, *header), *data = csv_list
        csv_dict = {}
        for row in data:
            key, *values = row
            csv_dict[key] = {key: float(value) for key, value in zip(header, values)}

        return csv_dict

    @staticmethod
    def get_production_per_tech_dict():
        """
        Create a dictionary with tuples (technology, country) as keys and production volumes as values.
        :return: technology to production volume dictionary
        :rtype: dict
        """

        if not PRODUCTION_PER_TECH.is_file():
            raise FileNotFoundError(
                "The production per technology dictionary file could not be found."
            )
        csv_dict = {}
        with open(PRODUCTION_PER_TECH) as f:
            input_dict = csv.reader(f, delimiter=";")
            for row in input_dict:
                csv_dict[(row[0], row[1])] = row[2]

        return csv_dict

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
        locations = self.geo.iam_to_ecoinvent_location(remind_region)

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

    def create_new_markets_low_voltage(self):
        """
        Create low voltage market groups for electricity, by receiving medium voltage market groups as inputs
        and adding transformation and distribution losses.
        Contribution from solar power is added here as well.
        Does not return anything. Modifies the database in place.
        """
        # Loop through REMIND regions

        for region in self.rmd.electricity_markets.coords["region"].values:
            created_markets = []
            # Create an empty dataset
            new_dataset = {
                "location": region,
                "name": "market group for electricity, low voltage",
                "reference product": "electricity, low voltage",
                "unit": "kilowatt hour",
                "database": self.db[1]["database"],
                "code": str(uuid.uuid4().hex),
                "comment": "Dataset produced from REMIND scenario output results",
            }

            # First, add the reference product exchange
            new_exchanges = [
                {
                    "uncertainty type": 0,
                    "loc": 1,
                    "amount": 1,
                    "type": "production",
                    "production volume": 0,
                    "product": "electricity, low voltage",
                    "name": "market group for electricity, low voltage",
                    "unit": "kilowatt hour",
                    "location": region,
                },
                {
                    "uncertainty type": 0,
                    "loc": 2.99e-9,
                    "amount": 2.99e-9,
                    "type": "technosphere",
                    "production volume": 0,
                    "product": "sulfur hexafluoride, liquid",
                    "name": "market for sulfur hexafluoride, liquid",
                    "unit": "kilogram",
                    "location": "RoW",
                },
                {
                    "uncertainty type": 0,
                    "loc": 2.99e-9,
                    "amount": 2.99e-9,
                    "type": "biosphere",
                    "input": ("biosphere3", "35d1dff5-b535-4628-9826-4a8fce08a1f2"),
                    "name": "Sulfur hexafluoride",
                    "unit": "kilogram",
                    "categories": ("air", "non-urban air or from high stacks"),
                },
                {
                    "uncertainty type": 0,
                    "loc": 8.74e-8,
                    "amount": 8.74e-8,
                    "type": "technosphere",
                    "production volume": 0,
                    "product": "distribution network, electricity, low voltage",
                    "name": "distribution network construction, electricity, low voltage",
                    "unit": "kilometer",
                    "location": "RoW",
                },
            ]

            # Second, add an input to of sulfur hexafluoride emission to compensate the transformer's leakage
            # And an emission of a corresponding amount

            # Third, transmission line

            # Fourth, add the contribution of solar power
            solar_amount = 0
            gen_tech = list(
                (
                    tech
                    for tech in self.rmd.electricity_markets.coords["variables"].values
                    if "Solar" in tech
                )
            )
            for technology in gen_tech:
                # If the solar power technology contributes to the mix
                if self.rmd.electricity_markets.loc[region, technology] != 0.0:
                    # Fetch ecoinvent regions contained in the REMIND region
                    ecoinvent_regions = self.geo.iam_to_ecoinvent_location(region)

                    # Contribution in supply
                    amount = self.rmd.electricity_markets.loc[region, technology].values
                    solar_amount += amount

                    # Get the possible names of ecoinvent datasets
                    ecoinvent_technologies = self.powerplant_map[
                        self.rmd.rev_electricity_market_labels[technology]
                    ]

                    # Fetch electricity-producing technologies contained in the REMIND region
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

                    for supplier in suppliers:
                        share = self.get_production_weighted_share(supplier, suppliers)

                        new_exchanges.append(
                            {
                                "uncertainty type": 0,
                                "loc": (amount * share),
                                "amount": (amount * share),
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
                                "low voltage, " + self.scenario + ", " + str(self.year),
                                "n/a",
                                region,
                                0,
                                0,
                                supplier["name"],
                                supplier["location"],
                                share,
                                (share * amount),
                            ]
                        )
            # Fifth, add:
            # * an input from the medium voltage market minus solar contribution, including distribution loss
            # * an self-consuming input for transformation loss

            transf_loss, distr_loss = self.get_production_weighted_losses("low", region)

            new_exchanges.append(
                {
                    "uncertainty type": 0,
                    "loc": 0,
                    "amount": (1 - solar_amount) * (1 + distr_loss),
                    "type": "technosphere",
                    "production volume": 0,
                    "product": "electricity, medium voltage",
                    "name": "market group for electricity, medium voltage",
                    "unit": "kilowatt hour",
                    "location": region,
                }
            )

            new_exchanges.append(
                {
                    "uncertainty type": 0,
                    "loc": 0,
                    "amount": transf_loss,
                    "type": "technosphere",
                    "production volume": 0,
                    "product": "electricity, low voltage",
                    "name": "market group for electricity, low voltage",
                    "unit": "kilowatt hour",
                    "location": region,
                }
            )

            created_markets.append(
                [
                    "low voltage, " + self.scenario + ", " + str(self.year),
                    "n/a",
                    region,
                    transf_loss,
                    distr_loss,
                    "low voltage, " + self.scenario + ", " + str(self.year),
                    region,
                    1,
                    (1 - solar_amount) * (1 + distr_loss),
                ]
            )

            with open(
                DATA_DIR
                / "logs/log created electricity markets {} {}-{}.csv".format(
                    self.scenario, self.year, date.today()
                ),
                "a",
            ) as csv_file:
                writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")
                for line in created_markets:
                    writer.writerow(line)

            new_dataset["exchanges"] = new_exchanges
            self.db.append(new_dataset)

    def create_new_markets_medium_voltage(self):
        """
        Create medium voltage market groups for electricity, by receiving high voltage market groups as inputs
        and adding transformation and distribution losses.
        Contribution from solar power is added in low voltage market groups.
        Does not return anything. Modifies the database in place.
        """
        # Loop through REMIND regions
        gen_region = (
            region for region in self.rmd.electricity_markets.coords["region"].values
        )

        created_markets = []

        for region in gen_region:
            # Create an empty dataset
            new_dataset = {
                "location": region,
                "name": "market group for electricity, medium voltage",
                "reference product": "electricity, medium voltage",
                "unit": "kilowatt hour",
                "database": self.db[1]["database"],
                "code": str(uuid.uuid1().hex),
                "comment": "Dataset produced from REMIND scenario output results",
            }

            # First, add the reference product exchange
            new_exchanges = [
                {
                    "uncertainty type": 0,
                    "loc": 1,
                    "amount": 1,
                    "type": "production",
                    "production volume": 0,
                    "product": "electricity, medium voltage",
                    "name": "market group for electricity, medium voltage",
                    "unit": "kilowatt hour",
                    "location": region,
                }
            ]

            # Second, add:
            # * an input from the high voltage market, including transmission loss
            # * an self-consuming input for transformation loss

            transf_loss, distr_loss = self.get_production_weighted_losses(
                "medium", region
            )
            new_exchanges.append(
                {
                    "uncertainty type": 0,
                    "loc": 0,
                    "amount": 1 + distr_loss,
                    "type": "technosphere",
                    "production volume": 0,
                    "product": "electricity, high voltage",
                    "name": "market group for electricity, high voltage",
                    "unit": "kilowatt hour",
                    "location": region,
                }
            )

            new_exchanges.append(
                {
                    "uncertainty type": 0,
                    "loc": 0,
                    "amount": transf_loss,
                    "type": "technosphere",
                    "production volume": 0,
                    "product": "electricity, medium voltage",
                    "name": "market group for electricity, medium voltage",
                    "unit": "kilowatt hour",
                    "location": region,
                }
            )

            # Third, add an input to of sulfur hexafluoride emission to compensate the transformer's leakage
            # And an emission of a corresponding amount
            new_exchanges.append(
                {
                    "uncertainty type": 0,
                    "loc": 5.4e-8,
                    "amount": 5.4e-8,
                    "type": "technosphere",
                    "production volume": 0,
                    "product": "sulfur hexafluoride, liquid",
                    "name": "market for sulfur hexafluoride, liquid",
                    "unit": "kilogram",
                    "location": "RoW",
                }
            )
            new_exchanges.append(
                {
                    "uncertainty type": 0,
                    "loc": 5.4e-8,
                    "amount": 5.4e-8,
                    "type": "biosphere",
                    "input": ("biosphere3", "35d1dff5-b535-4628-9826-4a8fce08a1f2"),
                    "name": "Sulfur hexafluoride",
                    "unit": "kilogram",
                    "categories": ("air", "non-urban air or from high stacks"),
                }
            )

            # Fourth, transmission line
            new_exchanges.append(
                {
                    "uncertainty type": 0,
                    "loc": 1.8628e-8,
                    "amount": 1.8628e-8,
                    "type": "technosphere",
                    "production volume": 0,
                    "product": "transmission network, electricity, medium voltage",
                    "name": "transmission network construction, electricity, medium voltage",
                    "unit": "kilometer",
                    "location": "RoW",
                }
            )

            new_dataset["exchanges"] = new_exchanges

            created_markets.append(
                [
                    "medium voltage, " + self.scenario + ", " + str(self.year),
                    "n/a",
                    region,
                    transf_loss,
                    distr_loss,
                    "medium voltage, " + self.scenario + ", " + str(self.year),
                    region,
                    1,
                    1 + distr_loss,
                ]
            )

            self.db.append(new_dataset)

        with open(
            DATA_DIR
            / "logs/log created electricity markets {} {}-{}.csv".format(
                self.scenario, self.year, date.today()
            ),
            "a",
        ) as csv_file:
            writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")
            for line in created_markets:
                writer.writerow(line)

    def create_new_markets_high_voltage(self):
        """
        Create high voltage market groups for electricity, based on electricity mixes given by REMIND.
        Contribution from solar power is added in low voltage market groups.
        Does not return anything. Modifies the database in place.
        """
        # Loop through REMIND regions
        gen_region = (
            region for region in self.rmd.electricity_markets.coords["region"].values
        )
        gen_tech = list(
            (
                tech
                for tech in self.rmd.electricity_markets.coords["variables"].values
                if "Solar" not in tech
            )
        )

        created_markets = []

        for region in gen_region:

            # Fetch ecoinvent regions contained in the REMIND region
            ecoinvent_regions = self.geo.iam_to_ecoinvent_location(region)

            # Create an empty dataset
            new_dataset = {
                "location": region,
                "name": "market group for electricity, high voltage",
                "reference product": "electricity, high voltage",
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
                    "product": "electricity, high voltage",
                    "name": "market group for electricity, high voltage",
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
                    "product": "electricity, high voltage",
                    "name": "market group for electricity, high voltage",
                    "unit": "kilowatt hour",
                    "location": region,
                }
            )

            # Fetch solar contribution in the mix, to subtract it
            # as solar energy is an input of low-voltage markets

            index_solar = [
                ind
                for ind in self.rmd.rev_electricity_market_labels
                if "solar" in ind.lower()
            ]
            solar_amount = self.rmd.electricity_markets.loc[
                region, index_solar
            ].values.sum()

            # Loop through the REMIND technologies
            for technology in gen_tech:

                # If the given technology contributes to the mix
                if self.rmd.electricity_markets.loc[region, technology] != 0.0:

                    # Contribution in supply
                    amount = self.rmd.electricity_markets.loc[region, technology].values

                    # Get the possible names of ecoinvent datasets
                    ecoinvent_technologies = self.powerplant_map[
                        self.rmd.rev_electricity_market_labels[technology]
                    ]

                    # Fetch electricity-producing technologies contained in the REMIND region
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
            / "logs/log created electricity markets {} {}-{}.csv".format(
                self.scenario, self.year, date.today()
            ),
            "w",
        ) as csv_file:
            writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")
            writer.writerow(
                [
                    "dataset name",
                    "energy type",
                    "IAM location",
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
        Links electricity input exchanges to new datasets with the appropriate IAM location:
        * "market for electricity, high voltage" --> "market group for electricity, high voltage"
        * "market for electricity, medium voltage" --> "market group for electricity, medium voltage"
        * "market for electricity, low voltage" --> "market group for electricity, low voltage"
        Does not return anything.
        """

        # Filter all activities that consume high voltage electricity

        for ds in ws.get_many(
            self.db, ws.exclude(ws.contains("name", "market group for electricity"))
        ):

            for exc in ws.get_many(
                ds["exchanges"],
                *[
                    ws.either(
                        *[
                            ws.contains("name", "market for electricity"),
                            ws.contains("name", "electricity voltage transformation"),
                            ws.contains("name", "market group for electricity"),
                        ]
                    )
                ]
            ):
                if exc["type"] != "production" and exc["unit"] == "kilowatt hour":
                    if "high" in exc["product"]:
                        exc["name"] = "market group for electricity, high voltage"
                        exc["product"] = "electricity, high voltage"
                        exc["location"] = self.geo.ecoinvent_to_iam_location(
                            exc["location"]
                        )
                    if "medium" in exc["product"]:
                        exc["name"] = "market group for electricity, medium voltage"
                        exc["product"] = "electricity, medium voltage"
                        try:
                            exc["location"] = self.geo.ecoinvent_to_iam_location(
                                exc["location"]
                            )
                        except KeyError:
                            print(exc)
                    if "low" in exc["product"]:
                        exc["name"] = "market group for electricity, low voltage"
                        exc["product"] = "electricity, low voltage"
                        exc["location"] = self.geo.ecoinvent_to_iam_location(
                            exc["location"]
                        )
                if "input" in exc:
                    exc.pop("input")

    def find_ecoinvent_fuel_efficiency(self, ds, fuel_filters):
        """
        This method calculates the efficiency value set initially, in case it is not specified in the parameter
        field of the dataset. In Carma datasets, fuel inputs are expressed in megajoules instead of kilograms.

        :param ds: a wurst dataset of an electricity-producing technology
        :param fuel_filters: wurst filter to to filter fule input exchanges
        :return: the efficiency value set by ecoinvent
        """

        def calculate_input_energy(fuel_name, fuel_amount, fuel_unit):

            if fuel_unit == "kilogram" or fuel_unit == "cubic meter":

                lhv = [
                    self.fuels_lhv[k] for k in self.fuels_lhv if k in fuel_name.lower()
                ][0]
                return float(lhv) * fuel_amount / 3.6

            if fuel_unit == "megajoule":
                return fuel_amount / 3.6

            if fuel_unit == "kilowatt hour":
                return fuel_amount

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
                            calculate_input_energy(
                                exc["name"], exc["amount"], exc["unit"]
                            )
                            for exc in ds["exchanges"] if exc["name"] in fuel_filters
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
        to the efficiency given by the IAM.

        :param ds: wurst dataset of an electricity-producing technology
        :param fuel_filters: wurst filter to filter the fuel input exchanges
        :param technology: label of an electricity-producing technology
        :return: a rescale factor to change from ecoinvent efficiency to the efficiency given by the IAM
        :rtype: float
        """

        ecoinvent_eff = self.find_ecoinvent_fuel_efficiency(ds, fuel_filters)

        # If the current efficiency is too high, there's an issue, and the dataset is skipped.
        if ecoinvent_eff > 1.1:
            print(
                "The current efficiency factor for the dataset {} has not been found."
                "Its current efficiency will remain".format(
                    ds["name"]
                )
            )
            return 1

        # If the current efficiency is precisely 1, it is because it is not the actual power generation dataset
        # but an additional layer (for example, int eh case of CCS added to CHP).
        if ecoinvent_eff == 1:
            return 1

        remind_locations = self.geo.ecoinvent_to_iam_location(ds["location"])
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

        # Sometimes, the efficiency factor is set to 1, when not value si available
        # Therefore, we should ignore that
        if remind_eff == 1:
            return 1

        # Sometimes, the efficiency factor from the IAM is nto defined
        # Hence, we filter for "nan" and return a scaling factor of 1.

        if np.isnan(remind_eff):
            return 1

        with open(
            DATA_DIR
            / "logs/log power plant efficiencies change {} {} {}-{}.csv".format(
                self.model, self.scenario, self.year, date.today()
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

        return {
            tech: {
                "eff_func": self.find_fuel_efficiency_scaling_factor,
                "technology filters": self.powerplant_map[tech],
                "fuel filters": self.powerplant_fuels_map[tech],
            }
            for tech in self.rmd.electricity_efficiency_labels.keys()
        }

    def update_electricity_efficiency(self):
        """
        This method modifies each ecoinvent coal, gas,
        oil and biomass dataset using data from the REMIND model.
        Return a wurst database with modified datasets.

        :return: a wurst database, with rescaled electricity-producing datasets.
        :rtype: list
        """

        technologies_map = self.get_remind_mapping()

        if not os.path.exists(DATA_DIR / "logs"):
            os.makedirs(DATA_DIR / "logs")

        with open(
            DATA_DIR
            / "logs/log power plant efficiencies change {} {} {}-{}.csv".format(
                self.model, self.scenario, self.year, date.today()
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

            datasets = [d for d in self.db
                        if d["name"] in dict_technology["technology filters"]
                        and d["unit"] == "kilowatt hour"
                        ]

            # no activities found? Check filters!
            assert len(datasets) > 0, "No dataset found for {}".format(remind_technology)
            for ds in datasets:
                # Modify using remind efficiency values:
                scaling_factor = dict_technology["eff_func"](
                    ds, dict_technology["fuel filters"], remind_technology
                )
                self.update_ecoinvent_efficiency_parameter(ds, scaling_factor)

                # Rescale all the technosphere exchanges according to REMIND efficiency values
                wurst.change_exchanges_by_constant_factor(
                    ds,
                    float(scaling_factor),
                    [],
                    [ws.doesnt_contain_any("name", self.emissions_map)],
                )

                # Update biosphere exchanges according to GAINS emission values
                for exc in ws.biosphere(
                    ds, ws.either(*[ws.contains("name", x) for x in self.emissions_map])
                ):
                    remind_emission_label = self.emissions_map[exc["name"]]

                    remind_emission = self.rmd.electricity_emissions.loc[
                        dict(
                            region=self.geo.iam_to_GAINS_region(
                                self.geo.ecoinvent_to_iam_location(ds["location"])
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

    def update_electricity_markets(self):
        """
        Delete electricity markets. Create high, medium and low voltage market groups for electricity.
        Link electricity-consuming datasets to newly created market groups for electricity.
        Return a wurst database with modified datasets.

        :return: a wurst database with new market groups for electricity
        :rtype: list
        """
        # We first need to delete 'market for electricity' and 'market group for electricity' datasets
        print("Remove old electricity datasets")
        list_to_remove = [
            "market group for electricity, high voltage",
            "market group for electricity, medium voltage",
            "market group for electricity, low voltage",
            "market for electricity, high voltage",
            "market for electricity, medium voltage",
            "market for electricity, low voltage",
            "electricity, high voltage, import",
            "electricity, high voltage, production mix",
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
            / "logs/log deleted electricity markets {} {} {}-{}.csv".format(
                self.model, self.scenario, self.year, date.today()
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
        print("Create high voltage markets.")
        self.create_new_markets_high_voltage()
        print("Create medium voltage markets.")
        self.create_new_markets_medium_voltage()
        print("Create low voltage markets.")
        self.create_new_markets_low_voltage()

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
