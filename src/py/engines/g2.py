import requests, re, json, time
from logging import Logger
from bs4 import BeautifulSoup
from aqt import QWebEngineView, QUrl, mw, QWebEnginePage, QThread, QObject
from ..engine import *
from multiprocessing import Process, Pipe, set_start_method, get_start_method

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
        def fetch_url(url, conn):
            Render(url, conn)

        result = []
        # Parse max no of matches
        maxn = 0
        if m := re.match(r'(.*?)\s*maxn:(\d+)(.*)', query):
            maxn = int(m.group(2))
            if m.group(1) and m.group(3):
                query = f'{m.group(1).strip()} {m.group(3).strip()}'
            else:
                query = m.group(1).strip() if m.group(1) else m.group(3).strip()

        def onload():
            print(f'html: {browser.toHtml()}')

        def cb(val):
            print(f"cb: {val}")

        print("run")
        browser = QWebEnginePage()
        print(f"loading URL {_URL}&q=a.+vertebralis")
        browser.load(QUrl(f'{_URL}&q=a.+vertebralis'))
        from time import time
        t = time()
        print(f'time: {t}')
        while browser.isLoading() and time() - t < 10:
            print('waiting')
            mw.app.processEvents()
        print(f"got html: {browser.toHtml()}")
        print("running js")
        browser.runJavaScript(r"document.innerHTML", resultCallback=cb)
        #print(f'html: {browser.toHtml()}')
        print('setting result')
        result = [Match(title='one', url="urlone"), Match(title='two', url="urltwo")]

        


        #set_start_method("spawn") # Anki already sets it to spawn
        #url = QUrl(f'{_URL}&q=a.+vertebralis')
        #parent, child = Pipe()
        #proc = Process(target=fetch_url, name='headless browser', args=(url, child))
        #proc.start()
        #print(parent.recv())   # prints the HTML of the webpage
        #proc.join()



        #info('main line')
        #p = Process(target=f, args=('bob',), name="headless", group=None, kwargs=())
        #p.start()
        #p.join()

        """print('setting up thread')
        thread = WorkerThread()
        thread.start()
        thread.wait()
        print(f"reading {result}")"""
        
        """for img in imgs:
            title = img.select_one('h3').string
            img.select_one('div.islib')"""
        
        return result


def info(title):
    print(title)
    print('module name:', __name__)
    print('parent process:', os.getppid())
    print('process id:', os.getpid())

def f(name):
    info('function f')
    print('hello', name)


class Render(QWebEnginePage):
    def __init__(self, url, conn):
        self.app = QApplication(sys.argv)
        QWebEnginePage.__init__(self)
        self.html = ''
        self.loadFinished.connect(self._on_load_finished)
        self.load(QUrl(url))
        self.conn = conn
        self.app.exec_()

    def _on_load_finished(self):
        self.toHtml(self.Callable)

    def Callable(self, html_str):
        self.html = html_str
        self.conn.send(html_str)
        self.app.quit()





class WorkerThread(QThread):
    def run(self):
        print("run")
        browser = QWebEnginePage()
        print("setting URL")
        browser.setUrl(QUrl(f'{_URL}&q=a.+vertebralis'))
        print(f'html: {browser.toHtml()}')
        global result
        result = [{'what': 'ever'}, {'what': 'else'}]
