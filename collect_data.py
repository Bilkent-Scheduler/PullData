from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import json
from datetime import datetime
    
class Lecture:
    def __init__(self, day, start_time, end_time, place):
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
        self.place = place
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        
class Section:
    def __init__(self, no, instructor):
        self.no = no
        self.instructor = instructor
        self.hours = []
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

class Course:
    def __init__(self, no, name):
        self.no = no
        self.name = name
        self.sections = []
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
               
class Dept:
    def __init__(self, code, dept_name, faculty_name):
        self.code = code
        self.dept_name = dept_name
        self.faculty_name = faculty_name
        self.courses = []
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

class Offerings:
    def __init__(self, pull_time):
        self.pull_time = pull_time
        self.depts = []
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


def get_day_no(day_str):
    return {
        'Mon': 0,
        'Tue': 1,
        'Wed': 2,
        'Thu': 3,
        'Fri': 4,
        'Sat': 5,
        'Sun': 6
    }[day_str]

def calculate_time(time_str):
    x = int(time_str.split(":")[0])*60
    x += int(time_str.split(":")[1])
    return x

def englishify(st):
    trans_table = st.maketrans("ğüşıöçĞÜŞİÖÇ", "gusiocGUSIOC")
    return st.translate(trans_table)

coptions = Options() 
#coptions.add_argument("--headless")


browser = webdriver.Chrome(options=coptions)
url = "https://stars.bilkent.edu.tr/homepage/plain_offerings"

browser.get(url)
time.sleep(1)
source = browser.page_source

while source.find("Applications which run automatic") != -1:
    
    captcha_answer = input("Please enter captcha: ")
    browser.find_element_by_id("user_code").send_keys(captcha_answer)
    browser.find_element_by_class_name("actionbutton").click()
    time.sleep(1)
    source = browser.page_source

off = Offerings(str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
print("Pulling offerings in", off.pull_time)

course_lines = browser.find_element_by_id("ccTable").find_element_by_tag_name("tbody").find_elements_by_tag_name("tr")

for i in range(len(course_lines)):
    course_line = browser.find_element_by_id("ccTable").find_element_by_tag_name("tbody").find_elements_by_tag_name("tr")[i]
    course_info = course_line.find_elements_by_tag_name("td")
    dp = Dept(course_info[0].text, course_info[1].text, course_info[2].text)
    print("Pulling", dp.code)
    
    course_line.click()
    time.sleep(1)
    
    lines = []
    if(browser.page_source.find("no course") == -1):
        lines = browser.find_element_by_id("poTable").find_element_by_tag_name("tbody").find_elements_by_tag_name("tr")
    else:
        print("no courses")
        off.depts.append(dp)
        browser.get(url)
        time.sleep(1)
        continue
    
    
    print(len(lines), "courses")
    
    for line in lines:
        course_infos = line.find_elements_by_tag_name("td")
        course_code = int(course_infos[0].text.split("-")[0].split()[1])
        course_name = course_infos[1].text
        section_no = int(course_infos[0].text.split("-")[1])
        instructor = englishify(course_infos[2].text)
        
        ns = Section(section_no, instructor)
        print("\t" +str(course_code) + "-" + str(section_no), course_name + ",", instructor)
        
        schedule_text = course_infos[-2].text
        if schedule_text != "":
            for schedule_line in schedule_text.split("\n"):
                schedule_words = schedule_line.split()
                
                day_no = get_day_no(schedule_words[0])
                
                start_time = calculate_time(schedule_words[1].split("-")[0])
                end_time = calculate_time(schedule_words[1].split("-")[1])
                
                place = ""
                try:
                    place = schedule_words[2].replace("(", "").replace(")", "")
                except:
                    place = "-"
                
                print("\t\t" + str(day_no), start_time, end_time, place)
                lec = Lecture(day_no, start_time, end_time, place)
                ns.hours.append(lec)
        
        boo = False
        for qw in dp.courses:
            if qw.no == course_code:
                qw.sections.append(ns)
                boo = True
                break
        if not boo:
            newcourse = Course(course_code, course_name)
            newcourse.sections.append(ns)
            dp.courses.append(newcourse)
        
    off.depts.append(dp)          
    
    browser.get(url)
    time.sleep(1)
json_str = off.toJSON()
f = open( "data.json", "w")
f.write(json_str)
f.close()
browser.quit()