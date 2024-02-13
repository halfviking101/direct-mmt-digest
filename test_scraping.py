#!/usr/bin/env python3
import sys, json, httpx, time, os
import concurrent.futures
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta

header = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36"}
cookies = {"s_sess": "%20tp%3D3696%3B%20s_ppv%3Dlanding%25253Abrand%25253Ahomepage%25253Aindia-MHP%252C16%252C16%252C583%3B"}

current_date = datetime.now()
check_in_date = (current_date + relativedelta(days=1)).strftime("%m%d%Y")
check_out_date = (current_date + relativedelta(days=2)).strftime("%m%d%Y")

try:
    with httpx.Client(http2=True, headers=header, cookies=cookies) as client:
        s = client.get(url="https://www.makemytrip.com/")

    cookies = dict(s.cookies)
except:
    print("An error occured while conencting to MMT")
    sys.exit(0)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i : i + n]


def send_requests(mmt_id, trb_id):
    mmt_url = f"https://www.makemytrip.com/hotels/hotel-details/?hotelId={mmt_id}&checkin={check_in_date}&checkout={check_out_date}"
    trb_url = f"https://www.treebo.com/api/v5/hotels/{trb_id}/details/"
    with httpx.Client(http2=True, headers=header, cookies=cookies) as client:
        response = client.get(url=mmt_url)

    soup = BeautifulSoup(response.content, "html.parser")
    if soup.title == "Site Maintenance":
        return {"status": 404, "url": mmt_url}

    sc_tags = soup.find_all("script")
    data = None
    for val in sc_tags:
        if val.string and val.string[:27] == "window.__INITIAL_STATE__ = ":
            data = json.loads(val.string[27:])
            break

    if data is None or data["hotelDetail"].get("staticDetail") is None:
        return {"status": 404, "url": mmt_url}

    mmtData = data["hotelDetail"]["staticDetail"]["hotelDetails"]
    try:
        trbData = httpx.get(trb_url).json()["data"]
    except:
        return {"status": 404, "url": trb_url}

    return {"mmt": mmtData, "trb": trbData}


with open("trb_mmt.json") as f:
    trb_mmt = json.load(f)

hotel_ids = set(filter(None, map(lambda s: s.strip(), os.getenv("HOTEL_ID").split(","))))
batch = [(id, trb_mmt[id]) for id in hotel_ids if trb_mmt.get(id)]
start_time = time.time()
merged_data = tuple()
failed = []
success, fails = 0, 0
with concurrent.futures.ThreadPoolExecutor(max_workers=40) as tpe:
    ftu = {tpe.submit(send_requests, mmt_id, trb_id): (mmt_id, trb_id) for trb_id, mmt_id in batch}
    for f in concurrent.futures.as_completed(ftu):
        mmt_id, trb_id = ftu[f]
        data = f.result()
        if data.get("status") == 404:
            failed.append((trb_id, mmt_id))
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
