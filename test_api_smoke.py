import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_system_status():
    resp = requests.get(f"{BASE_URL}/system/status")
    print("GET /system/status ->", resp.status_code)
    assert resp.status_code == 200
    print(resp.json())

def test_jobs():
    resp = requests.get(f"{BASE_URL}/jobs/")
    print("GET /jobs/ ->", resp.status_code)
    assert resp.status_code == 200
    print(resp.json())

def test_search_semantic():
    resp = requests.post(f"{BASE_URL}/search/semantic", params={"query": "test", "limit": 10})
    print("POST /search/semantic ->", resp.status_code)
    assert resp.status_code == 200
    print(resp.json())

def test_search_keyword():
    resp = requests.post(f"{BASE_URL}/search/keyword", params={"query": "test"})
    print("POST /search/keyword ->", resp.status_code)
    assert resp.status_code == 200
    print(resp.json())

if __name__ == "__main__":
    print("Waiting for server to start...")
    time.sleep(2)
    print("Running tests...")
    test_system_status()
    test_jobs()
    test_search_semantic()
    test_search_keyword()
    print("All smoke tests passed!")
