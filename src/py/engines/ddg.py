"""
DuckDuckGo search engine: Credit to [Deepan](https://github.com/deepanprabhu)
and [deedy5](https://github.com/deedy5) for the DDG api implementation

NOTES
https://help.duckduckgo.com/duckduckgo-help-pages/results/syntax/ doesn't
seem to work, only these: [exact term]", +/-[term], site:[url]
Additional modifier maxn:\d implemented
"""

import requests, re, json, time
from logging import Logger
from ..engine import *
_URL = 'https://duckduckgo.com/'

class DDG(Engine):
    """DDG search engine implementation"""
    @staticmethod
    def title():
        return "DuckDuckGo (API)"

    def __init__(self, logger: Logger):
        self.logger = logger

    def legend(self):
        return '"[exact term]", +/-[term], site:[url], maxn:[max results]'

    def tooltip(self):
        return (
            '<b>SEARCH ENGINE SYNTAX</b>'
            '<ul><li><code>dogs cats</code>: dogs or cats in results</li>'
            '<li><code>"dogs and cats"</code>: Exact term "dogs and cats" in results</li>'
            '<li><code>+dogs cats</code>: more dogs in results</li>'
            '<li><code>dogs -cats</code>: less cats in results</li>'
            '<li><code>intitle:dogs</code>: Only results with webview.page() title including "dogs"</li>'
            '<li><code>maxn:10</code>: Only first 10 results (default all)</li></ul>'
        )

    def search(self, query: str):

        result: list[Match] = []
        # Parse max no of matches                
        maxn = -1
        maxn_match = re.fullmatch(r"(^|(.*?)\s)maxn:(\d+)($|(\s.*))", query)
        if maxn_match:
            maxn = int(maxn_match.group(3))
            query = maxn_match.group(2) if maxn_match.group(2) else ""
            query += maxn_match.group(5) if maxn_match.group(5) else ""

        headers = {
           'authority': 'duckduckgo.com',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'sec-fetch-dest': 'empty',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'referer': 'https://duckduckgo.com/',
            'accept-language': 'en-US,en;q=0.9' 
        }
        
        _ = {
            'authority': 'duckduckgo.com',
            'accept': 'application/json, text/javascript, */*; q=0.01', #"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9,hi;q=0.8",
            "cache-control": "max-age=0",
            "sec-ch-ua": "\"Google Chrome\";v=\"113\", \"Chromium\";v=\"113\", \"Not-A.Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "sec-gpc": "1",
            "upgrade-insecure-requests": "1",
            "cookie": "p=-2; ah=us-en; l=us-en",
            "Referer": "https://duckduckgo.com/",
            "Referrer-Policy": "origin"
        }
    
        # Get vqd token for the search
        res = requests.get(
            f'{_URL}/?va=f&t=hg&q={query}&iax=images&ia=images',
            headers=headers
        )
        print(f'token res: {res.text}')
        if res and (m := re.match(
            r'.*?vqd=([\'"]?)(.*?)(?:[\'"&].*|$)',
            res.text
        )):
            vqd = m.group(2)
        else:
            print("no vqd matched")
            return None

        params = {
            'l': 'wt-wt', # region wt-wt: no region
            #'l': 'us-en', # region
            'o': 'json', # output
            #'s': 0,
            'q': query, # query
            'vqd': vqd, # vqd-session
            'f': ',,,', # filters f"{timelimit},{size},{color},{type_image},{layout},{license_image}
            'p': -1, # safe-search off
            'v7exp': 'a' # ?
        }
        request = _URL + "i.js"
        while True:
            data = None
            for _ in range(3):
                try:
                    print(f'query: {request}, headers: {headers}, params: {params}')
                    res = requests.get(url=request, headers=headers, params=params)
                    print(f'res: {res}')
                    data = json.loads(res.text)
                    break
                except ValueError as e:
                    time.sleep(1)
            if data is None:
                return None
            for item in data['results']:
                result.append(Match(
                    title=item['title'],
                    url=item['image'],
                    width=item['width'],
                    height=item['height']
                ))
                maxn -= 1
                if maxn == 0:
                    break
            if maxn == 0 or 'next' not in data:
                break
            request = _URL + data['next']
        return result
