Coupling Integrated Assessment Models and ecoinvent for prospective environmental impact assessment
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


.. image:: https://travis-ci.org/romainsacchi/premise.svg?branch=master
    :target: https://travis-ci.org/romainsacchi/premise
    :alt: Travis status

.. image:: https://coveralls.io/repos/github/romainsacchi/premise/badge.svg?branch=master
    :target: https://coveralls.io/github/romainsacchi/premise?branch=master
    :alt: Coveralls status

.. image:: https://readthedocs.org/projects/premise/badge/?version=latest
    :target: https://premise.readthedocs.io/en/latest/
    :alt: Readthedocs status

.. image:: https://badge.fury.io/py/premise.svg
    :target: https://badge.fury.io/py/premise
    :alt: Pypi package version

Introduction
============

**premise** allows to align the life cycle inventories contained in the life cycle inventory database **ecoinvent 3 cutoff**
with the output results of Integrated Assessment Models (IAM), such as **REMIND** or **IMAGE**,
in order to produce life cycle inventories under future policy scenarios for any year between 2005 and 2100.

More specifically, **premise** will apply a series of transformation functions to ecoinvent.

In the latest version (0.1.7), the following transformation functions are available:

* **update_electricity_to_iam_data()**: alignment of regional electricity production mixes as well as efficiencies for a number of
  electricity production technologies, including Carbon Capture and Storage technologies.
* **update_vehicles()**: fuel markets that supply transport vehicles are adjusted according to the IAM projections,
  including penetration of bio- and synthetic fuels.
* **update_cement_to_iam_data()**: adjustment of technologies for cement production (dry, semi-dry, wet, with pre-heater or not),
  fuel efficiency of kilns, fuel mix of kilns (including biomass and waste fuels) and clinker-to-cement ratio.
* **update_steel_to_iam_data()**: adjustment of process efficiency, fuel mix and share of secondary steel in steel markets.
* **update_solar_PV()**: adjustment of solar PV modules with projected developments reported in `Bauer et al. <https://www.psi.ch/sites/default/files/import/ta/PublicationTab/Final-Report-BFE-Project.pdf>`_

However, whether or not these transformation functions can be applied will depend on the existence of the necessary variables in
the IAM file you use as input.


.. csv-table:: Availability of transformation functions
    :file: table_1.csv
    :widths: 10 10 30 10 10 10 10
    :header-rows: 1


The following REMIND IAM files come with the library:

* SSP2
    1.  **Base:** counter-factual scenario with no climate policy implemented
    2.  **NPi** (National Policies implemented): scenario  describes energy,  climate  and  economic  projections for the  period  until 2030, and equivalent efforts thereafter. See `CD-LINKS modelling protocol <https://www.cd-links.org/wp-content/uploads/2016/06/CD-LINKS-global-exercise-protocol_secondround_for-website.pdf>`_ for details.
    3.  **NDC**: All emission reductions and other mitigation commitments of the Nationally Determined Contributions under the Paris Agreement are implemented. See `CD-LINKS modelling protocol <https://www.cd-links.org/wp-content/uploads/2016/06/CD-LINKS-global-exercise-protocol_secondround_for-website.pdf>`_ for details.
    4.  **PkBudg 1300/1100/900**: Climate policies to limit cumulative 2011-2100 CO2 emissions to 1300 / 1100 / 900 over the entire time horizon (“not-to-exceed”). Correspond to 2°, well-below 2° and 1.5° targets. Other greenhouse gases are priced with the CO2e-price using 100year global warming potentials.

The following IMAGE IAM files come with the library:

* SSP2
    1.  **Base** counter-factual scenario with no climate policy implemented

You can however use any other IAM files.

Additionally, a number of inventories for emerging technologies are added upon the creation of a new database.

* electricity production using various fuels (including biomass and biogas) with Carbon Capture and Storage (CCS) `Volkart et al. 2013 <https://doi.org/10.1016/j.ijggc.2013.03.003>`_
* hydrogen production from electrolysis from different world regions,
* hydrogen production from steam methane reforming (SMR) and auto-thermal reforming (ATR) of natural gas and biogas, with and without CCS `Antonini et al. 2020 <https://doi.org/10.1039/D0SE00222D>`_
* hydrogen production from coal gasification `Antonini et al. 2020 <https://doi.org/10.1039/D0SE00222D>`_
* hydrogen production from woody biomass gasification, with and without CCS `Antonini et al. 2020 <https://doi.org/10.1039/D0SE00222D>`_
* synthetic fuels from Fischer-Tropsh (diesel), Methanol-to-liquid (gasoline) and electrolchemical methanation (gas) processes,
  using direct air capture (DAC) `Zhang et al. 2019 <https://doi.org/10.1039/C9SE00986H>`_
