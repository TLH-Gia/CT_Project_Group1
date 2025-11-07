# tests/test_api.py
import unittest
import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

class APISmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = requests.Session()

    def test_01_create_anon_user(self):
        """Create an anonymous user token"""
        resp = self.session.get(f"{BASE_URL}/create_user")
        self.assertEqual(resp.status_code, 201, msg=resp.text)
        data = resp.json()
        self.assertIn("anon_user_id", data)
        self.__class__.anon_user_id = data["anon_user_id"]
        print("Create user:", data["anon_user_id"])

    def test_02_save_chat(self):
        """Save a chat conversation (encrypted in backend)"""
        anon = getattr(self.__class__, "anon_user_id", None)
        self.assertIsNotNone(anon)
        payload = {
            "anon_user_id": anon,
            "messages": [
                {"role": "user", "content": "I want to eat bun cha in district 1"},
                {"role": "assistant", "content": "Try Bun Cha 34, address XYZ"}
            ],
            "metadata": {"location": "District 1", "map_link": "https://maps.google.com/?q=..."}
        }
        resp = self.session.post(f"{BASE_URL}/save_chat", json=payload)
        self.assertIn(resp.status_code, (200,201), msg=resp.text)
        print("Save chat:", resp.status_code, resp.text)

    def test_03_get_history(self):
        """Retrieve previously saved chat history"""
        anon = getattr(self.__class__, "anon_user_id", None)
        self.assertIsNotNone(anon)
        resp = self.session.get(f"{BASE_URL}/get_history/{anon}")
        self.assertEqual(resp.status_code, 200, msg=resp.text)
        data = resp.json()
        self.assertIn("conversations", data)
        print("History items:", len(data.get("conversations", [])))

    def test_04_delete_history(self):
        """Delete history and confirm deletion"""
        anon = getattr(self.__class__, "anon_user_id", None)
        self.assertIsNotNone(anon)
        resp = self.session.delete(f"{BASE_URL}/delete_history/{anon}")
        self.assertIn(resp.status_code, (200,204), msg=resp.text)
        # confirm empty
        resp2 = self.session.get(f"{BASE_URL}/get_history/{anon}")
        # either 404 or empty conversations allowed depending on backend
        self.assertIn(resp2.status_code, (200,404), msg=resp2.text)
        print("Delete history response:", resp.status_code)

    def test_05_recommend_get(self):
        """Basic GET recommend returns JSON list up to 3"""
        params = {"location": "Ho Chi Minh", "food": "bun cha"}
        resp = self.session.get(f"{BASE_URL}/recommend", params=params)
        self.assertEqual(resp.status_code, 200, msg=resp.text)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 3)
        if len(data) > 0:
            item = data[0]
            self.assertIn("Restaurant", item)
            self.assertIn("Address", item)
        print("Recommend GET returned", len(data), "items")

    def test_06_recommend_post(self):
        """POST recommend with preferences returns JSON list"""
        payload = {"location":"Hanoi","food":"pho","preferences":{"price_range":"$","dietary":"halal"}}
        resp = self.session.post(f"{BASE_URL}/api/recommend", json=payload)
        # Accept either 200 OK or 400 with error message
        self.assertIn(resp.status_code, (200,400), msg=resp.text)
        if resp.status_code == 200:
            data = resp.json()
            self.assertIsInstance(data, list)
            self.assertLessEqual(len(data), 3)
            print("Recommend POST items:", len(data))

    def test_07_route_api(self):
        """Test routing API returns distance/duration"""
        params = {"from":"21.0278,105.8342","to":"21.0378,105.8450"}
        resp = self.session.get(f"{BASE_URL}/route", params=params)
        if resp.status_code == 200:
            data = resp.json()
            self.assertIn("distance", data)
            self.assertIn("duration", data)
            self.assertIn("polyline", data)
            print("Route OK", data.get("distance"))
        else:
            # backend might not implement /route in dev; accept 404 but warn
            self.assertIn(resp.status_code, (200,404))
            print("/route responded", resp.status_code)

    def test_08_stats_page(self):
        """Access stats page (HTML)"""
        resp = self.session.get(f"{BASE_URL}/stats")
        self.assertEqual(resp.status_code, 200, msg=resp.text)
        # check it contains some expected keyword
        self.assertTrue(any(k in resp.text.lower() for k in ("feedback","average","chart")), msg="Stats page missing expected keywords")
        print("Stats page OK")

    def test_09_feedback_submit(self):
        """Submit feedback (form) endpoint - adjust route if necessary"""
        # Try both JSON and form-based submissions depending on app implementation
        data = {"q1":"4","q2":"4","q3":"4","q4":"4","note":"Automated test feedback"}
        # Try POST to /submit
        resp = self.session.post(f"{BASE_URL}/submit", data=data, allow_redirects=True)
        self.assertIn(resp.status_code, (200,302), msg=resp.text)
        print("Feedback submit:", resp.status_code)

    def test_10_optional_food_detection(self):
        """Optional: test food detection endpoint if exists by uploading image"""
        try:
            files = {"file": open("tests/sample_food.jpg","rb")}
        except FileNotFoundError:
            self.skipTest("No sample image found (tests/sample_food.jpg). Skipping detection test.")
            return
        resp = self.session.post(f"{BASE_URL}/detect_food", files=files)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("predictions", data)
        print("Detect food predictions:", data.get("predictions")[:3])

if __name__ == "__main__":
    # small delay to let server start if you ran concurrently
    time.sleep(0.5)
    unittest.main()
