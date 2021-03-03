from . import DATA_DIR

from wurst import searching as ws
import csv
import pprint
import wurst
import bw2io
from bw2data.database import DatabaseChooser

FILEPATH_FIX_NAMES = (DATA_DIR / "fix_names.csv")
FILEPATH_BIOSPHERE_FLOWS = (DATA_DIR / "dict_biosphere.txt")


class DatabaseCleaner:
    """
    Class that cleans the datasets contained in the inventory database for further processing.


    :ivar source_type: type of the database source. Can be ´brightway´ or 'ecospold'.
    :vartype source_type: str
    :ivar source_db: name of the source database if `source_type` == 'brightway'
    :vartype source_db: str
    :ivar source_file_path: filepath of the database if `source_type` == 'ecospold'.
    :vartype source_file_path: str

    """

    def __init__(self, source_db, source_type, source_file_path):

        if source_type == 'brightway':
            # Check that database exists
            if len(DatabaseChooser(source_db)) == 0:
                raise NameError('The database selected is empty. Make sure the name is correct')
            self.db = wurst.extract_brightway2_databases(source_db)

        if source_type == 'ecospold':
            # The ecospold data needs to be formatted
            ei = bw2io.SingleOutputEcospold2Importer(source_file_path, source_db)
            ei.apply_strategies()
            self.db = ei.data
            # Location field is added to exchanges
            self.add_location_field_to_exchanges()
            # Product field is added to exchanges
            self.add_product_field_to_exchanges()
            # Parameter field is converted from a list to a dictionary
            self.transform_parameter_field()

    def add_negative_CO2_flows_for_biomass_ccs(self):
        """
        Rescale the amount of all exchanges of carbon dioxide, non-fossil by a factor -9 (.9/-.1),
        to account for sequestered CO2.

        All CO2 capture and storage in the Carma datasets is assumed to be 90% efficient.
        Thus, we can simply find out what the new CO2 emission is and then we know how much gets stored in the ground.
        It's very important that we ONLY do this for biomass CCS plants, as only they will have negative emissions!

        Modifies in place (does not return anything).

        """
        for ds in ws.get_many(self.db, ws.contains('name', 'storage'), ws.equals('database', 'Carma CCS')):
            for exc in ws.biosphere(ds, ws.equals('name', 'Carbon dioxide, non-fossil')):
                wurst.rescale_exchange(exc, (0.9 / -0.1), remove_uncertainty=True)

    @staticmethod
    def get_fix_names_dict():
        """
        Loads a csv file into a dictionary. This dictionary contains a few location names
        that need correction in the wurst inventory database.

        :return: dictionary that contains names equivalence
        :rtype: dict
        """
        with open(FILEPATH_FIX_NAMES) as f:
            return dict(filter(None, csv.reader(f, delimiter=";")))

    def get_rev_fix_names_dict(self):
        """
        Reverse the fix_names dicitonary.

        :return: dictionary that contains names equivalence
        :rtype: dict
        """
        return {v: k for k, v in self.get_fix_names_dict().items()}

    @staticmethod
    def remove_nones(db):
        """
        Remove empty exchanges in the datasets of the wurst inventory database.
        Modifies in place (does not return anything).

        :param db: wurst inventory database
        :type db: list

        """
        exists = lambda x: {k: v for k, v in x.items() if v is not None}
        for ds in db:
            ds["exchanges"] = [exists(exc) for exc in ds["exchanges"]]

    def find_product_given_lookup_dict(self, lookup_dict):
        """
        Return a list of location names, given the filtering conditions given in `lookup_dict`.
        It is, for example, used to return a list of location names based on the name and the unit of a dataset.


        :param lookup_dict: a dictionary with filtering conditions
        :return: a list of location names
        :rtype: list
        """
        return [
            x["product"]
            for x in wurst.searching.get_many(
                self.db, *[ws.equals(k, v) for k, v in lookup_dict.items()]
            )
        ]

    def find_location_given_lookup_dict(self, lookup_dict):
        """
        Return a list of location names, given the filtering conditions given in `lookup_dict`.
        It is, for example, used to return a list of location names based on the name and the unit of a dataset.


        :param lookup_dict: a dictionary with filtering conditions
        :return: a list of location names
        :rtype: list
        """
        return [
            x["location"]
            for x in wurst.searching.get_many(
                self.db, *[ws.equals(k, v) for k, v in lookup_dict.items()]
            )
        ]

    def add_location_field_to_exchanges(self):
        """Add the `location` key to the production and
        technosphere exchanges in :attr:`db`.

        :raises IndexError: if no corresponding activity (and reference product) can be found.

        """
        d_location = {(a['database'], a['code']): a['location'] for a in self.db}
        for a in self.db:
            for e in a['exchanges']:
                if e['type'] == 'technosphere':
                    exc_input = e['input']
                    e['location'] = d_location[exc_input]

    def add_product_field_to_exchanges(self):
        """Add the `product` key to the production and
        technosphere exchanges in :attr:`db`.

        For production exchanges, use the value of the `reference_product` field.
        For technosphere exchanges, search the activities in :attr:`db` and
        use the reference product.

        :raises IndexError: if no corresponding activity (and reference product) can be found.

        """
        # Create a dictionary that contains the 'code' field as key and the 'product' field as value
        d_product = {a['code']: (a['reference product'], a['name']) for a in self.db}
        # Add a `product` field to the production exchange
        for x in self.db:
            for y in x["exchanges"]:
                if y["type"] == "production":
                    if "product" not in y:
                        y["product"] = x["reference product"]

                    if y["name"] != x["name"]:
                        y["name"] = x["name"]

        # Add a `product` field to technosphere exchanges
        for x in self.db:
            for y in x["exchanges"]:
                if y["type"] == "technosphere":
                    # Check if the field 'product' is present
                    if 'product' not in y:
                        y['product'] = d_product[y['input'][1]][0]

                    # If a 'reference product' field is present, we make sure it matches with the new 'product' field
                    if 'reference product' in y:
                        try:
                            assert y['product'] == y['reference product']
                        except AssertionError:
                            y['product'] = d_product[y['input'][1]][0]

                    # Ensure the name is correct
                    y['name'] = d_product[y['input'][1]][1]

    def transform_parameter_field(self):
        # When handling ecospold files directly, the parameter field is a list.
        # It is here transformed into a dictionary
        for x in self.db:
            x['parameters'] = {k['name']: k['amount'] for k in x['parameters']}

    # Functions to clean up Wurst import and additional technologies
    def fix_unset_technosphere_and_production_exchange_locations(
            self, matching_fields=("name", "unit")
    ):
        """
        Give all the production and technopshere exchanges with a missing location name the location of the dataset
        they belong to.
        Modifies in place (does not return anything).

        :param matching_fields: filter conditions
        :type matching_fields: tuple

        """
        for ds in self.db:

            # collect production exchanges that simply do not have a location key and set it to
            # the location of the dataset
            for exc in wurst.production(ds):
                if "location" not in exc:
                    exc["location"] = ds["location"]

            for exc in wurst.technosphere(ds):
                if "location" not in exc:
                    locs = self.find_location_given_lookup_dict(
                        self.db, {k: exc.get(k) for k in matching_fields}
                    )
                    if len(locs) == 1:
                        exc["location"] = locs[0]
                    else:
                        print(
                            "No unique location found for exchange:\n{}\nFound: {}".format(
                                pprint.pformat(exc), locs
                            )
                        )

    def prepare_datasets(self):
        """
        Clean datasets for all databases listed in scenarios: fix location names, remove
        empty exchanges, etc.



        """

        # Set missing locations to ```GLO``` for datasets in ``database``
        print("Set missing location of datasets to global scope.")
        wurst.default_global_location(self.db)
        # Set missing locations to ```GLO``` for exchanges in ``datasets``
        print("Set missing location of production exchanges to scope of dataset.")
        print("Correct missing location of technosphere exchanges.")
        self.fix_unset_technosphere_and_production_exchange_locations()
        # Remove empty exchanges
        print("Remove empty exchanges.")
        self.remove_nones(self.db)

        return self.db
