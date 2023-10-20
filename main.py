from LCIdatabase import Database
from LCIutilities import Utilities
                

db = Database()
u = Utilities(db)

#u.buildDatabaseFromScratch()

#u.rebuildDatabaseFromStored()

#updates = u.updateCurrentSemester()

#u.exportDatabase()

u.databaseSummary()
