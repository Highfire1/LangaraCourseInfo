# LangaraCourseInfo

This project collects course and transfer information from Langara College, Vancouver, into an SQLite database.

Once built, the database weighs around 15 MB for all data (~250 MB with source HTML/PDFs), which should be lightweight enough for most uses.

The transfer agreement scraper currently takes an excruciating amount of time - approximately an hour - this will be improved with multithreading in the future.

# Collected Data

 - Course Information: course description & other attributes
 - Course Offerings: dating from 1999 - present.
 - Transfer Information: only active transfer agreements are collected.

# Stack  
 - SQLite
 - Selenium
 - Beautifulsoup
