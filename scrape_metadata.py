'''
Script for scraping metadata from the LLE site for all shots 
that one has access to
'''
from user import username, password
import os
from selenium.webdriver.common import keys, by
Keys,  By = keys.Keys(), by.By()
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from pdb import set_trace as st
import json
import time
from datetime import datetime

def save_to_json(my_dict, fname):
    my_json = json.dumps(my_dict)
    with open(fname, "w") as f:
        f.write(my_json)
        
def load_json(fname): #function for loading in json files
    with open(fname) as json_file: #assign opened file to object json_file
        data=json.load(json_file) #load data
    return data
        
class DriverHandler:
    """
    class for smoothly handling the opening of the webdriver
    """
    def __init__(self, headerless = False, op_sys = "linux"):
        """
        headerless:bool
            True if we don't want to display the webpage
            this is the default
            not displaying the webpage makes it faster
        """
        if op_sys == "windows":
            driver_loc = "chromedriver_win32/chromedriver.exe"
        elif op_sys == "linux":
            homedir = os.path.expanduser("~")
            driver_loc = "chromedriver_liux64/chromedriver"
            from pdb import set_trace as s 
            #s()
            driver_loc = f"chromedriver/stable/chromedriver"
        else:
            raise Exception("Only handled for linux and windows currently")
        self.s = Service(driver_loc)
        self.headerless = headerless
        self.op_sys = op_sys
        
    def get_http(self, http_address):
        self.options = webdriver.ChromeOptions()
        if self.headerless == True:
            self.options.add_argument("--headless")
            self.options.add_argument('--window-size=1920,1080')
        if self.op_sys == "linux":
            #self.options.add_argument("--headless")
            self.options.add_argument("--disable-dev-shm-usage")
            self.options.add_argument("--no-sandbox")
        if self.op_sys == "windows":
            default_storage_directory = os.getcwd() + "\\Data\\"
        elif self.op_sys == "linux":
            default_storage_directory = os.getcwd() + "/Data/tgz_files"
            #print(default_storage_directory)
        prefs = {"download.default_directory":default_storage_directory}
        self.options.add_experimental_option('prefs', prefs)
        #self.options.add_argument(f"download.default_directory={default_storage_directory}")
        max_tries = 3 #maximum number of tries at getting the url
        tries = 0
        while tries < 3:
            try:
                self.driver = webdriver.Chrome(service=self.s, options = self.options)
                self.driver.get(http_address)
                tries = 3 #set tries equal to max to escape the loop
            except:
                tries += 1 #add attempt
        
    def close(self):
        self.driver.close()

def pull_up_main_page():
    '''
    Function for pulling up the lle shot page
    '''
    entry_url = f"https://{username}:{password}@epops.lle.rochester.edu/lir"
    d = DriverHandler()
    d.get_http(entry_url)
    return d

class ShotRow:
    """Class for handling a single row in the shot table"""
    def __init__(self, row_obj:webdriver.remote.webelement.WebElement):
        """Initialization of shot row

        Args:
            row_obj (webdriver.remote.webelement.WebElement): _description_

        Returns:
            None
        """
        self.row_obj = row_obj
    
    def get_info(self):
        entries = self.row_obj.find_elements(By.CSS_SELECTOR, "*")
        info = []
        for entry in entries:
            if entry.text.lower() not in info and entry.text.lower() not in ["", " ", "download images"]:
                info.append(entry.text)
        return info

