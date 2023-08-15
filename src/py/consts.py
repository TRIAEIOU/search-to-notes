import os
from aqt.utils import Qt
from anki.consts import *

# MISC CONSTANTS
LIST_DLG_HMAX = 500
TERM_ROLE = Qt.ItemDataRole.UserRole + 1

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
CLOZE_PROMPTS = [
    {
        'prompt': CLOZE_PROMPT_TERM,
        'label': 'Term prompt/clozed image(s)'
    }, {
        'prompt': CLOZE_PROMPT_IMAGE,
        'label': 'Image(s) prompt/clozed term in table'
    }
]
STR_DECK_TIP = 'Deck to insert generated notes in.'
STR_TYPE_TIP = 'Which type of note to generate.'
STR_TERM_LBL = 'Term field'
STR_TERM_TIP = 'Note field into which the search term should be inserted.'
STR_IMG_LBL = 'Image field'
STR_IMG_TIP = 'Note field into which the selected images should be inserted.'
STR_TITLE_FLD_LBL = 'Title field'
STR_TITLE_FLD_TIP = 'Note field into which the title (configured on right) should be inserted. Select <code>&lt;none&gt;</code> for no title insertion.'
STR_TITLE_TIP = 'Title to insert in supplied field (configured on left).'
STR_CLOZE_LBL = 'Cloze field'
STR_CLOZE_TIP = 'Field to insert the clozes and their respective prompt in (configured on left).'
STR_PROMPT_TIP = 'Whether to use search term as "prompt" and images as "answers" (in cloze)<ul><li><code>Term prompt/clozed image(s)</code>: Each search term will be followed by a cloze containing the selected images.</li><li><code>Image(s) prompt/clozed term in table</code>: Generates a table with one row per search term. All selected images will be visible in the left column and the search term will be inside a cloze in the right column.</li></ul>'

# MISC STRINGS
STR_SELECT_TITLE = 'Select file'
STR_SELECT_FILTER = 'Text files (*.txt)'
STR_RUN_CONFIRM_TEXT = 'Run the following queries?'
STR_RUN_CONFIRM_TITLE = 'Run search query'
STR_QUERY_IMGS = 'Getting images...'
STR_QUERY_SEARCH = 'Searching %(query)s...'
STR_MATCH_NONE = '%(engine)s search for "%(query)s" returned None, search engine plugin broken?'
STR_DOWNLOADING = 'Downloading `%(url)s`...'
STR_DL_SKIPPED = 'The following images were found but not downloaded'
STR_GEN_FINISHED = '<b>Note generation finished</b><br>%(count)d %(type)s(s) generated.</div>'
STR_GEN_SKIPPED = '<b>Items skipped</b><br>No notes generated for the following search terms (no search matches or no matches selected):'
STR_SKIPPED_COPY = 'Copy skipped to clipboard'
STR_PROMPT_LOG = f'Search to notes add-on has detected an error log, consider reviewing it for any privacy concerns and then post the contents to the add-on support thread (https://forums.ankiweb.net/t/search-to-notes-support-thread/16286) to help the author and other users. The debuglog can be found here: "{DEBUG_FILE}".'

