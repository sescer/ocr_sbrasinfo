import requests
from bs4 import BeautifulSoup
import os
import logging
import fitz
import pytesseract as tess  
from PIL import Image  
from pdf2image import convert_from_path  
import re
from multiprocessing import Pool
import subprocess
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import re
from collections import defaultdict

logging.basicConfig(level=logging.INFO)


IMAGES_DIR = "images"
TEXT_DIR = "texts"

def convert_pdf_to_text(file_name):   
    pages = []
    images = convert_from_path(file_name)  
    for i, image in enumerate(images):
        try:
            os.makedirs(IMAGES_DIR, exist_ok=True)
            filename = f"{IMAGES_DIR}/page_" + str(i) + "_" + os.path.basename(file_name) + ".jpeg"  
            image.save(filename, "JPEG")  
            text = tess.image_to_string(Image.open(filename),lang="rus")
            pages.append(text)  

        except Exception as e:
            logging.error(str(e))
    os.makedirs(TEXT_DIR, exist_ok=True)
    output_file_name = TEXT_DIR + "/" + os.path.basename(file_name) + ".txt"
    out_text = "\n".join(pages)
    with open(output_file_name, "w") as f:
        f.write(out_text)  
    return out_text


def remove_digits_from_end(s):
    return re.sub(r'\d+$', '', s)

def get_next_page_url(url, pagenum):
    while True:
        try:
            response = requests.get(remove_digits_from_end(url) + str(pagenum), verify=False)
            if response.status_code != 200:
                logging.info(response.status_code)
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            next_page = soup.find('li', class_='pager__item--next')
            if next_page:
                next_page_link = next_page.find('a', rel='next')
                if next_page_link:
                    return True, remove_digits_from_end(url) + str(pagenum+1)
            return None, None
        except Exception as e:
            logging.warning(e)



def get_pdf_links(url):
    while True:
        try:
            response = requests.get(url, verify=False)
            if response.status_code != 200:
                logging.info(response.status_code)
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            pdf_links = soup.find_all('a', href=True)
            return pdf_links
        except Exception as e:
            logging.warning(e)

def download_pdf(year, base_url):
        pagenum = 0
        url = f"{base_url}?year={year}&page={pagenum}"
        pdf_links = get_pdf_links(url)
        pdf_folder = f"pdfs/{year}"
        os.makedirs(pdf_folder, exist_ok=True)
        while True:
            for link in pdf_links:
                try:
                    href = link['href']
                    if href.endswith('.pdf'):
                        pdf_response = requests.get(f"https://www.sbras.info{href}", verify=False)
                        pdf_path = os.path.join(pdf_folder, href.split('/')[-1])
                        with open(pdf_path, 'wb') as file:
                            file.write(pdf_response.content)
                        logging.info(f'Downloaded {href}')
                except Exception as identifier:
                    logging.error(identifier)
            flag, url = get_next_page_url(url, pagenum)
            if flag is None:
                break
            pdf_links = get_pdf_links(url)
            pagenum += 1

def search_keywords_in_text(text, keywords):
    found_keywords = []
    for keyword in keywords:
        if keyword in text:
            found_keywords.append(keyword)
    return found_keywords


def append_results_to_file(found_keywords, filename):
    with open('res_new.txt', "a") as file:
        file.write(f"{filename}: {found_keywords} \n\n")


base_url = "https://www.sbras.info/printed/archive"
keywords = [
    "технолог",    # технологии
    "сельское хозяйство",
    "сельск",      # сельское хозяйство
    "хозяйств",     # хозяйство
    "исследовани",  # исследования
    "инноваци",     # инновации
    "разработк",    # разработки
    "агротехник",   # агротехника
    "урожайност",   # урожайность
    "экологи",      # экология
    "биотехнологи", # биотехнологии
    "удобрени",     # удобрения
    "механизаци",   # механизация
    "сельское хозяйство",
    "агробиотехнология",
    "земледелие",
    "животноводство",
    "сельские технологии",
    "скрещивание",
]
OCR_DIR = 'ocr'

def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def convert_pdf_to_text(file_name):
    processed_pdf = file_name.replace('.pdf', '_ocr.pdf')
    dir_path = os.path.dirname(file_name)
    os.makedirs(os.path.join(dir_path, OCR_DIR), exist_ok=True)
    subprocess.run(['ocrmypdf',"-l", "rus", '--jobs', '4', file_name, processed_pdf])

    text = extract_text_from_pdf(processed_pdf)
    return text

def process_year(year):
    download_pdf(year, base_url)
    pdf_folder = f"pdfs/{year}"
    os.makedirs(pdf_folder, exist_ok=True)
    for pdf_file in os.listdir(pdf_folder):
        try:
            pdf_path = os.path.join(pdf_folder, pdf_file)
            text= convert_pdf_to_text(pdf_path)
            # text = extract_text_from_pdf(pdf_path)
            found_keywords = search_keywords_in_text(text, keywords)
            if found_keywords:
                logging.info(f"Results: {found_keywords}")
                append_results_to_file(found_keywords, os.path.basename(pdf_path))
        except Exception as e:
            logging.error(e)

def parse_data_from_text(file_content):
    """ Parse the data from the given text content. """
    pattern = re.compile(r'(\d{4})_(\d+)\.pdf: \[([^\]]+)\]')
    data = defaultdict(lambda: defaultdict(int))

    for match in re.finditer(pattern, file_content):
        year, _, keywords_str = match.groups()
        keywords = keywords_str.split(', ')
        for keyword in keywords:
            keyword = keyword.strip("'").strip()
            data[year][keyword] += 1

    return data

def plot_keyword_frequency_by_year(data, output_filename):
    """ Plot the keyword frequency by year and save to a file. """
    df = pd.DataFrame(data).fillna(0)
    df = df[sorted(df.columns)].T
    df.to_csv('res.csv')
    plt.figure(figsize=(12, 8))
    sns.heatmap(df, annot=True, cmap="viridis", fmt="g")
    plt.title("Частота ключевых слов по годам")
    plt.ylabel("Годы")
    plt.xlabel("Ключевые слова")
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_filename)

if __name__ == "__main__":
    start_year = 2009
    end_year = 1960
    years = range(start_year, end_year, -1)
    with Pool() as process:
        s = process.map(process_year, years)
    with open('res.txt', 'r', encoding='utf-8') as file:
        file_content = file.read()
    parsed_data = parse_data_from_text(file_content)
    output_file_name = "keyword_frequency_chart.png"
    plot_keyword_frequency_by_year(parsed_data, output_file_name)


