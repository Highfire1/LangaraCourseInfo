from LangaraCourseInfo import Database, Utilities

db = Database()
u = Utilities(db)

#u.buildDatabaseFromScratch()

#u.rebuildDatabaseFromStored()

#updates = u.updateCurrentSemester()

#u.exportDatabase()

u.databaseSummary()
