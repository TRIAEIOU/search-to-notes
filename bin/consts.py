import os
from aqt.utils import Qt
from anki.consts import *

# MISC CONSTANTS
LIST_DLG_HMAX = 500
TERM_ROLE = Qt.ItemDataRole.UserRole + 1

# CONFIG KEYS
CFG_THUMBH = "Thumbnail height"
CFG_THUMBW = "Thumbnail width"
CFG_TEMPLATE =  "Query template"
CFG_ENGINE = "Engine"
CFG_IMGH = "Image height"
CFG_IMGW = "Image width"
CFG_DEFAULT = "DuckDuckGo (API)"
CFG_CLOZE_TABLE = "Cloze <table> attributes"
CFG_CLOZE_TD = "Cloze <td> attributes"
CFG_SC_PREV = "Shortcut previous term"
CFG_SC_NEXT = "Shortcut next term"
CFG_SC_CLOSE = "Shortcut close"
CFG_LIGHT = "Listview dark mode"
CFG_DARK = "Listview dark mode"

CFG_STATE = "Internal state"
CFG_GEOMETRY = "Geometry"
CFG_SPLITTER = "Splitter pos"
CFG_DECK = "Deck ID"
CFG_NOTE = "Note type ID"
CFG_DIR = "Dir"
CFG_TERM = "Term field"
CFG_IMAGE = "Image field"
CFG_IMGDLG_GEOMETRY = "Image zoom geometry"

# CLOZE NOTE GENERATION
CLOZE_PROMPT_TERM = 1
CLOZE_PROMPT_IMAGE = 2
CLOZE_PROMPTS = [{'prompt': CLOZE_PROMPT_TERM, 'label': 'Term prompt/clozed image(s)'}, {'prompt': CLOZE_PROMPT_IMAGE, 'label': 'Image(s) prompt/clozed term in table'}]

# MISC TEXT/LABELS
DEBUG_FILENAME = "s2n_error_log.txt"
DEBUG_PROMPTEDNAME = "s2n_error_log.prompt"
ADDON_DIR = os.path.dirname(os.path.realpath(__file__))
ENGINES_SUBDIR = "engines"
DEBUG_FILE = os.path.join(ADDON_DIR, DEBUG_FILENAME)
DEBUG_PROMPTED = os.path.join(ADDON_DIR, DEBUG_PROMPTEDNAME)
TITLE = "Search to notes"
LABEL = "Create notes from web image search"
NO_TITLE = "<none>"
QUERY_LEGEND = '<code>%0</code>: complete term, <code>%1</code>: first tab separated part, ...'
QUERY_TIP = """<b>QUERY TEMPLATE SYNTAX</b><br>
Search terms will be split on tab character and <code>%[digit]</code> in the search query substituted with corresponding segments:
<ul><li><code>%0</code>: complete term</li>
</li><code>%1</code> first segment (i.e. if no tabs present <code>%1</code> will be the same as <code>%0</code>)</li>
<li><code>%2</code> second segment</li>
<li>...</li></ul>
Any <code>%[digit]</code> without correspoding segments will be stripped from the query.<br>
<br>
Example: Search term <code>a. vertebralis    5</code> and query <code>%1 maxn:%2</code> will result in <code>a. vertebralis maxn:5</code> as the searched query.
"""
