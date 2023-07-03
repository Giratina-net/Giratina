import requests
from os import getenv

#envから取得
KUTT_HOST = getenv("KUTT_HOST")+"/api/v2/links"
KUTT_API_KEY = getenv("KUTT_API_KEY")

#kuttのapiを使って短縮する
def gen(url):
    try:
        r = requests.post(KUTT_HOST, data={"target": url}, headers={'X-API-KEY': KUTT_API_KEY}).json()
        return r['link']
    except:
        return "False"

