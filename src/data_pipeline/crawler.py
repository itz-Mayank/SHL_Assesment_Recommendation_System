import requests
from bs4 import BeautifulSoup
import json
import os
import time

# --- Configuration ---
CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"
OUTPUT_DIR = "data/crawled"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "shl_assessments.json")

# --- Helper Functions ---

def get_soup(url):
    """Fetches a static URL and returns a BeautifulSoup object."""
    print(f"  Fetching: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def make_absolute_url(url):
    """Ensures a URL is absolute."""
    if url.startswith('/'):
        return f"https://www.shl.com{url}"
    return url

def get_test_type_map(soup):
    """Builds a dictionary to map 'K' to 'Knowledge & Skills'."""
    key_map = {}
    try:
        tooltip = soup.find('div', id='productCatalogueTooltip')
        list_items = tooltip.find_all('li', class_='custom__tooltip-item')
        
        for item in list_items:
            key_tag = item.find('span', class_='product-catalogue__key')
            key = key_tag.text.strip()
            value = key_tag.next_sibling.strip()
            key_map[key] = value
            
    except Exception as e:
        print(f"  Warning: Could not build test type map. Using keys only. Error: {e}")
        
    print(f"  Built test type map: {key_map}")
    return key_map

def scrape_assessment_details(assessment_url):
    """
    Scrapes the individual assessment page for detailed information.
    This is the final TODO for you to complete.
    """
    # print(f"    > Scraping details from: {assessment_url}") # Optional
    soup = get_soup(assessment_url)
    if not soup:
        return None

    details = {
        "description": "No description found.", # Default
        "adaptive_support": "No",
        "duration": None,
        "remote_support": "No"
    }

    try:
        # --- This selector is a strong guess, you can improve it ---
        desc_div = soup.find('div', class_='product-catalogue__details-content')
        if desc_div:
            p_tags = desc_div.find_all('p')
            full_desc = " ".join([p.text.strip() for p in p_tags if p.text.strip()])
            if full_desc:
                details['description'] = full_desc
        
        # --- TODO: Find selectors for duration, adaptive, etc. ---
        # The PDF requires 'duration', 'adaptive_support', and 'remote_support'.
        # You will need to "Inspect" the page to find these.
        
        # Example:
        # info_list = soup.find('ul', class_='product-info-list')
        # if info_list:
        #     list_items = info_list.find_all('li')
        #     for item in list_items:
        #         if "Duration:" in item.text:
        #             duration_str = item.text.split(":")[-1].strip().split(" ")[0]
        #             try: details['duration'] = int(duration_str)
        #             except ValueError: pass
        
        return details

    except Exception as e:
        print(f"    Error parsing details for {assessment_url}: {e}")
        return None

def parse_page_for_items(soup, test_type_map):
    """
    Parses a single catalog page (full or partial)
    and returns a list of items.
    
    This is the v17 "Simple Robust" logic
    """
    all_assessments = []
    
    # --- v17 SMART PARSER ---
    # Find all table wrappers on the page
    all_table_wrappers = soup.find_all('div', class_='custom__table-wrapper')
    
    individual_tests_wrapper = None
    
    # Find the *correct* wrapper: the one that has data-entity-id rows
    for wrapper in all_table_wrappers:
        if wrapper.find('tr', attrs={'data-entity-id': True}):
            individual_tests_wrapper = wrapper
            break # Found it
    
    if not individual_tests_wrapper:
        print("  FAILURE: Could not find a table wrapper with 'data-entity-id' rows.")
        return [] # Return empty list
    # --- END v17 SMART PARSER ---

    product_rows = individual_tests_wrapper.find_all('tr', attrs={'data-entity-id': True})
    print(f"  Found {len(product_rows)} product rows on this page.")

    if not product_rows:
        return [] # This is how we find the end of the list

    for row in product_rows:
        try:
            link_tag = row.find('a')
            if not link_tag: continue

            assessment_name = link_tag.text.strip()
            assessment_url = make_absolute_url(link_tag.get('href'))

            key_tags = row.find_all('span', class_='product-catalogue__key')
            test_types = [test_type_map.get(tag.text.strip(), tag.text.strip()) for tag in key_tags]
            
            assessment_data = {
                "name": assessment_name,
                "url": assessment_url,
                "test_type": test_types
            }
            all_assessments.append(assessment_data)
        except Exception as e:
            print(f"  Error parsing a product row: {e}")
            continue
            
    return all_assessments

# --- Main Execution ---
def main():
    print("Starting SHL Assessment Crawler (v17 - Simple Loop)...")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"Scraping catalog: {CATALOG_URL}")
    main_soup = get_soup(CATALOG_URL)
    
    if not main_soup:
        print("Could not fetch the main catalog. Exiting.")
        return
        
    # 1. Build the map of 'K' -> 'Knowledge & Skills'
    test_type_map = get_test_type_map(main_soup)
    
    all_assessment_items = []
    page_count = 1
    
    while True:
        # Generate the URL. start=0 for page 1, start=12 for page 2, etc.
        start_index = (page_count - 1) * 12
        
        if start_index == 0:
            page_url = CATALOG_URL
            print("\nScraping Page 1 (Main Page)...")
            current_page_soup = main_soup
        else:
            page_url = f"{CATALOG_URL}?start={start_index}&type=1"
            print(f"\nScraping Page {page_count} ({page_url.split('?')[1]})...")
            current_page_soup = get_soup(page_url)
        
        if not current_page_soup:
            print("  Failed to fetch page. Stopping.")
            break
            
        items_on_page = parse_page_for_items(current_page_soup, test_type_map)
        
        # If a page comes back empty, we've reached the end
        if not items_on_page:
            print("  No items found on this page. This is the last page.")
            break
            
        all_assessment_items.extend(items_on_page)
        page_count += 1
        
        if start_index > 0:
            time.sleep(0.5) # Be polite

    print(f"\n--- Found {len(all_assessment_items)} total assessments across all {page_count-1} pages. ---")

    # 4. Scrape details for each assessment
    final_data = []
    start_time = time.time()
    for i, item in enumerate(all_assessment_items):
        percent_done = (i+1) / len(all_assessment_items) * 100
        print(f"  Processing item {i+1}/{len(all_assessment_items)} ({percent_done:.1f}%) - {item['name']}", end='\r')
        
        details = scrape_assessment_details(item['url'])
        
        if details:
            complete_data = {**item, **details}
            final_data.append(complete_data)
        
        time.sleep(0.2) 

    end_time = time.time()
    print(f"\nFinished processing all details in {end_time - start_time:.2f} seconds.")

    # 5. Save data to JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(final_data, f, indent=2)

    print(f"\n--- Crawling Complete ---")
    print(f"Successfully scraped {len(final_data)} assessments.")
    print(f"Data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()