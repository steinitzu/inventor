import os

from PySide.QtUiTools import QUiLoader
from PySide.QtCore import QFile

ui_dir = os.path.join(
    os.path.abspath(os.path.dirname(__file__))
    )

def get_ui(fname, parent=None):
    """
    Loads a the .ui file named `fname`.ui in `ui_dir` and returns a 
    python object of it.
    """
    loader = QUiLoader()
    #loader.registerCustomWidget(LibTreeView)
    #loader.registerCustomWidget(LibFilterEdit)
    f = QFile(os.path.join(ui_dir, fname+'.ui'))
    f.open(QFile.ReadOnly)
    widget = loader.load(f, parent=parent)
    f.close()
    return widget
