#!/usr/bin/env python3
import sys
import json
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from rich.console import Console
from rich.markdown import Markdown

header = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36"
}

# url = "https://www.makemytrip.com/hotels/hotel-details/?hotelId=202209302002021632&_uCurrency=INR&checkin=01042024&checkout=01052024&city=CTJAI&country=IN&lat=26.93763&lng=75.78794&locusId=CTJAI&locusType=city&rank=1&regionNearByExp=3&roomStayQualifier=2e0e&rsc=1e2e0e&searchText=Treebo%20Trend%20The%20Royal%20CM&topHtlId=202209302002021632&mtkeys=-3007853608503926677"
url = input("Enter URL: ")

# Getting data from MMT
s = requests.Session()
try:
    s.get("https://www.makemytrip.com/", headers=header)
    cookie = s.cookies.get_dict()
except:
    print("An error occured while conencting to MMT")
    sys.exit(0)

print("Fetching details from MakeMyTrip...", end="")
response = s.get(url, cookies=cookie, headers=header)
soup = BeautifulSoup(response.content, "html.parser")
if soup.title == "Site Maintenance":
    print(" Error: please update your python version and requests library.")
    sys.exit(0)

print(" done")
sc_tags = soup.find_all("script")
data = json.loads(sc_tags[1].string[27:])
mmtData = data["hotelDetail"]["staticDetail"]["hotelDetails"]

# Getting the ID of hotel from the JSON map.
with open("mmt_trb.json") as f:
    ingo_to_cs = json.load(f)

hotel_ingoId = mmtData["ingoId"]
try:
    hotel_id = ingo_to_cs[hotel_ingoId]
except:
    print("This hotel is not listed in Treebo's Website.")
    sys.exit()

# Getting data from Treebo
treebo_api_url = f"https://www.treebo.com/api/v5/hotels/{hotel_id}/details/"

try:
    print("Fetching details from Treebo Hotels...", end="")
    trbData = requests.get(treebo_api_url).json()["data"]
except:
    print("An error occured while fetching data from Treebo.")
    sys.exit(0)

print(" done")

# with open(f"mmt_{hotel_id}.json", "w") as f:
#     json.dump(mmtData, f, indent=2)

# with open(f"trb_{hotel_id}.json", "w") as f:
#     json.dump(trbData, f, indent=2)

# ---- processing data ----

# MMT Data Processing----------------------------------------

# with open("mmt_3523.json") as mmtF:
#     mmtData = json.load(mmtF)

# with open("trb_3523.json") as trbF:
#     trbData = json.load(trbF)

TrebLocationDisct, MMTLocationDict = (
    trbData["address"],
    mmtData["locationDetail"],
)

TrebPolicies, MMTPolicies = "", ""
TrebAmeneties, MMTAmeneties = "", ""
TrebName, MMTName = trbData["name"], mmtData["name"]
TrebLocation, MMTLocation = "", ""

for key, values in TrebLocationDisct.items():
    TrebLocation += str(values) + ","

for key, values in MMTLocationDict.items():
    MMTLocation += str(values) + ","


# Policies
for rule_dict in mmtData["houseRules"]["commonRules"]:
    for rules in rule_dict["rules"]:
        MMTPolicies += rules["text"] + ","

for rule_dict in mmtData["houseRules"]["extraBedPolicyList"]:
    for policyRules in rule_dict["policyRules"]:
        for terms in policyRules["extraBedTerms"]:
            MMTPolicies += terms["value"] + ","


# Amenities
for ameni_dict in mmtData["amenities"]:
    for facilities in ameni_dict["facilities"]:
        if "subText" in facilities:
            MMTAmeneties += facilities["name"] + facilities["subText"] + ","
        else:
            MMTAmeneties += facilities["name"] + ","


# Treebo Data Processing ---------------------------------------

# trbFacilites
for facil_dict in trbData["facilities"]:
    TrebAmeneties += facil_dict["name"] + ","

# Polices
for policy_dict in trbData["hotel_policies"]:
    TrebPolicies += policy_dict["description"] + ","

# print(MMTName)
# print(MMTPolicies)
# print(MMTLocation)
# print(MMTAmeneties)
# ------------------------------------------------------------

with open("GEMINI_API_KEY") as f:
    GOOGLE_API_KEY = f.read()

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-pro")
except:
    print("An error occured while connecting to Gemini AI.")

# Writing a prompt for Gemini and sending it
print("Comparing results using Gemini AI...")
print("(This might take some time)\n")
prompt = "Generate a concise report by mentioning key points as YES or NO in tabular form for the difference between the data obtained from two different websites : "
note = "1)DO not use the data from outside the information provided by me. 2) if data not avaialble print not specified: "

# nameResponse = model.generate_content(prompt + note + 'Treebo data : ' + TrebName + 'MMT data : ' + MMTName)
locationResponse = model.generate_content(
    prompt + note + "Treebo data : " + TrebLocation + "MMT data : " + MMTLocation
)
policyResponse = model.generate_content(
    prompt + note + "Treebo data : " + TrebPolicies + "MMT data : " + MMTPolicies
)
amenititesResponse = model.generate_content(
    prompt + note + "Treebo data : " + TrebAmeneties + "MMT data : " + MMTAmeneties
)

# print("***********NameResponse********************************************")
# print(nameResponse.text)
# print("\n")
# print("***********LocationResponse********************************************")
# print(locationResponse.text)
# print("\n")
# print("***********PolicyResponse********************************************")
# print(policyResponse.text)
# print("\n")
# print("***********AmenitiesResponse********************************************")
# print(amenititesResponse.text)

report_data = "# Location\n\n" + str(locationResponse.text) + "\n"
report_data += "\n# Policy\n\n" + str(policyResponse.text) + "\n"
report_data += "\n# Amenities\n\n" + str(amenititesResponse.text) + "\n"

# Printing the report on terminal
console = Console()
console.print(Markdown(report_data))

# Passing the data to the mailing script
data = {"hotel_name": trbData["name"], "report_data": report_data}
