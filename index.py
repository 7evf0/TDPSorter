import requests
import numpy as np
from bs4 import BeautifulSoup
import warnings
from urllib3.exceptions import InsecureRequestWarning

book_max = 1000
student_min = 150

city_numbers = range(1,82)
# Suppress warnings
warnings.simplefilter('ignore', InsecureRequestWarning)

print("Started!")

for number in city_numbers:
    # Request Data
    url = "https://www.meb.gov.tr/baglantilar/okullar/index.php?ILKODU=" + str(number)
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.text, features="html.parser")

    # Extract School Data
    school_html = soup.find_all("tr")
    schools = [[title.text.strip(), title.find_all('a')[1]['href']] for title in school_html[2:]]
    schools = np.array([[*map(lambda x: x.strip(),school[0].split('-')[:3]),school[1]] for school in schools])

    # Filter Schools
    primary_schools = np.array([school for school in schools if school[2].endswith('İlkokulu')])
    middle_schools = np.array([school for school in schools if school[2].endswith('Ortaokulu')])

    # Refine School Data
    primary_schools_raw = np.array([[school[0], school[1],' '.join(school[2].split(' ')[:-1]), school[3]] for school in primary_schools])
    middle_schools_raw = np.array([[school[0], school[1],' '.join(school[2].split(' ')[:-1]), school[3]] for school in middle_schools])

    # Find Matching Schools
    matching_schools = np.array([[*item1, item2[3]] for item1 in primary_schools_raw for item2 in middle_schools_raw if np.array_equal(item1[:-1], item2[:-1])])

    # Scrape Individual School Pages
    book_student_records = []

    for curr_school in matching_schools:
        curr_book_student_pair_list = []
        
        about_url_pre, about_url_mid = curr_school[3:]

        page_pre = requests.get(about_url_pre, verify=False)
        page_mid = requests.get(about_url_mid, verify=False)

        soup_pre = BeautifulSoup(page_pre.text, "html.parser")  # should be "html.parser"
        soup_mid = BeautifulSoup(page_mid.text, "html.parser")  # should be "html.parser"

        try:
            book_number_pre = int(soup_pre.find("i", class_="fa fa-book").parent.text.split(':')[1].strip())
        except:
            book_number_pre = 0
        
        try:
            student_number_pre = int(soup_pre.find("i", class_="fa fa-child").parent.text.split(':')[1].strip())
        except:
            student_number_pre = 0
        
        curr_book_student_pair_list.append((book_number_pre,student_number_pre))

        try:
            book_number_mid = int(soup_mid.find("i", class_="fa fa-book").parent.text.split(':')[1].strip())
        except:
            book_number_mid = 0
            
        try:
            student_number_mid = int(soup_mid.find("i", class_="fa fa-child").parent.text.split(':')[1].strip())
        except:
            student_number_mid = 0
        
        
        if book_number_pre == book_number_mid:
            total_book = book_number_pre
        else:
            total_book = book_number_pre + book_number_mid
            
        total_student = student_number_pre + student_number_mid
        
        if total_book <= book_max and total_student >= student_min:
            print(*curr_school[:3], "İlkokul" ,book_number_pre, student_number_pre)
            print(*curr_school[:3], "Ortaokul" ,book_number_mid, student_number_mid, "\n")
        
        curr_book_student_pair_list.append((book_number_mid,student_number_mid))

        book_student_records.append(curr_book_student_pair_list)

print("Ended Succesfully!")
