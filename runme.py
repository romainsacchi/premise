import brightway2 as bw
from rmnd_lca import *

# Call brightway2
bw.projects.set_current('H2')
print("Existing databases in the project:")
print(bw.databases)

# Extract the ecoinvent database, clean it, add additional inventories
ndb = NewDatabase(scenario = 'REMIND_generic_SSP2-NDC',
          year = 2030,
          source_db = 'ecoinvent_cut-off36',
          source_version = 3.6,
          filepath_to_remind_files = r"C:\Users\siala\Documents\REMIND\output\SSP2-NDC_2020-11-26_21.02.02"
         )

# Transform
ndb.update_heat_to_remind_data()
ndb.update_all()

# Export to Brightway2
ndb.write_db_to_brightway()

# Export to matrices
ndb.write_db_to_matrices()

import pdb; pdb.set_trace()