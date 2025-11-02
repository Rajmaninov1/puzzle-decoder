import requests

BASE_URL = "localhost:8080/fragment"


def fragment_endpoint_test(n: int):
    url = f"{BASE_URL}?id={n}"
    print(f"→ Requesting: {url}")
    response = requests.get(url, timeout=5)

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}\n")


if __name__ == "__main__":
    # Test a few sample IDs
    for i in range(1, 4):
        fragment_endpoint_test(i)
