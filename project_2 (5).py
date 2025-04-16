import requests
from bs4 import BeautifulSoup
import re
import os
import csv
import unittest

# IMPORTANT NOTE:
"""
If you are getting "encoding errors" while trying to open, read, or write from a file, add the following argument to any of your open() functions:
    encoding="utf-8-sig"

An example of that within the function would be:
    open("filename", "r", encoding="utf-8-sig")

There are a few special characters present from Airbnb that aren't defined in standard UTF-8 (which is what Python runs by default). This is beyond the scope of what you have learned so far in this class, so we have provided this for you just in case it happens to you. Good luck!
"""

def load_listing_results(html_file):
    listings = []

    with open(html_file, "r", encoding="utf-8-sig") as file:
        soup = BeautifulSoup(file, 'html.parser')

        # Each card is a parent with both title and listing link
        cards = soup.find_all('div', class_='c4mnd7m dir dir-ltr')

        for card in cards:
            title_tag = card.find('div', class_='t1jojoys')
            link_tag = card.find('a', href=True)

            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                href = link_tag['href']

                match = re.search(r'/rooms/(\d+)|/plus/(\d+)', href)
                if match:
                    listing_id = match.group(1) if match.group(1) else match.group(2)
                    listings.append((title, listing_id))

    return listings

def get_listing_details(listing_id):
    """
    INPUT: A string containing the listing id
    RETURN: A tuple
    """  
    listing_file = f"/Users/kelsiebackus/Desktop/SI206/si206-w25-proj2-kelsiebackuss/html_files/listing_{listing_id}.html"

    with open(listing_file, 'r', encoding='utf-8-sig') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # 1. POLICY NUMBER
    policy_number = "N/A"
    for li in soup.find_all('li'):
        if li.find('span') and 'Policy number' in li.text:
            policy_number = li.find('span').text.strip()
            break
    # 2. HOST LEVEL
    host_level = "regular"
    superhost_tag = soup.find('span', class_=re.compile(".*", re.I), string=re.compile("Superhost", re.I))
    if superhost_tag:
        host_level = "Superhost"

    # 3. HOST NAME
    host_name = "missing"
    name_tag = soup.find('div', class_='_cv5qq4')
    if name_tag:
        hosted_by_partition = name_tag.text.partition("hosted by")
        host_name = hosted_by_partition[-1].strip()

    # 4. PLACE TYPE
    place_type = "Unknown"
    if name_tag:
        description = name_tag.text.lower()
        if "entire" in description:
            place_type = "Entire Room"
        elif "private" in description:
            place_type = "Private Room"
        elif "shared" in description:
            place_type = "Shared Room"

    # 5. NUMBER OF REVIEWS
    num_reviews = 0

    for tag in soup.find_all('span', class_='a8jt5op'):
        text = tag.text.strip()
        if text.isdigit():
            num_reviews = int(text)
            break

    if num_reviews == 0:
        for tag in soup.find_all('span'):
            match = re.search(r'from (\d+) reviews', tag.text)
            if match:
                num_reviews = int(match.group(1))
                break

    # 6. NIGHTLY RATE
    nightly_rate = 0
    price_tag = soup.find('span', class_='_tyxjp1')
    if price_tag:
        price_str = price_tag.text.strip().replace('$', '').replace(',', '')
        try:
            nightly_rate = int(price_str)
        except:
            nightly_rate = 0

    return (policy_number, host_level, host_name, place_type, num_reviews, nightly_rate)
def create_listing_database(html_file): 
    """
    INPUT: A string containing the path of the html file
    RETURN: A list of tuples
    """
    listing_results = load_listing_results(html_file)
    full_listing_data = []

    for title, listing_id in listing_results:
        listing_details = get_listing_details(listing_id)
        full_listing_data.append((title, listing_id) + listing_details)
    
    return full_listing_data

def output_csv(data, filename): 
    """
    INPUT: A list of tuples and a string containing the filename
    RETURN: None
    """
    sorted_data = sorted(data, key=lambda x: x[6], reverse=True)
    with open(filename, mode='w', newline='', encoding='utf-8') as file:

        writer = csv.writer(file)

        writer.writerow(["Listing Title", "Listing ID", "Policy Number", "Host Level", "Host Name(s)", "Place Type", "Review Number", "Nightly Rate"])

        for row in sorted_data:
            writer.writerow(row)

def validate_policy_numbers(data):
    """
    INPUT: A list of tuples
    RETURN: A list of tuples
    """
    invalid_listings = []
    policy_pattern = re.compile(r'^STR-\d{7}$')

    for listing in data:
        title = listing[0]
        policy_number = listing[2]
        if not policy_pattern.match(policy_number):
            invalid_listings.append((title, policy_number, "Invalid policy number"))

    return invalid_listings

# EXTRA CREDIT 
def google_scholar_searcher(query): 
    """
    INPUT: query (str)
    Return: a list of titles on the first page (list)
    * see PDF instructions for more details
    """
    base_url = "https://scholar.google.com/scholar"
    params = {'q': query}

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        titles = []
        for item in soup.find_all('h3', class_='gs_rt'):
            title = item.get_text()
            titles.append(title)

        return titles
    else:
        print("Failed to retrieve results")
        return []

