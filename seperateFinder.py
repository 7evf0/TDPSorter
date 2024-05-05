import requests
import numpy as np
from bs4 import BeautifulSoup
import warnings
from urllib3.exceptions import InsecureRequestWarning
from progressbar import Percentage, ProgressBar, Bar, ETA, AnimatedMarker
import xlsxwriter
from datetime import date

book_max = 1000
student_min = 150

# Suppress warnings
warnings.simplefilter('ignore', InsecureRequestWarning)

cityNo = int(input("İstediğiniz şehrin plakasını girin (1-81): "))

# Request Data
url = "https://www.meb.gov.tr/baglantilar/okullar/index.php?ILKODU=" + str(cityNo)
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
matching_schools = np.array([[item1[0], item1[1], item1[2]] for item1 in primary_schools_raw for item2 in middle_schools_raw if np.array_equal(item1[:-1], item2[:-1])])
primary_schools_raw = np.array([item1 for item1 in primary_schools_raw if all(not np.array_equal(item1[:-1], item2) for item2 in matching_schools)])
middle_schools_raw = np.array([item1 for item1 in middle_schools_raw if all(not np.array_equal(item1[:-1], item2) for item2 in matching_schools)])
# Progress Bar
widgets = ['Veriler Alınıyor: ', AnimatedMarker()]
bar = ProgressBar(widgets=widgets, maxval=len(primary_schools_raw) + len(middle_schools_raw) + 1).start()

# Scrape Individual School Pages
book_student_records = []
bar.update(1)

i=2
schools_list = []
for curr_school in primary_schools_raw:
    
    about_url = curr_school[3]

    try:
        page = requests.get(about_url, verify=False)
    except:
        continue

    soup = BeautifulSoup(page.text, "html.parser")  # should be "html.parser"

    try:
        book_number = int(soup.find("i", class_="fa fa-book").parent.text.split(':')[1].strip())
    except:
        book_number = 0
    
    try:
        student_number = int(soup.find("i", class_="fa fa-child").parent.text.split(':')[1].strip())
    except:
        student_number = 0
    
    if book_number == 0:
        student_book_ratio = 999999
    else:
        student_book_ratio = student_number / book_number
    
    schools_list.append((*curr_school[:3], "İlkokul", book_number, student_number, student_book_ratio))

    bar.update(i)
    i = i + 1

for curr_school in middle_schools_raw:
    
    about_url = curr_school[3]

    try:
        page = requests.get(about_url, verify=False)
    except:
        continue

    soup = BeautifulSoup(page.text, "html.parser")  # should be "html.parser"

    try:
        book_number = int(soup.find("i", class_="fa fa-book").parent.text.split(':')[1].strip())
    except:
        book_number = 0
    
    try:
        student_number = int(soup.find("i", class_="fa fa-child").parent.text.split(':')[1].strip())
    except:
        student_number = 0
    
    if book_number == 0:
        student_book_ratio = 999999
    else:
        student_book_ratio = student_number / book_number
    
    schools_list.append((*curr_school[:3], "Ortaokul", book_number, student_number, student_book_ratio))

    bar.update(i)
    i = i + 1

schools_list = sorted(schools_list, key=lambda x: x[-1])
schools_list.reverse()

current_date = date.today()

# excel file creator
workbook = xlsxwriter.Workbook('excels/' + schools_list[0][0] + '-' + str(current_date) + '.xlsx')
worksheet = workbook.add_worksheet()

# inserting school data to excel file

worksheet.write("A1", "Şehir")
worksheet.write("B1", "İlçe")
worksheet.write("C1", "Okul İsmi")
worksheet.write("D1", "Okul Türü")
worksheet.write("E1", "Kitap Sayısı")
worksheet.write("F1", "Öğrenci Sayısı")
worksheet.write("G1", "Öğrenci/Kitap Oranı")

row = 2
col = 2
for school in schools_list:
    worksheet.write("A" + str(row), school[0])
    worksheet.write("B" + str(row), school[1])
    worksheet.write("C" + str(row), school[2])
    worksheet.write("D" + str(row), school[3])
    worksheet.write("E" + str(row), school[4])
    worksheet.write("F" + str(row), school[5])
    worksheet.write("G" + str(row), school[6])

    row = row + 1
    col = col + 1

workbook.close()
print("Ended Succesfully!")