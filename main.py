#!/usr/bin/env python3
import sys
from trycourier import Courier

email_id = input("Enter your email id: ")
from scrape_data import data

with open("COURIER_API_KEY") as f:
    auth_token = f.read()

client = Courier(auth_token=auth_token)

try:
    resp = client.send_message(
        message={
            "to": {"email": email_id},
            "template": "EKN5DXQEPB45NWG9FEYCRSV6Q6BJ",  # custom template for mail made in courier
            "data": data,
        }
    )
except:
    print("An error occured while mailing.")
    sys.exit()
finally:
    print(resp["requestId"])
