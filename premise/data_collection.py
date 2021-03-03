from . import DATA_DIR
import pandas as pd
from pathlib import Path
import csv

IAM_ELEC_MARKETS = DATA_DIR / "electricity" / "electricity_markets.csv"
IAM_ELEC_EFFICIENCIES = DATA_DIR / "electricity" / "electricity_efficiencies.csv"
IAM_ELEC_EMISSIONS = DATA_DIR / "electricity" / "electricity_emissions.csv"
IAM_HEAT_MARKETS = DATA_DIR / "heat" / "remind_heat_markets.csv"
IAM_HEAT_EFFICIENCIES = DATA_DIR / "heat" / "remind_heat_efficiencies.csv"
IAM_HEAT_EMISSIONS = DATA_DIR / "heat" / "remind_heat_emissions.csv"
GAINS_TO_IAM_FILEPATH = DATA_DIR / "GAINS_emission_factors" / "GAINStoREMINDtechmap.csv"
GNR_DATA = DATA_DIR / "cement" / "additional_data_GNR.csv"


class IAMDataCollection:
    """
    Class that extracts data from IAM output files.

    :ivar scenario: name of a IAM scenario
    :vartype scenario: str

    """

    def __init__(self, model, scenario, year, filepath_iam_files):
        self.model = model
        self.scenario = scenario
        self.year = year
        self.filepath_iam_files = filepath_iam_files
        self.data = self.get_iam_data()
        self.regions = [r for r in self.data.region.values if r != "World"]

        self.gains_data = self.get_gains_data()
        self.gnr_data = self.get_gnr_data()
        self.electricity_market_labels = self.get_iam_electricity_market_labels()
        self.electricity_efficiency_labels = (
            self.get_iam_electricity_efficiency_labels()
        )
        self.electricity_emission_labels = self.get_iam_electricity_emission_labels()
        self.rev_electricity_market_labels = self.get_rev_electricity_market_labels()
        self.rev_electricity_efficiency_labels = (
            self.get_rev_electricity_efficiency_labels()
        )
        self.electricity_markets = self.get_iam_electricity_markets()
        self.electricity_efficiencies = self.get_iam_electricity_efficiencies()
        self.electricity_emissions = self.get_gains_electricity_emissions()
        self.cement_emissions = self.get_gains_cement_emissions()
        self.steel_emissions = self.get_gains_steel_emissions()
        self.heat_market_labels = self.get_remind_heat_market_labels()
        self.heat_efficiency_labels = (
            self.get_remind_heat_efficiency_labels()
        )
        self.heat_emission_labels = self.get_remind_heat_emission_labels()
        self.rev_heat_market_labels = self.get_rev_heat_market_labels()
        self.rev_heat_efficiency_labels = (
            self.get_rev_heat_efficiency_labels()
        )
        self.heat_markets = self.get_remind_heat_markets()
        self.heat_efficiencies = self.get_remind_heat_efficiencies()
        self.heat_emissions = self.get_gains_heat_emissions()

    def get_iam_electricity_emission_labels(self):
        """
        Loads a csv file into a dictionary. This dictionary contains labels of electricity emissions
        in the selected IAM.

        :return: dictionary that contains emission names equivalence
        :rtype: dict
        """
        d = dict()
        with open(IAM_ELEC_EMISSIONS) as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if row[0] == self.model:
                    d[row[1]] = row[2]
        return d


    @staticmethod
    def get_iam_heat_emission_labels():
        """
        Loads a csv file into a dictionary. This dictionary contains labels of heat emissions
        in the selected IAM.

        :return: dictionary that contains emission names equivalence
        :rtype: dict
        """
        d = dict()
        with open(IAM_HEAT_EMISSIONS) as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if row[0] == self.model:
                    d[row[1]] = row[2]
        return d


    def get_iam_electricity_market_labels(self):
        """
        Loads a csv file into a dictionary. This dictionary contains labels of electricity markets
        in the IAM.

        :return: dictionary that contains market names equivalence
        :rtype: dict
        """
        d = dict()
        with open(IAM_ELEC_MARKETS) as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if row[0] == self.model:
                    d[row[1]] = row[2]
        return d
    
    
    @staticmethod
    def get_iam_heat_market_labels():
        """
        Loads a csv file into a dictionary. This dictionary contains labels of heat markets
        in the IAM.

        :return: dictionary that contains market names equivalence
        :rtype: dict
        """
        d = dict()
        with open(IAM_HEAT_MARKETS) as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if row[0] == self.model:
                    d[row[1]] = row[2]
        return d
        

    def get_iam_electricity_efficiency_labels(self):
        """
        Loads a csv file into a dictionary. This dictionary contains labels of electricity technologies efficiency
        in the IAM.

        :return: dictionary that contains market names equivalence
        :rtype: dict
        """

        d = dict()
        with open(IAM_ELEC_EFFICIENCIES) as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if row[0] == self.model:
                    d[row[1]] = row[2]
        return d


    @staticmethod
    def get_remind_heat_efficiency_labels():
        """
        Loads a csv file into a dictionary. This dictionary contains labels of heat technologies efficiency
        in Remind.

        :return: dictionary that contains market names equivalence
        :rtype: dict
        """
        with open(REMIND_HEAT_EFFICIENCIES) as f:
            return dict(filter(None, csv.reader(f, delimiter=";")))
            
            
    def get_rev_electricity_market_labels(self):
        return {v: k for k, v in self.electricity_market_labels.items()}

    def get_rev_electricity_efficiency_labels(self):
        return {v: k for k, v in self.electricity_efficiency_labels.items()}
        
    def get_rev_heat_market_labels(self):
        return {v: k for k, v in self.heat_market_labels.items()}

    def get_rev_heat_efficiency_labels(self):
        return {v: k for k, v in self.heat_efficiency_labels.items()}

    def get_iam_data(self):
        """
        Read the IAM result file and return an `xarray` with dimensions:
        * region
        * variable
        * year

        :return: an multi-dimensional array with IAM data
        :rtype: xarray.core.dataarray.DataArray
        """

        file_ext = {"remind": self.model + "_" + self.scenario + ".mif",
                    "image": self.model + "_" + self.scenario + ".xls"}

        filepath = Path(self.filepath_iam_files) / file_ext[self.model]

        if self.model == "remind":
            df = pd.read_csv(
                filepath, sep=";", index_col=["Region", "Variable", "Unit"]
            ).drop(columns=["Model", "Scenario"])

            # Filter the dataframe
            list_var = ("SE", "Tech", "FE", "Production", "Emi|CCO2", "Emi|CO2")

        elif self.model == "image":
            df = pd.read_excel(filepath, index_col=[2, 3, 4]).drop(
                columns=["Model", "Scenario"]
            )

            # Filter the dataframe
            list_var = (
                "Secondary Energy",
                "Efficiency",
                "Final Energy",
            )
        else:
            raise ValueError("The IAM model name {} is not valid. Currently supported: 'remind' or 'image'".format(self.model))

        if len(df.columns == 20):
            df.drop(columns=df.columns[-1], inplace=True)
        df.columns = df.columns.astype(int)
        df = df.reset_index()

        df = df.loc[df["Variable"].str.startswith(list_var)]

        df = df.rename(
            columns={"Region": "region", "Variable": "variables", "Unit": "unit"}
        )

        array = (
            df.melt(
                id_vars=["region", "variables", "unit"],
                var_name="year",
                value_name="value",
            )[["region", "variables", "year", "value"]]
            .groupby(["region", "variables", "year"])["value"]
            .mean()
            .to_xarray()
        )

        return array


    @staticmethod
    def get_gains_data():

        """
        Read the GAINS emissions csv file and return an `xarray` with dimensions:
        * region
        * pollutant
        * sector
        * year

        :return: a multi-dimensional array with GAINS emissions data
        :rtype: xarray.core.dataarray.DataArray

        """
        filename = "GAINS emission factors.csv"
        filepath = DATA_DIR / "GAINS_emission_factors" / filename

        gains_emi = pd.read_csv(
            filepath,
            skiprows=4,
            names=["year", "region", "GAINS", "pollutant", "scenario", "factor"],
        )
        gains_emi["unit"] = "Mt/TWa"
        gains_emi = gains_emi[gains_emi.scenario == "SSP2"]

        sector_mapping = pd.read_csv(GAINS_TO_IAM_FILEPATH).drop(
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
        gains_emi = gains_emi.melt(
            id_vars=["region", "pollutant", "unit", "GAINS"],
            var_name="year",
            value_name="value",
        )[["region", "pollutant", "GAINS", "year", "value"]]
        gains_emi = gains_emi.rename(columns={"GAINS": "sector"})
        array = (
            gains_emi.groupby(["region", "pollutant", "year", "sector"])["value"]
            .mean()
            .to_xarray()
        )

        return array / 8760  # per TWha --> per TWh


    def get_gnr_data(self):
        """
        Read the GNR csv file on cement production and return an `xarray` with dimensions:
        * region
        * year
        * variables

        :return: a multi-dimensional array with GNR data
        :rtype: xarray.core.dataarray.DataArray

        :return:
        """
        df = pd.read_csv(GNR_DATA)
        df = df[["region", "year", "variables", "value"]]

        gnr_array = (
            df.groupby(["region", "year", "variables"]).mean()["value"].to_xarray()
        )
        gnr_array = gnr_array.interpolate_na(
            dim="year", method="linear", fill_value="extrapolate"
        )
        gnr_array = gnr_array.interp(year=self.year)
        gnr_array = gnr_array.fillna(0)

        return gnr_array


    def get_iam_electricity_markets(self, drop_hydrogen=True):
        """
        This method retrieves the market share for each electricity-producing technology, for a specified year,
        for each region provided by the IAM.
        Electricity production from hydrogen can be removed from the mix (unless specified, it is removed).

        :param drop_hydrogen: removes hydrogen from the region-specific electricity mix if `True`.
        :type drop_hydrogen: bool
        :return: a multi-dimensional array with electricity technologies market share for a given year, for all regions.
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

        # If the year specified is not contained within the range of years given by the IAM
        if (
            self.year < self.data.year.values.min()
            or self.year > self.data.year.values.max()
        ):
            raise KeyError("year not valid, must be between 2005 and 2100")

        # Finally, if the specified year falls in between two periods provided by the IAM
        else:
            # Interpolation between two periods
            data_to_interp_from = self.data.loc[
                :, list_technologies, :
            ] / self.data.loc[:, list_technologies, :].groupby("region").sum(
                dim="variables"
            )
            return data_to_interp_from.interp(year=self.year)


    def get_iam_heat_markets(self):
        """
        This method retrieves the market share for each heat-producing technology, for a specified year,
        for each region provided by the IAM.

        :return: a multi-dimensional array with heat technologies market share for a given year, for all regions.
        :rtype: xarray.core.dataarray.DataArray

        """
        list_technologies = list(self.heat_market_labels.values())

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


    def get_iam_electricity_efficiencies(self, drop_hydrogen=True):
        """
        This method retrieves efficiency values for electricity-producing technology, for a specified year,
        for each region provided by the IAM.
        Electricity production from hydrogen can be removed from the mix (unless specified, it is removed).

        :param drop_hydrogen: removes hydrogen from the region-specific electricity mix if `True`.
        :type drop_hydrogen: bool
        :return: a multi-dimensional array with electricity technologies market share for a given year, for all regions.
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

        # If the year specified is not contained within the range of years given by the IAM
        if (
            self.year < self.data.year.values.min()
            or self.year > self.data.year.values.max()
        ):
            raise KeyError("year not valid, must be between 2005 and 2100")

        # Finally, if the specified year falls in between two periods provided by the IAM
        else:
            # Interpolation between two periods
            data_to_interp_from = self.data.loc[:, list_technologies, :]

            if self.model == "remind":
                return (
                    data_to_interp_from.interp(year=self.year) / 100
                )  # Percentage to ratio

            if self.model == "image":
                return data_to_interp_from.interp(year=self.year)


    def get_iam_heat_efficiencies(self):
        """
        This method retrieves efficiency values for heat-producing technology, for a specified year,
        for each region provided by the IAM.

        :return: a multi-dimensional array with heat technologies market share for a given year, for all regions.
        :rtype: xarray.core.dataarray.DataArray

        """
        list_technologies = list(self.heat_efficiency_labels.values())

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

        :return: a multi-dimensional array with emissions for different technologies for a given year, for all regions.
        :rtype: xarray.core.dataarray.DataArray

        """
        # If the year specified is not contained within the range of years given by the IAM
        if (
            self.year < self.gains_data.year.values.min()
            or self.year > self.gains_data.year.values.max()
        ):
            raise KeyError("year not valid, must be between 2005 and 2100")

        # Finally, if the specified year falls in between two periods provided by the IAM
        else:
            # Interpolation between two periods
            return self.gains_data.sel(
                sector=[v for v in self.electricity_emission_labels.values()]
            ).interp(year=self.year)

                
    def get_gains_heat_emissions(self):
        """
        This method retrieves emission values for heat-producing technology, for a specified year,
        for each region provided by GAINS.

        :return: a multi-dimensional array with emissions for different technologies for a given year, for all regions.
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
            return self.gains_data.sel(sector=[v for v in self.heat_emission_labels.values()]) \
                .interp(year=self.year)


    def get_gains_cement_emissions(self):
        """
        This method retrieves emission values for cement production, for a specified year,
        for each region provided by GAINS.

        :return: a multi-dimensional array with emissions for different technologies for a given year, for all regions.
        :rtype: xarray.core.dataarray.DataArray

        """
        # If the year specified is not contained within the range of years given by the IAM
        if (
            self.year < self.gains_data.year.values.min()
            or self.year > self.gains_data.year.values.max()
        ):
            raise KeyError("year not valid, must be between 2005 and 2100")

        # Finally, if the specified year falls in between two periods provided by the IAM
        else:
            # Interpolation between two periods
            return self.gains_data.sel(sector="CEMENT").interp(year=self.year)


    def get_gains_steel_emissions(self):
        """
        This method retrieves emission values for steel production, for a specified year,
        for each region provided by GAINS.

        :return: a multi-dimensional array with emissions for different technologies for a given year, for all regions.
        :rtype: xarray.core.dataarray.DataArray

        """
        # If the year specified is not contained within the range of years given by the IAM
        if (
            self.year < self.gains_data.year.values.min()
            or self.year > self.gains_data.year.values.max()
        ):
            raise KeyError("year not valid, must be between 2005 and 2100")

        # Finally, if the specified year falls in between two periods provided by the IAM
        else:
            # Interpolation between two periods
            return self.gains_data.sel(sector="STEEL").interp(year=self.year)