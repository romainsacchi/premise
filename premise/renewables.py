from wurst import searching as ws
from .utils import *
import re

class SolarPV:
    """
    Class that modifies solar PVs efficiency. It iterates through photovoltaic panel installation activities
    and modifies the area (m^2) required to achieve the given power capacity.
    For example, in ei 3.7, currently 22m^2 are required to achieve 3 kWp, meaning an efficiency of 12.6%,
    if we assume a maximal solar irradiation of 1000 W/m^2. In 2020, such installation should have an
    efficiency of about 18%.
    It is, for now, irrespective of the IAM scenario chosen.
    Source: p.357 of https://www.psi.ch/sites/default/files/import/ta/PublicationTab/Final-Report-BFE-Project.pdf
    This considers efficiencies of current and mature technologies today (18-20%), to efficiencies of PV currently in
    development for 2050 (24.5-25%), according to https://science.sciencemag.org/content/352/6283/aad4424/tab-pdf.
    :ivar db: database
    :vartype db: dict
    :ivar year: year
    :vartype year: int

    """

    def __init__(self, db, year):
        self.db = db
        self.year = year

    def update_efficiency_of_solar_PV(self):
        """
        Update the efficiency of solar PV modules.
        We look at how many square meters are needed per kilowatt of installed capacity
        to obtain thr current efficiency.
        Then we update the surface needed according to the projected efficiency.
        :return:
        """

        ds = ws.get_many(
            self.db,
            *[
                ws.contains('name', 'photovoltaic'),
                ws.either(ws.contains('name', 'installation'),
                          ws.contains('name', 'construction')),
                ws.doesnt_contain_any('name', ['market', 'factory']),
                ws.equals("unit", "unit"),
            ]
        )

        for d in ds:
            print(d["name"])
            power = float(re.findall('\d+', d["name"])[0])

            for exc in ws.technosphere(d, *[
                ws.contains('name', 'photovoltaic'),
                ws.equals('unit', 'square meter')
            ]):

                surface = float(exc["amount"])
                max_power = surface # in kW, since we assume a constant 1,000W/m^2
                current_eff = power / max_power
                new_eff = get_efficiency_ratio_solar_PV(self.year, power).values
                exc["amount"] *= float(current_eff/new_eff)
                d["parameters"] = {"efficiency": new_eff}

        return self.db
