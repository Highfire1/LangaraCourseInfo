# LangaraCourseInfo

This project collects course and transfer information from Langara College, Vancouver, into an SQLite database.

Once built, the database weighs around 15 MB for all data (~250 MB with source HTML/PDFs), which should be lightweight enough for most uses.

The transfer agreement scraper currently takes an excruciating amount of time - approximately an hour - this will be improved with multithreading in the future.

# Collected Data

 - Course Information: course description & other attributes
 - Course Offerings: dating from 1999 - present.
 - Transfer Information: only active transfer agreements are collected.

# Table Definitions
 - TransferInformation(subject, course_code, source, destination, credit, effective_start, effective_end)
 - CourseInfo(subject, course_code, credits, title, description, lecture_hours, seminar_hours, lab_hours, AR, SC, HUM, LSC, SCI, SOC, UT)
 - Sections(year, term, seats, waitlist, subject, course_code, crn, credits, additional_fees, repeat_limit)
 - Schedules(year, term, crn, type, days,, time, start_date, end_date, room, instructor)

 - SemesterHTML(year, term, sectionHTML, catalogueHTML, attributeHTML)
 - TransferPDF(subject, pdf)

# Stack  
 - SQLite
 - Selenium
 - Beautifulsoup