* passenger car inventories from the library `carculator <https://github.com/romainsacchi/carculator>`_
* medium and heavy duty trucks from the library `carculator_truck <https://github.com/romainsacchi/carculator_truck>`_


Requirements
------------
* Python language interpreter 3.x
* License for ecoinvent 3
* Some IAM output files come with the library ("REMIND_xxx.mif" for REMIND, "IMAGE_xxxx.xlsx" for IMAGE)
  and are located by default in the subdirectory "/data/iam_output_files".
  A file path can be specified to fetch IAM output files elsewhere on your computer.
* brightway2 (optional)

How to install this package?
----------------------------

Two options:

A development version with the latest advancements (but with the risks of unseen bugs),
is available on Conda:

.. code-block:: python

    conda install -c romainsacchi premise

For a more stable and proven version, from Pypi:

.. code-block:: python

    pip install premise

will install the package and the required dependencies.

How to use it?
--------------

Examples notebook
*****************

`This notebook <https://github.com/romainsacchi/premise/blob/master/examples/examples.ipynb>`_ will show you everything you need to know to use **premise**.

Methodology
-----------

Upon database creation, the ecoinvent database is loaded into a Python dictionary, to which additional
inventories are added, notably those of emerging technologies for power generation (i.e., with CCS), fuel
preparation (e.g., synthetic fuels) and transport (e.g., passenger cars and trucks).

After this, the following transformation functions can be applied to the database.

update_electricity_to_iam_data()
********************************

Main contributors
.................

`Brian Cox <https://github.com/brianlcox>`_,
`Alois Dirnaichner <https://github.com/Loisel>`_,
`Chris Mutel <https://github.com/cmutel>`_,
`Romain Sacchi <https://github.com/romainsacchi>`_

Adapted from: `Mendoza Beltran et al. 2018 <https://onlinelibrary.wiley.com/doi/full/10.1111/jiec.12825>`_

This transformation function reads electricity-related variables from the IAM file and adjusts electricity production
datasets and markets.

1. Power plants efficiencies
`premise` iterates through all the electricity production datasets that rely on fuel combustion.
This includes combustion of hard coal, lignite, natural gas and oil.
It identifies the current efficiency of the process, either by looking up in the parameters of the
dataset, or by calculating the fuel-to-electricity-output ratio.
Then, it looks up the expected efficiency for the technology from the IAM file for the year considered and rescales all the input
exchanges to that new efficiency ratio, including fuel inputs, infrastructure as well as carbon dioxide emissions.

2. Non-CO2 regulated emissions
`premise` iterates through all the electricity production datasets that rely on fuel combustion.
This includes combustion of hard coal, lignite, natural gas and oil.
It looks up the expected emissions for each technology for the year considered in the GAINS air emission model data.
It updates the corresponding emissions. This includes emissions of SO_2, CO, NO_x, NH_3 and NMVOC.

3. Electricity markets
`premise` deletes existing electricity markets.
Then, it creates new ones for each region of the IAM model, for high, medium and low voltage respectively.
Shares of each technology are looked up from the IAM file for the year considered.

High voltage markets are created first, where each technology contribute up to their share with the exception
of electricity from waste incineration and photovoltaic panels, and with the addition of a transmission loss.
Then, medium voltage markets take an input from high voltage markets,
with a voltage transformation loss and additional electricity from waste incineration.
Low voltage markets take an input from medium voltage markets with a voltage transformation loss and additional
electricity from photovoltaic-based technology.

update_vehicles()
*************

Main contributor
................

`Alois Dirnaichner <https://github.com/Loisel>`_
`Romain Sacchi <https://github.com/romainsacchi>`_

1. Electric vehicles
If passenger cars and/or truck inventories have been added upon the database creation, `update_vehicles()` will link
the electricity supply dataset these vehicles are using for battery charging or hydrogen production to the new
low voltage electricity markets created by `update_electricity_to_iam_data()`.

2. Internal combustion engine vehicles
If passenger cars and/or truck inventories have been added upon the database creation, `update_vehicles()` will link
the fuel supply of conventional, bio- and synthetic fuel to the closest geographical supplier.

