import requests, re, json
from logging import Logger
from bs4 import BeautifulSoup
from ..engine import *

def parseurl(url: str):
    """Parse URL into dict of components or None if invalid"""
    regex = re.compile( # https://stackoverflow.com/a/67099046
        r"(\w+://)?"                                        # protocol
        r"((?:[\w\-]+\.)*)"                                 # host/subdomain
        r"([\w\-]+)"                                        # domain
        r"(?:\.([\w\-]+))"                                  # top-level domain
        r"(/(?:[\w\-.,~!$&'()*+;=:@/]|%[0-9a-fA-F]{2})*)?"  # path
        r"(\?[^:/?#[\]@]+)*"                                # params
        r"(#.*)?"                                           # anchor
    )
    if res := regex.match(url):
        return {
            'protocol': res.group(1) or '',
            'host-subdomain': res.group(2)[:-1] if res.group(2) else '',
            'domain': res.group(3),
            'tld': res.group(4),
            'path': res.group(5)[1:] if res.group(5) else '',
            'params': res.group(6)[1:] if res.group(6) else '',
            'anchor': res.group(7)[1:] if res.group(7) else ''
        }
    return None

def decode_json(string: str):
    """Decode JSON string"""
    return json.loads(f'{{"1": "{string}"}}')['1']

class Google(Engine):
    """Google search engine implementation"""
    @staticmethod
    def title():
        return "Google"

    def __init__(self, logger: Logger, config: dict):
        self.logger = logger

    def legend(self):
        return '"[exact term]", +/-[term], site:[url], maxn:[max results]'

    def tooltip(self):
        return \
"""<b>SEARCH ENGINE SYNTAX</b>
<ul><li>cats dogs => cats or dogs in results</li>
<li>"cats and dogs" => Exact term "cats and dogs" in results</li>
<li>cats -dogs => Fewer dogs in results</li>
<li>cats +dogs => More dogs in results</li>
<li>site:commons.wikimedia.org => Only results from commons.wikimedia.org</li>
<li>intitle:anki => Only results with webview.page() title including "anki"</li>
<li>maxn:10 => Only first 10 results (default all)</li></ul>"""

    def search(self, query: str):
        # Parse max no of matches
        maxn = 0
        if m := re.match(r'(.*?)\s*maxn:(\d+)(.*)', query):
            maxn = int(m.group(2))
            if m.group(1) and m.group(3):
                query = f'{m.group(1).strip()} {m.group(3).strip()}'
            else:
                query = m.group(1).strip() if m.group(1) else m.group(3).strip()

        html = requests.get(
            url = "https://www.google.com/search",
            params = {
                "q": query,          # search query
                "tbm": "isch",                  # image results
                "hl": "en",                     # language of the search
                "gl": "us",                     # country where search comes from
                "ijn": "0"                      # page number
            },
            headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36"
            },
            cookies = {
                'CONSENT' : 'YES+'              # Google consent
            },
            timeout = 30
        )
        soup = BeautifulSoup(html.text, "html.parser")
        result = []

        # look in script tags with AF_initDataCallback calls which contain the data
        for script in re.findall(
                r"AF_initDataCallback\(([^<]+)\);",
                str(soup.select("script"))
            ):
            for (url, height_title, width) in re.findall(
                r'"(https?://[^"]+)"\s*,\s*(\d+|"[^"]+")\s*,\s*(\d+|null)',
                script
            ):
                url = decode_json(url)
                purl = parseurl(url)
                if not purl or (purl['domain'] == 'gstatic' and purl['tld'] == 'com'):
                    continue
                try:
                    h = int(height_title)
                    w = int(width)
                    result.append(Match(url=url, height=h, width=w))
                except:
                    if result:
                        result[-1].title = decode_json(height_title[1:-1])
                        if len(result) == maxn:
                            break

        return result