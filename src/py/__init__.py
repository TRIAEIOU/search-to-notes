############################## LICENSE ####################################
# MIT
###########################################################################

############################## CREDITS ####################################
# Credit to Deepan (https://github.com/deepanprabhu) for the DDG api
# implemenation: https://github.com/deepanprabhu/duckduckgo-images-api
###########################################################################

############################### NOTES #####################################
# SEARCH ENGINE IMPLEMENTATION
# Additional search engines are implemented in separate modules in the
# add-on directory. S2N expects the following functions from the engine:
#   def legend() -> str (text to be inserted under query box)
#   def tooltip() -> str (text/HTML to be used as tooltip for the query box)
#   def search(query: str) -> [{'title': <image name>, 'url': <url to image>,
#       'height': <image height>, 'width': <image width>} ...]
###########################################################################
import os, re, codecs, tempfile, requests, base64, importlib, time
from aqt import mw
from aqt.qt import *
from aqt.utils import *
from aqt.operations import CollectionOp, QueryOp
from anki import consts, collection
if qtmajor == 6:
    from . import main_dlg_qt6 as main_dlg, enter_dlg_qt6 as enter_dlg, image_dlg_qt6 as image_dlg, list_dlg_qt6 as list_dlg
elif qtmajor == 5:
    from . import main_dlg_qt5 as main_dlg, enter_dlg_qt5 as enter_dlg, image_dlg_qt5 as image_dlg, list_dlg_qt5 as list_dlg
from . import imghdr

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
S2N_VER = "1.0"
S2N_DEBUG_FILENAME = "s2n_error_log.txt"
S2N_DEBUG_PROMPTEDNAME = "s2n_error_log.prompt"
S2N_DIR = os.path.dirname(os.path.realpath(__file__))
S2N_DEBUG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), S2N_DEBUG_FILENAME)
S2N_DEBUG_PROMPTED = os.path.join(os.path.dirname(os.path.realpath(__file__)), S2N_DEBUG_PROMPTEDNAME)
S2N_TITLE = "Search to notes"
S2N_LABEL = "Create notes from web image search"
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

###########################################################################
# Debug
###########################################################################
import inspect, os, pprint

s2n_log_fh = None
def log(msg):
    global s2n_log_fh
    tm = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    frame = inspect.getouterframes(inspect.currentframe())[1]
    msg = f"\n{tm} [S2N{S2N_VER}/{os.path.basename(frame.filename)}:{frame.lineno} {frame .function}] {msg}"
    if not s2n_log_fh:
        if not os.path.exists(S2N_DEBUG_FILE):
            msg = msg[1:]
        s2n_log_fh = open(S2N_DEBUG_FILE, "a")  
    s2n_log_fh.write(msg)

s2n_log_printer = None
def pp(obj):
    global s2n_log_printer
    if not s2n_log_printer:
        s2n_log_printer = pprint.PrettyPrinter(indent=4)
    return s2n_log_printer.pformat(obj)



###########################################################################
# List dialog window
###########################################################################
class S2N_list_dlg(QDialog):
    def __init__(self, parent, title, text):
        QDialog.__init__(self, parent)
        self.ui = list_dlg.Ui_list_dlg()
        self.ui.setupUi(self)
        self.setWindowTitle(title)
        self.ui.text.setHtml(text)
        sc = QShortcut(QKeySequence('Ctrl+Return'), self)
        sc.activated.connect(self.accept)
        self.show()
        dg = self.geometry()
        dh = dg.height() - self.ui.text.height() + 5
        th = self.ui.text.document().size().height()
        dg.setHeight(dh + th if dh + th < LIST_DLG_HMAX else LIST_DLG_HMAX)
        self.setGeometry(dg)
        self.ui.text.verticalScrollBar().move(0, 0)
        self.ui.text.horizontalScrollBar().move(0, 0)
    

