import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pandas as pd

import string
import re
import os

# Create CSV file to save data to
CSVfile = 'drug_reviews.csv'
with open(CSVfile, 'w') as f:
    f.write('Drug,Rating,Reason,Side Effects,Comments,Sex,Age,Duration/Dosage,Date Added\n')

# Create User Agent
user_agent = UserAgent()
headers = {'User-Agent': user_agent.random}

# Find url to all the drugs review
print('--- Searching drugs by letters ----')
url_drugs = list()
for letter in string.ascii_uppercase:
    
    url = f'https://www.askapatient.com/drugalpha.asp?letter={letter}'
    webpage = requests.get(url, headers=headers).text
    soup = BeautifulSoup(webpage, 'html.parser')
    entry = soup.find('table', {'class': 'datatable searchresults'})
    table = entry.find_all('a')

    for drug in table:
        url_drugs.append(f"https://www.askapatient.com/{drug['href']}")
    
    print(f'Found {len(table)} drugs for the letter {letter}')

print()
print(f'Total number of drugs found: {len(url_drugs)}')
print()

# Extract data
print('--- Extracting Data ---')
drug_reviews = []
drug_added_count = 0

for url in url_drugs:
    
    # Get no of pages
    webpage = requests.get(url, headers=headers).text
    soup = BeautifulSoup(webpage, 'html.parser')
    entry = soup.find('div', {'id': 'searchResultsDetailHeader'})
    pages = entry.find_all('a')
    total_pages = len([int(page.text) for page in pages if page.text.isnumeric()]) + 1
    
    # Skip drugs with <= 40 reviews (2 page = 40 data rows)
    if total_pages <= 2: continue

    # Skip too many reviews for the same drug (10 page = 200 data rows )
    if total_pages > 10: total_pages = 10
    
    # Look into each page for that drug
    data_count = 0
    for page_no in range(1, total_pages+1):
        
        # Fetch the webpage content
        url = f"{url}&page={page_no}"
        webpage = requests.get(url, headers=headers).text
        soup = BeautifulSoup(webpage, 'html.parser')
        drug_name = soup.find('h1', {'class': 'floatLeft'}).text[:-8]
        table = soup.find('table', {'class': 'ratingsTable'})
        rows = table.find_all('td')[16:]
        rows = [rows[n:n+8] for n in range(0, len(rows), 8)]

        # Parse and add the data to dataframe
        for row in rows:
            
            try:
                data_entry = {
                    'Drug': drug_name,
                    'Rating': re.sub('\W+',' ',row[0].text).strip(),
                    'Reason': re.sub('\W+',' ',row[1].text).strip(),
                    'Side Effects': re.sub('\W+',' ',row[2].text).strip(),
                    'Comments': re.sub('\W+',' ',row[3].text).strip(),
                    'Sex': re.sub('\W+',' ',row[4].text).strip(),
                    'Age': float(row[5].text) if row[5].text else None,
                    'Duration/Dosage': re.sub('\W+',' ',row[6].text).strip(),
                    'Date Added': re.sub('\W+',' ',row[7].text).strip(),
                }
            
            except:
                log = f'Cannot add data for the entry: {row}'
                print("\033[91m {}\033[00m".format(log))
                continue

            drug_reviews.append(data_entry)
            data_count += 1
    
    print(f'Added {data_count} rows for {drug_name}.')
    drug_added_count += 1

    if drug_added_count == 10:
        
        print('--- Saving progress ---')
        df = pd.DataFrame(drug_reviews)
        df.to_csv(CSVfile, mode='a', header=False, index=False)
        drug_added_count = 0
        drug_reviews = list()

print('--- Finishing up ---')
df = pd.DataFrame(drug_reviews)
df.to_csv(CSVfile, mode='a', header=False, index=False,)

print()
print('--- Operation Complete ---')
print()