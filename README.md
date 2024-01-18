# Direct vs MMT Digest

Optimizing hotel sales through accurate OTA content management.

## About

One of our regular problems is that hotel’s OTA sales drop because the content on OTA isn’t correct and there are certain issues.  This results in:
- Loss of trust and credibility
- Reduced booking conversions
- Negative online reviews
- Competitive disadvantage

Objective is to, periodically, scrape content of our own properties from OTA (Makemytrip) and compare it with our Direct content and generate an email report.

## Technologies Used

- Language: [Python3](https://www.python.org/)
- Web scraping library: [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/)
- Emailing library: [Courier](https://www.courier.com/docs/getting-started/what-is-courier/)
- Generative AI: [Gemini](https://ai.google.dev/tutorials/python_quickstart)
- Treebo's Web API endpoint: https://www.treebo.com/api/v5/hotels/{hotel_id}/details/

## Setup

### Creating a Virtual Environment

- Install `venv` for Python3 by running `sudo apt install python3-venv` in your Linux terminal.
- Clone this repository locally, using `git clone https://github.com/halfviking101/direct-mmt-digest.git`
- Navigate inside the directory using `cd direct-mmt-digest`
- Run `python3 -m venv .env` to create a virtual environment in the current directory.
- Run `source .env/bin/activate` to activate the virtual environment.

### Installing the dependencies

- Run `pip install -r requirements.txt` to install the dependencies.

It will install the following libraries for python:
```
requests
beautifulsoup4
trycourier
google-generativeai
rich
markdown2
```

In order to setup a Courier account and get an API key, follow the instructions given on https://www.courier.com/docs/getting-started/quickstarts/python/

Copy the API key and paste it in the below command:
```
echo "PASTE_YOUR_API_KEY_HERE" > COURIER_API_KEY
```

Follow the below steps to generate a Gemini API key:
- To initiate the process, go to https://makersuite.google.com.
- Accept the terms of service and click on continue.
- Click on Get API Key link from the sidebar and Create API Key in new project button to generate the key.
- Copy the API key.
- Run `echo "PASTE_YOUR_API_KEY_HERE" > GEMINI_API_KEY`.

### Running the script

- Run `python main.py` to start execution of the script and follow the instructions thereafter.
- Enter your email id (where the report will be sent).
- After that, it will ask for the URL of hotel from MMT website.

The script will now scrape content from the MMT url, fetch the hotel details from Treebo, send a prompt to Gemini with the data and generate a markdown report to be emailed.