"""
Search to notes main application
"""
import os, codecs, tempfile, requests, base64, time, logging, ssl, subprocess
from collections import OrderedDict
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util.ssl_ import create_urllib3_context
from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import *
from aqt.operations import CollectionOp
from anki import consts, collection
from .consts import *
from .engine import *
from .ankiutils import *
from .translations import translations

if sys.platform == 'win32' or sys.platform == 'cygwin':
    CURL = "curl.exe" if shutil.which('curl.exe') else None
else:
    CURL = "curl" if shutil.which('curl') else None

if qtmajor == 6:
    from . import mainwindow_qt6 as ui_mainwindow, enterdialog_qt6 as ui_enterdialog, imagedialog_qt6 as ui_imagedialog, listdialog_qt6 as ui_listdialog
elif qtmajor == 5:
    from . import mainwindow_qt5 as ui_mainwindow, enterdialog_qt5 as ui_enterdialog, imagedialog_qt5 as ui_imagedialog, listdialog_qt5 as ui_listdialog
from . import imghdr

CVER = get_version()
NVER = "1.2.0"
engines: dict[str, Engine]

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



class MainWindow(QMainWindow):
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
    engines: list[Engine] = None
    engine: Engine = None

    def __init__(self):
        """
        Main add-on window
        """
        super().__init__(None, Qt.WindowType.Window)
        self.ui = ui_mainwindow.Ui_mainwindow()
        self.ui.setupUi(self)
        self.setWindowTitle(t('Search to notes'))

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
        self.ui.deck.setToolTip(t('Deck to insert generated notes in.'))
        for deck in mw.col.decks.all_names_and_ids(
            skip_empty_default=False,
            include_filtered=False
        ):
            self.ui.deck.addItem(deck.name, deck.id)
        self.ui.note.setToolTip(t('Which type of note to generate.'))
        for note_type in mw.col.models.all_names_and_ids():
            self.ui.note.addItem(note_type.name, note_type.id)
        self.select_note_type()
        self.ui.prompt.addItem(
            t('Term prompt/clozed image(s)'),
            CLOZE_PROMPT_TERM
        )
        self.ui.prompt.addItem(
            t('Image(s) prompt/clozed term in table'),
            CLOZE_PROMPT_IMAGE
        )

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
        self.show()
        #self.exec()


    def closeEvent(self, event):
        """
        Main dialog window "destructor" - actual destructor too late
        """
        self.save_state()


    def load_config(self):
        """
        Load configuration
        """
        config = mw.addonManager.getConfig(__name__)

        # Setup engines
        self.engines = load_engines()
        self.engine = self.engines[config.get(CFG_ENGINE, CFG_DEFAULT)](self.logger, config)
        self.ui.query_legend.setText(
            (f'{self.engine.title()}: ' if self.engine.title() else '') +
            t('<code>%0</code>: complete term, <code>%1</code>: first tab separated part, ...') +
            (f', {self.engine.legend()}' if self.engine.legend() else '')
        )
        self.ui.query_tpl.setToolTip(
            (f'{self.engine.title()}: ' if self.engine.title() else '') +
            t(
                '<b>QUERY TEMPLATE SYNTAX</b><br>'
                'Search terms will be split on tab character and <code>%[digit]</code> in the search query substituted with corresponding segments:'
                '<ul><li><code>%0</code>: complete term</li>'
                '<li><code>%1</code> first segment (i.e. if no tabs present <code>%1</code> will be the same as <code>%0</code>)</li>'
                '<li><code>%2</code> second segment</li>'
                '<li>...</li></ul>'
                'Any <code>%[digit]</code> without correspoding segments will be stripped from the query.<br><br>'
                'Example: Search term <code>a. vertebralis    5</code> and query <code>%1 maxn:%2</code> will result in <code>a. vertebralis maxn:5</code> as the searched query.'
            ) +
            (f'<br><br>{self.engine.tooltip()}' if self.engine.tooltip() else '')
        )

        # Icon sizes
        self.iconw = config.get(CFG_THUMBW, 200)
        self.iconh = config.get(CFG_THUMBH, 200)
        self.ui.image_lv.setIconSize(QSize(self.iconw, self.iconh))

        # Image size
        if v := config.get(CFG_IMGH):
            self.img_h = v
        if v := config.get(CFG_IMGW):
            self.img_w = v
        
        # Cloze formating
        if v := config.get(CFG_CLOZE_TABLE):
            self.cloze_table = v
        if v := config.get(CFG_CLOZE_TD):
            self.cloze_td = v

        # Shortcuts
        if v := config.get(CFG_SC_PREV):
            sc = QShortcut(QKeySequence(v), self)
            sc.activated.connect(
                lambda: self.ui.term_lv.setCurrentRow(
                    self.ui.term_lv.currentRow() - 1
                ) if self.ui.term_lv.currentRow() else None
            )
        if v := config.get(CFG_SC_NEXT):
            sc = QShortcut(QKeySequence(v), self)
            sc.activated.connect(
                lambda: self.ui.term_lv.setCurrentRow(
                    self.ui.term_lv.currentRow() + 1
                ) if self.ui.term_lv.currentRow() < self.ui.term_lv.count() - 1 else None
            )
        if v := config.get(CFG_SC_CLOSE):
            sc = QShortcut(QKeySequence(v), self)
            sc.activated.connect(self.close)

        # Styling
        if theme_manager.night_mode:
            self.ui.image_lv.setStyleSheet(config[CFG_DARK])
        else:
            self.ui.image_lv.setStyleSheet(config[CFG_LIGHT])

        # Internal state
        state = config[CFG_STATE]
        if v := state[CFG_GEOMETRY]:
            self.restoreGeometry(base64.b64decode(v))
        if v := state[CFG_SPLITTER]:
            self.ui.splitter.restoreState(base64.b64decode(v))
        if v := state[CFG_IMGDLG_GEOMETRY]:
            self.img_dlg.restoreGeometry(base64.b64decode(v))
        if v := state[CFG_DIR]:
            self.last_dir = v
        if v := state[CFG_DECK]:
            i = self.ui.deck.findData(v, flags=Qt.MatchFlag.MatchExactly)
            if i != -1: self.ui.deck.setCurrentIndex(i)
        if v := state[CFG_NOTE]:
            i = self.ui.note.findData(v, flags=Qt.MatchFlag.MatchExactly)
            if i != -1: self.ui.note.setCurrentIndex(i)
        if v := state[CFG_TERM]:
            i = self.ui.term.findText(v)
            if i != -1: self.ui.term.setCurrentIndex(i)
        if v := state[CFG_IMAGE]:
            i = self.ui.image.findText(v)
            if i != -1: self.ui.image.setCurrentIndex(i)
        self.ui.query_tpl.setText(state.get(CFG_TEMPLATE, ''))

    def save_state(self):
        """
        Save current state to file
        """
        config = mw.addonManager.getConfig(__name__)
        config[CFG_STATE] = {
            CFG_GEOMETRY: base64.b64encode(self.saveGeometry()).decode('utf-8'),
            CFG_SPLITTER: base64.b64encode(self.ui.splitter.saveState()).decode('utf-8'),
            CFG_IMGDLG_GEOMETRY: base64.b64encode(self.img_dlg.saveGeometry()).decode('utf-8'),
            CFG_DIR: self.last_dir,
            CFG_DECK: self.ui.deck.currentData(),
            CFG_NOTE: self.ui.note.currentData(),
            CFG_TERM: self.ui.term.currentText(),
            CFG_IMAGE: self.ui.image.currentText(),
            CFG_TEMPLATE: self.ui.query_tpl.text()
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
        (path, filt) = QFileDialog.getOpenFileName(self, t('Select file'), self.last_dir, t('Text files (*.txt)'))
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

        def scale(file: str):
            # Create a new QImage with desired size, initialized to transparent color
            pixmap = QPixmap(file).scaled(
                self.iconw,
                self.iconh,
                Qt.AspectRatioMode.KeepAspectRatio
            )
            img = QImage(self.iconw, self.iconh, QImage.Format.Format_ARGB32)
            img.fill(Qt.GlobalColor.transparent)
            painter = QPainter(img)
            x = (self.iconw - pixmap.width()) / 2
            y = (self.iconh - pixmap.height()) / 2
            painter.drawPixmap(x, y, pixmap)
            painter.end()
            return QPixmap.fromImage(img)

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
                        img_itm.setIcon(QIcon(scale(match.file)))
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
        for itm in self.ui.image_lv.findItems("*", Qt.MatchFlag.MatchWildcard):
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
                .scaled(geom.width(), geom.height(), Qt.AspectRatioMode.KeepAspectRatio)
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
            self.ui.prompt.setToolTip(t('Whether to use search term as "prompt" and images as "answers" (in cloze)<ul><li><code>Term prompt/clozed image(s)</code>: Each search term will be followed by a cloze containing the selected images.</li><li><code>Image(s) prompt/clozed term in table</code>: Generates a table with one row per search term. All selected images will be visible in the left column and the search term will be inside a cloze in the right column.</li></ul>'))
            self.ui.term_lbl.setText(t('Title field'))
            self.ui.term.setToolTip(t('Note field into which the title (configured on right) should be inserted. Select <code>&lt;none&gt;</code> for no title insertion.'))
            self.ui.title.setToolTip(t('Title to insert in supplied field (configured on left).'))
            self.ui.image_lbl.setText(t('Cloze field'))
            self.ui.image.setToolTip(t('Field to insert the clozes and their respective prompt in (configured on left).'))
            self.ui.term.addItem(t('<none>'))
            self.ui.prompt_lbl.show()
            self.ui.prompt.show()
            self.ui.title.show()
        else:
            self.ui.term_lbl.setText(t('Term field'))
            self.ui.term.setToolTip(t('Note field into which the search term should be inserted.'))
            self.ui.image_lbl.setText(t('Image field'))
            self.ui.image.setToolTip(t('Note field into which the selected images should be inserted.'))
            self.ui.prompt_lbl.hide()
            self.ui.prompt.hide()
            self.ui.title.hide()
        self.ui.term.addItems(fields)
        self.ui.image.addItems(fields)

    def run_query(self):
        """
        Run search query and populate term-images, runs in main thread with custom
        progress bar
        """

        def curl_download(url: str):
            """Attempt to download URL using `curl`, return tuple (status_code, file)"""
            tmp = tempfile.NamedTemporaryFile(
                mode='wb',
                suffix='.jpg',
                dir=self.tmp_dir.name,
                delete=False
            )
            proc_info = subprocess.run(
                [
                    CURL,
                    '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36, Accept-Encoding:gzip,deflate',
                    '--connect-timeout', '5',
                    '-o', tmp.name,
                    '-L',                   # follow redirect
                    '-s',                   # silent
                    '-w', '%{http_code}',   # write final status_code to stdout
                    '-X', 'GET', url
                ],
                stdout=subprocess.PIPE,
                universal_newlines=True
            )
            try:
                code = int(proc_info.stdout.strip())
            except:
                code = 400
            return (code, tmp.name)

        def requests_download(url: str):
            """
            Attempt to download URL with `requests`, return tuple (status_code, file)
            """
            # Some anti-fingerprinting stuff to be able to download
            class TlsAdapter(HTTPAdapter):
                """
                Class to counter TLS fingerprinting
                https://scrapfly.io/blog/how-to-avoid-web-scraping-blocking-tls/
                """
                def __init__(self, ssl_options=0, **kwargs):
                    self.ssl_options = ssl_options
                    super(TlsAdapter, self).__init__(**kwargs)

                def init_poolmanager(self, *pool_args, **pool_kwargs):
                    # see "openssl ciphers" command for cipher names
                    ctx = create_urllib3_context(
                        ciphers="ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384", cert_reqs=ssl.CERT_REQUIRED,
                        options=self.ssl_options
                    )
                    self.poolmanager = PoolManager(*pool_args, ssl_context=ctx, **pool_kwargs)

            session = requests.Session()
            session.mount(
                "https://",
                TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1) # prio TLS1.2 
            )
            res = session.get(
                url = url,
                headers = OrderedDict([
                    ('Upgrade-Insecure-Requests', '1'),
                    ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'),
                    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'),
                    ('Accept-Encoding', 'gzip, deflate'),
                    ('Accept-Language', 'en-US,en;q=0.5')
                ]),
                allow_redirects=True,
                stream = True,
                timeout = 15,
                verify=False
            )
            if res.status_code != 200:
                self.logger.info(f"Non-200 return|match: {match}")
                return (res.status_code, None)

            res.raw.decode_content = True
            if e := imghdr.what(file=None, h=res.content):
                ext = f".{e}"
            else:
                self.logger.info(f"Unable to detect image type for {match.url}")
                ext = ".jpg"
            tmp = tempfile.NamedTemporaryFile(
                mode='wb',
                suffix=ext,
                dir=self.tmp_dir.name,
                delete=False
            )
            for chunk in res: tmp.file.write(chunk)
            return (res.status_code, tmp.name)

        if not self.terms: return

        # Confirm with user
        template = self.ui.query_tpl.text()
        border = '#D3D3D3' if theme_manager.night_mode else '#808080'
        html = f'<b>{t("Run the following queries?")}</b><br><table width="100%">'
        for term in self.terms:
            html += f'<tr><td style="padding: 5px; white-space:nowrap;">{term.term}:</td><td style="padding: 5px; padding-left: 10px;" width="100%">{term.query(template)}</td></tr>'
        html += '</table>'
        dlg = ListDialog(self, t('Run search queries'), html)
        dlg.ui.buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        if dlg.exec() != 1: return
        
        # Setup
        progress = QProgressDialog(parent=self, minimum=0, maximum=len(self.terms))
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setFixedWidth(400)
        lbl = QLabel(progress)
        lbl.setFixedWidth(400)
        lbl.setText(t('Getting images...'))
        progress.setLabel(lbl)
        progress.setAutoClose(False)
        progress.forceShow()
        mw.app.processEvents()
        if progress.wasCanceled(): return

        # Run queries
        cnt = 0
        for i, term in enumerate(self.terms):
            query = term.query(template)
            progress.setLabelText(t('Searching %(query)s...') % {'query': query})
            progress.setValue(i)
            mw.app.processEvents()
            if progress.wasCanceled(): return
            term.matches = self.engine.search(query)
            if term.matches is None:
                msg = t('%(engine)s search for "%(query)s" returned None, search engine plugin broken?') % {'engine': self.engine.title(), 'query': query}
                self.logger.warning(msg)
                raise Exception(msg)
            cnt += len(term.matches)
        progress.setValue(len(self.terms))
        
        # Download images
        if self.tmp_dir: self.tmp_dir.cleanup()
        self.tmp_dir = tempfile.TemporaryDirectory()
        progress.setValue(0)
        progress.setMaximum(cnt)
        progress.setAutoClose(True)
        mw.app.processEvents()
        if progress.wasCanceled(): return
        i = 0
        all_skipped = {}
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )
        for term in self.terms:
            matches = []
            skipped = []
            for match in term.matches:
                progress.setLabelText(t('Downloading `%(url)s`...') % {'url': match.url})
                progress.setValue(i)
                mw.app.processEvents()
                if progress.wasCanceled(): return
                i += 1
                try:
                    if CURL: (status_code, file) = curl_download(match.url)
                    else: (status_code, file) = requests_download(match.url)
                    if status_code == 200:
                        match.file = file
                        matches.append(match)
                    else:
                        skipped.append(f'{match.url} ({status_code})')
                except Exception as e:
                    self.logger.info(f'Exception `{match.url}`: {e}')
                    skipped.append(f'{match.url} ({e})')
 
            term.matches = matches
            if skipped:
                all_skipped[term.term] = skipped
        progress.setValue(cnt)

        # Update GUI
        self.ui.generate.setEnabled(True)
        if self.ui.term_lv.currentRow() == 0:
            self.ui.term_lv.setCurrentRow(-1)
        self.ui.image_lv.setEnabled(True)
        self.ui.term_lv.setCurrentRow(0)

        # Alert user to skipped images
        if all_skipped:
            msg = ''
            for k, v in all_skipped.items():
                msg += f'{k}:<ul><li>{"</li><li>".join(v)}</li></ul>'
            box = show_info(title=t('The following images were found but not downloaded'), text=msg, parent=self)
            box.setTextFormat(Qt.TextFormat.RichText)


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
                    if term_fld != t('<none>'):
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
            msg = t('<b>Note generation finished</b><br>%(count)d %(type)s(s) generated.</div>') % {
                'count': result.count,
                'type': 'cloze' if result.note_type == consts.MODEL_CLOZE else 'note'
            }
            if result.skipped:
                skipped = ""
                msg += f'<br><br>{t("<b>Items skipped</b><br>No notes generated for the following search terms (no search matches or no matches selected):")}<br><br>'
                for term in result.skipped:
                    msg += f"{term}<br>\n"
                    skipped += f"{term}\n"
                    skipped.rstrip()
            dlg = ListDialog(self, t('Search to notes'), msg)
            if result.skipped:
                copy = dlg.ui.buttonBox.addButton(t('Copy skipped to clipboard'), QDialogButtonBox.ButtonRole.ApplyRole)
                copy.clicked.connect(lambda: QApplication.clipboard().setText(skipped))
            dlg.exec()

        ###
        bgop = CollectionOp(parent=mw, op=background)
        bgop.success(finished)
        bgop.failure(finished)
        bgop.run_in_background()
        

