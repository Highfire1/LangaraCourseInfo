from datetime import datetime
import sqlite3
import time

from LCIdatabase import Database

from scrapers.DownloadTransferInfo import TransferScraper
from scrapers.DownloadLangaraInfo import DownloadAllTermsFromWeb, fetchTermFromWeb

from parsers.AttributesParser import AttributesParser
from parsers.SemesterParser import parseSemesterHTML
from parsers.CatalogueParser import CatalogueParser
from parsers.TransferParser import TransferParser

from schema.Attribute import Attributes
from schema.Catalogue import Catalogue
from schema.Semester import Course

class Utilities():
    def __init__(self, database:Database) -> None:
        self.db = database
        
    # Build Database from scratch, fetching new files from all data sources
    # WARNING: THIS TAKES ~ ONE HOUR TO RUN 
    def buildDatabase(self):
        start = time.time()
        
        # Download / Save Transfer Information
        s = TransferScraper(headless=True)
        s.downloadAllSubjects(start_at=0)
        TransferScraper.sendPDFToDatabase(self.db, delete=True)
        
        # Download / Save Langara HTML
        DownloadAllTermsFromWeb(self.db.insertLangaraHTML)

        # Begin parsing saved files
        self.rebuildDatabaseFromStored()
        
        end = time.time()
        hours, rem = divmod(end-start, 3600)
        minutes, seconds = divmod(rem, 60)
        total = "{:0>2}:{:0>2}:{:02d}".format(int(hours),int(minutes),int(seconds))
        print(f"Database built in {total}!")
        
    # Rebuild data by parsing stored HTML and PDF
    # Mostly used for debugging
    # WARNING: TAKES ~ TEN MINUTES
    def rebuildDatabaseFromStored(self):
        # Clear old data and recreate tables
        self.db.cursor.executescript("DROP TABLE Sections; DROP TABLE Schedules; DROP TABLE CourseInfo; DROP TABLE TransferInformation")
        self.db.connection.commit()
        self.db.createTables()
        
        # TODO: Fetching 200 mb of HTML files at once seems questionable
        html = self.db.getAllLangaraHTML()
        
        catalogue = Catalogue()
        attributes = Attributes()
        
        for term in html:
            print(f"Parsing HTML for {term[0]}{term[1]} ({len(term[2])}).")
            
            db.insertSemester(parseSemesterHTML(term[2]))
            CatalogueParser.parseCatalogue(term[3], catalogue)
            AttributesParser.parseHTML(term[4], attributes)
        
        #print(catalogue)
        #print(attributes)
        self.db.insertCatalogueAttributes(catalogue, attributes)
        
        # Restore PDF files from database
        TransferScraper.retrieveAllPDFFromDatabase(self.db)
        transfers = TransferParser.parseTransferPDFs()
        self.db.insertTransfers(transfers)
        # Delete PDF files from filesystem
        #TransferScraper.sendPDFToDatabase()
    
    def exportDatabase(self):
        t = datetime.today()
        new_db = sqlite3.connect(f'LangaraCourseInfo{t.year}{t.month}{t.day}.db')
        # copies all tables
        query = "".join(line for line in self.db.connection.iterdump())
        new_db.executescript(query)
        # TODO: don't copy 200mb of data just to delete it half a second later
        new_db.executescript("DROP TABLE SemesterHTML; DROP TABLE TransferPDF; VACUUM")
        new_db.commit()
            
            
        
    def countSections(self, year=None, term=None):
        if year != None and term != None:
            query = "SELECT COUNT(*) FROM Sections WHERE year=? AND term=?"
            self.db.cursor.execute(query, (year, term))
        elif year != None:  
            query = "SELECT COUNT(*) FROM Sections WHERE year=?"
            self.db.cursor.execute(query, (year,))
        elif term != None:
            query = "SELECT COUNT(*) FROM Sections WHERE term=?"
            self.db.cursor.execute(query, (term,))
        else:
            self.db.cursor.execute("SELECT COUNT(*) FROM Sections")
        
        result = self.db.cursor.fetchone()
        return result[0]
    
    def databaseSummary(self):
        print("Database information:")
        n = self.db.cursor.execute("SELECT COUNT(*) FROM SemesterHTML").fetchone()
        print(f"{n[0]} semester HTML files found.")
        
        n = self.db.cursor.execute("SELECT COUNT(*) FROM TransferPDF").fetchone()
        print(f"{n[0]} transfer PDF files found.")
        
        n = self.db.cursor.execute("SELECT COUNT(*) FROM CourseInfo").fetchone()
        print(f"{n[0]} unique courses found.")
        
        n = self.db.cursor.execute("SELECT COUNT(*) FROM Sections").fetchone()
        print(f"{n[0]} unique course offerings found.")
        
        n = self.db.cursor.execute("SELECT COUNT(*) FROM Schedules").fetchone()
        print(f"{n[0]} unique schedule entries found.")
        
        n = self.db.cursor.execute("SELECT COUNT(*) FROM TransferInformation").fetchone()
        print(f"{n[0]} unique transfer agreements found.")
    
    def updateCurrentSemester(self) -> list[tuple[Course|None, Course]]:
        
        # Get Last semester.
        yt = self.db.cursor.execute("SELECT year, term FROM SemesterHTML ORDER BY year DESC, term DESC").fetchone()
                
        term = fetchTermFromWeb(yt[0], yt[1])
                    
        print(f"Parsing HTML for {term[0]}{term[1]} ({len(term[2])}).")
        semester = parseSemesterHTML(term[2])
        
        # Look for any changes to a course or schedule.
        changes:list[tuple[Course|None, Course]] = []
        
        for c in semester.courses:
            
            # Check if a section with all the same attributes exists in the database.
            db_course:Course = self.db.getSection(semester.year, semester.term, c.crn)

            if db_course == None:
                # This section has not been seen before in the database.
                changes.append((None, c))
                continue
            
            elif not c.isEqual(db_course):
                # This section has different information than in the database.
                changes.append((db_course, c))
                continue
            
            # Look for schedule changes.
            for s in c.schedule:
                
                if not s.isIn(db_course.schedule):
                    # The schedule for this section is different than in the database.
                    changes.append((db_course, c))
                    break
                
        db.insertSemester(semester)
        db.insertLangaraHTML(term[0], term[1], term[2], term[3], term[4])
        
        c = CatalogueParser.parseCatalogue(term[3])
        a = AttributesParser.parseHTML(term[4])
        self.db.insertCatalogueAttributes(c, a)
        
        return changes
                