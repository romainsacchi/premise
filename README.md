# ``rmnd_lca``

# Integrated Assessment Model-based life cycle inventories for prospective life cycle assessment.
## Coupling ecoinvent database with projections from REMIND IAM

[![Build Status](https://travis-ci.org/romainsacchi/rmnd-lca.svg?branch=master)](https://travis-ci.org/romainsacchi/rmnd-lca) [![Coverage Status](https://coveralls.io/repos/github/romainsacchi/rmnd-lca/badge.svg?branch=master)](https://coveralls.io/github/romainsacchi/rmnd-lca?branch=master) [![Documentation](https://readthedocs.org/projects/rmnd-lca/badge/?version=latest)](https://rmnd-lca.readthedocs.io/en/latest/) [![PyPI version](https://badge.fury.io/py/rmnd-lca.svg)](https://badge.fury.io/py/rmnd-lca)


Introduction
============

**rmnd-lca** allows to align the life cycle inventories contained in the **ecoinvent 3.5, 3.6 and 3.7 cutoff** databases with
the output results of the Integrated Assessment Model (IAM) **REMIND**, in order to produce life cycle inventories under
future policy scenarios (from business-as-usual to very ambitious climate scenarios) for any year between 2005 and 2150.

In the latest version (0.1.6), this includes:
* electricity generation: alignment of regional electricity production mixes as well as efficiencies for a number of
 electricity production technologies, including Carbon Capture and Storage technologies.

**REMIND** also adds to the generic ecoinvent database a number of inventories, notably:
* electricity production using various fuels (including biomass and biogas) with Carbon Capture and Storage (CCS) [Volkart et al. 2013](https://doi.org/10.1016/j.ijggc.2013.03.003)
* hydrogen production from electrolysis from different world regions,
* hydrogen production from steam methane reforming (SMR) and auto-thermal reforming (ATR) of natural gas and biogas, with and without CCS [Antonini et al. 2020](https://doi.org/10.1039/D0SE00222D)
* hydrogen production from coal gasification [Antonini et al. 2020](https://doi.org/10.1039/D0SE00222D)
* hydrogen production from woody biomass gasification, with and without CCS [Antonini et al. 2020](https://doi.org/10.1039/D0SE00222D)
* synthetic fuels from Fischer-Tropsh (diesel), Methanol-to-liquid (gasoline) and electrolchemical methanation (gas) processes,
 using direct air capture (DAC) [Zhang et al. 2019](https://doi.org/10.1039/C9SE00986H)
* passenger car inventories from the library [carculator](https://github.com/romainsacchi/carculator)


In upcoming versions, it will also include:
* clinker and cement production: alignment of regional performance for clinker production, including Carbon Capture and 
 Storage, clinker-to-cement ratio and cement grinding.
* primary and secondary steel production: projection of primary vs. secondary steel supply on steel markets, projection 
 of efficiencies and fuel mixes for primary steel production, as well as alignment of electricity mix used for secondary 
 steel production. 
* heat for residential and industrial purposes: projection of technology shares in heat markets.

Documentation
-------------
https://rmnd-lca.readthedocs.io/en/latest/

Objective
---------

The objective is to produce life cycle inventories under future energy policies, by modifying the inventory database
ecoinvent 3 to reflect projected energy policy trajectories.

Requirements
------------
* Python language interpreter 3.x
* License for ecoinvent 3
* REMIND IAM output files come with the library ("xxx.mif" and "GAINS emission factors.csv")
 and are located by default in the subdirectory "/data/remind_output_files/".
 A file path can be specified to fetch the REMIND IAM output files elsewhere on your computer.

How to install this package?
----------------------------

Two options:

A development version with the latest advancements (but with the risks of unseen bugs),
is available on Conda:

    conda install rmnd-lca

For a more stable and proven version, from Pypi:

    pip install rmnd-lca

will install the package and the required dependencies.

How to use it?
--------------

### Extract (using brightway2)

A preliminary requirement to the use this library is to have a `brightway2` project created and opened, with the
`ecoinvent 3.5 cutoff`, `ecoinvent 3.6 cutoff` or `ecoinvent 3.7 cutoff` database registered, so that:

```python

    import brightway2 as bw
    bw.projects.set_current('remind')
    bw.databases
```
returns
```
    Databases dictionary with 2 object(s):
	biosphere3
	ecoinvent 3.5 cutoff
```
Then, for a chosen policy and year between 2005 and 2150, the following function will:
* extract the ecoinvent database, clean it, add additional inventories for carbon capture and storage, biofuels, etc.

For example, here with the year 2028 and a baseline variant of a "middle of the road" socioeconomic pathway called "SSP2-Base":
```python
    from rmnd_lca import *
    ndb = NewDatabase(scenario = 'SSP2-Base',
              year = 2028,
              source_db = 'ecoinvent 3.7 cutoff',
              source_version = 3.7,
             )
```
The current variants available of SSP2 are:
* SSP2-Base: counterfactual scenario with no climate policy implementation.
* SSP2-NPi: NPi (National Policies implemented) scenario  describes energy, climate and economic projections for the period until 2030, and equivalent efforts thereafter.
* SSP2-NDC: All emission reductions and other mitigation commitments of the Nationally Determined Contributions under the Paris Agreement are implemented.
* SSP2-PkBudg900, SSP2-PkBudg1100, SSP2-PkBudg1300: PkBudg 1300/1100/900: Climate policies to limit cumulative 2011-2100 CO2 emissions to 1300/1100/900 gigatons over the entire time horizon (not-to-exceed). Correspond to 2°, well-below 2° and 1.5° targets respectively. Other greenhouse gases are priced with the CO2e-price using 100year global warming potentials.

Further description of those scenarios is provided [here](https://github.com/romainsacchi/rmnd-lca/blob/master/rmnd_lca/data/remind_output_files/description.md).

Note that, by default, the library will look for REMIND output files ("xxx.mif" files and "GAINS emission factors.csv") in the
"data/remind_output_files" subdirectory. If those are not located there, you need to specify the path to
the correct directory, as such::
```python
    from rmnd_lca import *
    ndb = NewDatabase(scenario = 'SSP2-Base',
              year = 2028,
              source_db = 'ecoinvent 3.7 cutoff',
              source_version = 3.7,
              r"C:\Users\username\Documents\Remind output files"
             )
```

### Extract (without brightway2)

If you are not using brightway2, you may load the ecoinvent database
from its *ecospold2* files (available from the ecoinvent website),
like shown in the example below, by specifying `source_type = 'ecospold'`
and the file path to the ecospold files in `source_file_path`.

```python
    from rmnd_lca import *
    ndb = NewDatabase(scenario = 'SSP2-Base',
                  year = 2028,
                  source_db = 'ecoinvent 3.5 cutoff',
                  source_version = 3.5,
                  source_type = 'ecospold',
                  source_file_path = r"C:\Users\path\ecoinvent 3.5_cutoff_ecoSpold02\datasets"
                 )
```


### Transform

A series of transformations can be performed on the extracted database.
Currently, only the transformation regarding:
* electricity generation and distribution


is implemented.

All the transformation functions can be executed like so:

```python
    ndb.update_all()
```

But they can also be executed separately, as the following subsections show.

#### Electricity

The following function will:
* remove existing electricity markets
* replace them by regional markets (high, medium and low voltage) with a geographical scope and production mix
  defined by the REMIND model for that year,
* relink electricity-consuming activities to the newly created electricity markets,
* update the efficiency of electricity-producing technologies (fuel-input-to-energy-output ratio),
according to the projections given by REMIND,
* and rescale fuel-related emissions of electricity-producing technologies according to their newly defined efficiency.


```python
    ndb.update_electricity_to_remind_data()
```
returns
```python
    Remove old electricity datasets
    Create high voltage markets.
    Create medium voltage markets.
    Create low voltage markets.
    Link activities to new electricity markets.
    Log of deleted electricity markets saved in C:\Users\username\Documents\GitHub\rmnd-lca\rmnd_lca\data\logs
    Log of created electricity markets saved in C:\Users\username\Documents\GitHub\rmnd-lca\rmnd_lca\data\logs
    Rescale inventories and emissions for Coal IGCC
    Rescale inventories and emissions for Coal IGCC CCS
    Rescale inventories and emissions for Coal PC
    Rescale inventories and emissions for Coal PC CCS
    Rescale inventories and emissions for Coal CHP
    Rescale inventories and emissions for Gas OC
    Rescale inventories and emissions for Gas CC
    Rescale inventories and emissions for Gas CHP
    Rescale inventories and emissions for Gas CCS
    Rescale inventories and emissions for Oil
    Rescale inventories and emissions for Biomass CHP
    Rescale inventories and emissions for Biomass IGCC CCS
    Rescale inventories and emissions for Biomass IGCC
```

Note that logs of:
* deleted and created electricity markets
* changes in efficiencies for each power plant
are created in the `data/logs/` directory as MS Excel files, within rmnd_lca working directory.

#### Cement (not available yet)

The following function will:
* remove existing datasets for clinker production, clinker markets, cement production and cement markets
* replace them by regional production and market datasets
* for the new clinker production datasets, the following aspects are adjusted:
  * the kiln technology mix (wet vs. semi-wet vs. dry, with or without pre-heater and pre-calciner),
  * the kiln thermal efficiency,
  * the fuel mix (fossil vs. biogenic),
  * the fossil and biogenic CO2 emissions,
  * the emission of pollutants (BC, CO, Hg, etc.)
  * and the application of carbon capture, if needed
* for the new cement production datasets, the following aspects are adjusted: the power consumption (for grinding)
* for the new market datasets for average cement, the clinker-to-cement ratio is adjusted
* and relink cement-consuming activities to the newly created cement markets.

```python
    ndb.update_cement_to_remind_data()
```
returns
```python
    Log of deleted cement datasets saved in C:\Users\romai\Documents\GitHub\rmnd-lca\rmnd_lca\data\logs
    Log of created cement datasets saved in C:\Users\romai\Documents\GitHub\rmnd-lca\rmnd_lca\data\logs
    Create new clinker production datasets and delete old datasets
    Create new clinker market datasets and delete old datasets
    Adjust clinker-to-cement ratio in "unspecified cement" datasets
    Create new cement production datasets and adjust electricity consumption
    Create new cement market datasets
    Relink cement production datasets to new clinker production datasets
    Relink cement production datasets to new clinker market datasets
    Relink cement market datasets to new cement production datasets
    Relink activities to new cement datasets
```

Note that logs of deleted and created clinker and cement datasets are created in
the `data/logs/` directory as MS Excel files, within rmnd_lca working directory.

### Load (export back to brightway2)

Once the process is completed, the resulting database is registered back into the current Brightway2 project:
```python
    ndb.write_db_to_brightway()
```
returns
```
    Write new database to Brightway2.
    15223 datasets
    540424 exchanges
    0 unlinked exchanges

    Writing activities to SQLite3 database:
    Created database: ecoinvent_BAU_2028
```

### Load (export to matrices)

If you do not use brightway2, it is possible to export the transformed database into matrices.

```python
    ndb.write_db_to_matrices()
```
returns
```
    Write new database to matrix.
    Matrices saved in C:\Users\username\Documents\GitHub\rmnd-lca\rmnd_lca\data\matrices.
```

Two matrices are created:
* matrix A: contains product exchanges
* matrix B: contains exchanges between activities and the biosphere

Two other files are exported:
* A_matrix_index: maps row/column index of A_matrix to activity label
* B_matrix_index: maps row index of B_matrix to biosphere flow label

The column indices of B_matrix are similar to the row/column indices of A_matrix.

# Support

Do not hesitate to contact the development team at [romain.sacchi@psi.ch](mailto:romain.sacchi@psi.ch)
or [aloisdir@pik-potsdam.de](aloisdir@pik-potsdam.de).

## Maintainers

* [Romain Sacchi](https://github.com/romainsacchi)
* [Alois Dirnaichner](https://github.com/Loisel)
* [Tom Mike Terlouw](https://github.com/tomterlouw)
* [Laurent Vandepaer](https://github.com/lvandepaer)
* [Chris Mutel](https://github.com/cmutel/)

## Contributing

See [contributing](https://github.com/romainsacchi/rmnd-lca/blob/master/CONTRIBUTING.md).

## License

[BSD-3-Clause](https://github.com/romainsacchi/rmnd-lca/blob/master/LICENSE).
Copyright 2020 Potsdam Institute for Climate Impact Research, Paul Scherrer Institut.
