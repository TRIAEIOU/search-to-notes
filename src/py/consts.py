import os
from aqt.utils import Qt
from anki.consts import *
from .ankiutils import *

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

# CONFIG KEYS
CFG_THUMBH = "Thumbnail height"
CFG_THUMBW = "Thumbnail width"
CFG_TEMPLATE = "Query template"
CFG_ENGINE = "Engine"
CFG_IMGH = "Image height"
CFG_IMGW = "Image width"
CFG_DEFAULT = "Google"
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
