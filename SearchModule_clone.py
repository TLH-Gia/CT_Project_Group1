import os
import json
import csv
import pandas as pd
import requests
from requests.structures import CaseInsensitiveDict
from dotenv import load_dotenv

# Google Gemini Libraries (CORRECTED IMPORTS)
# 'types as glm' is no longer needed for Schema
import google.generativeai as genai
# We keep 'types' import if needed for other features, but rename it to avoid confusion
from google.generativeai import types

# Load environment variables from .env file
load_dotenv()

# --- GLOBAL VARIABLES ---
# Read API Keys from .env
GOOGLE_API = os.getenv("GOOGLE_API_KEY")
GEOAPIFY_API = os.getenv("GEOAPIFY_API_KEY")

# Desired number of results
Quantity = 5

# Configure Gemini
if GOOGLE_API:
    genai.configure(api_key=GOOGLE_API)
else:
    print("Error: GOOGLE_API_KEY not found. Please check the .env file.")
    exit()

# --- GEMINI NLP AND LOCATION PROCESSING FUNCTIONS ---

def geminiNLP(prompt):
    """Uses Gemini to extract Categories, Location, and map the Category."""
    try:
        with open("RestaurantFormat.txt", "r", encoding="utf-8") as f:
            cat_file = f.read()
    except FileNotFoundError:
        print("Error: 'RestaurantFormat.txt' file not found.")
        return None

    system_context = (
        "You are a category filter and mapper.\n"
        "Below is the complete list of standard categories:\n"
        f"{cat_file}\n"
        "Task: From the user's prompt, identify the Categories (food keywords) and Location (place name). "
        "Then map each Category to the standard list above and put it in the 'Mapped' field. "
        "Example: 'Korean food' -> 'korean'."
    )

    # --- THIS IS THE FIX ---
    # Replaced the broken glm.Schema object with a Python dictionary
    schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "Categories": {"type": "STRING", "description": "Food keywords/type from the user's prompt."},
                "Location": {"type": "STRING", "description": "Location extracted from the prompt."},
                "Mapped": {"type": "STRING", "description": "Category mapped to the standard list (e.g., 'catering', 'coffee', 'chinese')."},
            },
            "required": ["Categories", "Location", "Mapped"]
        }
    }
    # --- END OF FIX ---

    model = genai.GenerativeModel('gemini-2.5-flash')

    response = model.generate_content(
        [system_context, "User prompt: " + prompt],
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": schema  # Pass the dictionary here
        }
    )

    try:
        data = json.loads(response.text)
        return data
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: Response is not valid JSON. Details: {e}")
        print("Raw response:", response.text)
        return None
    except Exception as e:
        print(f"Error calling GeminiNLP: {e}")
        return None

def bboxForLocation(location="District 7, HCMC"):
    """Uses Nominatim to get the Bounding Box (BBox) for a location."""
    if not location:
        print("Error: Location is empty. Using default BBox for HCMC.")
        return "106.59,10.68,107.01,10.97"  # Default BBox for HCMC

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location,
        "polygon_geojson": 1,
        "format": "json"
    }
    headers = CaseInsensitiveDict()
    headers["User-Agent"] = "MyAppForRestaurantSearch/1.0 (https://your-website.com)"

    try:
        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        if data and "boundingbox" in data[0]:
            bbox_data = data[0]["boundingbox"]
            south = float(bbox_data[0])
            north = float(bbox_data[1])
            west = float(bbox_data[2])
            east = float(bbox_data[3])
            return f"{west},{south},{east},{north}"
        else:
            print(f"BBox not found for location: {location}. Using default BBox.")
            return "106.59,10.68,107.01,10.97"
    except requests.exceptions.RequestException as e:
        print(f"Error calling Nominatim API: {e}")
        return "106.59,10.68,107.01,10.97"


