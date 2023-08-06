import requests, re, json, time
from logging import Logger
from bs4 import BeautifulSoup
from aqt import QWebEngineView, QUrl, mw, QWebEnginePage, QThread, QObject, QWebChannel, pyqtSlot
from typing import Callable
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
        # Parse max no of matches
        maxn = 0
        if m := re.match(r'(.*?)\s*maxn:(\d+)(.*)', query):
            maxn = int(m.group(2))
            if m.group(1) and m.group(3):
                query = f'{m.group(1).strip()} {m.group(3).strip()}'
            else:
                query = m.group(1).strip() if m.group(1) else m.group(3).strip()

        def onload(*_):
            nonlocal loaded
            loaded = True
        
        def onscript(res):
            nonlocal result
            result = res or ""

        # Setup browser
        print("Setup browser")
        page = QWebEnginePage()
        channel = QWebChannel(page)
        py = Bridge(page)
        channel.registerObject("py", py)
        page.setWebChannel(channel)

        # Load google search
        print("Load search")
        loaded = False
        connection = page.loadFinished.connect(onload)
        page.load(QUrl(f'{_URL}q={query}'))
        while not loaded:
            mw.app.processEvents()
        
        # Script page to get result
        print("Script")
        result = None
        page.runJavaScript(f'''(async function () {{
            await new Promise(r => setTimeout(r, 2000));
            itms = [];
            document.querySelectorAll('h3').forEach((el) => {{itms.push(el.innerText)}})
            return JSON.stringify(itms);
        }})();''',
        onscript)
        while result is None:
            mw.app.processEvents()
        
        # Parse results
        print(f"Parse results: {result}")
        result = json.loads(result)
        print(f"Parsed results: {result}")
        return result

class Bridge(QObject):
    """Class to handle js bridge"""
    @pyqtSlot(str, result=str)
    def cmd(self, cmd):
        print(f'cmd: {cmd}')
        pass
