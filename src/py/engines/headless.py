"""
# phantom.py
Simple but fully scriptable headless QtWebKit browser using PyQt5 in Python3,
specialized in executing external JavaScript and generating PDF files. A lean
replacement for other bulky headless browser frameworks.
## Usage
If you have a display attached:
    ./phantom.py <url> <pdf-file> [<javascript-file>]
    
If you don't have a display attached (i.e. on a remote server):
    xvfb-run ./phantom.py <url> <pdf-file> [<javascript-file>]
Arguments:
<url> Can be a http(s) URL or a path to a local file
<pdf-file> Path and name of PDF file to generate
[<javascript-file>] (optional) Path and name of a JavaScript file to execute
## Features
* Generate a PDF screenshot of the web page after it is completely loaded.
* Optionally execute a local JavaScript file specified by the argument
   <javascript-file> after the web page is completely loaded, and before
   the PDF is generated.
* console.log's will be printed to stdout.
* Easily add new features by changing the source code of this script, without
   compiling C++ code. For more advanced applications, consider attaching
   PyQt objects/methods to WebKit's JavaScript space by using
   `QWebFrame::addToJavaScriptWindowObject()`.
If you execute an external <javascript-file>, phantom.py has no way of knowing
when that script has finished doing its work. For this reason, the external
script should execute `console.log("__PHANTOM_PY_DONE__");` when done. This will
trigger the PDF generation, after which phantom.py will exit. If no
`__PHANTOM_PY_DONE__` string is seen on the console for 10 seconds, phantom.py
will exit without doing anything. This behavior could be implemented more
elegantly without console.log's but it is the simplest solution.
It is important to remember that since you're just running WebKit, you can use
everything that WebKit supports, including the usual JS client libraries, CSS,
CSS @media types, etc.
## Dependencies
* Python3
* PyQt5
* xvfb (optional for display-less machines)
Installation of dependencies in Debian Stretch is easy:
    apt-get install xvfb python3-pyqt5 python3-pyqt5.qtwebkit
    
Finding the equivalent for other OSes is an exercise that I leave to you.
## Examples
Given the following file /tmp/test.html
    <html>
      <body>
        <p>foo <span id="id1">foo</span> <span id="id2">foo</span></p>
      </body>
      <script>
        document.getElementById('id1').innerHTML = "bar";
      </script>
    </html>
    
... and the following file /tmp/test.js:
    document.getElementById('id2').innerHTML = "baz";
    console.log("__PHANTOM_PY_DONE__");
    
... and running this script (without attached display) ...
    xvfb-run python3 phantom.py /tmp/test.html /tmp/out.pdf /tmp/test.js
    
... you will get a PDF file /tmp/out.pdf with the contents "foo bar baz".
Note that the second occurrence of "foo" has been replaced by the web page's own
script, and the third occurrence of "foo" by the external JS file.
## License
Copyright 2017 Michael Karl Franzl
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import sys, traceback

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtCore import QTimer

  
class Render(QWebEngineView):
  def __init__(self, url, outfile, jsfile):
    self.app = QApplication(sys.argv)
    QWebEngineView.__init__(self)

    self.jsfile = jsfile
    self.outfile = outfile
    
    qurl = QUrl.fromUserInput(url)
    
    print("phantom.py: URL=", qurl, "OUTFILE=", outfile, "JSFILE=", jsfile)
    
    # The PDF generation only happens when the special string __PHANTOM_PY_DONE__
    # is sent to console.log(). The following JS string will be executed by
    # default, when no external JavaScript file is specified.
    self.js_contents = "setTimeout(function() { console.log('__PHANTOM_PY_DONE__') }, 500);"

    if jsfile:
      try:
        f = open(self.jsfile)
        self.js_contents = f.read()
        f.close()
      except:
        print(traceback.format_exc())
        self._exit(10)
        
    self.loadFinished.connect(self._loadFinished)
    self.page().load(qurl)
    self.javaScriptConsoleMessage = self._onConsoleMessage
    
    # Run for a maximum of 10 seconds
    watchdog = QTimer()
    watchdog.setSingleShot(True)
    watchdog.timeout.connect(lambda: self._exit(1))
    watchdog.start(10000)
    
    self.app.exec()
    
    
  def _onConsoleMessage(self, txt, lineno, filename):
    print("CONSOLE", lineno, txt, filename)
    if "__PHANTOM_PY_DONE__" in txt:
      # If we get this magic string, it means that the external JS is done
      self._print()
      self._exit(0)
  
  
  def _loadFinished(self, result):
    print("phantom.py: Loading finished!")
    print("phantom.py: Evaluating JS from", self.jsfile, ", (", self.js_contents, ")")
    self.frame = self.page()
    self.frame.runJavaScript(self.js_contents)
    

  def _print(self):
    print("phantom.py: Printing...")
    printer = QPrinter()
    printer.setPageMargins(10, 10, 10, 10, QPrinter.Millimeter)
    printer.setPaperSize(QPrinter.A4)
    printer.setCreator("phantom.py by Michael Karl Franzl")
    printer.setOutputFormat(QPrinter.PdfFormat);
    printer.setOutputFileName(self.outfile);
    self.frame.print(printer)
    
  def _exit(self, val):
    print("phantom.py: Exiting with val", val)
    self.app.exit(val) # Qt exit
    exit(val) # Python exit
    
    
def main():
  if (len(sys.argv) < 3):
    print("USAGE: ./phantom.py <url> <pdf-file> [<javascript-file>]")
  else:
    url = sys.argv[1]
    outfile = sys.argv[2]
    jsfile = sys.argv[3] if len(sys.argv) > 3 else None
    r = Render(url, outfile, jsfile)


if __name__ == "__main__":
  main()