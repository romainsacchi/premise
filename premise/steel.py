import wurst
from wurst import searching as ws
from wurst.searching import NoResults
import itertools
from .geomap import Geomap
from .activity_maps import InventorySet
from .utils import *
import uuid
import copy


class Steel:
    """
    Class that modifies steel markets in ecoinvent based on REMIND output data.

    :ivar db: database dictionary from :attr:`.NewDatabase.db`
    :vartype db: dict
    :ivar model: can be 'remind' or 'image'. str from :attr:`.NewDatabase.model`
    :vartype model: str
    :ivar rmd: xarray that contains IAM data, from :attr:`.NewDatabase.rdc`
    :vartype rmd: xarray.DataArray
    :ivar year: year, from :attr:`.NewDatabase.year`
    :vartype year: int
    
    """

    def __init__(self, db, model, rmd, year):
        self.db = db
        self.rmd = rmd
        self.year = year
        self.steel_data = self.rmd.data.interp(year=self.year)
        self.fuels_lhv = get_lower_heating_values()
        self.fuels_co2 = get_fuel_co2_emission_factors()
        self.remind_fuels = get_correspondance_remind_to_fuels()
        self.geo = Geomap(model=model)
        mapping = InventorySet(self.db)
        self.emissions_map = mapping.get_remind_to_ecoinvent_emissions()
        self.fuel_map = mapping.generate_fuel_map()
        self.material_map = mapping.generate_material_map()

    def fetch_proxies(self, name):
        """
        Fetch dataset proxies, given a dataset `name`.
        Store a copy for each REMIND region.
        If a REMIND region does not find a fitting ecoinvent location,
        fetch a dataset with a "RoW" location.
        Delete original datasets from the database.

        :return:
        """
        d_map = {
            self.geo.ecoinvent_to_iam_location(d['location']): d['location']
            for d in ws.get_many(
                self.db,
                ws.equals("name", name)
            )
        }

        list_remind_regions = [
            c[1] for c in self.geo.geo.keys()
            if type(c) == tuple and c[0] == "REMIND"
        ]

        if 'market' in name:
            d_remind_to_eco = {r: d_map.get(r, "GLO") for r in list_remind_regions}
        else:
            d_remind_to_eco = {r: d_map.get(r, "RoW") for r in list_remind_regions}

        d_act = {}

        for d in d_remind_to_eco:
            try:
                ds = ws.get_one(
                    self.db,
                    ws.equals("name", name),
                    ws.contains("reference product", "steel"),
                    ws.equals("location", d_remind_to_eco[d]),
                )

            except ws.NoResults:
                print('No dataset {} found for the REMIND region {}'.format(name, d))
                continue
            except ws.MultipleResults:
                print("Multiple results for {} found for the REMIND region {}".format(name, d))

                ds = ws.get_many(
                    self.db,
                    ws.equals("name", name),
                    ws.contains("reference product", "steel"),
                    ws.equals("location", d_remind_to_eco[d]),
                )

                for x in ds:
                    print(x["name"], x["location"], x["reference product"])

                raise

            d_act[d] = copy.deepcopy(ds)
            d_act[d]["location"] = d
            d_act[d]["code"] = str(uuid.uuid4().hex)

            if "input" in d_act[d]:
                d_act[d].pop("input")


            for prod in ws.production(d_act[d]):
                prod['location'] = d

                if "input" in prod:
                    prod.pop("input")

        deleted_markets = [
            (act['name'], act['reference product'], act['location']) for act in self.db
                   if act["name"] == name
        ]

        with open(DATA_DIR / "logs/log deleted steel datasets.csv", "a") as csv_file:
            writer = csv.writer(csv_file,
                                delimiter=';',
                                lineterminator='\n')
            for line in deleted_markets:
                writer.writerow(line)

        # Remove old datasets
        self.db = [act for act in self.db
                   if act["name"] != name]


        return d_act

    @staticmethod
    def remove_exchanges(d, list_exc):

        keep = lambda x: {
            k: v
            for k, v in x.items()
            if not any(ele in x["name"] for ele in list_exc)
        }

        for r in d:
            d[r]["exchanges"] = [keep(exc) for exc in d[r]["exchanges"]]
            d[r]["exchanges"] = [v for v in d[r]["exchanges"] if v]

        return d

    @staticmethod
    def get_shares_from_production_volume(ds):
        """
        Return shares of supply based on production volumes
        :param ds: list of datasets
        :return: dictionary with (dataset name, dataset location) as keys, shares as values. Shares total 1.
        :rtype: dict
        """
        dict_act = {}
        total_production_volume = 0
        for act in ds:
            for exc in ws.production(act):
                dict_act[(act["name"], act["location"], act["reference product"], act["unit"])] = float(
                    exc.get("production volume", 1)
                )
                total_production_volume += float(exc.get("production volume", 1))

        for d in dict_act:
            dict_act[d] /= total_production_volume

        return dict_act

    def get_suppliers_of_a_region(
            self, iam_regions, ecoinvent_technologies, reference_product
    ):
        """
        Return a list of datasets which location and name correspond to the region, name and reference product given,
        respectively.

        :param iam_regions: list of REMIND regions
        :type iam_regions: list
        :param ecoinvent_technologies: list of names of ecoinvent dataset
        :type ecoinvent_technologies: list
        :param reference_product: reference product
        :type reference_product: str
        :return: list of wurst datasets
        :rtype: list
        """
        list_regions = [self.geo.iam_to_ecoinvent_location(region)
                        for region in iam_regions]
        list_regions = [x for y in list_regions for x in y]

        return ws.get_many(
            self.db,
            *[
                ws.either(
                    *[
                        ws.equals("name", supplier)
                        for supplier in ecoinvent_technologies
                    ]
                ),
                ws.either(
                    *[
                        ws.equals("location", loc)
                        for loc in list_regions
                    ]
                ),
                ws.equals("reference product", reference_product),
            ]
        )

    def relink_datasets(self, name, ref_product):
        """
        For a given dataset name, change its location to a REMIND location,
        to effectively link the newly built dataset(s).

        :param ref_product:
        :param name: dataset name
        :type name: str
        """
        list_remind_regions = [
            c[1] for c in self.geo.geo.keys() if type(c) == tuple and c[0] == "REMIND"
        ]

        for act in self.db:
            for exc in act['exchanges']:
                try:
                    exc["name"]
                except KeyError:
                    print(exc)
                if (exc['name'], exc.get('product')) == (name, ref_product) and exc['type'] == 'technosphere':
                    if act['location'] not in list_remind_regions:
                        if act['location'] == "North America without Quebec":
                            exc['location'] = 'USA'
                        else:
                            try:
                                exc['location'] = self.geo.ecoinvent_to_iam_location(act['location'])
                            except:
                                print("cannot find for {}".format(act["location"]))
                    else:
                        exc['location'] = act['location']

    def update_pollutant_emissions(self, ds):
        """
        Update pollutant emissions based on GAINS data.
        :return:
        """

        # Update biosphere exchanges according to GAINS emission values
        for exc in ws.biosphere(
                ds, ws.either(*[ws.contains("name", x) for x in self.emissions_map])
            ):
            remind_emission_label = self.emissions_map[exc["name"]]

            try:
                remind_emission = self.rmd.steel_emissions.loc[
                    dict(
                        region=ds["location"],
                        pollutant=remind_emission_label
                    )
                ].values.item(0)
            except KeyError:
                # TODO: fix this.
                # GAINS does not have a 'World' region, hence we use China as a temporary fix
                remind_emission = self.rmd.steel_emissions.loc[
                    dict(
                        region='CHA',
                        pollutant=remind_emission_label
                    )
                ].values.item(0)


            if exc["amount"] == 0:
                wurst.rescale_exchange(
                    exc, remind_emission / 1, remove_uncertainty=True
                )
            else:
                wurst.rescale_exchange(exc, remind_emission / exc["amount"])
        return ds

    def adjust_recycled_steel_share(self, dict_act):
        """
        Adjust the supply shares of primary and secondary steel, based on REMIND data.

        :param dict_act: dictionary with REMIND region as keys and datasets as values.
        :type dict_act: dict
        :return: same dictionary, with modified exchanges
        :rtype: dict
        """

        dict_act = self.remove_exchanges(dict_act, ['steel production'])

        for d, act in dict_act.items():
            remind_region = d

            total_production_volume = self.steel_data.sel(region=remind_region, variables='Production|Industry|Steel')
            primary_share = (self.steel_data.sel(region=remind_region, variables='Production|Industry|Steel|Primary') / total_production_volume).values
            secondary_share = 1 - primary_share

            print(d, act["name"], act["location"])


            try:
                ds = ws.get_one(self.db,
                           ws.equals('reference product', act['reference product']),
                           ws.contains('name', 'steel production'),
                           ws.contains('name', 'converter'),
                            ws.contains('location', 'RoW'))

                act['exchanges'].append(
                    {
                        "uncertainty type": 0,
                        "loc": 1,
                        "amount": primary_share,
                        "type": "technosphere",
                        "production volume": 1,
                        "product": ds['reference product'],
                        "name": ds['name'],
                        "unit": ds['unit'],
                        "location": remind_region,
                    }
                )
            except NoResults:
                secondary_share = 1

            ds = ws.get_one(self.db,
                       ws.equals('reference product', act['reference product']),
                       ws.contains('name', 'steel production'),
                       ws.contains('name', 'electric'),
                       ws.contains('location', 'RoW'))

            act['exchanges'].append(
                {
                    "uncertainty type": 0,
                    "loc": 1,
                    "amount": secondary_share,
                    "type": "technosphere",
                    "production volume": 1,
                    "product": ds['reference product'],
                    "name": ds['name'],
                    "unit": ds['unit'],
                    "location": remind_region,
                }
            )

        return dict_act

    def generate_activities(self):
        """
        This function generates new activities for primary and secondary steel production and add them to the ecoinvent db.
        
        :return: NOTHING. Returns a modified database with newly added steel activities for the corresponding year
        """

        print("The validity of the datasets produced from the integration of the steel sector is not yet fully tested. Consider the results with caution.")

        print('Log of deleted cement datasets saved in {}'.format(DATA_DIR / 'logs'))
        print('Log of created cement datasets saved in {}'.format(DATA_DIR / 'logs'))

        with open(DATA_DIR / "logs/log deleted steel datasets.csv", "w") as csv_file:
            writer = csv.writer(csv_file,
                                delimiter=';',
                                lineterminator='\n')
            writer.writerow(['dataset name', 'reference product', 'location'])

        with open(DATA_DIR / "logs/log created steel datasets.csv", "w") as csv_file:
            writer = csv.writer(csv_file,
                                delimiter=';',
                                lineterminator='\n')
            writer.writerow(['dataset name', 'reference product', 'location'])


        print('Create steel markets for differention regions')
        print('Adjust primary and secondary steel supply shares in steel markets')

        created_datasets = list()
        for i in (
                  ("market for steel, low-alloyed", "steel, low-alloyed"),
                  ("market for steel, chromium steel 18/8", "steel, chromium steel 18/8")
                  ):
            act_steel = self.fetch_proxies(i[0])
            act_steel = self.adjust_recycled_steel_share(act_steel)
            self.db.extend([v for v in act_steel.values()])

            created_datasets.extend([(act['name'], act['reference product'], act['location'])
                            for act in act_steel.values()])

            self.relink_datasets(i[0], i[1])


        for i in (
                  ("market for steel, unalloyed", "steel, unalloyed"),
                  ("market for steel, chromium steel 18/8, hot rolled", "steel, chromium steel 18/8, hot rolled"),
                  ("market for steel, low-alloyed, hot rolled", "steel, low-alloyed, hot rolled")
                  ):
            act_steel = self.fetch_proxies(i[0])
            self.db.extend([v for v in act_steel.values()])

            created_datasets.extend([(act['name'], act['reference product'], act['location'])
                            for act in act_steel.values()])

            self.relink_datasets(i[0], i[1])

        print('Relink new steel markets to steel-consuming activities')

        # Determine all steel activities in the db. Delete old datasets.
        print('Create new steel production datasets and delete old datasets')
        d_act_primary_steel = {mat: self.fetch_proxies(mat) for mat in self.material_map['steel, primary']}
        d_act_secondary_steel = {mat: self.fetch_proxies(mat) for mat in self.material_map['steel, secondary']}
        d_act_steel = {**d_act_primary_steel, **d_act_secondary_steel}

                
        # Delete fuel exchanges and delete empty exchanges. Fuel exchanges to remove:
        list_fuels = [
                    "diesel",
                    "coal",
                    "lignite",
                    "coke",
                    "fuel",
                    "meat",
                    "gas",
                    "oil",
                    "electricity",
                    ]

        d_act_steel = {k: self.remove_exchanges(v, list_fuels) for k, v in d_act_steel.items()}

        # List final energy carriers used in steel production
        l_FE = [v.split('|') for v in self.steel_data.coords['variables'].values
                if "FE" in v and "steel" in v.lower()
                    and 'electricity' not in v.lower()]

        # List second energy carriers
        l_SE = [v.split('|') for v in self.steel_data.coords['variables'].values
                if "SE" in v
                and 'electricity' not in v.lower()
                and 'fossil' not in v.lower()]

        # Filter second energy carriers used in steel production
        # TODO: for now, we ignore CCS
        list_second_fuels = sorted(list(set(['|'.join(x) for x in l_SE if len(x) == 3 for y in l_FE if y[2] in x])))
        list_second_fuels = [list(g) for _, g in itertools.groupby(list_second_fuels, lambda x: x.split('|')[1])]

        d_fuel_types = {
            'SE|Gases|Biomass': 'biogas',
            'SE|Gases|Coal': 'gas from coal',
            'SE|Gases|Hydrogen': 'hydrogen',
            'SE|Gases|Natural Gas': 'natural gas',
            'SE|Gases|Non-Biomass': 'natural gas',
            'SE|Gases|Waste': 'biogas',
            #'SE|Heat|Biomass': 'heat from biomass',
            #'SE|Heat|CHP': 'heat from CHP',
            #'SE|Heat|Coal': 'heat from coal',
            #'SE|Heat|Gas': 'heat from gas',
            #'SE|Heat|Geothermal': 'heat from geothermal',
            'SE|Hydrogen|Biomass': 'hydrogen from biomass',
            'SE|Hydrogen|Coal': 'hydrogen from coal',
            'SE|Hydrogen|Gas': 'hydrogen from natural gas',
            'SE|Liquids|Biomass': 'bioethanol',
            'SE|Liquids|Coal': 'synthetic diesel from coal',
            'SE|Liquids|Gas': 'synthetic fuel from natural gas',
            'SE|Liquids|Hydrogen': 'syntehtic fuel from natural gas',
            'SE|Liquids|Oil': 'light fuel oil',
            'SE|Solids|Biomass': 'waste',
            'SE|Solids|Coal': 'hard coal',
            'SE|Solids|Traditional Biomass': 'wood pellet'
        }

        print("list_second_fuels", list_second_fuels)
        print("REMIND fuels", self.remind_fuels)

        # Loop through primary steel technologies
        for d in d_act_steel:

            # Loop through REMIND regions
            for k in d_act_steel[d]:

                fuel_fossil_co2, fuel_biogenic_co2 = 0, 0

                # Get amount of fuel per fuel type
                for count, fuel_type in enumerate(['|'.join(y) for y in l_FE if 'Primary' in y]):

                    # Amount of specific fuel, for a specific region
                    fuel_amount = self.steel_data.sel(variables=fuel_type, region=k)\
                          * (self.steel_data.sel(variables=list_second_fuels[count], region=k)
                             / self.steel_data.sel(variables=list_second_fuels[count], region=k).sum(dim='variables'))

                    # Divide the amount of fuel by steel production, to get unitary efficiency
                    fuel_amount /= self.steel_data.sel(region=k, variables='Production|Industry|Steel|Primary')

                    # Convert from EJ per Mt steel to MJ per kg steel
                    fuel_amount *= 1000

                    for c, i in enumerate(fuel_amount):
                        if i > 0:
                            fuel_name, activity_name, fuel_ref_prod = self.remind_fuels[list_second_fuels[count][c]].values()
                            fuel_lhv = self.fuels_lhv[fuel_name]
                            fuel_qty = i.values.item(0) / fuel_lhv
                            fuel_fossil_co2 += fuel_qty * self.fuels_co2[fuel_name]["co2"] * (1 - self.fuels_co2[fuel_name]["bio_share"])
                            fuel_biogenic_co2 += fuel_qty * self.fuels_co2[fuel_name]["co2"] * self.fuels_co2[fuel_name]["bio_share"]

                            # Fetch respective shares based on production volumes
                            fuel_suppliers = self.get_shares_from_production_volume(
                                self.get_suppliers_of_a_region([k],
                                                               [activity_name],
                                                               fuel_ref_prod))
                            if len(fuel_suppliers) == 0:
                                fuel_suppliers = self.get_shares_from_production_volume(
                                    self.get_suppliers_of_a_region(['World', 'EUR'],
                                                                   [activity_name],
                                                                   fuel_ref_prod))
                            new_exchanges = []
                            for supplier in fuel_suppliers:
                                new_exchanges.append({
                                    "uncertainty type": 0,
                                    "loc": 1,
                                    "amount": fuel_suppliers[supplier] * fuel_qty,
                                    "type": "technosphere",
                                    "production volume": 1,
                                    "product": supplier[2],
                                    "name": supplier[0],
                                    "unit": supplier[3],
                                    "location": supplier[1],
                                })

                            d_act_steel[d][k]['exchanges'].extend(new_exchanges)

                # Update fossil CO2 exchange
                try:
                    fossil_co2_exc = [e for e in d_act_steel[d][k]['exchanges'] if e['name'] == 'Carbon dioxide, fossil'][0]
                    fossil_co2_exc['amount'] = fuel_fossil_co2
                    fossil_co2_exc['uncertainty type'] = 0
                except IndexError:
                    # There isn't a fossil CO2 emissions exchange (e.g., electric furnace)
                    fossil_co2_exc = {
                        "uncertainty type": 0,
                        "loc": 1,
                        "amount": fuel_fossil_co2,
                        "type": "biosphere",
                        "production volume": 0,
                        "name": "Carbon dioxide, non-fossil",
                        "unit": "kilogram",
                        "input": ('biosphere3', 'eba59fd6-f37e-41dc-9ca3-c7ea22d602c7'),
                        "categories": ('air',),
                    }
                    d_act_steel[d][k]['exchanges'].append(fossil_co2_exc)

                try:
                    # Update biogenic CO2 exchange, minus CO2 captured
                    biogenic_co2_exc = [e for e in d_act_steel[d][k]['exchanges'] if e['name'] == 'Carbon dioxide, non-fossil'][0]
                    biogenic_co2_exc['amount'] = fuel_biogenic_co2
                    biogenic_co2_exc['uncertainty type'] = 0

                except IndexError:
                    # There isn't a biogenic CO2 emissions exchange
                    biogenic_co2_exc = {
                        "uncertainty type": 0,
                        "loc": 1,
                        "amount": fuel_biogenic_co2,
                        "type": "biosphere",
                        "production volume": 0,
                        "name": "Carbon dioxide, non-fossil",
                        "unit": "kilogram",
                        "input": ('biosphere3', 'eba59fd6-f37e-41dc-9ca3-c7ea22d602c7'),
                        "categories": ('air',),
                    }
                    d_act_steel[d][k]['exchanges'].append(biogenic_co2_exc)

                # Electricity consumption per kg of steel
                # Electricity, in EJ per year, divided by steel production, in Mt per year
                # Convert to obtain kWh/kg steel
                if d in self.material_map['steel, primary']:

                    electricity = (self.steel_data.sel(region=k, variables = 'FE|Industry|Electricity|Steel|Primary').values
                                                            / self.steel_data.sel(region=k,
                                                                                  variables='Production|Industry|Steel|Primary').values)\
                                * 1000 / 3.6

                else:

                    electricity = (self.steel_data.sel(region=k, variables = 'FE|Industry|Electricity|Steel|Secondary').values
                                                            / self.steel_data.sel(region=k,
                                                                                  variables='Production|Industry|Steel|Secondary').values)\
                                * 1000 / 3.6


                # Add electricity exchange
                d_act_steel[d][k]['exchanges'].append({
                                "uncertainty type": 0,
                                "loc": 1,
                                "amount": electricity,
                                "type": "technosphere",
                                "production volume": 0,
                                "product": 'electricity, medium voltage',
                                "name": 'market group for electricity, medium voltage',
                                "unit": 'kilowatt hour',
                                "location": k,
                            })

                # Relink all activities to the newly created activities

                name = d_act_steel[d][k]['name']
                ref_prod = d_act_steel[d][k]['reference product']



            # Update non fuel-related emissions according to GAINS
            d_act_steel[d] = {k: self.update_pollutant_emissions(v) for k, v in d_act_steel[d].items()}

            self.db.extend([v for v in d_act_steel[d].values()])

            # Relink new steel activities to steel-consuming activities
            self.relink_datasets(name, ref_prod)

            created_datasets.extend([(act['name'], act['reference product'], act['location'])
                                for act in d_act_steel[d].values()])

        print('Relink new steel production activities to specialty steel markets and other steel-consuming activities ')

        with open(DATA_DIR / "logs/log created steel datasets.csv", "a") as csv_file:
            writer = csv.writer(csv_file,
                                delimiter=';',
                                lineterminator='\n')
            for line in created_datasets:
                writer.writerow(line)

        return self.db
