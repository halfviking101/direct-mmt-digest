#!/usr/bin/env python3
import json
from bs4 import BeautifulSoup
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import concurrent.futures
import os

header = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36"
}

current_date = datetime.now()
check_in_date = (current_date + relativedelta(days=1)).strftime("%m%d%Y")
check_out_date = (current_date + relativedelta(days=2)).strftime("%m%d%Y")

s = requests.Session()
try:
    s.get("https://www.makemytrip.com/", headers=header)
    cookie = s.cookies.get_dict()
except:
    print("An error occured while conencting to MMT")
    sys.exit(0)


def send_requests(mmt_id, trb_id):
    mmt_url = f"https://www.makemytrip.com/hotels/hotel-details/?hotelId={mmt_id}&checkin={check_in_date}&checkout={check_out_date}"
    trb_url = f"https://www.treebo.com/api/v5/hotels/{trb_id}/details/"
    response = s.get(mmt_url, cookies=cookie, headers=header)
    soup = BeautifulSoup(response.content, "html.parser")
    if soup.title == "Site Maintenance":
        return {"status": 404}

    sc_tags = soup.find_all("script")
    data = json.loads(sc_tags[1].string[27:])
    mmtData = data["hotelDetail"]["staticDetail"]["hotelDetails"]
    try:
        trbData = requests.get(trb_url).json()["data"]
    except:
        return {"status": 404}

    return {"mmt": mmtData, "trb": trbData}


with open("mmt_trb.json") as f:
    mmt_trb = json.load(f)

# mmt_trb = {"202309291210185381": "3890", "202309291227363579": "3889"}
if not os.path.exists("fetched_data"):
    os.mkdir("fetched_data")

with concurrent.futures.ThreadPoolExecutor(max_workers=40) as tpe:
    ftu = {
        tpe.submit(send_requests, mmt_id, trb_id): (mmt_id, trb_id)
        for mmt_id, trb_id in mmt_trb.items()
    }

    for f in concurrent.futures.as_completed(ftu):
        mmt_id, trb_id = ftu[f]
        data = f.result()
        if data.get("status") == 404:
            print("Failed for MMT", mmt_id, "and TRB", trb_id)
            continue
        else:
            print("Success for", trb_id)

        with open(f"fetched_data/{trb_id}.json", "w") as f:
            json.dump(data, f, indent=2)
