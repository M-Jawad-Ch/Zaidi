import requests
import json
import environ

env = environ.Env()

def scrape(urls):
    try:
        url = env.get_value('LAMBDA_SCRAPER_URL')
        params = {"urls": json.dumps([*urls])}

        res = requests.get(url, params=params)
        return res.json()
    except:
        return None