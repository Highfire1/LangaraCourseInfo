import sqlite3
from schema.Attribute import Attributes
from schema.Catalogue import Catalogue

from schema.Semester import Semester
from schema.Transfer import Transfer

class Database():
    def __init__(self) -> None:
        self.connection = sqlite3.connect("LangaraCourseInfo.db")
        self.cursor = self.connection.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS TransferInformation(
                subject,
                course_code,
                source,
                destination,
                credit,
                effective_start,
                effective_end,
                PRIMARY KEY (subject, course_code, source, destination, effective_start, effective_end)
                );""")

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS CourseInfo(
                subject TEXT,
                course_code INTEGER,
                credits REAL,
                title TEXT,
                description TEXT,
                lecture_hours INTEGER,
                seminar_hours INTEGER,
                lab_hours INTEGER,
                AR bool,
                SC bool,
                HUM bool,
                LSC bool,
                SCI bool,
                SOC bool,
                UT bool,
                PRIMARY KEY (subject, course_code)
            );""")

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Sections(
                year,
                term,
                RP,
                seats,
                waitlist,
                subject,
                course_code,
                crn,
                credits,
                additional_fees,
                repeat_limit,
                PRIMARY KEY (year, term, crn)
                );""")
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Schedules(
                year,
                term,
                crn,
                type,
                days,
                time,
                start_date,
                end_date,
                room,
                instructor,
                FOREIGN KEY (year, term, crn) REFERENCES Sections (year, term, crn)
                );""")
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS SemesterHTML(
                year,
                term,
                sectionHTML TEXT,
                catalogueHTML TEXT,
                attributeHTML TEXT,
                PRIMARY KEY (year, term)
            );""")
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS TransferPDF(
                subject TEXT,
                pdf BLOB,
                PRIMARY KEY (subject)
            );""")
        
        
        self.connection.commit()
    
    #def insertMultipleSemesterHTML(self, html:list[tuple[int, int, str]]):
    #    for term in html:
    #        self.insert_SemesterHTML(term[0], term[1], term[2])
    
    def insertLangaraHTML(self, year:int, term:int, sectionHTML, catalogueHTML, attributeHTML):
        # TODO: why does this need to be tupled twice?
        data = (year, term, sectionHTML, catalogueHTML, attributeHTML)
        self.cursor.execute("INSERT OR REPLACE INTO SemesterHTML VALUES(?, ?, ?, ?, ?)", data)
        self.connection.commit()
        
        #print(f"Saved HTML for {year}{term}.")
        
    def getSemesterHTML(self, year, term) -> tuple[str, str, str]:
        self.cursor.execute("SELECT html FROM SemesterHTML WHERE year = ? AND term = ?", (year, term))
        return self.cursor.fetchone()

    # Guaranteed to be sorted from newest to oldest
    def getAllLangaraHTML(self) -> list[tuple[int, int, str, str, str]]:
        self.cursor.execute("SELECT * FROM SemesterHTML ORDER BY year DESC, term DESC")
        return self.cursor.fetchall()

    def insert_Semester(self, semester: Semester):
        section = []
        for c in semester.courses:
            section.append((semester.year, semester.term, c.RP, c.seats, c.waitlist, c.subject, c.course_code, c.crn, c.credits, c.add_fees, c.rpt_limit))
        
        self.cursor.executemany("INSERT OR REPLACE INTO Sections VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", section)
        self.connection.commit()
        
        sched = []
        for c in semester.courses:
            for s in c.schedule:
                sched.append((semester.year, semester.term, c.crn, s.type.name, s.days, s.time, s.start, s.end, s.room, s.instructor))
        self.cursor.executemany("INSERT OR REPLACE INTO Schedules VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sched)
        self.connection.commit()
    
    def insertCatalogueAttributes(self, catalogue:Catalogue, attributes:Attributes):
        data = []
        for c in catalogue.courses:
            data.append((c.subject, c.course_code, c.credits, c.title, c.description, c.hours["lecture"], c.hours["seminar"], c.hours["lab"]))
        
        a = []
        for c in catalogue.courses:
            a.append(f"{c.subject}{c.course_code}")
        a.sort()
        for i in a:
            pass
            #print(i)
        
        # TODO: fix putting nulls in the database
        self.cursor.executemany("INSERT OR REPLACE INTO CourseInfo VALUES(?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL)", data)
        
        data = []
        for a in attributes.attributes:
            at = a.attributes
            data.append((at["AR"], at["SC"], at["HUM"], at["LSC"], at["SCI"], at["SOC"], at["UT"], a.subject, a.course_code))
        
        self.cursor.executemany("UPDATE CourseInfo SET AR=?, SC=?, HUM=?, LSC=?, SCI=?, SOC=?, UT=? WHERE subject=? AND course_code=?", data)

        self.connection.commit()
        
        """"AR" : table_items[i+1],
                    "SC": table_items[i+2],
                    "HUM": table_items[i+3],
                    "LSC": table_items[i+4],
                    "SCI": table_items[i+5],
                    "SOC": table_items[i+6],
                    "UT": table_items[i+7],  
        """
        
        
        pass
        
        """subject TEXT,
                course_code INTEGER,
                credits REAL,
                title TEXT,
                lecture_hours INTEGER,
                seminar_hours INTEGER,
                lab_hours INTEGER,
                AR bool,
                SC bool,
                HUM bool,
                LSC bool,
                SCI bool,
                SOC bool,
                UT bool,
                PRIMARY KEY (subject, course_code
        """

    
    def insertTransfers(self, transfers:list[Transfer]):
        data = []
        for t in transfers:
            data.append((t.subject, t.course_code, t.source, t.destination, t.credit, t.effective_start, t.effective_end))
        
        self.cursor.executemany("INSERT OR REPLACE INTO TransferInformation VALUES(?, ?, ?, ?, ?, ?, ?)", data)
        self.connection.commit()
    
    def insertTransferPDF(self, subject, bytes):
        data = (subject, bytes)
        self.cursor.execute("INSERT OR REPLACE INTO TransferPDF VALUES(?, ?)", data)
        self.connection.commit()
    
    def getAllTransferPDF(self) -> list[tuple[str, bytes]]:
        self.cursor.execute("SELECT * FROM TransferPDF")
        return self.cursor.fetchall()