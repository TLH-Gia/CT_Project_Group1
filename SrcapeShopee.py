import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service  # <-- Import Service
from webdriver_manager.chrome import ChromeDriverManager  # <-- Import this
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
city_url = "https://shopeefood.vn/ho-chi-minh/food/deals"
BASE_URL = "https://shopeefood.vn"
PAGES_TO_SCRAPE = 10  # <-- Set how many pages you want to click through
output_csv = "ho_chi_minh_shopeefood_details.csv"


# ==============================================================================
# --- FUNCTION TO SCRAPE A SINGLE RESTAURANT'S DETAIL PAGE ---
# ==============================================================================
def scrape_restaurant_details(soup, url):
    # Initialize all result variables to a safe default
    name = "Unknown Name"
    address = ""
    rating = None
    menu_dishes = []  # Initialize a list to hold the dish names

    try:
        # 1. Scrape Name and Address
        name_elem = soup.select_one('h1.name-restaurant')
        name = name_elem.get_text(strip=True) if name_elem else name

        address_elem = soup.select_one('div.address-restaurant')
        address = address_elem.get_text(strip=True) if address_elem else address

        # 2. Scrape Rating
        rating_container = soup.select_one('div.rating')
        if rating_container:
            stars_div = rating_container.select_one('div.stars')

            if stars_div:
                full_stars = len(stars_div.select('span.full'))
                half_stars = len(stars_div.select('span.half'))
                rating = full_stars + (half_stars * 0.5)

        # 3. Scrape Menu Dishes (New Addition)
        # Use the specific selector for the dish name: h2.item-restaurant-name
        DISH_SELECTOR = 'h2.item-restaurant-name'

        dish_elements = soup.select(DISH_SELECTOR)

        # Loop through the first 8 elements only
        for i, dish_elem in enumerate(dish_elements):
            if i >= 7:  # Stop after 8 dishes
                break

            dish_name = dish_elem.get_text(strip=True)
            if dish_name:
                menu_dishes.append(dish_name)

        # 4. Return the results
        return {
            "restaurant_name": name,
            "address": address,
            "rating": rating,
            "page_url": url,
            # Join the list of dishes into a single string for the CSV column
            "top_7_dishes": " | ".join(menu_dishes)
        }

    except Exception as e:
        print(f"  > Error parsing detail page {url}: {e}")
        return None

# ==============================================================================
# --- MAIN SCRIPT ---
# ==============================================================================

# --- SETUP SELENIUM (Using Webdriver-Manager) ---
options = Options()
# options.add_argument("--headless")
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# --- LOGIN MANUALLY ---
driver.get("https://shopeefood.vn/")
print("Please log in in the opened browser, then press Enter here.")
input("Press Enter after login is complete...")

# ==============================================================================
# --- PART 1: GET ALL RESTAURANT LINKS (WITH PAGINATION) ---
# ==============================================================================

# --- MODIFIED PART 1: GET ALL RESTAURANT LINKS (WITH PAGINATION) ---

print("\n--- Starting to scrape links using PAGINATION ---")
driver.get(city_url)
print("Waiting for list page (Page 1) to load...")
time.sleep(5)  # Initial wait for page 1 (can be replaced by a smart wait if needed)

restaurant_urls = set()  # Use a set to avoid duplicate links
LINK_SELECTOR = 'a.item-content'  # The robust selector for restaurant links

for page_num in range(PAGES_TO_SCRAPE):
    current_page = page_num + 1
    next_page = page_num + 2
    print(f"\nScraping Page {current_page}/{PAGES_TO_SCRAPE}...")

    # 1. Parse the *current* page's HTML
    try:
        # Wait for the restaurant link elements to be visible
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, LINK_SELECTOR))
        )
        print("Page content loaded.")
    except Exception as e:
        print("Page timed out or no restaurants found. Skipping page.")
        continue  # Skip to the next click

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # 2. Find all links on *this* page
    link_tags = soup.select(LINK_SELECTOR)
    page_links_found = 0
    for tag in link_tags:
        # Check if tag exists and has the 'href' attribute
        if tag and tag.has_attr('href'):
            relative_url = tag['href']

            # --- CRITICAL FIX: Ensure proper URL combination ---
            # If the href is relative (starts with '/'), prepend BASE_URL
            if relative_url.startswith('/'):
                full_url = BASE_URL + relative_url
            else:
                full_url = relative_url  # Use as is if it's already a full URL

            if full_url not in restaurant_urls:
                restaurant_urls.add(full_url)
                page_links_found += 1

    print(f"Found {page_links_found} new links on this page. Total unique links: {len(restaurant_urls)}")

    # 3. Find and click the "Next Page" button
    if page_num == PAGES_TO_SCRAPE - 1:
        print("Reached target page limit. Stopping pagination.")
        break

    # --- PAGINATION LOGIC ---
    try:
        # Scroll to the bottom to ensure the pagination footer is visible
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        # The link for the next page number (e.g., "2" when on page 1)
        NEXT_PAGE_XPATH = f'//a[text()="{next_page}"]'

        # Wait for the next page number link to be clickable
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, NEXT_PAGE_XPATH))
        )

        driver.execute_script("arguments[0].click();", next_button)
        print(f"Clicked 'Page {next_page}'. Waiting for new content...")
        time.sleep(5)

    except Exception as e:
        print(f"Could not find or click 'Page {next_page}' button. Trying the icon...")

        # --- Fallback for the Icon-based "Next" Button ---
        try:
            ICON_SELECTOR = 'span.icon.icon-paging-next'
            next_icon = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ICON_SELECTOR))
            )
            next_button = next_icon.find_element(By.XPATH, './..')  # Get parent <a> tag

            if "disabled" in next_button.get_attribute("class"):
                print("Next page icon button is disabled. Reached the end.")
                break

            driver.execute_script("arguments[0].click();", next_button)
            print("Clicked 'Next Page' icon fallback.")
            time.sleep(5)

        except Exception as e_fallback:
            print(f"Could not find or click icon button either. Stopping pagination.")
            print(f"Final Pagination Error: {e_fallback}")
            break
        # --- End of Fallback ---

print(f"\nFinished collecting links. Total found: {len(restaurant_urls)}")

# ==============================================================================
# --- PART 2: LOOP THROUGH LINKS AND SCRAPE DETAILS ---
# ==============================================================================

all_restaurant_data = []
print("\n--- Starting to scrape detail pages ---")

for i, url in enumerate(list(restaurant_urls)):
    print(f"Scraping {i + 1}/{len(restaurant_urls)}: {url}")
    try:
        driver.get(url)
        time.sleep(3)  # Wait for detail page
        detail_soup = BeautifulSoup(driver.page_source, "html.parser")
        data = scrape_restaurant_details(detail_soup, url)
        if data:
            all_restaurant_data.append(data)
    except Exception as e:
        print(f"  > FAILED to load page {url}: {e}")
    time.sleep(2)  # Be polite

# ==============================================================================
# --- PART 3: CLEANUP & EXPORT ---
# ==============================================================================
driver.quit()

print(f"\n--- SUCCESS ---")
print(f"Scraped details for {len(all_restaurant_data)} restaurants.")

if all_restaurant_data:
    df = pd.DataFrame(all_restaurant_data)
    df.to_csv(output_csv, index=False)
    print(f"Saved data to {output_csv}")
    print("\n--- Data Preview ---")
    print(df.head())
else:
    print("No data was scraped. Check selectors and page load times.")