import sys
from engines import *
from bs4 import BeautifulSoup
from logging import Logger

log = Logger('rengine')
engine = load()['Google (BS)'](logger=log, application=QApplication(sys.argv),
 config={})

for m in engine.search("a. vertebralis"):
    print(m.url)