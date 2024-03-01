#!/usr/bin/env python3
import google.generativeai as genai
from trycourier import Courier
import sys, time, os, json, requests
import boto3
from test_scraping import merged_data
from flask import abort, json
from bs4 import BeautifulSoup


def render_content(text, api_url, gfm=False, context=None,
                   username=None, password=None):
    """
    Renders the specified markup using the GitHub API.
    """
    if gfm:
        url = '{}/markdown'.format(api_url)
        data = {'text': text, 'mode': 'gfm'}
        if context:
            data['context'] = context
        data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        headers = {'content-type': 'application/json; charset=UTF-8'}
    else:
        url = '{}/markdown/raw'.format(api_url)
        data = text.encode('utf-8')
        headers = {'content-type': 'text/x-markdown; charset=UTF-8'}
    auth = (username, password) if username or password else None
    r = requests.post(url, headers=headers, data=data, auth=auth)
    # Relay HTTP errors
    if r.status_code != 200:
        try:
            message = r.json()['message']
        except Exception:
            message = r.text
        abort(r.status_code, message)
    return r.text


def convert_markdown_to_csv(data):
    api_url = 'https://api.github.com'
    html_table = render_content(data, api_url, True, None, None, None)

    soup = BeautifulSoup(html_table, "html.parser")
    tables = soup.find_all('table')  # Find all tables in the HTML
    headings = soup.find_all('h1')
    f = open(f'hotels_table.csv', 'a')
    for idx, table in enumerate(tables):

        rows = table.find_all('tr')
        ths = table.find_all(['th'])
        write_th_to_file = ''
        if idx == 0:
            f.write(f'---------{headings[idx].string}---------')
            f.write("\n")
        f.write(f'*******{headings[idx+1].string}*******')
        f.write('\n')
        for th in ths:
            if th.string is not None:
                # Add Markdown table heading in CSV
                write_th_to_file += (f'**{th.string}**' + ',')
            else:
                write_th_to_file += (' ' + ',')
        write_th_to_file = write_th_to_file[:-1]

        f.write(write_th_to_file)
        f.write('\n')

        for row in rows[1:]:
            write_td_to_file = ''
            tds = row.find_all('td')
            for td in tds:
                if td.string is not None:
                    write_td_to_file += (td.string + ',')
                else:
                    write_td_to_file += (' ' + ',')
            write_td_to_file = write_td_to_file[:-1]
            f.write(write_td_to_file)
            f.write('\n')
        f.write('\n')

    f.close()


def get_secret(secret_name, region_name):
    # Create a Secrets Manager client
    client = boto3.client(service_name="secretsmanager", region_name=region_name)
    try:
        secret_value_response = client.get_secret_value(SecretId=secret_name)
        return json.loads(secret_value_response["SecretString"])
    except Exception as e:
        print(e)

    return {"error": "Could not fetch from Secrets Manager"}


def filter_data(data_obj):
    filtered_merged_data = tuple()

    for data in data_obj:
        TrebLocationDict, MMTLocationDict = (
            data["trb"]["address"],
            data["mmt"]["locationDetail"],
        )

        TrebPolicies, MMTPolicies = "", ""
        TrebAmeneties, MMTAmeneties = "", ""
        TrebName, MMTName = data["trb"]["name"], data["mmt"]["name"]
        TrebLocation, MMTLocation = "", ""

        for key, values in TrebLocationDict.items():
            TrebLocation += str(values) + ","

        for key, values in MMTLocationDict.items():
            MMTLocation += str(values) + ","

        # Policies
        for rule_dict in data["mmt"]["houseRules"]["commonRules"]:
            for rules in rule_dict["rules"]:
                MMTPolicies += rules["text"] + ","

        for rule_dict in data["mmt"]["houseRules"]["extraBedPolicyList"]:
            for policyRules in rule_dict["policyRules"]:
                for terms in policyRules["extraBedTerms"]:
                    MMTPolicies += terms["value"] + ","

        # Amenities
        for ameni_dict in data["mmt"]["amenities"]:
            for facilities in ameni_dict["facilities"]:
                if "subText" in facilities:
                    MMTAmeneties += facilities["name"] + facilities["subText"] + ","
                else:
                    MMTAmeneties += facilities["name"] + ","

        # ---- Treebo Data Processing ----
        for facil_dict in data["trb"]["facilities"]:
            TrebAmeneties += facil_dict["name"] + ","

        # Polices
        for policy_dict in data["trb"]["hotel_policies"]:
            TrebPolicies += policy_dict["description"] + ","

        hotel_object = {
            "mmt": {
                "name": MMTName,
                "location": MMTLocation,
                "policies": MMTPolicies,
                "amenities": MMTAmeneties,
                "hotel_id": data["mmt"]["id"],
            },
            "trb": {
                "name": TrebName,
                "location": TrebLocation,
                "policies": TrebPolicies,
                "amenities": TrebAmeneties,
                "hotel_id": data["trb"]["id"],
            },
        }

        filtered_merged_data += (hotel_object,)

    return filtered_merged_data