class ShotTable:
    """Class for handling a shot table with rows of shots found on the lle shot info site
    """
    def __init__(self, driver_handler:DriverHandler):
        """initialization function

        Args:
            driver_handler (DriverHandler): DriverHandler with page currently on the page we want to examine

        Returns:
            _type_: _description_
        """
        x_path = '/html/body/div[2]/div/table[3]/tbody'
        self.table = driver_handler.driver.find_element(By.XPATH, x_path)
        self.rows_retrieved = False #boolean for whether the rows have been retrieved from the table
        self.labels_retrieved = False #boolean for whether col labels have been retrieved
    
    def get_shot_rows(self):
        """Function for getting all shots from a table object"""
        if self.rows_retrieved == False:
            self.rows = [ShotRow(i) for i in self.table.find_elements(By.CSS_SELECTOR, 'tr')]
            self.rows_retrieved = True
            
    def get_labels(self):
        """Getting labels for the columns in the table
        """
        if self.labels_retrieved == False:
            self.get_shot_rows()
            header_info = self.rows[0].get_info()
            self.labels = [i.lower().replace("of", "").replace(" ", "_").replace("#", "num").replace("(", "").replace(")", "") for i in self.rows[0].get_info()]
            self.labels_retrieved = True
        
    def get_table_info(self):
        """Function for getting all information for all rows in the table
        """
        self.get_labels()
        table_info = {}
        for count, row in enumerate(self.rows):
            if count > 0: #skip 0 because that is where the labels are
                info = row.get_info()
                print(f"=====\nlabels: {self.labels}\ninfo: {info}\n=====")
                shot_dict = {}
                try:
                    for c, item in enumerate(info):
                        if c>0:
                            shot_dict[self.labels[c]] = item
                except:
                    print(f"FAILED TO SCRAPE {info[0]}")
                table_info[info[0]] = shot_dict
        self.info = table_info

        
