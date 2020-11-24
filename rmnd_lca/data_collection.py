from . import DATA_DIR
import pandas as pd
import xarray as xr
from pathlib import Path
import csv
import numpy as np

REMIND_ELEC_MARKETS = (DATA_DIR / "electricity" / "remind_electricity_markets.csv")
REMIND_ELEC_EFFICIENCIES = (DATA_DIR / "electricity" / "remind_electricity_efficiencies.csv")
REMIND_ELEC_EMISSIONS = (DATA_DIR / "electricity" / "remind_electricity_emissions.csv")
GAINS_TO_REMIND_FILEPATH = (DATA_DIR / "GAINStoREMINDtechmap.csv")
GNR_DATA = (DATA_DIR / "cement" / "additional_data_GNR.csv")


class RemindDataCollection:
    """
    Class that extracts data from REMIND output files.

    :ivar scenario: name of a Remind scenario
    :vartype scenario: str

    """

    def __init__(self, scenario, year, filepath_remind_files):
        self.scenario = scenario
        self.year = year
        self.filepath_remind_files = filepath_remind_files
        self.data = self.get_remind_data()
        self.regions = [r for r in self.data.region.values if r != "World"]

        self.gains_data = self.get_gains_data()
        self.gnr_data = self.get_gnr_data()
        self.electricity_market_labels = self.get_remind_electricity_market_labels()
        self.electricity_efficiency_labels = (
            self.get_remind_electricity_efficiency_labels()
        )
        self.electricity_emission_labels = self.get_remind_electricity_emission_labels()
        self.rev_electricity_market_labels = self.get_rev_electricity_market_labels()
        self.rev_electricity_efficiency_labels = (
            self.get_rev_electricity_efficiency_labels()
        )
        self.electricity_markets = self.get_remind_electricity_markets()
        self.electricity_efficiencies = self.get_remind_electricity_efficiencies()
        self.electricity_emissions = self.get_gains_electricity_emissions()
        self.cement_emissions = self.get_gains_cement_emissions()
        self.steel_emissions = self.get_gains_steel_emissions()


    @staticmethod
    def get_remind_electricity_emission_labels():
        """
        Loads a csv file into a dictionary. This dictionary contains labels of electricity emissions
        in Remind.

        :return: dictionary that contains emission names equivalence
        :rtype: dict
        """
        with open(REMIND_ELEC_EMISSIONS) as f:
            return dict(filter(None, csv.reader(f, delimiter=";")))

    @staticmethod
    def get_remind_electricity_market_labels():
        """
        Loads a csv file into a dictionary. This dictionary contains labels of electricity markets
        in Remind.

        :return: dictionary that contains market names equivalence
        :rtype: dict
        """
        with open(REMIND_ELEC_MARKETS) as f:
            return dict(filter(None, csv.reader(f, delimiter=";")))

    @staticmethod
    def get_remind_electricity_efficiency_labels():
        """
        Loads a csv file into a dictionary. This dictionary contains labels of electricity technologies efficiency
        in Remind.

        :return: dictionary that contains market names equivalence
        :rtype: dict
        """
        with open(REMIND_ELEC_EFFICIENCIES) as f:
            return dict(filter(None, csv.reader(f, delimiter=";")))

    def get_rev_electricity_market_labels(self):
        return {v: k for k, v in self.electricity_market_labels.items()}

    def get_rev_electricity_efficiency_labels(self):
        return {v: k for k, v in self.electricity_efficiency_labels.items()}

    def get_remind_data(self):
        """
        Read the REMIND csv result file and return an `xarray` with dimensions:
        * region
        * variable
        * year

        :return: an multi-dimensional array with Remind data
        :rtype: xarray.core.dataarray.DataArray

        """

        filename = self.scenario + ".mif"

        filepath = Path(self.filepath_remind_files) / filename
        df = pd.read_csv(
            filepath, sep=";", index_col=["Region", "Variable", "Unit"]
        ).drop(columns=["Model", "Scenario"])
        if(len(df.columns == 20)):
            df.drop(columns=df.columns[-1], inplace=True)
        df.columns = df.columns.astype(int)
        df = df.reset_index()

        # Filter the dataframe
        list_var = (
            "SE",
            "Tech",
            "FE",
            "Production",
            "Emi|CCO2",
            "Emi|CO2"
        )

        df = df.loc[
            df["Variable"].str.startswith(list_var)
        ]

        df = df.rename(columns={"Region": "region", "Variable": "variables", "Unit": "unit"})

        array = df.melt(id_vars=["region", "variables", "unit"],
                        var_name="year",
                        value_name="value")[["region", "variables", 'year', "value"]] \
            .groupby(["region", "variables", 'year'])["value"].mean().to_xarray()

        return array
    
    def get_gains_data(self):
        """
        Read the GAINS emissions csv file and return an `xarray` with dimensions:
        * region
        * pollutant
        * sector
        * year

        :return: an multi-dimensional array with GAINS emissions data
        :rtype: xarray.core.dataarray.DataArray

        """
        filename = "GAINS emission factors.csv"
        filepath = (DATA_DIR / "remind_output_files" / filename)

        gains_emi = pd.read_csv(
            filepath,
            skiprows=4,
            names=["year", "region", "GAINS", "pollutant", "scenario", "factor"],
        )
        gains_emi["unit"] = "Mt/TWa"
        gains_emi = gains_emi[gains_emi.scenario == "SSP2"]

        sector_mapping = pd.read_csv(GAINS_TO_REMIND_FILEPATH).drop(
            ["noef", "elasticity"], axis=1
        )

        gains_emi = (
            gains_emi.join(sector_mapping.set_index("GAINS"), on="GAINS")
                .dropna()
                .drop(["scenario", "REMIND"], axis=1)
                .pivot_table(
                index=["region", "GAINS", "pollutant", "unit"],
                values="factor",
                columns="year",
            )
        )

        gains_emi = gains_emi.reset_index()
        gains_emi = gains_emi.melt(id_vars=["region", "pollutant", "unit", 'GAINS'],
                                   var_name="year",
                                   value_name="value")[["region", "pollutant", 'GAINS', 'year', 'value']]
        gains_emi = gains_emi.rename(columns={'GAINS': 'sector'})
        array = gains_emi.groupby(["region", "pollutant", 'year', 'sector'])["value"].mean().to_xarray()

        return array / 8760  # per TWha --> per TWh

    def get_gnr_data(self):
        """
        Read the GNR csv file on cement production and return an `xarray` with dimensions:
        * region
        * year
        * variables

        :return: an multi-dimensional array with GNR data
        :rtype: xarray.core.dataarray.DataArray

        :return:
        """
        df = pd.read_csv(
            GNR_DATA)
        df = df[["region", "year", "variables", "value"]]

        gnr_array = df.groupby(["region", "year", "variables"]).mean()["value"].to_xarray()
        gnr_array = gnr_array.interpolate_na(dim='year', method='linear', fill_value='extrapolate')
        gnr_array = gnr_array.interp(year=self.year)
        gnr_array = gnr_array.fillna(0)

        return gnr_array

    def get_remind_electricity_markets(self, drop_hydrogen=True):
        """
        This method retrieves the market share for each electricity-producing technology, for a specified year,
        for each region provided by REMIND.
        Electricity production from hydrogen can be removed from the mix (unless specified, it is removed).

        :param drop_hydrogen: removes hydrogen from the region-specific electricity mix if `True`.
        :type drop_hydrogen: bool
        :return: an multi-dimensional array with electricity technologies market share for a given year, for all regions.
        :rtype: xarray.core.dataarray.DataArray

        """
        # If hydrogen is not to be considered, it is removed from the technologies labels list
        if drop_hydrogen:
            list_technologies = [
                l
                for l in list(self.electricity_market_labels.values())
                if "Hydrogen" not in l
            ]
        else:
            list_technologies = list(self.electricity_market_labels.values())

        # If the year specified is not contained within the range of years given by REMIND
        if (
                self.year < self.data.year.values.min()
                or self.year > self.data.year.values.max()
        ):
            raise KeyError("year not valid, must be between 2005 and 2150")

        # Finally, if the specified year falls in between two periods provided by REMIND
        else:
            # Interpolation between two periods
            data_to_interp_from = self.data.loc[
                                  :, list_technologies, :
                                  ] / self.data.loc[:, list_technologies, :].groupby("region").sum(dim="variables")
            return data_to_interp_from.interp(year=self.year)

    def get_remind_fuel_mix_for_ldvs(self):
        """
        This method retrieves the fuel production mix
        used in the transport sector for LDVs,
        for a specified year, for each region provided by REMIND.

        Note that synthetic fuels are preferred by LDVs so the share is much larger
        compared to the general blend supplied to the transport sector.

        :return: an multi-dimensional array with market share for a given year, for all regions.
        :rtype: xarray.core.dataarray.DataArray

        """

        # add fossil fuel entry
        data = xr.concat([
            self.data,
            (self.data.loc[:, "FE|Transport|Liquids|Coal", :] +
             self.data.loc[:, "FE|Transport|Liquids|Oil", :]).expand_dims({
                 "variables": ["FE|Transport|Liquids|Fossil"]
             })], dim="variables")

        hydro_techs = [
            "SE|Liquids|Hydrogen",
            "FE|Transport|Pass|Road|LDV|Liquids",
        ]
        hydro = data.loc[:, hydro_techs, :]

        # all synthetic liquids to LDVs
        hydro = (hydro.loc[:, "SE|Liquids|Hydrogen"]
                 /data.loc[:, "FE|Transport|Pass|Road|LDV|Liquids"])
        hydro = hydro.where(hydro < 1, 1)

        other_techs = [
            "FE|Transport|Liquids|Biomass",
            "FE|Transport|Liquids|Fossil"
        ]
        others = data.loc[:, other_techs]
        others.coords["variables"] = others.coords["variables"]\
                                       .str[21:]
        others = others / others.sum(dim="variables")

        # concat
        full = xr.concat([
            hydro.expand_dims({"variables": ["Hydrogen"]}),
            (1-hydro) * others], "variables")

        # shares all sum to 1?
        assert(np.allclose(full.sum(dim="variables"), 1))
        # If the year specified is not contained within
        # the range of years given by REMIND
        if (
                self.year < self.data.year.values.min()
                or self.year > self.data.year.values.max()
        ):
            raise KeyError("year not valid, must be between 2005 and 2150")
        # Finally, if the specified year falls in
        # between two periods provided by REMIND
        else:
            # Interpolation between two periods
            return full.interp(year=self.year).transpose()

    def get_remind_electricity_efficiencies(self, drop_hydrogen=True):
        """
        This method retrieves efficiency values for electricity-producing technology, for a specified year,
        for each region provided by REMIND.
        Electricity production from hydrogen can be removed from the mix (unless specified, it is removed).

        :param drop_hydrogen: removes hydrogen from the region-specific electricity mix if `True`.
        :type drop_hydrogen: bool
        :return: an multi-dimensional array with electricity technologies market share for a given year, for all regions.
        :rtype: xarray.core.dataarray.DataArray

        """
        # If hydrogen is not to be considered, it is removed from the technologies labels list
        if drop_hydrogen:
            list_technologies = [
                l
                for l in list(self.electricity_efficiency_labels.values())
                if "Hydrogen" not in l
            ]
        else:
            list_technologies = list(self.electricity_efficiency_labels.values())

        # If the year specified is not contained within the range of years given by REMIND
        if (
                self.year < self.data.year.values.min()
                or self.year > self.data.year.values.max()
        ):
            raise KeyError("year not valid, must be between 2005 and 2150")

        # Finally, if the specified year falls in between two periods provided by REMIND
        else:
            # Interpolation between two periods
            data_to_interp_from = self.data.loc[:, list_technologies, :]
            return (
                    data_to_interp_from.interp(year=self.year) / 100
            )  # Percentage to ratio

    def get_gains_electricity_emissions(self):
        """
        This method retrieves emission values for electricity-producing technology, for a specified year,
        for each region provided by GAINS.

        :return: an multi-dimensional array with emissions for different technologies for a given year, for all regions.
        :rtype: xarray.core.dataarray.DataArray

        """
        # If the year specified is not contained within the range of years given by REMIND
        if (
                self.year < self.gains_data.year.values.min()
                or self.year > self.gains_data.year.values.max()
        ):
            raise KeyError("year not valid, must be between 2005 and 2150")

        # Finally, if the specified year falls in between two periods provided by REMIND
        else:
            # Interpolation between two periods
            return self.gains_data.sel(sector=[v for v in self.electricity_emission_labels.values()]) \
                .interp(year=self.year)

    def get_gains_cement_emissions(self):
        """
        This method retrieves emission values for cement production, for a specified year,
        for each region provided by GAINS.

        :return: an multi-dimensional array with emissions for different technologies for a given year, for all regions.
        :rtype: xarray.core.dataarray.DataArray

        """
        # If the year specified is not contained within the range of years given by REMIND
        if (
                self.year < self.gains_data.year.values.min()
                or self.year > self.gains_data.year.values.max()
        ):
            raise KeyError("year not valid, must be between 2005 and 2150")

        # Finally, if the specified year falls in between two periods provided by REMIND
        else:
            # Interpolation between two periods
            return self.gains_data.sel(sector='CEMENT').interp(year=self.year)

    def get_gains_steel_emissions(self):
        """
        This method retrieves emission values for steel production, for a specified year,
        for each region provided by GAINS.

        :return: an multi-dimensional array with emissions for different technologies for a given year, for all regions.
        :rtype: xarray.core.dataarray.DataArray

        """
        # If the year specified is not contained within the range of years given by REMIND
        if (
                self.year < self.gains_data.year.values.min()
                or self.year > self.gains_data.year.values.max()
        ):
            raise KeyError("year not valid, must be between 2005 and 2150")

        # Finally, if the specified year falls in between two periods provided by REMIND
        else:
            # Interpolation between two periods
            return self.gains_data.sel(sector='STEEL').interp(year=self.year)
