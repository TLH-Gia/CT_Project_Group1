import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def get_recipe_links(driver, main_url):
    """
    Visits the main URL and scrapes all individual recipe links.
    """
    print(f"Scraping main page for recipe links: {main_url}")
    driver.get(main_url)
    # Wait for the page to load
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    links = set()  # Use a set to avoid duplicate links
    # Find all <a> tags with the attribute data-type="post"
    for a_tag in soup.find_all('a', attrs={'data-type': 'post'}):
        href = a_tag.get('href')
        if href and href.startswith('https://savourthepho.com/'):
            links.add(href)

    print(f"Found {len(links)} unique recipe links.")
    return list(links)


def scrape_recipe_details(driver, url):
    """
    Visits a single recipe URL and scrapes its name, description,
    and ingredients.
    """
    driver.get(url)
    time.sleep(2)  # Be polite to the server

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    recipe_data = {
        'name': 'Not Found',
        'description': 'Not Found',
        'ingredients': 'Not Found',
        'url': url
    }

    try:
        # 1. Scrape the Name
        # <h2 class="wprm-recipe-name ...">...</h2>
        name_tag = soup.find('h2', class_='wprm-recipe-name')
        if name_tag:
            recipe_data['name'] = name_tag.get_text(strip=True)

        # 2. Scrape the Description
        # NOTE: Your example description HTML is from the main post.
        # This selector targets the structured 'summary' field
        # from the recipe card plugin, which is more reliable.
        desc_tag = soup.find('div', class_='wprm-recipe-summary')
        if desc_tag:
            recipe_data['description'] = desc_tag.get_text(strip=True)

        # 3. Scrape the Ingredients
        # <li class="wprm-recipe-ingredient">...</li>
        ingredient_tags = soup.find_all('li', class_='wprm-recipe-ingredient')
        if ingredient_tags:
            ingredients_list = []
            for li in ingredient_tags:
                # Combine all parts (amount, unit, name, notes)
                full_ingredient = li.get_text(separator=' ', strip=True)
                ingredients_list.append(full_ingredient)

            # Join all ingredients with a newline for a clean list
            recipe_data['ingredients'] = '\n'.join(ingredients_list)

    except Exception as e:
        print(f"Error scraping {url}: {e}")

    return recipe_data


# --- Main script execution ---
if __name__ == "__main__":

    # Setup Selenium WebDriver
    # This automatically downloads and manages the correct chromedriver
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in background (optional)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=service, options=options)

    main_url = "https://savourthepho.com/authentic-vietnamese-recipes/"
    all_recipes_data = []

    try:
        # Phase 1: Get all links from the main page
        recipe_urls = get_recipe_links(driver, main_url)

        # Phase 2: Scrape each individual recipe page
        for i, url in enumerate(recipe_urls):
            print(f"Scraping {i + 1}/{len(recipe_urls)}: {url}")
            data = scrape_recipe_details(driver, url)
            all_recipes_data.append(data)
            print(f"  -> Done: {data['name']}")

    finally:
        # Ensure the browser closes even if an error occurs
        driver.quit()

    # Phase 3: Create Pandas DataFrame
    print("\nScraping complete. Creating DataFrame...")
    df = pd.DataFrame(all_recipes_data)

    # Display the results
    print(df.head())

    # Optional: Save to a CSV file
    df.to_csv('savourthepho_recipes.csv', index=False)
    print("Data saved to savourthepho_recipes.csv")