def restaurantForLocation(bbox, Categories="catering", keyword=None):
    """Uses Geoapify Places API to find restaurants within the BBox."""
    if not GEOAPIFY_API:
        print("Error: GEOAPIFY_API_KEY not found. Cannot search for restaurants.")
        return {"features": []}

    base_url = "https://api.geoapify.com/v2/places"
    params = {
        "apiKey": GEOAPIFY_API,
        "limit": 50,  # Get more than Quantity so Gemini can rank
        "filter": f"rect:{bbox}",
    }

    if Categories:
        params["categories"] = Categories

    if keyword and keyword != "":
        params["text"] = keyword

    try:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Geoapify API: {e}")
        return {"features": []}


# --- NEW GEMINI FUNCTION: MERGE AND RANK ---

# --- NEW GEMINI FUNCTION: MERGE AND RANK ---

def rankAndMerge(geoapify_list, shopeefood_list, keyword): # Added 'keyword'
    """
    Uses Gemini to perform fuzzy matching, FILTER by keyword, and
    rank the combined list by local rating.
    """
    global Quantity

    shopeefood_subset = shopeefood_list[:500]

    # --- UPDATED PROMPT ---
    system_context = (
        "You are a restaurant data filter and matcher. Your task is to combine the following two restaurant lists:\n\n"
        f"1. List from Geoapify (location data):\n {json.dumps(geoapify_list, ensure_ascii=False, indent=2)}\n\n"
        f"2. List from Shopeefood (rating data):\n {json.dumps(shopeefood_subset, ensure_ascii=False, indent=2)}\n\n"
        f"The user's dish/keyword is: '{keyword}'\n\n"
        "Follow these steps:\n"
        "1. For each restaurant in the Geoapify list, find the best match in the Shopeefood list (based on 'Name' and 'Address').\n"
        "2. **Filter** the matched list to **only include restaurants** where the 'Name' from Shopeefood (or 'Cuisine' from Geoapify) contains the keyword: '{keyword}'.\n"
        "3. Add the 'Local_Rating' field to the *filtered* results.\n"
        "4. **Sort** the final filtered list by 'Local_Rating' in **descending** order.\n"
        f"5. **Limit** the final number of results to **{Quantity}**."
    )
    # --- END OF UPDATE ---

    schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "Name": {"type": "STRING"},
                "Address": {"type": "STRING"},
                "Cuisine": {"type": "STRING", "description": "Type of cuisine/dish (e.g., Pho, Bun Dau, Spicy Noodles)."},
                "Local_Rating": {"type": "NUMBER", "description": "The local user rating."},
            },
            "required": ["Name", "Address", "Cuisine", "Local_Rating"]
        }
    }

    model = genai.GenerativeModel('gemini-2.5-flash')

    response = model.generate_content(
        system_context,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": schema
        }
    )

    try:
        data = json.loads(response.text)
        return data
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError in Gemini Ranking: {e}")
        print("Raw response:", response.text)
        return []
    except Exception as e:
        print(f"Error calling rankAndMerge: {e}")
        return []

# --- FILE EXPORT FUNCTIONS ---

