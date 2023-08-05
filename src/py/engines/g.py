import requests, re, json, time
from logging import Logger
from bs4 import BeautifulSoup
from aqt import QWebEngineView, QUrl, mw, QWebEnginePage, QThread, QObject
from ..engine import *

_URL = 'https://www.google.com/search?source=lnms&tbm=isch&'
result: str

class Google(Engine):
    """Google search engine (BeautifulSoup) implementation"""
    @staticmethod
    def title():
        return "Google (BS)"

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
<li>intitle:anki => Only results with page title including "anki"</li>
<li>maxn:10 => Only first 10 results (default all)</li></ul>"""

    def search(self, query: str):
        result = []
        # Parse max no of matches
        maxn = 0
        if m := re.match(r'(.*?)\s*maxn:(\d+)(.*)', query):
            maxn = int(m.group(2))
            if m.group(1) and m.group(3):
                query = f'{m.group(1).strip()} {m.group(3).strip()}'
            else:
                query = m.group(1).strip() if m.group(1) else m.group(3).strip()
        
        print('setting up thread')
        thread = WorkerThread()
        thread.start()
        thread.wait()
        print(f"reading {result}")
        
        """for img in imgs:
            title = img.select_one('h3').string
            img.select_one('div.islib')"""
        
        return result


class WorkerThread(QThread):
    def run(self):
        print("run")
        browser = QWebEnginePage()
        print("setting URL")
        browser.setUrl(QUrl(f'{_URL}&q=a.+vertebralis'))
        print(f'html: {browser.toHtml()}')
        global result
        result = [{'what': 'ever'}, {'what': 'else'}]
