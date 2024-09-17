import json
import textwrap
import google.generativeai as genai
from IPython.display import Markdown

# MMT Data Processing----------------------------------------

with open("mmt_3523.json") as mmtF:
    mmtData = json.load(mmtF)

with open("trb_3523.json") as trbF:
    trbData = json.load(trbF)

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


def to_markdown(text):
    text = text.replace("•", "  *")
    return Markdown(textwrap.indent(text, "> ", predicate=lambda _: True))


GOOGLE_API_KEY = "AIzaSyBw_oyaD2U8JDe2EfACHyYXulbMte3yMxs"
genai.configure(api_key=GOOGLE_API_KEY)

# for m in genai.list_models():
#     if "generateContent" in m.supported_generation_methods:
#         print(m.name)

model = genai.GenerativeModel("gemini-pro")

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

report_data = "**Location**\n" + locationResponse.text + "\n"
report_data += "\n**Policy**\n" + policyResponse.text + "\n"
report_data += "\n**Amenities**\n" + amenititesResponse.text + "\n"


from rich.console import Console
from rich.markdown import Markdown
from markdown2 import markdown


console = Console()
console.print(Markdown(report_data))

data = {"hotel_name": trbData["name"], "report_data": markdown(report_data)}
