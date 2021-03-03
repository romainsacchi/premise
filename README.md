# ``premise``

<div style="text-align:center">
<img src="https://github.com/romainsacchi/premise/raw/master/docs/large.png" height="300"/>
</div>

# **PR**ospective **E**nviron**M**ental **I**mpact As**SE**ssment
## Coupling the ecoinvent database with projections from Integrated Assessment Models (IAM)

Previously named *rmnd-lca*. *rmnd-lca* was designed to work with the IAM model REMIND only.
As it now evolves towards a more IAM-neutral approach, a change of name was considered.
 
[![Build Status](https://travis-ci.org/romainsacchi/premise.svg?branch=master)](https://travis-ci.org/romainsacchi/premise) [![Build status](https://ci.appveyor.com/api/projects/status/qdtgf7tngv652x03?svg=true)](https://ci.appveyor.com/project/romainsacchi/premise) [![Coverage Status](https://coveralls.io/repos/github/romainsacchi/premise/badge.svg?branch=master)](https://coveralls.io/github/romainsacchi/premise?branch=master) [![Documentation](https://readthedocs.org/projects/premise/badge/?version=latest)](https://premise.readthedocs.io/en/latest/) ![PyPI](https://img.shields.io/pypi/v/premise)

Documentation
-------------
[https://premise.readthedocs.io/en/latest/](https://premise.readthedocs.io/en/latest/)

Objective
---------

The objective is to produce life cycle inventories under future energy policies, by modifying the inventory database
ecoinvent 3 to reflect projected energy policy trajectories.

Requirements
------------
* Python language interpreter 3.x
* License for [ecoinvent 3][1]
* Some IAM output files come with the library ("REMIND_xxx.mif" for REMIND, "IMAGE_xxxx.xlsx" for IMAGE)
 and are located by default in the subdirectory "/data/iam_output_files".
 A file path can be specified to fetch IAM output files elsewhere on your computer.
 * [brightway2][2] (optional)

How to install this package?
----------------------------

Two options:

A development version with the latest advancements (but with the risks of unseen bugs),
is available from Anaconda Cloud:

    conda install -c romainsacchi premise

For a more stable and proven version, from Pypi:

    pip install premise

will install the package and the required dependencies.

Introduction
============

**premise** allows to align the life cycle inventories contained in the **ecoinvent 3.5, 3.6 and 3.7 cutoff** databases with
the output results of Integrated Assessment Models (IAM) **[REMIND][3]** and **[IMAGE][4]**, in order to produce life cycle inventories under
future policy scenarios (from business-as-usual to very ambitious climate scenarios) for any year between 2005 and 2100.

Inputs
------

Either:
* ecoinvent v.3.5, 3.6 or 3.7 as a registered brightway2 database
* ecoinvent v.3.5, 3.6 or 3.7 as [ecospold2][5] files

Transformations
---------------

More specifically, **premise** will apply a series of transformation functions to ecoinvent.

In the latest version (0.1.7), the following transformation functions are available:

* **update_electricity_to_iam_data()**: alignment of regional electricity production mixes as well as efficiencies for a number of
electricity production technologies, including Carbon Capture and Storage technologies.
* **update_vehicles()**: fuel markets that supply transport vehicles are adjusted according to the IAM projections,
including penetration of bio- and synthetic fuels. Then, given a fleet composition, markets for passenger cars and trucks are created.
Finally, these transport markets link back to transport-consuming activities.
* **update_cement_to_iam_data()**: adjustment of technologies for cement production (dry, semi-dry, wet, with pre-heater or not),
fuel efficiency of kilns, fuel mix of kilns (including biomass and waste fuels) and clinker-to-cement ratio.
* **update_steel_to_iam_data()**: adjustment of process efficiency, fuel mix and share of secondary steel in steel markets.
* **update_solar_PV()**: adjustment of solar PV modules efficiency, to reflect current (18-20%) and future (25%) efficiencies.
However, whether or not these transformation functions can be applied will depend on the existence of the necessary variables in
the IAM file you use as input.

|Function                        |Implemented?|Description                                                            |REMIND|IMAGE|Other IAM|Comment                               |
|--------------------------------|------------|-----------------------------------------------------------------------|------|-----|---------|--------------------------------------|
|update_electricity_to_iam_data()| Yes        | Aligns electricity markets and power plants efficiencies     | Yes  | Yes | No      |                                      |
|update_vehicles()               | Yes        | Aligns fuel supply markets with IAM and creates transport markets | Yes  | Yes | No      |                                      |
|update_cement_to_iam_data()     | Yes        | Aligns clinker and cement production and supply | Yes  | Yes | Yes     | Uses external data sources ([WBCSD][6] and [IEA][7])|
|update_steel_to_iam_data()      | Yes        | Align primary and secondary steel production and supply| Yes  | No  | No      | Only works with REMIND at the moment.|
|update_metal_markets()          | Not yet    | Align metal extraction and supply with IAM                            | No   | No  | No      |                                      |
|update_solar_PV()               | Yes        | Align solar PV modules efficiency | Yes | Yes | Yes | Uses external data source ([PSI]][7]) |

The following REMIND IAM files come with the library:

* SSP2
    1.  **Base:** counter-factual scenario with no climate policy implemented
    2.  **NPi** (*N*ational *P*olicies *i*mplemented): scenario  describes energy,  climate  and  economic  projections for the  period  until 2030, and equivalent efforts thereafter. See [CD-LINKS modelling protocol][8] for details.
    3.  **NDC**: All emission reductions and other mitigation commitments of the *N*ationally*D*etermined *C*ontributions under the Paris Agreement are implemented. See [CD-LINKS modelling protocol][8] for details.
    4.  **PkBudg 1300/1100/900**: Climate policies to limit cumulative 2011-2100 CO2 emissions to 1300 / 1100 / 900 over the entire time horizon (“not-to-exceed”). Correspond to 2°, well-below 2° and 1.5° targets. Other greenhouse gases are priced with the CO2e-price using 100year global warming potentials.

The following IMAGE IAM file comes with the library:

* SSP2
    1.  **Base** counter-factual scenario with no climate policy implemented

You can however use any other IAM files.

Additionally, a number of inventories for emerging technologies are added upon the creation of a new database.

* electricity production using various fuels (including biomass and biogas) with Carbon Capture and Storage (CCS) [Volkart et al. 2013][9]
* hydrogen production from electrolysis from different world regions,
* hydrogen production from steam methane reforming (SMR) and auto-thermal reforming (ATR) of natural gas and biogas, with and without CCS [Antonini et al. 2020][10]
* hydrogen production from coal gasification [Antonini et al. 2020][10]
* hydrogen production from woody biomass gasification, with and without CCS [Antonini et al. 2020][10]
* synthetic fuels from Fischer-Tropsh (diesel), Methanol-to-liquid (gasoline) and electrolchemical methanation (gas) processes,
 using direct air capture (DAC) [Zhang et al. 2019][11]
* passenger car inventories from the library [carculator][12]
* medium and heavy duty trucks from the library [carculator_truck][13]

Outputs
-------

Either:
* a database to register in a brightway2 project
* a sparse matrix representation of the database stored in csv files
* a SimaPro CSV file for SimaPro 9.x

How to use it?
--------------

The best way is to follow [the examples from the Jupyter Notebook](https://github.com/romainsacchi/premise/blob/master/examples/examples.ipynb). 

# Support

Do not hesitate to contact the development team at [romain.sacchi@psi.ch](mailto:romain.sacchi@psi.ch)
or [aloisdir@pik-potsdam.de](mailto:aloisdir@pik-potsdam.de).

## Maintainers

* [Romain Sacchi](https://github.com/romainsacchi)
* [Alois Dirnaichner](https://github.com/Loisel)
* [Tom Mike Terlouw](https://github.com/tomterlouw)
* [Laurent Vandepaer](https://github.com/lvandepaer)
* [Chris Mutel](https://github.com/cmutel/)

## Contributing

See [contributing](https://github.com/romainsacchi/premise/blob/master/CONTRIBUTING.md).

## References

[1]:https://www.ecoinvent.org/
[2]:https://brightway.dev/
[3]:https://www.pik-potsdam.de/en/institute/departments/transformation-pathways/models/remind
[4]:https://models.pbl.nl/image/index.php/IMAGE_framework
[5]:https://www.ecoinvent.org/data-provider/data-provider-toolkit/ecospold2/ecospold2.html
[6]:https://gccassociation.org/sustainability-innovation/gnr-gcca-in-numbers/
[7]:https://www.psi.ch/sites/default/files/import/ta/PublicationTab/Final-Report-BFE-Project.pdf
[8]:https://www.iea.org/reports/technology-roadmap-low-carbon-transition-in-the-cement-industry
[9]:https://www.cd-links.org/wp-content/uploads/2016/06/CD-LINKS-global-exercise-protocol_secondround_for-website.pdf
[10]:https://doi.org/10.1016/j.ijggc.2013.03.003
[11]:https://doi.org/10.1039/D0SE00222D
[12]:https://doi.org/10.1039/C9SE00986H
[13]:https://github.com/romainsacchi/carculator
[14]:https://github.com/romainsacchi/carculator_truck

## License

[BSD-3-Clause](https://github.com/romainsacchi/premise/blob/master/LICENSE).
Copyright 2020 Potsdam Institute for Climate Impact Research, Paul Scherrer Institut.
