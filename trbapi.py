import requests
import json

params = {"search_string": input("Hotel Name: ")}

response = requests.get(
    "https://www.treebo.com/api/v1/search/autocomplete/", params=params
).json()

hotel_id = response["data"][0]["hotel_id"]

treebo_api_url = f"https://www.treebo.com/api/v5/hotels/{hotel_id}/details/"

trbapi_data = requests.get(treebo_api_url).json()["data"]

with open(f"{hotel_id}.json", "w") as f:
    json.dump(trbapi_data, f, indent=2)