###########################################################################
# Main dialog window
###########################################################################
class S2N_main_dlg(QDialog):
    ############
    # Attributes
    terms = []
    #[{
    #   'term': str,
    #   'query': str,
    #   'matches': [{
    #       'title': str,
    #       'url': str,
    #       'file': str,
    #       'selected': bool
    #   }, ...]
    # }, ...]

    last_dir = ""
    tmp_dir = None
    thumbw = 200
    thumbh = 200
    img_h = -1
    img_w = -1
    cloze_table = ""
    cloze_td = ""
    engine = None

    ###########################################################################
    # Main dialog window constructor
    ###########################################################################
    def __init__(self):
        # Main add-on window
        QDialog.__init__(self, mw)
        self.ui = main_dlg.Ui_main_dlg()
        self.ui.setupUi(self)
        self.setWindowTitle(S2N_TITLE)

        # Main add-on window signals & slots
        self.ui.note.currentTextChanged.connect(self.select_note_type)
        self.ui.enter.clicked.connect(self.enter_terms)
        self.ui.file.clicked.connect(self.select_file)
        self.ui.query_tpl.returnPressed.connect(self.run_query)
        self.ui.search.clicked.connect(self.run_query)
        self.ui.generate.clicked.connect(self.generate_notes)
        self.ui.close.clicked.connect(self.close)
        self.ui.term_lv.currentItemChanged.connect(self.set_current_term)
        self.ui.image_lv.customContextMenuRequested.connect(lambda point: self.zoom_image(self.ui.term_lv.currentRow(), self.ui.image_lv.row(self.ui.image_lv.itemAt(point))) if self.ui.image_lv.itemAt(point) else None)
        sc = QShortcut(QKeySequence('Ctrl+Return'), self)
        sc.activated.connect(self.ui.generate.click)

        # Main window population from collection
        decks = mw.col.decks.all_names_and_ids(skip_empty_default=False, include_filtered=False)
        for deck in decks:
            self.ui.deck.addItem(deck.name, deck.id)
        note_types = mw.col.models.all_names_and_ids()
        for note_type in note_types:
            self.ui.note.addItem(note_type.name, note_type.id)
        self.select_note_type()
        for prompt in CLOZE_PROMPTS:
            self.ui.prompt.addItem(prompt['label'], prompt['prompt'])

        # Image zoom window
        self.image_dlg = QDialog(self)
        self.image_dlg_ui = image_dlg.Ui_image_dlg()
        self.image_dlg_ui.setupUi(self.image_dlg)
        self.image_dlg_ui.gfx.mousePressEvent = self.image_dlg_mousepressevent
        sc = QShortcut(QKeySequence('Return'), self.ui.image_lv)
        sc.activated.connect(lambda: self.zoom_image(self.ui.term_lv.currentRow(), self.ui.image_lv.currentRow()) if self.ui.image_lv.hasFocus() else None)
        sc = QShortcut(QKeySequence('Return'), self.image_dlg)
        sc.activated.connect(lambda: self.image_dlg.close())

        # Load user config and restore states
        self.load_config()
        self.exec()




    ###########################################################################
    # Main dialog window "destructor" - actual destructor too late
    ###########################################################################
    def closeEvent(self, event):
        self.save_config()


    ###########################################################################
    # Load configuration from config Dict (from Anki config file normally)
    ###########################################################################
    def load_config(self):
        config = mw.addonManager.getConfig(__name__)
        engine = f".{DEFAULT_ENGINE}"
        if config.get(ENGINE):
            engine = f".{config[ENGINE]}"
        self.engine = importlib.import_module(engine, package=__name__)
        self.ui.query_legend.setText(QUERY_LEGEND + (f', {self.engine.legend()}' if self.engine.legend() else ''))
        self.ui.query_tpl.setToolTip(QUERY_TIP + (f'<br><br>{self.engine.tooltip()}' if self.engine.tooltip() else ''))

        if config.get(GEOMETRY):
            self.restoreGeometry(base64.b64decode(config[GEOMETRY]))
        if config.get(SPLITTER):
            self.ui.splitter.restoreState(base64.b64decode(config[SPLITTER]))
        if config.get(THUMB_HEIGHT) and config.get(THUMB_WIDTH):
            self.ui.image_lv.setIconSize(QSize(config[THUMB_WIDTH], config[THUMB_HEIGHT]))
        if config.get(DIR):
            self.last_dir = config[DIR]
        if config.get(QUERY_TEMPLATE):
            self.ui.query_tpl.setText(config[QUERY_TEMPLATE])
        if config.get(DECK):
            i = self.ui.deck.findData(config[DECK], flags=Qt.MatchExactly)
            if i != -1:
                self.ui.deck.setCurrentIndex(i)
        if config.get(NOTE):
            i = self.ui.note.findData(config[NOTE], flags=Qt.MatchExactly)
            if i != -1:
                self.ui.note.setCurrentIndex(i)
        if config.get(IMG_HEIGHT):
            self.img_h = config[IMG_HEIGHT]
        if config.get(IMG_WIDTH):
            self.img_w = config[IMG_WIDTH]
        if config.get(CLOZE_TABLE):
            self.cloze_table = config[CLOZE_TABLE]
        if config.get(CLOZE_TD):
            self.cloze_td = config[CLOZE_TD]

        # Fields
        if config.get(TERM):
            i = self.ui.term.findText(config[TERM])
            if i != -1:
                self.ui.term.setCurrentIndex(i)
        if config.get(IMAGE):
            i = self.ui.image.findText(config[IMAGE])
            if i != -1:
                self.ui.image.setCurrentIndex(i)
        if config.get(IMGDLG_GEOMETRY):
            self.image_dlg.restoreGeometry(base64.b64decode(config[IMGDLG_GEOMETRY]))

        # Shortcuts
        if config.get(SC_TERM_UP):
            sc = QShortcut(QKeySequence(config[SC_TERM_UP]), self)
            sc.activated.connect(lambda: self.ui.term_lv.setCurrentRow(self.ui.term_lv.currentRow() - 1) if self.ui.term_lv.currentRow() else None)
        if config.get(SC_TERM_DOWN):
            sc = QShortcut(QKeySequence(config[SC_TERM_DOWN]), self)
            sc.activated.connect(lambda: self.ui.term_lv.setCurrentRow(self.ui.term_lv.currentRow() + 1) if self.ui.term_lv.currentRow() < self.ui.term_lv.count() - 1 else None)



    ###########################################################################
    # Save current configuration to file
    ###########################################################################
    def save_config(self):
        icon_size = self.ui.image_lv.iconSize()
        config = {
            GEOMETRY: base64.b64encode(self.saveGeometry()).decode('utf-8'),
            SPLITTER: base64.b64encode(self.ui.splitter.saveState()).decode('utf-8'),
            THUMB_HEIGHT: icon_size.height(),
            THUMB_WIDTH: icon_size.width(),
            QUERY_TEMPLATE: self.ui.query_tpl.text(),
            DECK: self.ui.deck.currentData(),
            NOTE: self.ui.note.currentData(),
            IMG_HEIGHT: self.img_h,
            IMG_WIDTH: self.img_w,
            CLOZE_TABLE: self.cloze_table,
            CLOZE_TD: self.cloze_td,
            DIR: self.last_dir,
            TERM: self.ui.term.currentText(),
            IMAGE: self.ui.image.currentText(),
            IMGDLG_GEOMETRY: base64.b64encode(self.image_dlg.saveGeometry()).decode('utf-8'),
            ENGINE: self.engine.__name__.rsplit('.', 1)[-1]
        }
        mw.addonManager.writeConfig(__name__, config)


    ###########################################################################
    # Clear/reset terms, matches, deleting temporary image files etc.
    ###########################################################################
    def reset(self):
        self.ui.image_lv.setEnabled(False)
        self.ui.generate.setEnabled(False)
        for term in self.terms:
            for match in term['matches']:
                if match.get('file') and os.path.exists(match['file']):
                    os.remove(match['file'])
        self.terms.clear()
        self.ui.term_lv.clear()
        self.ui.image_lv.clear()




    ###########################################################################
    # Button press to open Open File dialog
    ###########################################################################
    def select_file(self):
        (path, filt) = QFileDialog.getOpenFileName(self, "Select file", self.last_dir, "Text files (*.txt)")
        if path:
            with codecs.open(path, encoding='utf-8') as fh:
                file = fh.read().strip()
            self.reset()
            self.load_terms(file.split('\n'))
            self.last_dir = os.path.dirname(path)


    ###########################################################################
    # Button press to open edit field to enter/paste terms
    ###########################################################################
    def enter_terms(self):
        dlg = QDialog(self)
        ui = enter_dlg.Ui_enter_dlg()
        ui.setupUi(dlg)
        sc = QShortcut(QKeySequence('Ctrl+Return'), dlg)
        sc.activated.connect(lambda: dlg.accept())

        tmp = ""
        for term in self.terms:
            tmp = f"{tmp}{term['term']}\n"
        tmp.rstrip()
        ui.terms.document().setPlainText(tmp)
        dlg.show()
        if dlg.exec_() == 1:
            self.load_terms(ui.terms.document().toPlainText().split('\n'))

    
    ###########################################################################
    # Load list of terms into data structure and setup terms lv
    ###########################################################################
    def load_terms(self, new_terms):
        self.reset()
        if new_terms:
            for term in new_terms:
                sterm = term.strip()
                if sterm:
                    self.terms.append({'term': sterm, 'query': '', 'matches': []})
                    itm = QListWidgetItem(sterm)
                    self.ui.term_lv.addItem(itm)
            self.set_current_term(self.ui.term_lv.item(0), None)


    ###########################################################################
    # Term selected - store old image selection and setup new
    ###########################################################################
    def set_current_term(self, current, previous):
        if self.ui.image_lv.isEnabled():
            # Store previous selection then clear image lv
            self.store_image_selection()
            self.ui.image_lv.clear()

            if current: # If new selected term setup image lv
                index = self.ui.term_lv.row(current)
                for (i, match) in enumerate(self.terms[index]['matches']):
                    if match.get('file'):
                        img_itm = QListWidgetItem(match['title'])
                        img_itm.setData(TERM_ROLE, index)
                        img_itm.setIcon(QIcon(match['file']))
                        img_itm.setToolTip(match['url'])
                        self.ui.image_lv.addItem(img_itm)
                        if i == 0: # Needs to be done before setSeleced to avoid toggle
                            self.ui.image_lv.setCurrentRow(0)
                        img_itm.setSelected(match['selected'])
                    else:
                        print(f">>>>>>>>>>>>>>>>>>>>>No file found for: {match}")
                if self.ui.image_lv.count():
                    self.ui.image_lv.scrollToTop()
                    self.ui.image_lv.setFocus()
                    

    ###########################################################################
    # Term selected - store old image selection and setup new
    ###########################################################################
    def store_image_selection(self):
        for itm in self.ui.image_lv.findItems("*", Qt.MatchWildcard):
            ti = itm.data(TERM_ROLE)
            ii = self.ui.image_lv.row(itm)
            
            # Sanity check for debug
            if ti < 0 or ii < 0:
                log(f"Image_lv index error|ti: {ti}|ii: {ii}|terms: {self.terms}")
            elif ti >= len(self.terms):
                log(f"Image_lv > terms|ti: {ti}|ii: {ii}|terms: {self.terms}")
            elif not 'matches' in self.terms[ti]:
                log(f"Image_lv != terms|ti: {ti}|ii: {ii}|terms: {self.terms[ti]}")
            elif ii >= len(self.terms[ti]['matches']):
                log(f"Image_lv > term matches|ti: {ti}|ii: {ii}|term['matches']: {self.terms[ti]['matches']}")
            elif not 'selected' in self.terms[ti]['matches'][ii]:
                log(f"Match missing selected|ti: {ti}|ii: {ii}|match: {self.terms[ti]['matches'][ii]}")
            else:
                self.terms[ti]['matches'][ii]['selected'] = itm.isSelected()

    ###########################################################################
    # Show zoomed image of supplied term and match index
    ###########################################################################
    def zoom_image(self, term_index, match_index):
        if term_index < self.ui.term_lv.count() and match_index < self.ui.image_lv.count():
            self.image_dlg.setWindowTitle(self.terms[term_index]['matches'][match_index]['title'])
            geom = self.image_dlg.geometry()
            pix = QPixmap(self.terms[term_index]['matches'][match_index]['file']).scaled(geom.width(), geom.height(), Qt.KeepAspectRatio)
            self.image_dlg_ui.gfx.setPixmap(pix)
            self.image_dlg.show()


    ###########################################################################
    # Mouse press handler for image zoom dialog
    ###########################################################################
    def image_dlg_mousepressevent(self, event):
        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
            self.image_dlg.close()
        else:
            super(QLabel, self.image_dlg.gfx).mousePressEvent(event)


    ###########################################################################
    # Set available fields to match selected note type
    ###########################################################################
    def select_note_type(self):
        note_tid = self.ui.note.currentData()
        note = mw.col.models.get(note_tid)
        fields = mw.col.models.field_names(note)
        self.ui.term.clear()
        self.ui.image.clear()
        if note['type'] == consts.MODEL_CLOZE:
            self.ui.term_lbl.setText("Title field")
            self.ui.image_lbl.setText("Cloze field")
            self.ui.term.addItem(NO_TITLE)
            self.ui.prompt_lbl.show()
            self.ui.prompt.show()
            self.ui.title.show()
        else:
            self.ui.term_lbl.setText("Term field")
            self.ui.image_lbl.setText("Image field")
            self.ui.prompt_lbl.hide()
            self.ui.prompt.hide()
            self.ui.title.hide()
        self.ui.term.addItems(fields)
        self.ui.image.addItems(fields)



    ###########################################################################
    # Build query from template and terms into terms
    ###########################################################################
    def build_queries(self, terms, query_template):
        for term in terms:
            # Replace all %0 with complete term
            term['query'] = re.sub(r"(?<!%)%0(?!\d)", term['term'], query_template)
            # Parse term parts and replace corresponding %\d's in query
            parts = term['term'].split('\t')
            for (i, part) in enumerate(parts):
                term['query'] = re.sub(rf"(?<!%)%{str(i + 1)}(?!\d)", part, term['query'])
            # Eat any remaining %\d's
            term['query'] = re.sub(r"(?<!%)%\d+", '', term['query'])
        return terms


    ###########################################################################
    # Run search query and populate term-images
    ###########################################################################
    def run_query(self):
        ###############
        # Function to run network actions in background thread
        def background(col):
            cnt = 0
            for term in self.terms:
                term['matches'] = []
                for search_match in self.engine.search(term['query']):
                    res = requests.get(search_match['url'], stream = True)
                    if res.status_code == 200:
                        res.raw.decode_content = True
                        ext = imghdr.what('', h=res.content)
                        if ext:
                            ext = f".{ext}"
                        else:
                            print(f">>>>>>>>>>>>>>Unable to detect image type for {search_match['url']}")
                            ext = ".jpeg"
                        tmp_file = tempfile.NamedTemporaryFile(suffix=ext, dir=self.tmp_dir.name, delete=False)
                        tmp_file.file.write(res.content)
                        # Debug sanity check
                        if not ('title' in search_match and 'url' in search_match and 'height' in search_match and 'width' in search_match):
                            log(f"Search match key error|search_match: {search_match}")
                        else:
                            term['matches'].append({'title': search_match['title'], 'url': search_match['url'], 'height': search_match['height'], 'width': search_match['width'], 'file': tmp_file.name, 'selected': False})
                        cnt += 1
                    else:
                        log(f"Non-200 return|search_match: {search_match}")

            return type('obj', (object,), {'changes' : collection.OpChanges, 'count': cnt})()

        ###############
        # Run when background thread finishes - update GUI
        def finished(result):
            self.ui.generate.setEnabled(True)
            if self.ui.term_lv.currentRow() == 0:
                self.ui.term_lv.setCurrentRow(-1)
            self.ui.image_lv.setEnabled(True)
            self.ui.term_lv.setCurrentRow(0)

        ###############
        # Root run_query code
        if self.tmp_dir:
            self.tmp_dir.cleanup()
        self.tmp_dir = tempfile.TemporaryDirectory()
        if len(self.terms):
            self.terms = self.build_queries(self.terms, self.ui.query_tpl.text())
            queries = '<b>Run the following queries?</b><br><table style="border: 1px solid black; border-collapse: collapse;" width="100%">'
            for term in self.terms:
                queries += f'<tr><td style="border: 1px solid black; padding: 5px; white-space:nowrap;">{term["term"]}</td><td style="border: 1px solid black; padding: 5px;" width="100%">{term["query"]}</td></tr>'
            queries += '</table>'

            dlg = S2N_list_dlg(self, "Run search query", queries)
            dlg.ui.buttonBox.addButton(QDialogButtonBox.Cancel)
            if dlg.exec() == 1:
                bgop = CollectionOp(parent=mw, op=background)
                bgop.success(finished)
                bgop.failure(finished)
                bgop.run_in_background()
    #           QueryOp(parent=self, op=lambda col: background_query(self, self.ui.query_tpl.text())).success(background_query_finished).with_progress().run_in_background() # Doesn't work until 2.1.50




    ###########################################################################
    # Generate notes from term-images
    ###########################################################################
    def generate_notes(self):
        self.store_image_selection() # To store last selections
        deck = self.ui.deck.currentData()
        note_type_id = self.ui.note.currentData()
        prompt = self.ui.prompt.currentData()
        term_fld = self.ui.term.currentText()
        image_fld = self.ui.image.currentText()
        title = self.ui.title.text()

        ###############
        # Function for running note generation in background thread
        def background(col):
             # Calculate how to scale image
            def scale_img(cw, ch, w, h):
                if (cw < 0 or w <= cw) and (ch < 0 or h <= ch):
                    return None
                rw = cw/w
                rh = ch/h
                return (cw, h*rw) if rw < rh else (w*rh, ch)

            note_type = col.models.get(note_type_id)
            cnt = 0
            skipped = []
            changes = collection.OpChanges

            # Generate cloze style note
            if note_type['type'] == consts.MODEL_CLOZE:
                if self.terms:
                    content = ""
                    for term in self.terms:
                        s_matches = []
                        images = ""
                        for match in term['matches']:
                            if(match['selected']):
                                s_matches.append(match)
                        if s_matches:
                            cnt += 1
                            for match in s_matches:
                                file = mw.col.media.add_file(match['file'])
                                dim = scale_img(self.img_w, self.img_h, match['width'], match['height'])
                                dim = f' width="{dim[0]}" height="{dim[1]}"' if dim else ""
                                images += f'<img src="{file}"{dim}><br>'                            
                            if prompt == CLOZE_PROMPT_TERM:
                                content += f'{term["term"]}: {{{{c{str(cnt)}::{images[:-4]}}}}}<br>'
                            else:
                                content += f'<tr><td {self.cloze_td}>{images[:-4]}</td><td {self.cloze_td}>{{{{c{str(cnt)}::{term["term"]}}}}}</td></tr>'
                        else: # No matches or no selected matches
                            skipped.append(term['term'])
                    if content:
                        note = mw.col.new_note(note_type)
                        if prompt == CLOZE_PROMPT_IMAGE:
                            content = f"<table {self.cloze_table}>{content}</table>"
                        if term_fld != NO_TITLE:
                            note[term_fld] = title
                        note[image_fld] = content
                        changes = mw.col.add_note(note, deck)

            # Generate regular style note
            else:
                for term in self.terms:
                    if term['matches']:
                        note = mw.col.new_note(note_type)
                        note[term_fld] = term['term']
                        for match in term['matches']:
                            if(match['selected']):
                                file = mw.col.media.add_file(match['file'])
                                dim = scale_img(self.img_w, self.img_h, match['width'], match['height'])
                                dim = f' width="{dim[0]}" height="{dim[1]}"' if dim else ""
                                note[image_fld] += f'<img src="{file}"{dim}>'
                        if note[image_fld]:
                            changes = mw.col.add_note(note, deck)
                            cnt += 1
                        else:  # No selected matches for term
                            skipped.append(term['term'])
                    else: # No matches for term
                        skipped.append(term['term'])

            return type('obj', (object,), {'changes' : changes, 'skipped': skipped, 'count': cnt, 'note_type': note_type['type']})()
        
        ###########################################################################
        # Run when background thread finishes - show result
        def finished(result):
            note_str = "cloze" if result.note_type == consts.MODEL_CLOZE else "note"
            msg = f'<b>Note generation finished</b><br>{result.count} {note_str}(s) generated.</div>'
            if result.skipped:
                skipped = ""
                msg += '<br><br><b>Items skipped</b><br>No notes generated for the following search terms (no search matches or no matches selected):<br><br>'
                for term in result.skipped:
                    msg += f"{term}<br>\n"
                    skipped += f"{term}\n"
                    skipped.rstrip()
            dlg = S2N_list_dlg(self, S2N_TITLE, msg)
            if result.skipped:
                copy = dlg.ui.buttonBox.addButton('Copy skipped to clipboard', QDialogButtonBox.ButtonRole.ApplyRole)
                copy.clicked.connect(lambda: QApplication.clipboard().setText(skipped))
            dlg.exec()

        ###############
        # Root generate_notes code
        # Run note generation in background thread, get Qt info before bg thread launch
        bgop = CollectionOp(parent=mw, op=background)
        bgop.success(finished)
        bgop.failure(finished)
        bgop.run_in_background()
        


###########################################################################
# Add on start up
###########################################################################
action = QAction(S2N_LABEL, mw)
action.triggered.connect(lambda: S2N_main_dlg())
mw.form.menuTools.addAction(action)

# Ask user to post debug log 
if os.path.exists(S2N_DEBUG_FILE) and (not os.path.exists(S2N_DEBUG_PROMPTED) or os.path.getmtime(S2N_DEBUG_FILE) > os.path.getmtime(S2N_DEBUG_PROMPTED)):
    showInfo(f'Search to notes add-on has detected an error log, consider reviewing it for any privacy concerns and then post the contents to the add-on support thread (https://forums.ankiweb.net/t/search-to-notes-support-thread/16286) to help the author and other users. The debuglog can be found here: "{S2N_DEBUG_FILE}".')
    with open(S2N_DEBUG_PROMPTED, "w") as fh:
        fh.write(time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(time.ctime(os.path.getmtime(S2N_DEBUG_FILE)))))