class ShotSummary:
    """Class for scraping data from a shot summary
    """
    def __init__(self, shotID):
        self.shotID = shotID
        self.d = DriverHandler()
        from user import user1, user2
        users = user1, user2
        data_found = False
        num_attempts = 0
        while data_found == False:
            try:
                self.url = f"https://{users[num_attempts]['username']}:{users[num_attempts]['password']}@epops.lle.rochester.edu/lir?goSingle=goSingle&singleReport=Admin_Summary&shotnumber={shotID}"
                self.get_page()
                data_found = True
            except:
                if num_attempts < len(users) - 1:
                    num_attempts += 1
                else:
                    raise Exception(f"Data not accessible for either user")
        self.table_found = False #boolean for whether we have found the table yet
        self.info_retrieved = False #boolean for whether pulseshape, timing and energy info has been retrieved
        
    def get_page(self):
        self.d.get_http(self.url)
        
    def get_pulseshape_info(self):
        if self.table_found == False:
            self.get_table()
        found_pulseshape_info = False
        for row in self.rows:
            #found_pulseshape_info = False
            subelements = row.find_elements(By.CSS_SELECTOR, "*")
            subelements = [i for i in subelements if i.text != ""]
            row_title = subelements[0].text
            clean_title = row_title.replace("/", "").replace("(", "").replace(")", "").replace(":", "").replace(" ", "").lower()
            if clean_title == "pulseshapelengths":
                pulseshape_info = subelements[1].text.split("\n")
                cleaned_pulseshape_info = {}
                for item in pulseshape_info:
                    split = item.split(":")
                    beam_name = split[0].replace(" ", "")
                    pulseshape_name = split[1].replace(" ", "")
                    cleaned_pulseshape_info[beam_name] = pulseshape_name
                found_pulseshape_info = True
        if found_pulseshape_info == False: #handle the case where pulseshape info is not included
            cleaned_pulseshape_info = None
            self.has_pulseshape_info = False
        else:
            self.has_pulseshape_info = True
        return cleaned_pulseshape_info
        
    def get_timing_info(self):
        if self.table_found == False:
            self.get_table()
        found_timing_info = False
        for row in self.rows:
            subelements = row.find_elements(By.CSS_SELECTOR, "*")
            subelements = [i for i in subelements if i.text != ""]
            row_title = subelements[0].text
            clean_title = row_title.replace("/", "").replace("(", "").replace(")", "").replace(":", "").replace(" ", "").lower()
            if clean_title == "beamtiming":
                cleaned_timing_info = {}
                timing_info = subelements[1].text.split("\n")
                for item in timing_info:
                    split = item.split(":")
                    beam_name = split[0].replace(" ", "")
                    timing = float(split[1].replace(" ", "").replace("ns", ""))*10**-9
                    cleaned_timing_info[beam_name] = timing
                real_cleaned_timing_info = {}
                real_timing_info = subelements[2].text.split("\n")
                for item in real_timing_info:
                    split = item.split(":")
                    beam_name = split[0].replace(" ", "")
                    timing = float(split[1].replace(" ", "").replace("ns", ""))*10**-9
                    real_cleaned_timing_info[beam_name] = timing
                found_timing_info = True
        cleaned_timing_info, real_cleaned_timing_info = (None, None) if found_timing_info == False else (cleaned_timing_info, real_cleaned_timing_info)
        return {"requested": cleaned_timing_info, "real": real_cleaned_timing_info}
            
    def get_energy_info(self):
        if self.table_found == False:
            self.get_table()
        found_energy_info = False
        for row in self.rows:
            subelements = row.find_elements(By.CSS_SELECTOR, "*")
            subelements = [i for i in subelements if i.text != ""]
            row_title = subelements[0].text
            clean_title = row_title.replace("/", "").replace("(", "").replace(")", "").replace(":", "").replace(" ", "").lower()
            if clean_title == "energydeliveredattermination":
                cleaned_energy_info = {}
                energy_info = subelements[1].text.split("\n")
                for item in energy_info:
                    split = item.split(":")
                    beam_name = split[0].replace(" ", "")
                    req_total_energy = split[1].replace(" ", "").replace("J", "").replace("(", "").replace(")", "").replace("U", "").replace("V", "").replace("I", "").replace("R", "")
                    cleaned_energy_info[beam_name] = float(req_total_energy)
                real_cleaned_energy_info = {}
                real_energy_info = subelements[2].text.split("\n")
                for item in real_energy_info:
                    split = item.split(":")
                    beam_name = split[0].replace(" ", "")
                    total_energy = split[1].replace(" ", "").replace("J", "").replace("(", "").replace(")", "").replace("U", "").replace("V", "").replace("I", "").replace("R", "")
                    real_cleaned_energy_info[beam_name] = float(total_energy)
                found_energy_info = True
        cleaned_energy_info = None if found_energy_info == False else cleaned_energy_info
        real_cleaned_energy_info = None if found_energy_info == False else real_cleaned_energy_info
        print(f"=====\n{cleaned_energy_info}, {real_cleaned_energy_info}\n=====")
        return {"requested": cleaned_energy_info, "real": real_cleaned_energy_info}
        
    def get_all_info(self):
        self.pulseshape = self.get_pulseshape_info()
        self.timing = self.get_timing_info()
        self.energy = self.get_energy_info()
        beam_dict = {}
        for beam in self.timing["requested"].keys():
            timing = [self.timing["requested"][beam], self.timing["real"][beam]] if self.timing["requested"] != None else None
            if self.energy["requested"] == None:
                energy = None
            else:
                energy = [self.energy["requested"][beam], self.energy["requested"][beam]]
            if self.pulseshape != None:
                pulseshape = self.pulseshape[beam] 
            else:
                pulseshape = None
            beam_dict[beam] = {
                "start_time": timing,
                "energy": energy,
                "pulseshape": pulseshape
            }
        if os.path.exists(f"info.json"): #if the path exists, add to the existing json, otherwisemake a new one
            data = load_json("info.json") 
            if self.shotID in data.keys(): #delete data if it is already there
                del data[self.shotID]
            data[self.shotID] = beam_dict
        else:
            data = {self.shotID:beam_dict}
        save_to_json(data, "info.json")
        self.info_retrieved = True
    
    def get_shot_request(self):
        #Gets and returns the shot request dict for this shot
        if self.info_retrieved == False:
            self.get_all_info()
        beam_dict = {}
        for beam in self.timing["requested"].keys():
            timing = self.timing["requested"][beam] if self.timing["requested"] != None else None
            if self.energy["requested"] == None:
                energy = None
            else:
                energy = self.energy["requested"][beam]
            if self.pulseshape != None:
                pulseshape = self.pulseshape[beam] 
            else:
                pulseshape = None
            beam_dict[beam] = {
                "start_time": timing,
                "energy": energy,
                "pulseshape": pulseshape
            }
        shot_info = {f"{self.shotID}":beam_dict}
        print(shot_info)
        return shot_info
        
    def get_table(self):
        if self.table_found == False:
            self.table = self.d.driver.find_element(By.XPATH, '//*[@id="right"]/div/table/tbody')
            self.rows = self.table.find_elements(By.CSS_SELECTOR, "tr")
            self.table_found = True      

