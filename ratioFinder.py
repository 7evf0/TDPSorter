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
matching_schools = np.array([[*item1, item2[3]] for item1 in primary_schools_raw for item2 in middle_schools_raw if np.array_equal(item1[:-1], item2[:-1])])

# Progress Bar
widgets = ['Veriler Alınıyor: ', AnimatedMarker()]
bar = ProgressBar(widgets=widgets, maxval=len(matching_schools) + 1).start()

# Scrape Individual School Pages
book_student_records = []
bar.update(1)

i=2
schools_list = []
for curr_school in matching_schools:
    
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
    
    if total_book == 0:
        student_book_ratio = 999999
    else:
        student_book_ratio = total_student / total_book
    
    schools_list.append((*curr_school[:3], book_number_pre, student_number_pre, book_number_mid, student_number_mid, total_book, total_student, student_book_ratio))

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
worksheet.write("D1", "İlkokul Kitap Sayısı")
worksheet.write("E1", "İlkokul Öğrenci Sayısı")
worksheet.write("F1", "Ortaokul Kitap Sayısı")
worksheet.write("G1", "Ortaokul Öğrenci Sayısı")
worksheet.write("H1", "Bütün Kitap Sayısı")
worksheet.write("I1", "Bütün Öğrenci Sayısı")
worksheet.write("J1", "Öğrenci/Kitap Oranı")

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
    worksheet.write("H" + str(row), school[7])
    worksheet.write("I" + str(row), school[8])
    worksheet.write("J" + str(row), school[9])

    row = row + 1
    col = col + 1

workbook.close()
print("Ended Succesfully!")