3. Markets for passenger cars (upcoming)
Fleet projections from the IAM are used to build markets for passenger cars and trucks. Once these markets are built,
they replace existing markets and link back to transport-consuming activities.

update_cement_to_iam_data()
***************************

Main contributor
................

`Romain Sacchi <https://github.com/romainsacchi>`_

`premise` uses a combination of two external data sources:

* `WBCSD's GNR database <https://gccassociation.org/gnr/>`_ for historical data (1990 - 2018) on clinker and cement production, fuel mixes, clinker-to-cement ratio, etc.
* `IEA's technology roadmap for the cement industry <https://www.iea.org/reports/technology-roadmap-low-carbon-transition-in-the-cement-industry>`_ for projected data on clinker and cement production.

1. Clinker production
Existing national datasets for clinker production in ecoinvent are adapted to a regional level (a region that fits
the geographical scope of each IAM region).

For each clinker production dataset, the following aspects are adjusted:

* the thermal efficiency of the kiln: it is calculated as the product of the projected efficiency of each kiln technology
  (dry, semi-dry, wet, with or without pre-calciner, with or without pre-heater) and the expected share of each technology
  for the concerned region and year.
* the fuel mix: the use of fossil fuel, waste fuel and biomass fuel is adjusted, based on the thermal efficiency of the kiln
  and the calorific value of each fuel.
* fuel-related emissions (fossil and biogenic CO_2)): they are adjusted based on the fuel mix and thermal efficiency of the kiln as well as their
  respective emissions factors.
* other emissions: emissions of SO_2, CO, NO_x, NH_3 and NMVOC are adjusted based on the GAINS air emission model data
  for the cement sector.
* carbon capture and storage (CCS): if the IAM file provides a number for CCS for cement production for that region and
  that year, additional input of electricity and heat are added for the CO2 capture. Note that, if the GNR or IEA data indicates
  on-site production of electricity and heat based on waste heat recovery, the recovered amounts are subtracted to the
  electricity and heat needed for the CO_2 capture.

2. Cement production
`premise` deletes existing national cement production datasets and create regional ones instead, to match the IAM regions.
Then, it adjusts the electricity requirement to the value indicated by the GNR
database or the IEA projections. Most of that electricity is used for grinding.
Finally, it re-links all the ecoinvent activities that consume cement to the newly created cement production datasets
(mostly cement markets).

3. Cement markets
`premise` iterates through the market datasets for average cement (called "unspecified cement" in ecoinvent).
For each of these datasets, it will modify the supply share of each cement production dataset in that market in order to reach
the clinker-to-cement ratio indicated by the GNR database or the IEA projections for the concerned region
and year, in order to consider the use of supplementary cimentitious materials (e.g., fly ash, slag, calcined clay, etc.).
Finally, it re-links all the ecoinvent activities that consume cement  to the newly created cement market datasets
(mostly concrete production markets).

update_steel_to_iam_data()
**************************

Main contributors
.................

`Tom Terlouw <https://github.com/tomterlouw>`_,
`Romain Sacchi <https://github.com/romainsacchi>`_

Remark 1: still in development

Remark 2: only works with the variables of the industry module of REMIND

1. Steel markets
`premise` starts by deleting existing steel markets and replacing them by regional steel markets (for each region of
the IAM). Within each of these markets, the respective shares of primary and secondary steel are adjusted.
After this, steel-consuming datasets in ecoinvent are re-linked to the new steel market datasets, based on their location.

2. Steel production
For each REMIND region, the specific energy efficiency for primary and secondary steel production
is fetched from the REMIND data. In parallel, the fuel mix for each process types is also fetched (coal, oil,
natural gas and biomass-based fuel). With this information, the energy efficiency, fuel mix and resulting fossil and
biogenic CO_2 emissions are updated in each steel production dataset.
After this, steel-consuming datasets in ecoinvent are re-linked to the new steel production datasets, based on their location.

update_solar_PV()
**************************

Main contributor
.................

`Romain Sacchi <https://github.com/romainsacchi>`_


1. Solar PV efficiency module
`premise` iterates through photovoltaic panel installation activities (residential -- on roof -- and commercial
-- on ground) and adjusts the required panels area required to fulfill the peak power of the installation with
current and future efficiencies. As the efficiency increases, the surface of panels to mount diminishes.