############################## LICENSE ####################################
# MIT
###########################################################################

############################## CREDITS ####################################
# Credit to Deepan (https://github.com/deepanprabhu) for the DDG api
# implemenation: https://github.com/deepanprabhu/duckduckgo-images-api
###########################################################################

############################### NOTES #####################################
# https://help.duckduckgo.com/duckduckgo-help-pages/results/syntax/ doesn't
# seem to work, only these: [exact term]", +/-[term], site:[url]
# Additional modifier maxn:\d implemented
###########################################################################
import requests
import re
import json
import time

DDG = 'https://duckduckgo.com/'

def legend():
    return '"[exact term]", +/-[term], site:[url], maxn:[max results]'

def tooltip():
    return """<b>SEARCH ENGINE SYNTAX</b>
<ul><li>cats dogs => cats or dogs in results</li>
<li>"cats and dogs" => Exact term "cats and dogs" in results</li>
<li>cats -dogs => Fewer dogs in results</li>
<li>cats +dogs => More dogs in results</li>
<li>site:commons.wikimedia.org => Only results from commons.wikimedia.org</li>
<li>intitle:anki => Only results with page title including "anki"</li>
<li>maxn:10 => Only first 10 results (default all)</li></ul>"""

def search(query):
    result = []
    # Parse max no of matches                
    maxn = -1
    maxn_match = re.fullmatch(r"(^|(.*?)\s)maxn:(\d+)($|(\s.*))", query)
    if maxn_match:
        maxn = int(maxn_match.group(3))
        query = maxn_match.group(2) if maxn_match.group(2) else ""
        query += maxn_match.group(5) if maxn_match.group(5) else ""
    params = { 'q': query }
    post = requests.post(DDG, data=params)
    res = re.search(r'vqd=([\d-]+)\&', post.text, re.M | re.I)
    if not res:
        return None
    vqd = res.group(1)

    headers = {
        'authority': 'duckduckgo.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'sec-fetch-dest': 'empty',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'referer': 'https://duckduckgo.com/',
        'accept-language': 'en-US,en;q=0.9',
    }
    params = (
        ('l', 'us-en'),
        ('o', 'json'),
        ('q', query),
        ('vqd', vqd),
        ('f', ',,,'),
        ('p', '1'),
        ('v7exp', 'a'),
    )

    request = DDG + "i.js"
    while True:
        while True:
            try:
                res = requests.get(request, headers=headers, params=params)
                data = json.loads(res.text)
                break
            except ValueError as e:
                time.sleep(1)
        for item in data['results']:
            result.append({
                'title': item['title'],
                'url' : item['image'],
                'width': item['width'],
                'height': item['height']
                #'thumbnail url': item['thumbnail'],
                #'source': item['source']
            })
            maxn -= 1
            if maxn == 0:
                break
        if maxn == 0 or 'next' not in data:
            break
        request = DDG + data['next']
    return result
