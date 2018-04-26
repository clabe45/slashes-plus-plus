import sys
import re
import copy

from PyQt5.QtWidgets import QApplication

import gui

app = QApplication(sys.argv)
ex = gui.Window()
sys.exit(app.exec_())