def generate_reports(filtered_merge_data, model):
    for data in filtered_merge_data:
        # Writing a prompt for Gemini and sending it
        print("Comparing results using Gemini AI...")
        print("(This might take some time)\n")
        subject_line = "Points to be noted during generating the response:"
        prompt = (
            "Generate a concise report by mentioning key points "
            "as YES or NO in tabular form for the difference between "
            "the data obtained from two different websites :")
        note = (
            "1)(major priority) You have to generate the report without using any commas in it!!"
            "2)DO not use the data from outside the information provided to you"
            "3)If data not available print not specified ")
        end_line = "Here is the data provided to you"
        cumulative_prompt = prompt + subject_line + note + end_line

        locationResponse = model.generate_content(
            cumulative_prompt + "Treebo data : " + data["trb"]["location"] + "MMT data : " + data["mmt"]["location"]
        )
        policyResponse = model.generate_content(
            cumulative_prompt + "Treebo data : " + data["trb"]["policies"] + "MMT data : " + data["mmt"]["policies"]
        )
        amenititesResponse = model.generate_content(
            cumulative_prompt + "Treebo data : " + data["trb"]["amenities"] + "MMT data : " + data["mmt"]["amenities"]
        )

        report_data = "# Treebo Hotel ID-{}   MMT Hotel ID-{}".format(data["trb"]["hotel_id"],
                                                                      data["mmt"]["hotel_id"]) + "\n"
        report_data += "\n# Location\n\n" + str(locationResponse.text) + "\n"
        report_data += "\n# Policy\n\n" + str(policyResponse.text) + "\n"
        report_data += "\n# Amenities\n\n" + str(amenititesResponse.text) + "\n"
        # Converting Markdown format to csv format
        convert_markdown_to_csv(report_data)
        # Passing the data to the mailing script
        val = {"hotel_name": data["trb"]["name"], "report_data": report_data}
        yield val


if __name__ == "__main__":
    # Email Ids of the recipient provided as environment variable
    email_ids = list(filter(None, map(lambda s: s.strip(), os.getenv("EMAIL_ID").split(","))))
    if len(email_ids) > 1:
        recipient = [{"email": id} for id in email_ids]
    else:
        recipient = {"email": email_ids[0]}

    # Fetch secrets from AWS Secrets Manager
    secret_name = "treebo/production/aps1-cluster/apps/shared-credentials/postgres"
    region_name = "ap-south-1"
    secrets = get_secret(secret_name, region_name)
    if secrets.get("error"):
        print(secrets["error"])
        sys.exit()

    courier_api = secrets["COURIER_API_KEY"]
    client = Courier(auth_token=courier_api)

    gemini_api = secrets["GEMINI_API_KEY"]
    try:
        genai.configure(api_key=gemini_api)
        model = genai.GenerativeModel("gemini-pro")
    except:
        print("An error occured while connecting to Gemini AI.")
        sys.exit()

    start_time = time.time()
    # Filtering the merged dataset
    fmd = filter_data(merged_data)
    # Generating reports of the filtered dataset
    for report in generate_reports(fmd, model):
        # Send Email
        try:
            resp = client.send_message(
                message={
                    "to": recipient,
                    "template": "EKN5DXQEPB45NWG9FEYCRSV6Q6BJ",  # custom template for mail made in courier
                    "data": report,
                }
            )
        except:
            print(f"An error occured while mailing report for {report['hotel_name']}.")
            continue
        finally:
            print(resp["requestId"])

    print("--- gemini+email: %s seconds ---" % (time.time() - start_time))
