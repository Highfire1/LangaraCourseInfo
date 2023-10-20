import sqlite3
from schema.Attribute import Attributes
from schema.Catalogue import Catalogue

from schema.Semester import Course, ScheduleEntry, Semester
from schema.Transfer import Transfer

class Database:
    def __init__(self, database_name="LangaraCourseInfo.db") -> None:
        self.connection = sqlite3.connect(database_name)
        self.cursor = self.connection.cursor()
        
        self.createTables()
    
    def createTables(self):
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
                crn,
                subject,
                course_code,
                section,
                credits,
                title,
                additional_fees,
                repeat_limit,
                notes,
                PRIMARY KEY (year, term, crn)
                );""")
        
        # Yes, all those primary keys are neccessary
        # :/
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
                PRIMARY KEY (year, term, crn, type, days, time, start_date, end_date, room, instructor)
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
        self.cursor.execute("SELECT sectionHTML, catalogueHTML, attributeHTML FROM SemesterHTML WHERE year = ? AND term = ?", (year, term))
        return self.cursor.fetchone()

    # Guaranteed to be sorted from newest to oldest
    def getAllLangaraHTML(self) -> list[tuple[int, int, str, str, str]]:
        self.cursor.execute("SELECT * FROM SemesterHTML ORDER BY year DESC, term DESC")
        return self.cursor.fetchall()

    def insert_Semester(self, semester: Semester):
        section = []
        for c in semester.courses:
            section.append((semester.year, semester.term, c.RP, c.seats, c.waitlist, c.crn, c.subject, c.course_code, c.section, c.credits, c.title, c.add_fees, c.rpt_limit, c.notes))
        
        self.cursor.executemany("INSERT OR REPLACE INTO Sections VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", section)
        self.connection.commit()
        
        
        # Must delete old schedules because sometimes the SIS does that
        delete = []
        for c in semester.courses:
            delete.append((semester.year, semester.term, c.crn))
        self.cursor.executemany("DELETE FROM Schedules WHERE year=? AND term=? AND crn=?", delete)
        self.connection.commit()
        
        # Re add all schedules
        sched = []
        for c in semester.courses:
            for s in c.schedule:
                sched.append((semester.year, semester.term, c.crn, s.type.value, s.days, s.time, s.start, s.end, s.room, s.instructor))
                
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
    
    def getSection(self, year, term, crn) -> Course | None:
        c = self.cursor.execute("SELECT * FROM Sections WHERE year=? AND term=? AND crn=?", (year, term, crn))
        c = c.fetchone()
        
        if c is None:
            return None
        
        c = Course(RP=c[2], seats=c[3], waitlist=c[4], crn=c[5], subject=c[6], course_code=c[7], section=c[8], credits=c[9], title=c[10], add_fees=c[11], rpt_limit=c[12], notes=c[13], schedule=[])
        
        c.schedule = self.getSchedules(year, term, c.crn)
        
        assert c.schedule is not None
        
        return c
     
    
    def getSchedules(self, year, term, crn) -> ScheduleEntry | None:
        s_db = self.cursor.execute("SELECT * FROM Schedules WHERE year=? AND term=? AND crn=?", (year, term, crn))
        s_db = s_db.fetchall()
                
        if s_db is None:
            return None

        scheds:list[ScheduleEntry] = []
        for s in s_db:
                        
            scheds.append(ScheduleEntry(type=s[3], days=s[4], time=s[5], start=s[6], end=s[7], room=s[8], instructor=s[9]))
        return scheds