def writeCSV(RestaurantList):
    """Exports the restaurant list to a CSV file."""
    if not RestaurantList:
        print("Restaurant list is empty, cannot write CSV.")
        return

    fieldnames = list(RestaurantList[0].keys())

    with open("Restaurant_Ranked.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(RestaurantList)
    print("Results written to Restaurant_Ranked.csv")


def writeJSON(RestaurantList):
    """Exports the restaurant list to a JSON file."""
    with open("Restaurant_Ranked.json", "w", encoding="utf-8") as file:
        json.dump(RestaurantList, file, ensure_ascii=False, indent=4)
    print("Results written to Restaurant_Ranked.json")


# --- MAIN EXECUTION FUNCTION ---

# --- MAIN EXECUTION FUNCTION ---

def main():
    shopeefood_list = []
    try:
        df_shopeefood = pd.read_csv("ho_chi_minh_shopeefood_details.csv")
        df_shopeefood = df_shopeefood[['restaurant_name', 'address', 'rating']].rename(
            columns={'restaurant_name': 'Name', 'rating': 'Local_Rating'}
        )
        df_shopeefood = df_shopeefood[df_shopeefood['Local_Rating'].notna() & (df_shopeefood['Local_Rating'] > 0.0)]
        shopeefood_list = df_shopeefood.to_dict(orient='records')
        print(f"Successfully loaded and filtered {len(shopeefood_list)} local review entries.")
    except FileNotFoundError:
        print("Error: 'ho_chi_minh_shopeefood_details.csv' file not found. Skipping local ranking.")

    prompt = input("Enter a prompt (e.g., bun dau restaurant in district 3): ")

    dictionary = geminiNLP(prompt)
    if not dictionary or not dictionary[0]:
        print("Could not extract information from the prompt.")
        return

    location = dictionary[0].get("Location", "")
    mapped_category = dictionary[0].get("Mapped", "catering")
    keyword = dictionary[0].get("Categories", "")  # This is our dish name, e.g., "bun dau"

    print(f"\n=> Location: {location}, Category: {mapped_category}, Keyword: {keyword}")

    bbox = bboxForLocation(location)

    # --- THIS IS THE FIX ---
    # 1. Broaden Geoapify search: Do NOT pass the specific 'keyword' here.
    data = restaurantForLocation(bbox, mapped_category)
    # --- END OF FIX ---

    geoapify_list = []
    for i in data.get("features", []):
        props = i["properties"]
        cuisine = None
        if "catering" in props and "cuisine" in props["catering"]:
            cuisine = props["catering"]["cuisine"]
        elif "datasource" in props and "raw" in props["datasource"] and "cuisine" in props["datasource"]["raw"]:
            cuisine = props["datasource"]["raw"]["cuisine"]

        geoapify_list.append({
            "Name": props.get("name"),
            "Address": props.get("address_line2"),
            "Cuisine": cuisine
        })

    print(f"Found {len(geoapify_list)} restaurants from Geoapify.")

    if shopeefood_list and geoapify_list:
        print("\nUsing Gemini to rank and merge data...")
        # --- THIS IS THE FIX ---
        # 2. Filter with Gemini: Pass the 'keyword' to rankAndMerge.
        final_list = rankAndMerge(geoapify_list, shopeefood_list, keyword)
        # --- END OF FIX ---
    else:
        print("\nNo local data for ranking. Displaying raw Geoapify results.")
        final_list = geoapify_list

    if final_list:
        writeCSV(final_list)
        writeJSON(final_list)

        print("\n--- 🌟 Ranked Restaurant Results (Top 5) 🌟 ---")
        for idx, i in enumerate(final_list[:Quantity]):
            print(f"[{idx + 1}] Name: {i.get('Name')}")
            print(f"    Address: {i.get('Address')}")
            print(f"    Cuisine: {i.get('Cuisine')}")
            if 'Local_Rating' in i:
                print(f"    Local Rating: {i['Local_Rating']}")
            print("-" * 30)
    else:
        print("No restaurants matching the criteria were found.")

if __name__ == "__main__":
    try:
        import pandas as pd
    except ImportError:
        print("Pandas library required: pip install pandas")
        exit()

    if not os.path.exists("RestaurantFormat.txt"):
        print("Creating default RestaurantFormat.txt. Please customize it.")
        with open("RestaurantFormat.txt", "w", encoding="utf-8") as f:
            f.write("catering\ncoffee\nbakery\nkorean\nchinese\nfast_food\n")

    if not GOOGLE_API or not GEOAPIFY_API:
        print("\n⚠️ MISSING API KEY: Please create a .env file in the same directory and add the following lines:")
        print("GOOGLE_API_KEY=\"[YOUR_GEMINI_API_KEY]\"")
        print("GEOAPIFY_API_KEY=\"[YOUR_GEOAPIFY_API_KEY]\"")
    else:
        main()