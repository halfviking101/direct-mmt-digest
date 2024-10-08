#!/usr/bin/env python3
import sys
import json
import requests
import time
import concurrent.futures
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
        return {"status": 404, "url": mmt_url}

    sc_tags = soup.find_all("script")
    data = None
    for val in sc_tags:
        if val.string and val.string[:27] == "window.__INITIAL_STATE__ = ":
            data = json.loads(val.string[27:])
            break

    # data = json.loads(sc_tags[1].string[27:])
    if (
        data is None
        or data["hotelDetail"].get("staticDetail") is None
        or data["hotelDetail"]["staticDetail"].get("hotelDetails") is None
    ):
        return {"status": 404, "url": mmt_url}

    mmtData = data["hotelDetail"]["staticDetail"]["hotelDetails"]
    try:
        trbData = requests.get(trb_url).json()["data"]
    except:
        return {"status": 404, "url": trb_url}

    return {"mmt": mmtData, "trb": trbData}


with open("mmt_trb.json") as f:
    mmt_trb = json.load(f)

success, fails = 0, 0
start_time = time.time()
merged_data = tuple()
failed = []
with concurrent.futures.ThreadPoolExecutor(max_workers=40) as tpe:
    ftu = {
        tpe.submit(send_requests, mmt_id, trb_id): (mmt_id, trb_id)
        for mmt_id, trb_id in list(mmt_trb.items())[:50]
    }

    for f in concurrent.futures.as_completed(ftu):
        mmt_id, trb_id = ftu[f]
        data = f.result()
        if data.get("status") == 404:
            # print("Failed for MMT", mmt_id, "and TRB", trb_id)
            failed.append(data["url"])
            fails += 1
            continue
        else:
            success += 1

        merged_data += (data,)

print("fails:", fails, "success:", success)
print("size:", sys.getsizeof(merged_data) / 1024, "KB")
print("--- %s seconds ---" % (time.time() - start_time))

if len(failed) != 0:
    print("Failed:", *failed, sep="\n")