# Main ##################################################################
def init():
    load_translation(translations)
    action = QAction(t("Create notes from web image search"), mw)
    if sc := mw.addonManager.getConfig(__name__).get('Shortcut open'):
        action.setShortcut(sc)
    action.triggered.connect(lambda: MainWindow())
    mw.form.menuTools.addAction(action)
    
    # config/meta.json format changed in 1.2.0
    if strvercmp(CVER, '1.2.0') < 0:
        # Update meta.json format
        if meta := mw.addonManager.addonMeta(os.path.dirname(__file__)):
            state = {
                CFG_GEOMETRY: meta['config'].pop(CFG_GEOMETRY, ''),
                CFG_SPLITTER: meta['config'].pop(CFG_SPLITTER, ''),
                CFG_IMGDLG_GEOMETRY: meta['config'].pop(CFG_IMGDLG_GEOMETRY, ''),
                CFG_DIR: meta['config'].pop(CFG_DIR, ''),
                CFG_DECK: meta['config'].pop(CFG_DECK, ''),
                CFG_NOTE: meta['config'].pop(CFG_NOTE, ''),
                CFG_TERM: meta['config'].pop(CFG_TERM, ''),
                CFG_IMAGE: meta['config'].pop(CFG_IMAGE, ''),
                CFG_TEMPLATE: meta['config'].pop(CFG_TEMPLATE, '')
            }
            meta['config'][CFG_STATE] = state
            # Use legacy to overwrite config changes
            mw.addonManager.writeAddonMeta(os.path.dirname(__file__), meta)

    if strvercmp(CVER, NVER) < 0:
        set_version(NVER)

    # Ask user to post debug log 
    if os.path.exists(DEBUG_FILE) and (not os.path.exists(DEBUG_PROMPTED) or os.path.getmtime(DEBUG_FILE) > os.path.getmtime(DEBUG_PROMPTED)):
        show_info(t('Search to notes add-on has detected an error log, consider reviewing it for any privacy concerns and then post the contents to the add-on support thread (https://forums.ankiweb.net/t/search-to-notes-support-thread/16286) to help the author and other users. The debuglog can be found here: "%(file)s".' % {'file': DEBUG_FILE}))
        with open(DEBUG_PROMPTED, "w") as fh:
            fh.write(time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(time.ctime(os.path.getmtime(DEBUG_FILE)))))

gui_hooks.main_window_did_init.append(init)