class PageHandler:
    def __init__(self):
        self.driver = DriverHandler()
        self.driver.get_http(f"https://{username}:{password}@epops.lle.rochester.edu/lir")
        
    def change_page(self):
        prev_shots_button = self.driver.driver.find_element(By.XPATH, '//*[@id="main"]/div/table[4]/tbody/tr/td[2]/a')
        prev_shots_button.click()
        
    def get_all_data(self):
        data_pulls = []
        still_looking = True
        while still_looking == True:
            table = ShotTable(self.driver)
            prev_url = self.driver.driver.current_url
            table.get_table_info()
            data_pulls.append(table.info)
            self.change_page()
            current_url = self.driver.driver.current_url
            if current_url == prev_url:
                still_looking = False
        all_data = {}
        for data in data_pulls:
            for key in data.keys():
                all_data[key] = data[key]
        save_to_json(all_data, "scraped_lle.json")
        return all_data

def download_tgz(shot_name):
    """Function for downloading data file to Data/tgz_files

    Args:
        shot_no (_type_): _description_
    """
    fpath = f"https://{username}:{password}@epops.lle.rochester.edu/lir?singleReport=Download_Images&shotnumber={shot_name}"
    d = DriverHandler()
    d.get_http(fpath)
    files_to_dl = "/html/body/form[2]/select/option"
    options = d.driver.find_elements(By.XPATH, files_to_dl)
    #st()
    for option in options:
        if "processed_shot_data" in option.text:
            print(option.text)
            file_to_download = option
    file_to_download.click() #click on processed shot data file to download
    download_button_xpath = "/html/body/form[2]/p/input"
    download_button = d.driver.find_element(By.XPATH, download_button_xpath)
    import time
    time.sleep(0.5)
    download_button.click()
    time.sleep(5) #wait for file to finish downloading
    os.rename("Data/tgz_files/omega.tgz", f"Data/tgz_files/s{shot_name}.tgz")
    
def scrape_everything():
    """Function for scraping all shots that one has access to
    """
    from shot_info2 import add_shot_request, shot_requests
    p = PageHandler()
    all_shots = p.get_all_data()
    #all_shots = load_json("scraped_lle.json")
    date = f"{datetime.now().year}_{datetime.now().month}_{datetime.now().day}"
    report_num = len([i for i in os.listdir("reports") if i.split("__")[0] == date]) + 1
    report_name = f"{date}__{report_num}.json"
    report = {}
    for c, shot in enumerate(all_shots.keys()):
        if c >= 10: 
            pass
        from shot_info2 import shot_requests as sr
        if f"s{shot}" not in sr.keys():
            shot_name = shot
            #try to get the shot summary n times before quitting
            tries = 0
            max_tries = 3
            while tries < max_tries:
                try:
                    s = ShotSummary(shot_name)
                    s.get_page()
                    request = s.get_shot_request()
                    tries = max_tries
                except:
                    tries += 1
            try:
                add_shot_request(request) #add the shot request if not already there
                report[shot] = False
            except:
                report[shot] = True
        save_to_json(report, f"reports/{report_name}")

        if f"s{shot}.tgz" not in os.listdir("Data/tgz_files"):
            #grab tar file if we don't already have it
            try: #try to download the file
                download_tgz(shot_name)
                all_shots[shot]["found_tgz"] = True
            except: #if we can't find the file to download
                all_shots[shot]["found_tgz"] = False
                
            #time.sleep(1) #wait for the file to download
            #os.rename("Data/tgz_files/omega.tgz", f"Data/tgz_files/s{shot_name}.tgz")
    
test_shot_summary = 0
test_table_class = 0
test_page_handler = 0
test_tgz_download = 0
scrape = 1

if test_shot_summary == True:
    s = ShotSummary("38474")
    s.get_page()
    s.get_shot_request()
    
if test_table_class == True:
    driver = pull_up_main_page()
    #t = ShotTable(driver)
    #t.get_table_info()
    #print(t.info)
    
if test_page_handler == True:
    p = PageHandler()
    data = p.get_all_data()
    for shot in data.keys():
        print(shot)
        for item in data[shot].keys():
            print(f"    {item}: {data[shot][item]}")
            
if test_tgz_download == True:
    download_tgz("38635")
            
if scrape == True:
    scrape_everything()
    
            
    
