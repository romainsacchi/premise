from wurst.geo import geomatcher

from rmnd_lca import DATA_DIR

REGION_MAPPING_FILEPATH = (DATA_DIR / "regionmappingH12.csv")


class Geomap:
    """
    Map ecoinvent locations to REMIND regions and vice-versa.
    """

    def __init__(self):
        self.geo = self.get_REMIND_geomatcher()

    @staticmethod
    def get_REMIND_geomatcher():
        """
        Load a geomatcher object from the `constructive_geometries`library and add definitions.
        It is used to find correspondences between REMIND and ecoinvent region names.
        :return: geomatcher object
        :rtype: wurst.geo.geomatcher
        """
        with open(REGION_MAPPING_FILEPATH) as f:
            f.readline()
            csv_list = [[val.strip() for val in r.split(";")] for r in f.readlines()]
            l = [(x[1], x[2]) for x in csv_list]

        # List of countries not found
        countries_not_found = ["CC", "CX", "GG", "JE", "BL"]

        rmnd_to_iso = {}
        iso_to_rmnd = {}

        # Build a dictionary that maps region names (used by REMIND) to ISO country codes
        # And a reverse dictionary that maps ISO country codes to region names
        for ISO, region in l:
            if ISO not in countries_not_found:
                try:
                    rmnd_to_iso[region].append(ISO)
                except KeyError:
                    rmnd_to_iso[region] = [ISO]

                iso_to_rmnd[region] = ISO

        geo = geomatcher
        geo.add_definitions(rmnd_to_iso, "REMIND")

        return geo

    def remind_to_ecoinvent_location(self, location, contained=False):
        """
        Find the corresponding ecoinvent region given a REMIND region.

        :param location: name of a REMIND region
        :type location: str
        :return: name of an ecoinvent region
        :rtype: str
        """

        if location != "World":
            location = ("REMIND", location)

            ecoinvent_locations = []
            try:
                searchfunc = (self.geo.contained
                              if contained else self.geo.intersects)
                for r in searchfunc(location):
                    if not isinstance(r, tuple):
                        ecoinvent_locations.append(r)
                    else:
                        if r[0] != "REMIND":
                            ecoinvent_locations.append(r[1])

                # TODO: Dirty trick. In the future, "CA" should be removed from "RNA". Also, "GLO" should not appear.
                if location == ("REMIND", "USA"):
                    ecoinvent_locations = [e for e in ecoinvent_locations if "CA" not in e]

                # Current behaviour of `intersects` is to include "GLO" in all REMIND regions.
                if location != ("REMIND", "World"):
                    ecoinvent_locations = [e for e in ecoinvent_locations if e != "GLO"]

                return ecoinvent_locations
            except KeyError:
                print("Can't find location {} using the geomatcher.".format(location))

        else:
            return ["GLO"]

    def ecoinvent_to_remind_location(self, location):
        """
        Return a REMIND region name for a 2-digit ISO country code given.
        Set rules in case two REMIND regions are within the ecoinvent region.

        :param location: 2-digit ISO country code
        :type location: str
        :return: REMIND region name
        :rtype: str
        """

        mapping = {"GLO": "World", "RoW": "CAZ", "IAI Area, Russia & RER w/o EU27 & EFTA": "REF"}
        if location in mapping:
            return mapping[location]

        remind_location = [
            r[1]
            for r in self.geo.within(location)
            if r[0] == "REMIND" and r[1] != "World"
        ]

        mapping = {
            ("AFR", "MEA"): "AFR",
            ("AFR", "SSA"): "AFR",
            ("EUR", "NEU"): "EUR",
            ("EUR", "REF"): "EUR",
            ("OAS", "CHA"): "OAS",
            ("OAS", "EUR"): "OAS",
            ("OAS", "IND"): "OAS",
            ("OAS", "JPN"): "OAS",
            ("OAS", "MEA"): "OAS",
            ("OAS", "REF"): "OAS",
            ("USA", "CAZ"): "USA",
        }

        # If we have more than one REMIND region
        if len(remind_location) > 1:
            # TODO: find a more elegant way to do that
            for key, value in mapping.items():
                # We need to find the most specific REMIND region
                if len(set(remind_location).intersection(set(key))) == 2:
                    remind_location.remove(value)
            return remind_location[0]
        elif len(remind_location) == 0:
            print("no location for {}".format(location))
        else:
            return remind_location[0]
