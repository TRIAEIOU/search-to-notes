import requests, re, json, time
from logging import Logger
from bs4 import BeautifulSoup
from . import *

class Google(Engine):
    """Google search engine (BeautifulSoup) implementation"""
    @staticmethod
    def title():
        return "Google (BS)"

    def __init__(self, logger: Logger):
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
        maxn = -1

        return result