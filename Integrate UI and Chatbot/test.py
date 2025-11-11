from dotenv import load_dotenv
import os

load_dotenv()
print("GEOAPIFY_API:", os.getenv("GEOAPIFY_API"))
print("GOOGLE_API:", os.getenv("GOOGLE_API"))
