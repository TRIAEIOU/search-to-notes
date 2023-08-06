import requests, re, json, time
from logging import Logger
from bs4 import BeautifulSoup
from aqt import QWebEngineView, QUrl, mw, QWebEnginePage, QThread, QObject, QWebChannel
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
        def await_(f: Callable, cb_index: int = None, *args):
            """Await result from callback"""
            def cb(*args):
                """Generic callback"""
                nonlocal done, result
                result = args
                done = True

            done = False
            result = None

            # Insert our own callback in the correct place
            if not args:
                args = (cb,)
            else:
                args_ = list(args)
                args_.insert(cb_index, cb)
                args_ = tuple(args_)        

            # Call and wait
            f(*args)
            while not done:
                mw.app.processEvents()

            return result

        result = []
        # Parse max no of matches
        maxn = 0
        if m := re.match(r'(.*?)\s*maxn:(\d+)(.*)', query):
            maxn = int(m.group(2))
            if m.group(1) and m.group(3):
                query = f'{m.group(1).strip()} {m.group(3).strip()}'
            else:
                query = m.group(1).strip() if m.group(1) else m.group(3).strip()

        print("run")
        browser = QWebEnginePage()
        #browser.loadFinished.connect(onload)

        print(f"loading URL {_URL}q={query}")
        browser.load(QUrl(f'{_URL}q={query}'))
        html = await_(browser.toHtml)
        print(f"got html: {html[:50]} from await_")

        print('setting result')
        result = [Match(title='one', url="urlone"), Match(title='two', url="urltwo")]

        
        return result

class Bridge(QObject):
    def __init__(self, scraper: Scraper):
        self.scraper = scraper

    @pyqtSlot(str, result=str)
    def cmd(self, cmd, res):
        print(f"cmd received: {cmd} - {res}")
        if cmd.startswith('result: '):
            self.scraper.result = json.loads(cmd[len('result: '):])


class Scraper:
    def __init__(self):
        self.page = QWebEnginePage()
        channel = QWebChannel(self.page)
        py = Bridge(self)
        channel.registerObject("py", py)
        self.page.setWebChannel(channel)
    
    def scrape(self, url: str):
        def onload(*_):
            nonlocal loaded
            loaded = True
        
        def onscript(res):
            nonlocal result
            result = json.loads(res)

        # Load google search
        loaded = False
        connection = self.page.loadFinished.connect(onload)
        self.page.load(QUrl(url))
        while not loaded:
            mw.app.processEvents()
        
        # Script page to get result
        result = None
        self.page.runJavaScript(f'''document.innerHTML''', onscript)
        while result is None:
            mw.app.processEvents()

        return result

       
