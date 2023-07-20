import os
from aqt.utils import Qt
from anki.consts import *

# MISC CONSTANTS
LIST_DLG_HMAX = 500
TERM_ROLE = Qt.ItemDataRole.UserRole + 1

# CONFIG KEYS
GEOMETRY = "Geometry"
SPLITTER = "Splitter pos"
THUMB_HEIGHT = "Thumbnail height"
THUMB_WIDTH = "Thumbnail width"
QUERY_TEMPLATE =  "Query template"
DECK = "Deck ID"
NOTE = "Note type ID"
DIR = "Dir"
TERM = "Term field"
IMAGE = "Image field"
IMGDLG_GEOMETRY = "Image zoom geometry"
ENGINE = "Engine"
IMG_HEIGHT = "Image height"
IMG_WIDTH = "Image width"
DEFAULT_ENGINE = "ddg"
CLOZE_TABLE = "Cloze <table> attributes"
CLOZE_TD = "Cloze <td> attributes"
SC_TERM_UP = "Shortcut previous term"
SC_TERM_DOWN = "Shortcut next term"

# CLOZE NOTE GENERATION
CLOZE_PROMPT_TERM = 1
CLOZE_PROMPT_IMAGE = 2
CLOZE_PROMPTS = [{'prompt': CLOZE_PROMPT_TERM, 'label': 'Term prompt/clozed image(s)'}, {'prompt': CLOZE_PROMPT_IMAGE, 'label': 'Image(s) prompt/clozed term in table'}]

# MISC TEXT/LABELS
DEBUG_FILENAME = "s2n_error_log.txt"
DEBUG_PROMPTEDNAME = "s2n_error_log.prompt"
DIR = os.path.dirname(os.path.realpath(__file__))
ENGINES_DIR = os.path.join(DIR, "engines")
DEBUG_FILE = os.path.join(DIR, DEBUG_FILENAME)
DEBUG_PROMPTED = os.path.join(DIR, DEBUG_PROMPTEDNAME)
TITLE = "Search to notes"
LABEL = "Create notes from web image search"
NO_TITLE = "<none>"
QUERY_LEGEND = '%0: complete term, %1: first tab separated part, ...'
QUERY_TIP = """<b>QUERY TEMPLATE SYNTAX</b><br>
Search terms will be split on tab character and %[digit] in the search query substituted with corresponding segments:
<ul><li>%0 complete term</li>
</li>%1 first segment (i.e. if no tabs present %1 will be the same as %0)</li>
<li>%2 second segment</li>
<li>...</li></ul>
Any %[digit] without correspoding segments will be stripped from the query.<br>
<br>
Example: Search term "a. vertebralis    5" and query "%1 maxn:%2" will result in "a. vertebralis maxn:5" as the searched query.
"""
