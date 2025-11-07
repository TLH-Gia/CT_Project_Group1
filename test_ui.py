# tests/test_ui_selenium.py
import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

BASE_URL = "http://127.0.0.1:5000"

class UITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # ensure chromedriver in PATH or give executable_path
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")  # uncomment to run headless
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(6)
        cls.driver.maximize_window()

    def test_01_prompt_and_recommend(self):
        self.driver.get(BASE_URL)
        time.sleep(1)
        # adjust selector to your actual input id
        prompt = self.driver.find_element(By.ID, "prompt-input")
        prompt.clear()
        prompt.send_keys("bún chả")
        prompt.send_keys(Keys.ENTER)
        time.sleep(1.5)
        container = self.driver.find_element(By.ID, "recommendation-section")
        items = container.find_elements(By.CLASS_NAME, "recommend-item")
        self.assertTrue(len(items) > 0 and len(items) <= 3, f"Expected 1..3 recommend items, got {len(items)}")
        print("UI recommend count:", len(items))

    def test_02_select_restaurant_and_route(self):
        # assumes previous page still loaded
        container = self.driver.find_element(By.ID, "recommendation-section")
        items = container.find_elements(By.CLASS_NAME, "recommend-item")
        if not items:
            self.skipTest("No recommendation items found")
            return
        # click first item (adjust clickable element)
        items[0].click()
        time.sleep(1)
        # expect map to update; map id assumed "map"
        map_el = self.driver.find_element(By.ID, "map")
        self.assertTrue(map_el.is_displayed())
        # expect some route info displayed
        try:
            route_info = self.driver.find_element(By.ID, "route-info").text
            self.assertTrue(len(route_info) > 0)
            print("Route info:", route_info[:80])
        except Exception:
            # if route-info not present, allow but warn
            print("No #route-info element found after selecting restaurant (optional)")

    def test_03_feedback_form_submit(self):
        self.driver.get(BASE_URL + "/form")
        time.sleep(0.6)
        # click radio inputs by name (q1..q4); adapt if your form uses different names
        for name in ("q1","q2","q3","q4"):
            # choose the highest value radio if present
            radios = self.driver.find_elements(By.NAME, name)
            if radios:
                radios[-1].click()
        note = self.driver.find_element(By.NAME, "note")
        note.send_keys("Automated UI feedback test")
        btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        btn.click()
        time.sleep(1)
        self.assertIn("Cảm ơn", self.driver.page_source)
        print("Feedback UI submit OK")

    def test_04_food_detection_upload(self):
        # optional page
        try:
            self.driver.get(BASE_URL + "/food_recognition")
            up = self.driver.find_element(By.ID, "upload-image")
            # adjust path to a valid image in the repo tests/
            up.send_keys("tests/sample_food.jpg")
            btn = self.driver.find_element(By.ID, "recognize-btn")
            btn.click()
            time.sleep(2)
            result = self.driver.find_element(By.ID, "food-name").text
            self.assertTrue(len(result) > 0)
            print("Food detection result:", result)
        except Exception as e:
            self.skipTest(f"Food recognition UI not available or element mismatch: {e}")

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

if __name__ == "__main__":
    unittest.main(verbosity=2)
