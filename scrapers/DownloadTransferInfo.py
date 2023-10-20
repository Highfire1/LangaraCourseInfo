from selenium import webdriver
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options

import os
import fitz

class TransferScraper:
    def __init__(self, institution = "LANG", delay = 0.3, headless = True) -> None:
        
        print("Launching Selenium...")
        
        options = Options()
        if headless == True:
            options.add_argument("--headless")
        # download files to \downloads
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference('browser.download.dir', f"{os.path.abspath(os.getcwd())}\downloads")
        
        options.set_preference("browser.cache.disk.enable", False)
        options.set_preference("browser.cache.memory.enable", False)
        options.set_preference("browser.cache.offline.enable", False)
        options.set_preference("network.http.use-cache", False)

        driver = webdriver.Firefox(options=options)
        driver.implicitly_wait(10)
        driver.set_window_size(200, 800)
        driver.execute_script("document.body.style.zoom = '50%'")

        self.driver = driver
        self.d:int = delay
        self.actions = ActionChains(driver)
        
        self.institution = institution
        self.subjects:list[tuple[str, str]] = []
        
        
        
    # Go back to starting page and set institution.
    def initialize(self):
        link = "https://www.bctransferguide.ca/transfer-options/search-courses/"
        
        self.driver.switch_to.new_window('tab')
        old = self.driver.window_handles[0]
        new = self.driver.window_handles[1]
        self.driver.switch_to.window(old)
        self.driver.close()
        self.driver.switch_to.window(new)
        
        self.driver.get(link)
        
        # scroll down a bit
        self.actions.scroll_by_amount(0, 700).pause(self.d).perform()
        
        # select institution
        wait = WebDriverWait(self.driver, 15)
        institutionEl = wait.until(EC.presence_of_element_located((By.ID, "institutionSelect")))
        
        # TODO: figure out why setting institution breaks sometimes
        self.actions.pause(2).perform()
        self.actions.move_to_element(institutionEl).pause(self.d).click().pause(self.d).send_keys(self.institution).pause(self.d).send_keys(Keys.ENTER).pause(self.d).perform()
        self.actions.pause(2).perform()
        
        
    def generate_subjects(self) -> list[tuple[str, str]]:

        subjectsEl = self.driver.find_elements(By.CLASS_NAME, "multiselect__content")
        subjectsHTML = subjectsEl[2].get_attribute('innerHTML')
        splitHTML = subjectsHTML.split('title="')
        
        for i in splitHTML:
            data = i[0:200].split('"')[0]
            
            # ignore first title
            if "<!----> <li class=" in data:
                continue
                
            subj = data.split(" - ")[0]
            if " - " in data:
                desc = data.split(" - ")[1].replace("&amp;", "&").strip()
            else:
                desc = None
            self.subjects.append((subj, desc))
        
        print(f"Found transfer information for {len(self.subjects)} subjects.")
        return self.subjects
        

    def downloadSubject(self, subject:tuple[str, str]):
                
        self.initialize()
        de = self.d
        
        subjectEl = self.driver.find_element(By.ID, "subjectSelect")
        courseEl = self.driver.find_element(By.ID, "courseNumber")

        # Select subject from list
        search = subject[0]
        if subject[1] != None:
            search += " - "
        
        self.actions.move_to_element(subjectEl).click().pause(de).send_keys(search).pause(de).perform()
        
        search = subject[0]
        if subject[1] != None:
            search += " - "
            

        subj = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{search}')]")
        self.actions.move_to_element(subj).click().pause(de).perform()
      
        # make request
        self.actions.move_to_element(courseEl).click().pause(de).send_keys(Keys.ENTER).perform()
        
        # wait for request to load
        wait = WebDriverWait(self.driver, 90) 
        wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Showing result')]")))

        # TODO: doesn't trigger?
        if "Please try again" in self.driver.page_source:
            print(f"There are no active transfer agreements for {subject[0]}.")
            return
            
        # TODO: basic diagnostics e.g. how many courses transfer for the subject
        
        
        # save PDF
        pdfButton = self.driver.find_element(By.XPATH, f"//*[contains(text(), 'Save to PDF')]")
        self.actions.pause(3).perform()
        self.actions.move_to_element(pdfButton).click().perform()
        
        # Wait for new tab to open
        wait = WebDriverWait(self.driver, 90) 
        wait.until(EC.number_of_windows_to_be(2))
        
        parent = self.driver.window_handles[0]
        chld = self.driver.window_handles[1]
        self.driver.switch_to.window(chld)
        
        try:
            wait = WebDriverWait(self.driver, 90)
            wait.until(EC.title_contains("course"))
        
            print("PDF did not download in 90 seconds.")
        except NoSuchWindowException:
            print("PDF downloaded.")
            # close pdf window and navigate back to transfer search
            wait = WebDriverWait(self.driver, 10) 
            wait.until(EC.number_of_windows_to_be(2))
            
            pdf = self.driver.window_handles[1]
            self.driver.switch_to.window(pdf)
            self.driver.close()
            self.driver.switch_to.window(parent)
                
    def downloadAllSubjects(self, start_at=0):
                
        self.initialize()
        self.generate_subjects()

        if start_at > 0:
            print(f"Skipping {start_at} subjects.")
        
        for i, s in enumerate(self.subjects):
            
            if i < start_at - 1:
                continue
            
            print(f"Downloading transfer information for {s[0]} - {s[1]} ({i+1}/{len(self.subjects)}).")
            try:
                self.downloadSubject(s)
            except Exception as e:
                print(f"Failed to download {s[0]} - {s[1]}: {e}")
        
        self.driver.quit()
        
        
            
    # Sends PDFs in /downloads to the database then maybe delete them
    def sendPDFToDatabase(database, delete = True):
        dir = "downloads/"
        pdfs = os.listdir(dir)
                        
        for i, p in enumerate(pdfs):
            
            with fitz.open(dir+p) as pdf:
                text = chr(12).join([page.get_text() for page in pdf])
            
            info = text[0:100].split()
            subject = info[5]
            agreements = info[7]
            courses = info[11]
            institutions = info[14]
            
            with open(dir+p, "rb") as fi:
                database.insertTransferPDF(subject, fi.read())
                
            #print(f"Inserted transfer agreements for {subject} into the database ({i+1}/{len(pdfs)}).")
        
        print(f"Inserted {len(pdfs)} PDFs into the database.")
        
        if delete:
            for p in pdfs:
                os.remove(dir+p)       
            
    def retrieveAllPDFFromDatabase(database, path="downloads/"):
        dir = path
        
        # don't overwrite files
        # assert len(os.listdir(dir)) == 0, f"Empty {dir} before retrieving PDFs!"
    
        pdfs = database.getAllTransferPDF()
                
        for p in pdfs:
            
            subj = "".join(x for x in p[0] if x.isalnum()) # sanitize
            filename = f"{dir}{subj} Transfer Information.pdf"
            
            with open(filename, "wb") as fi:
                fi.write(p[1])
        
