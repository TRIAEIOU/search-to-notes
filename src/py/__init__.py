"""
Search to notes main application
"""
import os, re, codecs, tempfile, requests, base64, importlib, time, logging
from dataclasses import dataclass
from aqt import mw
from aqt.qt import *
from aqt.utils import *
from aqt.operations import CollectionOp, QueryOp
from anki import consts, collection
from .consts import *
from .engines import *
from .ankiutils import *

if qtmajor == 6:
    from . import maindialog_qt6 as ui_maindialog, enterdialog_qt6 as ui_enterdialog, imagedialog_qt6 as ui_imagedialog, listdialog_qt6 as ui_listdialog
elif qtmajor == 5:
    from . import maindialog_qt5 as ui_maindialog, enterdialog_qt5 as ui_enterdialog, imagedialog_qt5 as ui_imagedialog, listdialog_qt5 as ui_listdialog
from . import imghdr

CVER = get_version()
NVER = "1.1.0"

class ListDialog(QDialog):
    """
    List  dialog window - to input search terms
    """
    def __init__(self, parent, title, text):
        QDialog.__init__(self, parent)
        self.ui = ui_listdialog.Ui_ListDialog()
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



class MainDialog(QDialog):
    """
    Main window
    """
    logger = logging.getLogger('S2N')
    terms: list[Term] = []
    last_dir = ""
    tmp_dir: str = None
    thumbw = 200
    thumbh = 200
    img_h = -1
    img_w = -1
    cloze_table = ""
    cloze_td = ""
    engine: Engine = None

    def __init__(self):
        """
        Main add-on window
        """
        QDialog.__init__(self, mw)
        self.ui = ui_maindialog.Ui_MainDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(TITLE)

        # Signals & slots
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
        self.img_dlg = QDialog(self)
        self.img_dlg_ui = ui_imagedialog.Ui_ImageDialog()
        self.img_dlg_ui.setupUi(self.img_dlg)
        self.img_dlg_ui.gfx.mousePressEvent = self.img_dlg_mousepressevent
        sc = QShortcut(QKeySequence('Return'), self.ui.image_lv)
        sc.activated.connect(lambda: self.zoom_image(self.ui.term_lv.currentRow(), self.ui.image_lv.currentRow()) if self.ui.image_lv.hasFocus() else None)
        sc = QShortcut(QKeySequence('Return'), self.img_dlg)
        sc.activated.connect(lambda: self.img_dlg.close())

        # Load user config and restore states
        self.load_config()
        self.exec()


    def closeEvent(self, event):
        """
        Main dialog window "destructor" - actual destructor too late
        """
        self.save_config()


    def load_config(self):
        """
        Load configuration from config Dict (from Anki config file normally)
        """
        config = mw.addonManager.getConfig(__name__)
        self.engine = engines.get(config.get(ENGINE, DEFAULT_ENGINE), DEFAULT_ENGINE)(self.logger)
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
            i = self.ui.deck.findData(config[DECK], flags=Qt.MatchFlag.MatchExactly)
            if i != -1:
                self.ui.deck.setCurrentIndex(i)
        if config.get(NOTE):
            i = self.ui.note.findData(config[NOTE], flags=Qt.MatchFlag.MatchExactly)
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
            self.img_dlg.restoreGeometry(base64.b64decode(config[IMGDLG_GEOMETRY]))

        # Shortcuts
        if config.get(SC_TERM_UP):
            sc = QShortcut(QKeySequence(config[SC_TERM_UP]), self)
            sc.activated.connect(lambda: self.ui.term_lv.setCurrentRow(self.ui.term_lv.currentRow() - 1) if self.ui.term_lv.currentRow() else None)
        if config.get(SC_TERM_DOWN):
            sc = QShortcut(QKeySequence(config[SC_TERM_DOWN]), self)
            sc.activated.connect(lambda: self.ui.term_lv.setCurrentRow(self.ui.term_lv.currentRow() + 1) if self.ui.term_lv.currentRow() < self.ui.term_lv.count() - 1 else None)

    def save_config(self):
        """
        Save current configuration to file
        """
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
            IMGDLG_GEOMETRY: base64.b64encode(self.img_dlg.saveGeometry()).decode('utf-8'),
            ENGINE: self.engine.title()
        }
        mw.addonManager.writeConfig(__name__, config)

    def reset(self):
        """
        Clear/reset terms, matches, deleting temporary image files etc.
        """
        self.ui.image_lv.setEnabled(False)
        self.ui.generate.setEnabled(False)
        self.terms.clear()
        self.ui.term_lv.clear()
        self.ui.image_lv.clear()

    def select_file(self):
        """
        Button press to open Open File dialog
        """
        (path, filt) = QFileDialog.getOpenFileName(self, "Select file", self.last_dir, "Text files (*.txt)")
        if path:
            with codecs.open(path, encoding='utf-8') as fh:
                file = fh.read().strip()
            self.reset()
            self.load_terms(file.split('\n'))
            self.last_dir = os.path.dirname(path)

    def enter_terms(self):
        """
        Button press to open edit field to enter/paste terms
        """
        dlg = QDialog(self)
        ui = ui_enterdialog.Ui_EnterDialog()
        ui.setupUi(dlg)
        QShortcut(QKeySequence('Ctrl+Return'), dlg).activated.connect(lambda: dlg.accept())
        ui.terms.document().setPlainText("\n".join([t.term for t in self.terms]))
        if dlg.exec() == 1:
            self.load_terms(ui.terms.document().toPlainText().split('\n'))

    def load_terms(self, new_terms: list[str]):
        """
        Load list of terms into data structure and setup terms lv
        """
        self.reset()
        for term in [t.strip() for t in new_terms if t]:
            self.terms.append(Term(term=term))
            self.ui.term_lv.addItem(term)
        self.set_current_term(self.ui.term_lv.item(0), None)

    def set_current_term(self, current, previous):
        """
        Term selected - store old image selection and setup new
        """
        if self.ui.image_lv.isEnabled():
            # Store previous selection then clear image lv
            self.store_image_selection()
            self.ui.image_lv.clear()

            if current: # If new selected term setup image lv
                i = self.ui.term_lv.row(current)
                for (ii, match) in enumerate(self.terms[i].matches):
                    if match.file:
                        img_itm = QListWidgetItem(match.title)
                        img_itm.setData(TERM_ROLE, i)
                        img_itm.setIcon(QIcon(match.file))
                        img_itm.setToolTip(match.url)
                        self.ui.image_lv.addItem(img_itm)
                        if ii == 0: # Needs to be done before setSeleced to avoid toggle
                            self.ui.image_lv.setCurrentRow(0)
                        img_itm.setSelected(match.selected)
                    else:
                        self.logger.warning(f"No file found for: {match}")
                if self.ui.image_lv.count():
                    self.ui.image_lv.scrollToTop()
                    self.ui.image_lv.setFocus()
                    

    def store_image_selection(self):
        """
        Store image selection
        """
        for itm in self.ui.image_lv.findItems("*", Qt.MatchWildcard):
            ti = itm.data(TERM_ROLE)
            ii = self.ui.image_lv.row(itm)
            
            # Sanity checks for debug
            if ti < 0 or ii < 0:
                self.logger.warning(f"Image_lv index error|ti: {ti}|ii: {ii}|terms: {self.terms}")
            elif ti >= len(self.terms):
                self.logger.warning(f"Image_lv > terms|ti: {ti}|ii: {ii}|terms: {self.terms}")
            elif ii >= len(self.terms[ti].matches):
                self.logger.warning(f"Image_lv > term matches|ti: {ti}|ii: {ii}|term.matches: {self.terms[ti].matches}")
            else:
                self.terms[ti].matches[ii].selected = itm.isSelected()

    def zoom_image(self, term_index, match_index):
        """
        Show zoomed image of supplied term and match index
        """
        if term_index < self.ui.term_lv.count() and match_index < self.ui.image_lv.count():
            self.img_dlg.setWindowTitle(self.terms[term_index].matches[match_index].title)
            geom = self.img_dlg.geometry()
            self.img_dlg_ui.gfx.setPixmap(
                QPixmap(self.terms[term_index].matches[match_index].file)
                .scaled(geom.width(), geom.height(), Qt.KeepAspectRatio)
            )
            self.img_dlg.show()


    def img_dlg_mousepressevent(self, event):
        """
        Mouse press handler for image zoom dialog
        """
        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
            self.img_dlg.close()
        else:
            super(QLabel, self.img_dlg.gfx).mousePressEvent(event)


    def select_note_type(self):
        """
        Set available fields to match selected note type
        """
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

    def run_query(self):
        """
        Run search query and populate term-images
        """
        def background(col, template):
            """
            Function to run network actions in background thread
            """
            cnt = 0
            for term in self.terms:
                term.matches = []
                matches = self.engine.search(term.query(template))
                if matches is None:
                    msg = f'{self.engine.title()} search for "{term.query(template)}" returned None'
                    self.logger.warning(msg)
                    raise Exception(msg)
                else:
                    for match in matches:
                        res = requests.get(match.url, stream = True)
                        if res.status_code == 200:
                            res.raw.decode_content = True
                            ext = imghdr.what('', h=res.content)
                            if ext:
                                ext = f".{ext}"
                            else:
                                self.logger.warning(f"Unable to detect image type for {match.url}")
                                ext = ".jpeg"
                            tmp = tempfile.NamedTemporaryFile(suffix=ext, dir=self.tmp_dir.name, delete=False)
                            tmp.file.write(res.content)
                            # Debug sanity check
                            if match.title == None or match.url == None:
                                self.logger.warning(f"Search match key error|match: {match}")
                            else:
                                match.file = tmp.name
                                term.matches.append(match)
                            cnt += 1
                        else:
                            self.logger.info(f"Non-200 return|match: {match}")

            return type('obj', (object,), {'changes' : collection.OpChanges, 'count': cnt})()

        def finished(result):
            """
            Run when background thread finishes - update GUI
            """
            self.ui.generate.setEnabled(True)
            if self.ui.term_lv.currentRow() == 0: self.ui.term_lv.setCurrentRow(-1)
            self.ui.image_lv.setEnabled(True)
            self.ui.term_lv.setCurrentRow(0)

        # Root run_query code
        if self.tmp_dir: self.tmp_dir.cleanup()
        self.tmp_dir = tempfile.TemporaryDirectory()
        template = self.ui.query_tpl.text()
        if len(self.terms):
            html = '<b>Run the following queries?</b><br><table style="border: 1px solid black; border-collapse: collapse;" width="100%">'
            for term in self.terms:
                html += f'<tr><td style="border: 1px solid black; padding: 5px; white-space:nowrap;">{term.term}</td><td style="border: 1px solid black; padding: 5px;" width="100%">{term.query(template)}</td></tr>'
            html += '</table>'

            dlg = ListDialog(self, "Run search query", html)
            dlg.ui.buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
            if dlg.exec() == 1:
                #bgop = CollectionOp(parent=mw, op=background)
                #bgop.success(finished)
                #bgop.failure(finished)
                #bgop.run_in_background()
                QueryOp(parent=self, op=lambda col: background(self, template), success=finished).with_progress().run_in_background()


    def generate_notes(self):
        """
        Generate notes from term-images
        """
        self.store_image_selection() # To store last selections
        deck = self.ui.deck.currentData()
        note_type_id = self.ui.note.currentData()
        prompt = self.ui.prompt.currentData()
        term_fld = self.ui.term.currentText()
        image_fld = self.ui.image.currentText()
        title = self.ui.title.text()

        def background(col):
            """
            Function for running note generation in background thread
            """
            def scale_img(match: Match):
                """
                Calculate how to scale image
                """
                if (self.img_w < 0 or match.width <= self.img_w) and (self.img_h < 0 or match.height <= self.img_h):
                    return None
                rw = self.img_w/match.width
                rh = self.img_h/match.height
                return (self.img_w, match.height*rw) if rw < rh else (match.width*rh, self.img_h)
            
            def clozes(terms: list[Term], note_t):
                """
                Generate cloze type note from terms
                """
                content = ""
                cnt = 0
                changes = []
                skipped = []
                for term in self.terms:
                    if matches := [m for m in term.matches if m.selected]:
                        cnt += 1
                        images = ""
                        for match in matches:
                            file = mw.col.media.add_file(match.file)
                            dim = scale_img(match)
                            dim = f' width="{dim[0]}" height="{dim[1]}"' if dim else ""
                            images += f'<img src="{file}"{dim}><br>'                            
                        if prompt == CLOZE_PROMPT_TERM:
                            content += f'{term.term}: {{{{c{str(cnt)}::{images[:-4]}}}}}<br>'
                        else:
                            content += f'<tr><td {self.cloze_td}>{images[:-4]}</td><td {self.cloze_td}>{{{{c{cnt}::{term.term}}}}}</td></tr>'
                    else: # No matches or no selected matches
                        skipped.append(term.term)
                if content:
                    note = mw.col.new_note(note_t)
                    if prompt == CLOZE_PROMPT_IMAGE:
                        content = f"<table {self.cloze_table}>{content}</table>"
                    if term_fld != NO_TITLE:
                        note[term_fld] = title
                    note[image_fld] = content
                    # Fixme: correct way to store changes
                    changes.append(mw.col.add_note(note, deck))
                
                return (cnt, changes, skipped)

            def standards(terms: list[Term], note_t):
                """Generate standard notes from terms"""
                cnt = 0
                changes = []
                skipped = []
                for term in self.terms:
                    if matches := [m for m in term.matches if m.selected]:
                        note = mw.col.new_note(note_t)
                        note[term_fld] = term.term
                        for match in matches:
                            file = mw.col.media.add_file(match.file)
                            dim = scale_img(match)
                            dim = f' width="{dim[0]}" height="{dim[1]}"' if dim else ""
                            note[image_fld] += f'<img src="{file}"{dim}>'
                        if note[image_fld]:
                            # Fixme: correct way to store changes
                            changes.append(mw.col.add_note(note, deck))
                            cnt += 1
                        else:  # No selected matches for term
                            skipped.append(term.term)
                    else: # No matches or no selected matches
                        skipped.append(term.term)
                
                return (cnt, changes, skipped)

            ###
            note_type = col.models.get(note_type_id)
            if note_type['type'] == consts.MODEL_CLOZE:
                (cnt, changes, skipped) = clozes(self.terms, note_type)
            else:
                (cnt, changes, skipped) = standards(self.terms, note_type)

            return type('obj', (object,), {'changes' : collection.OpChanges, 'skipped': skipped, 'count': cnt, 'note_type': note_type['type']})()
        
        def finished(result):
            """
            Run when background thread finishes - show result
            """
            note_str = "cloze" if result.note_type == consts.MODEL_CLOZE else "note"
            msg = f'<b>Note generation finished</b><br>{result.count} {note_str}(s) generated.</div>'
            if result.skipped:
                skipped = ""
                msg += '<br><br><b>Items skipped</b><br>No notes generated for the following search terms (no search matches or no matches selected):<br><br>'
                for term in result.skipped:
                    msg += f"{term}<br>\n"
                    skipped += f"{term}\n"
                    skipped.rstrip()
            dlg = ListDialog(self, TITLE, msg)
            if result.skipped:
                copy = dlg.ui.buttonBox.addButton('Copy skipped to clipboard', QDialogButtonBox.ButtonRole.ApplyRole)
                copy.clicked.connect(lambda: QApplication.clipboard().setText(skipped))
            dlg.exec()

        ###
        bgop = CollectionOp(parent=mw, op=background)
        bgop.success(finished)
        bgop.failure(finished)
        bgop.run_in_background()
        


###########################################################################
# Add on start up
action = QAction(LABEL, mw)
action.triggered.connect(lambda: MainDialog())
mw.form.menuTools.addAction(action)
# Load engines
engines = load()

if strvercmp(CVER, NVER) < 0:
    set_version(NVER)

# Ask user to post debug log 
if os.path.exists(DEBUG_FILE) and (not os.path.exists(DEBUG_PROMPTED) or os.path.getmtime(DEBUG_FILE) > os.path.getmtime(DEBUG_PROMPTED)):
    showInfo(f'Search to notes add-on has detected an error log, consider reviewing it for any privacy concerns and then post the contents to the add-on support thread (https://forums.ankiweb.net/t/search-to-notes-support-thread/16286) to help the author and other users. The debuglog can be found here: "{DEBUG_FILE}".')
    with open(DEBUG_PROMPTED, "w") as fh:
        fh.write(time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(time.ctime(os.path.getmtime(DEBUG_FILE)))))