# TODO: Don't forget to write your test cases! 
class TestCases(unittest.TestCase):
    def setUp(self):
        self.listings = load_listing_results('/Users/kelsiebackus/Desktop/SI206/si206-w25-proj2-kelsiebackuss/html_files/search_results.html')

    def test_load_listing_results(self):
        # check that the number of listings extracted is correct (18 listings)
        self.assertEqual(len(self.listings), 18)

        # check that the variable you saved after calling the function is a list
        self.assertEqual(type(self.listings), list)

        # check that each item in the list is a tuple
        self.assertTrue(all(type(item) == tuple for item in self.listings))
    
        # check that the first title and listing id tuple is correct (open the search results html and find it)
        self.assertEqual(self.listings[0], ('Loft in Mission District', '1944564'))

        # check that the last title and listing id tuple is correct (open the search results html and find it)
        self.assertEqual(self.listings[-1], ('Guest suite in Mission District', '467507'))

# Run the tests
    def test_get_listing_details(self):
        html_list = ["467507",
                     "1550913",
                     "1944564",
                     "4614763",
                     "6092596"]
        
        # call get_listing_details for i in html_list:
        listing_information = [get_listing_details(id) for id in html_list]

        # check that the number of listing information is correct
        self.assertEqual(len(listing_information), 5)
        for info in listing_information:
            # check that each item in the list is a tuple
            self.assertEqual(type(info), tuple)
            # check that each tuple has 6 elements
            self.assertEqual(len(info), 6)
            # check that the first four elements in the tuple are strings
            self.assertEqual(type(info[0]), str)
            self.assertEqual(type(info[1]), str)
            self.assertEqual(type(info[2]), str)
            self.assertEqual(type(info[3]), str)
            # check that the rest two elements in the tuple are integers
            self.assertEqual(type(info[4]), int)
            self.assertEqual(type(info[5]), int)

        # check that the first listing in the html_list has the correct policy number
        self.assertEqual(listing_information[0][0], "STR-0005349")

        # check that the last listing in the html_list has the correct place type
        self.assertEqual(listing_information[-1][3], 'Entire Room')

        # check that the third listing has the correct cost
        self.assertEqual(listing_information[2][5], 181)

    def test_create_listing_database(self):
        detailed_data = create_listing_database('/Users/kelsiebackus/Desktop/SI206/si206-w25-proj2-kelsiebackuss/html_files/search_results.html')

        # check that we have the right number of listings (18)
        self.assertEqual(len(detailed_data), 18)

        for item in detailed_data:
            # assert each item in the list of listings is a tuple
            self.assertEqual(type(item), tuple)
            # check that each tuple has a length of 8
            self.assertTrue(len(item), 8)

        # check that the first tuple is made up of the following:
        # ('Loft in Mission District', '1944564', '2022-004088STR', 'Superhost', 'Brian', 'Entire Room', 422, 181)
        self.assertEqual(detailed_data[0], ('Loft in Mission District', '1944564', '2022-004088STR', 'Superhost', 'Brian', 'Entire Room', 422, 181))

        # check that the last tuple is made up of the following:
        # ('Guest suite in Mission District', '467507', 'STR-0005349', 'Superhost', 'Jennifer', 'Entire Room', 324, 165)
        self.assertEqual(detailed_data[-1], ('Guest suite in Mission District', '467507', 'STR-0005349', 'Superhost', 'Jennifer', 'Entire Room', 324, 165))

    def test_output_csv(self):
        # call create_listing_database on "html_files/search_results.html" and save the result to a variable
        detailed_data = create_listing_database('/Users/kelsiebackus/Desktop/SI206/si206-w25-proj2-kelsiebackuss/html_files/search_results.html')

        # call output_csv() on the variable you saved
        output_csv(detailed_data, "test.csv")

        # read in the csv that you wrote
        with open("test.csv", "r", encoding="utf-8") as file:
            csv_reader = csv.reader(file)
            csv_lines = list(csv_reader)

        # check that there are 19 lines in the csv
        self.assertEqual(len(csv_lines), 19)

        # check that the header row is correct
        self.assertEqual(csv_lines[0], ['Listing Title', 'Listing ID', 'Policy Number', 'Host Level', 'Host Name(s)', 'Place Type', 'Review Number', 'Nightly Rate'])

        # check that the next row is the correct information about Guest suite in San Francisco
        self.assertEqual(csv_lines[1], ['Guest suite in San Francisco','6092596','STR-0000337','Superhost','Marc','Entire Room','713','164'])

        # check that the row after the above row is the correct infomration about Private room in Mission District
        self.assertEqual(csv_lines[2], ['Private room in Mission District','16204265','1081184﻿','Superhost','Koncha','Private Room','520','127'])

    def test_validate_policy_numbers(self):
        # call create_listing_database on "html_files/search_results.html"
        # and save the result to a variable
        detailed_data = create_listing_database('/Users/kelsiebackus/Desktop/SI206/si206-w25-proj2-kelsiebackuss/html_files/search_results.html')

        # call validate_policy_numbers on the variable created above and save the result as a variable
        invalid_listings = validate_policy_numbers(detailed_data)

        # check that the return value is a list
        self.assertEqual(type(invalid_listings), list)

        # check that the elements in the list are tuples
        self.assertTrue(all(isinstance(listing, tuple) for listing in invalid_listings))

        # and that there are exactly three element in each tuple
        self.assertTrue(all(len(listing) == 3 for listing in invalid_listings))

def main (): 
    detailed_data = create_listing_database('/Users/kelsiebackus/Desktop/SI206/si206-w25-proj2-kelsiebackuss/html_files/search_results.html')
    output_csv(detailed_data, "airbnb_dataset.csv")

if __name__ == '__main__':
    main()
    unittest.main(verbosity=2)

    # google_scholar_searcher test case
    query = "airbnb"
    titles = google_scholar_searcher(query)
    for title in titles:
        print(title)

