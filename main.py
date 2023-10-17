from datetime import datetime
import os
import sqlite3
import sys
import logging
import uvicorn
import schedule
import gzip
import time

from parsers.AttributesParser import AttributesParser

from parsers.SemesterParser import parseSemesterHTML
from parsers.CatalogueParser import CatalogueParser
from parsers.TransferParser import TransferParser
from database import Database
from schema.Attribute import Attributes
from schema.Catalogue import Catalogue

from scrapers.DownloadTransferInfo import TransferScraper
from scrapers.DownloadLangaraInfo import DownloadAllTermsFromWeb


class Utilities():
    def __init__(self, database:Database) -> None:
        self.db = database
        
    # Build Database from scratch 
    def buildDatabaseFromScratch(self):
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
    def rebuildDatabaseFromStored(self):
        # TODO: Fetching 200 mb of HTML files at once seems questionable
        html = self.db.getAllLangaraHTML()
        
        catalogue = Catalogue()
        attributes = Attributes()
        
        for term in html:
            print(f"Parsing HTML for {term[0]}{term[1]} ({len(term[2])}).")
            
            db.insert_Semester(parseSemesterHTML(term[2]))
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
    
    def exportDatabase(self):
        t = datetime.today()
        new_db = sqlite3.connect(f'LangaraCourseInfoExported{t.year}{t.month}{t.day}.db')
        query = "".join(line for line in self.db.connection.iterdump())
        new_db.executescript(query)
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
    
        
    
db = Database()
u = Utilities(db)

#u.buildDatabaseFromScratch()

#u.rebuildDatabaseFromStored()


u.exportDatabase()


# Utilities

#print(u.countSections(), "unique sections found")






#latest_semester_update()
#sys.exit()