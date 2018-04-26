import os
import os.path
import re

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import constants
import edit
import interpreter

# FIX CTRL-Q
class Window(QMainWindow):
	def __init__ (self):
		super(Window, self).__init__()
		self.basetitle = '///++'
		self.left = 10
		self.top = 40
		self.width = 640
		self.height = 480
		self.filename = ''
		self.changesMade = False		# neither changed nor unchanged; simply un-loaded
		self.referenceCursors = []	# composed of QTextCursor's (all containing selections)
		self.clipboard = QGuiApplication.clipboard()
		self.clipboard.changed.connect(self.clipboardChanged)
		self.initPrefs()
		self.initUI()
	def initPrefs(self):
		self.preferences = {}
		self.preferences['theme'] = 'Dark'
	def initUI(self):
		self.setWindowTitle(self.formatPath() + ' - ' + self.basetitle)
		self.setWindowIcon(self.createIcon('favicon.png'))
		self.setGeometry(self.left, self.top, self.width, self.height)
		self.center = QWidget(self)
		self.layout = QVBoxLayout(self.center)
		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.setCentralWidget(self.center)
		self.toolbar = self.addToolBar('Actions')	# so it exists for necessary method(s)
		self.layout.addWidget(self.toolbar)
		self.initStyle()
		self.initWidgets()
		self.refreshColors()
		self.zoomIndex = 0
		self.initActions()
		self.initMenus()
		self.initToolbar()
		self.show()
		self.statusBar().setStyleSheet('background-color:#666; color:white;')
		self.statusBar().showMessage('Welcome to ///++ (pronounced "Slashes Plus Plus"). Feel free to code...')
	def initActions(self):
		self.DEFAULT_LINE_WRAP = False
		self.DEFAULT_SHOW_PROGRESSION = True
		settings = QSettings(constants.AUTHOR, constants.APP_NAME)
		# FILE
		icon = self.createIcon('file-new.png')
		self.newAction = self.createAction(text='New', statusTip='Create new project', shortcut='Ctrl+N', icon=icon, callback=self.new)
		icon = self.createIcon('file-open.png')
		self.openAction = self.createAction(text='Open...', statusTip='Open existing project', shortcut='Ctrl+O', icon=icon, callback=self.open)
		icon = self.createIcon('file-save.png')
		self.saveAction = self.createAction(text='Save', statusTip='Save project', shortcut='Ctrl+S', icon=icon, callback=self.save)
		self.saveAsAction = self.createAction(text='Save As...', statusTip='Save project as...', shortcut='Ctrl+Shift+S', callback=self.saveAs)
		self.exitAction = self.createAction(text='E&xit', statusTip='Close the session', shortcut='Ctrl+Q', callback=self.close)
		# EDIT
		icon = self.createIcon('edit-undo.png')
		self.undoAction = self.createAction(text='Undo', statusTip='Undo last edit', shortcut='Ctrl+Z', icon=icon, callback=self.editor.undo)
		icon = self.createIcon('edit-redo.png')
		self.undoAction.setEnabled(False)
		self.redoAction = self.createAction(text='Redo', statusTip='Redo last edit', shortcut='Ctrl+Shift+Z', icon=icon, callback=self.editor.redo)
		self.redoAction.setEnabled(False)
		icon = self.createIcon('edit-cut.png')
		self.cutAction = self.createAction(text='Cut', statusTip='Cut selection to clipboard', shortcut='Ctrl+X', icon=icon	, callback=self.editor.cut)
		self.cutAction.setEnabled(False)
		icon = self.createIcon('edit-copy.png')
		self.copyAction = self.createAction(text='Copy', statusTip='Copy selection to clipboard', shortcut='Ctrl+C', icon=icon, callback=self.editor.copy)
		self.copyAction.setEnabled(False)
		icon = self.createIcon('edit-paste.png')
		self.pasteAction = self.createAction(text='Paste', statusTip='Paste clipboard contents', shortcut='Ctrl+V', icon=icon, callback=self.editor.paste)
		self.pasteAction.setEnabled(self.editor.canPaste())
		self.selectAllAction = self.createAction(text='Select &All', statusTip='Select all text', shortcut='Ctrl+A', callback=self.editor.selectAll)
		msg = 'Insert a reference to another /// file into the project'
		self.insertReferenceAction = self.createAction(text='Reference', statusTip=msg, shortcut='Ctrl+/', callback=self.insertReference)
		self.preferencesAction = self.createAction(text='Preferences', statusTip='Edit preferences', shortcut='Ctrl+,', callback=self.showPreferences)
		# VIEW
		self.zoomInAction = self.createAction('Zoom In', statusTip='Increase zoom level', shortcut=(Qt.CTRL+Qt.Key_Equal), callback=self.zoomIn)
		self.zoomOutAction = self.createAction('Zoom Out', statusTip='Decrease zoom level', shortcut=(Qt.CTRL+Qt.Key_Minus), callback=self.zoomOut)
		self.restoreZoomAction = self.createAction('Restore Default Zoom', statusTip='Restore Default Zoom', shortcut='Ctrl+0', callback=self.restoreZoom)
		self.lineWrapAction = self.createAction(text='Word Wrap', statusTip='Toggle word wrap', checkable=True, callback=self.updateLineWrap)
		lastState = settings.value('options/linewrap', self.DEFAULT_LINE_WRAP, bool)
		self.lineWrapAction.setChecked(lastState)
		self.updateLineWrap()
		# RUN
		msg = 'Show all steps of the program mutation'
		self.showProgressionAction = self.createAction(text='Display full progression', statusTip=msg, checkable=True)
		lastState = settings.value('options/progression', self.DEFAULT_SHOW_PROGRESSION, bool)
		self.showProgressionAction.setChecked(lastState)
		icon = self.createIcon('run-run.png')
		self.runAction = self.createAction(text='Run', icon=icon, statusTip='Run project', shortcut='Ctrl+Return', callback=self.run)
		self.aboutAction = self.createAction(text='About ///++', statusTip='Show credits', shortcut='F1', callback=self.showAbout)
	def createIcon(self, relativePath):
		return QIcon(os.path.join('icons', relativePath))
	def createAction(self, text, statusTip, callback=None, shortcut=None, icon=None, checkable=False):
		action = QAction(icon, text, self) if icon else QAction(text, self)
		if checkable:	action.setCheckable(checkable)
		if shortcut:
			action.setShortcut(shortcut)
		action.setStatusTip(statusTip)
		if callback:	action.triggered.connect(callback)
		return action
	def initMenus(self):
		mainMenu = self.menuBar()
		self.fileMenu = mainMenu.addMenu('&File')
		self.fileMenu.addAction(self.newAction)
		self.fileMenu.addAction(self.openAction)
		self.fileMenu.addAction(self.saveAction)
		self.fileMenu.addAction(self.saveAsAction)
		self.fileMenu.addAction(self.exitAction)
		self.editMenu = mainMenu.addMenu('&Edit')
		self.editMenu.addAction(self.undoAction)
		self.editMenu.addAction(self.redoAction)
		self.editMenu.addSeparator()
		self.editMenu.addAction(self.cutAction)
		self.editMenu.addAction(self.copyAction)
		self.editMenu.addAction(self.pasteAction)
		self.editMenu.addAction(self.selectAllAction)
		# self.insertMenu = self.editMenu.addMenu('&Insert')
		# self.insertMenu.addAction(self.insertReferenceAction)
		self.editMenu.addSeparator()
		self.editMenu.addAction(self.preferencesAction)
		self.viewMenu = mainMenu.addMenu('&View')
		self.viewMenu.addAction(self.lineWrapAction)
		self.zoomMenu = self.viewMenu.addMenu('&Zoom')
		self.zoomMenu.addAction(self.zoomInAction)
		self.zoomMenu.addAction(self.zoomOutAction)
		self.zoomMenu.addAction(self.restoreZoomAction)
		self.runMenu = mainMenu.addMenu('&Run')
		self.runMenu.addAction(self.showProgressionAction)
		self.runMenu.addAction(self.runAction)
		self.helpMenu = mainMenu.addMenu('&Help')
		self.helpMenu.addAction(self.aboutAction)
	def initToolbar(self):
		self.toolbar.setIconSize(QSize(20, 20))
		self.toolbar.addAction(self.newAction)
		self.toolbar.addAction(self.openAction)
		self.toolbar.addAction(self.saveAction)
		self.toolbar.addAction(self.undoAction)
		self.toolbar.addAction(self.redoAction)
		self.toolbar.addAction(self.cutAction)
		self.toolbar.addAction(self.copyAction)
		self.toolbar.addAction(self.pasteAction)
		self.toolbar.addAction(self.runAction)
	def initStyle(self):
		settings = QSettings(constants.AUTHOR, constants.APP_NAME)
		self.DEFAULT_THEME = 'Dark'
		self.DEFAULT_PATTERN_HIGHLIGHT = QColor(229, 30, 53)
		self.DEFAULT_REPLACEMENT_HIGHLIGHT = QColor(22, 88, 221)
		self.DEFAULT_SUBSTITUTION_HIGHLIGHT = QColor(239, 176, 35)

		self.theme = settings.value('style/theme', self.DEFAULT_THEME, str)
		self.patternSlashColor = settings.value('style/syntax/pattern-highlight', self.DEFAULT_PATTERN_HIGHLIGHT, QColor)
		self.replacementSlashColor = settings.value('style/syntax/replacement-highlight', self.DEFAULT_REPLACEMENT_HIGHLIGHT, QColor)
		self.substitutionSlashColor = settings.value('style/syntax/substitution-highlight', self.DEFAULT_SUBSTITUTION_HIGHLIGHT, QColor)

		self.printBlockColor = QColor(Qt.white)
	def refreshColors(self):
		self.patternBlockColor = self.patternSlashColor.lighter(140)
		self.replacementBlockColor = self.replacementSlashColor.lighter(140)
		self.editor.refreshStyle()
		self.output.refreshStyle()

	def initWidgets(self):
		initialZoomIndex = 4
		settings = QSettings(constants.AUTHOR, constants.APP_NAME)
		self.splitter = QSplitter(self)
		self.splitter.setOrientation(Qt.Vertical)
		self.splitter.setHandleWidth(4)
		self.splitter.setStyleSheet('background-color:#666')
		self.textEditsWithReferences = []
		self.editor = CodeEditor(self)
		for x in range(initialZoomIndex):	self.editor.zoomIn()
		self.splitter.addWidget(self.editor)

		self.output = Output(self)
		self.splitter.addWidget(self.output)
		for x in range(initialZoomIndex):	self.output.zoomIn()
		self.layout.addWidget(self.splitter)

		lastStates = settings.value('layout/sizes', type=int)
		if lastStates:
			self.splitter.setSizes(lastStates)
	def resizeEvent(self, event):
		super(Window, self).resizeEvent(event)
		self.width = event.size().width()
		self.height = event.size().height()
	def formatPath(self):
		return '[Untitled]' if self.filename == '' else os.path.basename(self.filename)
	def requestSaveChanges(self):
		if self.changesMade:
			msg = '%s has been modified. Save changes?'%self.formatPath()
			msgbox = QMessageBox(self)
			msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
			# msgbox.setWindowTitle('Save changes?')
			msgbox.setText(msg)
			answer = msgbox.exec_()
			if answer == QMessageBox.Yes:	return self.save()
			else:	return answer != QMessageBox.Cancel
		return True
	@pyqtSlot()
	def new(self):
		if not self.requestSaveChanges():	return
		self.filename = ''
		self.setWindowTitle(self.formatPath() + ' - ' + self.basetitle)
		self.editor.clear()
		self.statusBar().showMessage('New project created')
		self.changesMade = False
	@pyqtSlot()
	def open(self):
		if not self.requestSaveChanges():	return
		settings = QSettings(constants.AUTHOR, constants.APP_NAME)
		lastDir = settings.value('files/dir', os.path.expanduser('~/Documents'))
		filename, _ = QFileDialog.getOpenFileName(self, 'Open...', directory=lastDir)
		if filename:
			self.filename = filename
			self.readIn()
			settings.setValue('files/dir', os.path.dirname(filename))
			del settings	# save setting
		self.setWindowTitle(self.formatPath() + ' - ' + self.basetitle)
		self.statusBar().showMessage('%s opened' % self.formatPath())
		self.changesMade = False
	def readIn(self):
		file = open(self.filename, 'r')
		self.editor.setPlainText(file.read())
	@pyqtSlot()
	def save(self):
		if self.filename == '':
			self.saveAs()
		else:
			self.writeOut()
	def saveAs(self):
		settings = QSettings(constants.AUTHOR, constants.APP_NAME)
		lastDir = settings.value('files/dir', os.path.expanduser('~'))
		filename, _ = QFileDialog.getSaveFileName(self, 'Save as...', directory=lastDir)
		if filename:
			# a file was selected
			self.filename = filename
			self.setWindowTitle(self.formatPath() + ' - ' + self.basetitle)
			self.writeOut()
			settings.setValue('files/dir', os.dirname(filename))
			del settings
		return bool(filename)
	def writeOut(self):
		file = open(self.filename, 'w')
		file.write(self.editor.toPlainText())
		self.changesMade = False
		self.statusBar().showMessage('Changes saved')
	@pyqtSlot()
	def insertReference(self):
		caret = self.editor.textCursor()
		text = ' &filename '	# insert spacing too
		# add to self.referenceCursors if it doesn't contain one in range
		for selection in self.referenceCursors:
			if (
				(caret.anchor() >= selection.anchor() - 1 and caret.anchor() < selection.position()) or
				(caret.position() >= selection.anchor() - 1 and caret.position() < selection.position())
			   ):
				break
		else:
			anchorCache = caret.anchor()
			caret.insertText(text)	# this will be pseudo-ignore (see Highlighter.markReferences slot)
			caret.setPosition(anchorCache + 1)	# also moves anchor (+ 1 -> spacing)
			caret.setPosition(caret.position() + -1 + len(text) -1, QTextCursor.KeepAnchor)	# make selection (-1 -> spacing)

			self.referenceCursors.append(QTextCursor(caret))	# copy caret, so I can mutate it later
			for textEdit in self.textEditsWithReferences:
				textEdit.refreshStyle()	# a little hacky, but it works
				textEdit.highlighter.markReferences()

	@pyqtSlot()
	def showPreferences(self):
		PreferencesDialog(self).exec_()

	@pyqtSlot()
	def zoomIn(self):
		self.editor.zoomIn(2)
		self.zoomIndex += 2
	@pyqtSlot()
	def zoomOut(self):
		self.editor.zoomOut(2)
		self.zoomIndex -= 2
	@pyqtSlot()
	def restoreZoom(self):
		while self.zoomIndex > 0:	self.zoomOut()
		while self.zoomIndex < 0:	self.zoomIn()
	@pyqtSlot()
	def clipboardChanged(self):
		self.pasteAction.setEnabled(bool(self.clipboard.text()))
	@pyqtSlot()
	def updateLineWrap(self):
		wrap = True
		mode = QTextEdit.WidgetWidth if self.lineWrapAction.isChecked() else QTextEdit.NoWrap
		self.editor.setLineWrapMode(mode)
		self.output.setLineWrapMode(mode)
	@pyqtSlot()
	def run(self):
		self.output.setText('')
		interpreter.interpret(
			self.editor.toPlainText(),
			lambda s: self.output.setHtml(self.output.toHtml()+re.sub('\n', '<br>', s)),
			self.showProgressionAction.isChecked(),
			True
		)
	@pyqtSlot()
	def showAbout(self):
		msg = QMessageBox()
		msg.setWindowTitle('About ///++')
		msg.setTextFormat(Qt.RichText)
		msg.setText(
			"""
			Written and designed by clabe45.
			<br>Images by
			<a href="https://www.flaticon.com/constants.AUTHORs/picol">Picol</a> and <a href="https://www.flaticon.com/constants.AUTHORs/freepik">Freepik</a> at
			<a href="https://www.flaticon.com">flaticon.com</a>.
			""")
		msg.setDefaultButton(QMessageBox.Ok)
		msg.exec_()
	def closeEvent(self, event):
		settings = QSettings(constants.AUTHOR, constants.APP_NAME)
		if not self.requestSaveChanges():
			event.ignore()
			return
		settings.setValue('options/progression', self.showProgressionAction.isChecked())
		settings.setValue('options/linewrap', self.lineWrapAction.isChecked())
		settings.setValue('layout/sizes', self.splitter.sizes())
		settings.setValue('style/theme', self.theme)
		settings.setValue('style/syntax/pattern-highlight', self.patternSlashColor)		# highlight and slash are interchangeable
		settings.setValue('style/syntax/replacement-highlight', self.replacementSlashColor)
		settings.setValue('style/syntax/substitution-highlight', self.substitutionSlashColor)
		del settings	# write to disk

class ColoredTextEdit(QTextEdit):
	def __init__(self, parent, colorPerLine=False, useReferences=False):
		super().__init__(parent)
		self.parent = parent
		self.highlighter = Highlighter(self, colorPerLine)
		self.useReferences = useReferences
		if self.useReferences:
			self.parent.textEditsWithReferences.append(self)
	def refreshStyle(self):
		self.refreshStylesheet()
		self.highlighter.refresh()
		#self.setPlainText(self.toPlainText())
	def refreshStylesheet(self): pass


class Output(ColoredTextEdit):
	def __init__(self, parent):
		super().__init__(parent)
		self.parent = parent
		self.setReadOnly(True)
		self.refreshStylesheet()

	def refreshStylesheet(self):
		background = '#222' if self.parent.theme == 'Dark' else '#ddd'	# TODO: look at #ddd
		foreground = 'white' if self.parent.theme == 'Dark' else 'black'	# TODO: "
		self.setStyleSheet('background-color:%s; color:%s; font-family: Consolas; font-size: 16px;' % (background, foreground))

class CodeEditor(ColoredTextEdit):
	def __init__(self, parent):
		super().__init__(parent, useReferences=True)
		self.refreshStylesheet()
		self.parent = parent
		self.prevBlockCount = 1
		self.lineNumberArea = LineNumberArea(self)
		self.inStartup = True	# for ignoring the highlightBlock event on startup (so it won't set changesMade to True)
		self.prevPlainText = ''

		self.textChanged.connect(self.changed)
		self.undoAvailable.connect(lambda available: self.parent.undoAction.setEnabled(available))
		self.redoAvailable.connect(lambda available: self.parent.redoAction.setEnabled(available))
		self.copyAvailable.connect(self.updateSelectionActions)
		#self.connect(self, SIGNAL('updateRequest(QRect,int)'), self.updateLineNumberArea)
		#self.cursorPositionChanged.connect(self.highlightCurrentLine)
		#self.updateLineNumberAreaWidth()
	def refreshStylesheet(self):
		background = 'black' if self.parent.theme == 'Dark' else 'white'
		foreground = 'white' if self.parent.theme == 'Dark' else 'black'
		self.setStyleSheet('background-color:%s; color:%s; font-family: Consolas;' % (background, foreground))
	def changed(self):
		window = self.parent
		text = self.toPlainText()

		if text != '':
			window.statusBar().showMessage('')
		if not self.inStartup:
			if not window.changesMade:
				window.changesMade = True
		else:
			self.inStartup = False

		# check if any references should be deleted (a reference should be deleted if any character in it is deleted or inserted into it)
		edit_ = edit.detectEdit(self.prevPlainText, text) if text != self.prevPlainText and len(text) != len(self.prevPlainText) else None
		if edit_:
			editType = edit_[0]
			editPos = edit_[1]
			for selection in self.parent.referenceCursors:
				# account for padding (btw the cursors glitch out w/o padding)
				if (
					(editType == EditType.Deletion and editPos >= selection.anchor() - 1 and editPos < selection.position() + 1) or
					(editType == EditType.Insertion and editPos >= selection.anchor() - 1 and editPos < selection.position() + 1 - 1)
				   ):
					# deleteme
					self.parent.referenceCursors.remove(selection)

					posCache = selection.position()
					selection.setPosition(selection.anchor() - 1)	# move anchor back by one (for spacing)
					selection.setPosition(posCache, QTextCursor.KeepAnchor)
					selection.removeSelectedText()
		self.prevPlainText = text

		#self.checkUpdateLineNumberArea()
	def lineNumberAreaWidth(self):
		digits = 1
		count = max(1, self.document().blockCount())
		while count >= 10:
			count /= 10
			digits += 1
		space = 10 + self.fontMetrics().width('9') * digits
		return space
	def checkUpdateLineNumberArea(self):
		if self.prevBlockCount != self.document().blockCount():	self.updateLineNumberAreaWidth()
		self.prevBlockCount = self.document().blockCount()
	def updateLineNumberAreaWidth(self):
		self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
	def updateLineNumberArea(self, rect, dy):
		if dy:
			self.lineNumberArea.scroll(0, dy)
		else:
			self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
		if rect.contains(self.viewport().rect()):
			self.updateLineNumberAreaWidth(0)
	def lineNumberAreaPaintEvent(self, event):
		self.verticalScrollBar().setSliderPosition(self.verticalScrollBar().sliderPosition())

		painter = QPainter(self.lineNumberArea)
		painter.fillRect(event.rect(), Qt.darkGray if self.parent.preferences['theme'] == 'Dark' else Qt.lightGray)
		painter.setPen(Qt.lightGray if self.parent.preferences['theme'] == 'Dark' else Qt.darkGray)

		block = self.firstVisibleBlock()
		blockNumber = block.blockNumber()
		prevBlock = self.document().findBlockByNumber(blockNumber-1) if blockNumber > 0 else block
		translateY = self.verticalScrollBar().sliderPosition() if blockNumber > 0 else 0

		top = self.viewport().geometry().top()
		additionalMargin = None
		if blockNumber == 0:	additionalMargin = int(self.document().documentMargin() - 1 - self.verticalScrollBar().sliderPosition())
		else:
			rect = self.document().documentLayout().blockBoundingRect(prevBlock)
			additionalMargin = int(rect.translated(0, translateY).intersected(self.viewport().geometry().height()))
		top += additionalMargin
		bottom = top + self.document().documentLayout().blockBoundingRect(block).height()
		height = self.fontMetrics().height()

		while block.isValid() and (top <= event.rect().bottom()):
			if block.isVisible() and (bottom >= event.rect().top()):
				number = str(blockNumber + 1)
				painter.drawText(-6, top, self.lineNumberArea.width(), height, Qt.AlignRight, number)
			block = block.next()
			top = bottom
			bottom = top + self.document().documentLayout().blockBoundingRect(block).height()
			blockNumber += 1
	def resizeEvent(self, event):
		super().resizeEvent(event)
		cr = self.contentsRect()
		#self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))
	def highlightCurrentLine(self):
		extraSelections = []

		selection = QTextEdit.ExtraSelection()
		lineColor = QColor(Qt.darkGray if self.parent.preferences['theme'] == 'Dark' else Qt.lightGray).lighter(50)
		selection.format.setBackground(lineColor)
		selection.format.setProperty(QTextFormat.FullWidthSelection, True)
		selection.cursor = self.textCursor()
		selection.cursor.clearSelection()
		extraSelections.append(selection)

		self.setExtraSelections(extraSelections)
	# mimicking QPlainTextEdit's method !!
	def firstVisibleBlock(self):
		curs = QTextCursor(self.document())
		for x in range(self.document().blockCount()):
			block = curs.block()
			r1 = self.viewport().geometry()
			geom = self.viewport().geometry()
			r2 = self.document().documentLayout().blockBoundingRect(block).translated(geom.x(), geom.y() - self.verticalScrollBar().sliderPosition()).toRect()
			if r1.contains(r2, True):	return self.document().findBlock(x)
			curs.movePosition(QTextCursor.NextBlock)
	def insertFromMimeData(self, source):
		cb = QApplication.clipboard()
		self.insertPlainText(source.text())
	@pyqtSlot(bool)
	def updateSelectionActions(self, copyAvailable):
		window = self.parent
		window.copyAction.setEnabled(copyAvailable)
		window.cutAction.setEnabled(copyAvailable)

class LineNumberArea(QWidget):
	def __init__(self, editor):
		super().__init__(editor)
		self.editor = editor
	def sizeHint(self):
		return QSize(self.editor.lineNumberAreaWidth(), 0)
	def paintEvent(self, event):
		self.editor.lineNumberAreaPaintEvent(event)

class Highlighter(QSyntaxHighlighter):
	SUBSTITUTION_SLASH = QTextCharFormat()	# the third slash
	PRINT_BLOCK = QTextCharFormat()			# after the third slash
	PATTERN_SLASH = QTextCharFormat()		# slash pattern format
	PATTERN_BLOCK = QTextCharFormat()
	REPLACEMENT_SLASH = QTextCharFormat()		# slash replacement format
	REPLACEMENT_BLOCK = QTextCharFormat()
	REFERENCE =  QTextCharFormat()

	def __init__(self, parent, perLine=False):
		QSyntaxHighlighter.__init__(self, parent)
		self.parent = parent
		self.perLine = perLine	# whether to syntax-highlight seperately by line or together by full
		self.settings = QSettings(constants.AUTHOR, constants.APP_NAME)
		# style formats
		#self.SUBSTITUTION_SLASH.setBackground(QColor(0, 160, 107))
		#self.SUBSTITUTION_SLASH.setBackground(QColor(123, 42, 59))

		#self.PATTERN_SLASH.setBackground(QColor(0, 62, 163))
		#self.PATTERN_BLOCK.setForeground(QColor(100, 162, 255))
		#self.PATTERN_SLASH.setBackground(QColor(198, 181, 112))
		#self.PATTERN_BLOCK.setForeground(QColor(248, 231, 162))

		#self.REPLACEMENT_SLASH.setBackground(QColor(161, 0, 97))
		#self.REPLACEMENT_BLOCK.setForeground(QColor(255, 100, 197))
		#self.REPLACEMENT_SLASH.setBackground(QColor(84, 171, 128))
		#self.REPLACEMENT_BLOCK.setForeground(QColor(134, 221, 178))

	def refresh(self):
		window = self.parent.parent
		self.SUBSTITUTION_SLASH.setBackground(window.substitutionSlashColor)
		self.SUBSTITUTION_SLASH.setForeground(Qt.white)
		self.PRINT_BLOCK.setForeground(window.printBlockColor)

		self.PATTERN_SLASH.setBackground(window.patternSlashColor)
		self.PATTERN_SLASH.setForeground(Qt.white)
		self.PATTERN_BLOCK.setForeground(window.patternBlockColor)

		self.REPLACEMENT_SLASH.setBackground(window.replacementSlashColor)
		self.REPLACEMENT_SLASH.setForeground(Qt.white)
		self.REPLACEMENT_BLOCK.setForeground(window.replacementBlockColor)

		referenceColor = QColor(0,155,155)
		self.REFERENCE.setUnderlineStyle(QTextCharFormat.SingleUnderline)
		self.REFERENCE.setUnderlineColor(referenceColor)
		self.REFERENCE.setForeground(referenceColor)

		self.highlightBlock(self.parent.toPlainText())

	def highlightBlock(self, text):
		# if self.perLine:
			# index = 0
			# for line in text.split('\n'):
				# self.highlightSubBlock(index, line)
				# index += len(line)
		# else:
		self.highlightSubBlock(0, text)	# highlight whole block
		if self.parent.useReferences:	self.markReferences()
		self.setCurrentBlockState(0)

	def highlightSubBlock(self, start, text):
		pattern = r'(?<!\\)(?:(\\\\)*)(\/)'
		expression = re.compile(pattern)
		match = expression.search(text)
		state = 0		# 0 -> print; 1 -> pattern; 2 -> repl; 3 -> text
		while match:
			state = (state + 1) % 3
			index = match.start(2)	# get group 2 (\/)
			length = match.end(2) - match.start(2)
			if state == 0:			# print
				slashFormat = self.SUBSTITUTION_SLASH
				blockFormat = self.PRINT_BLOCK
			elif state == 1:		# pattern
				slashFormat = self.PATTERN_SLASH
				blockFormat = self.PATTERN_BLOCK
			elif state == 2:		# replacement
				slashFormat = self.REPLACEMENT_SLASH
				blockFormat = self.REPLACEMENT_BLOCK

			# mark '/'
			self.setFormat(start + index, length, slashFormat)
			# mark block (actual text)
			self.setFormat(start + index+length, len(text), blockFormat)
			match = expression.search(text, index + length)
	def markReferences(self):
		window = self.parent.parent
		# ('###', self.parent.toPlainText(), len(window.referenceCursors))
		for selection in window.referenceCursors:	# haha it's not javascript
			# print('#', selection.anchor(), selection.position())
			#if selection.anchor() != selection.position():
			length = selection.position() - selection.anchor()
			self.setFormat(selection.anchor(), length, self.REFERENCE)
		#if not len(window.referenceCursors):
			#self.setFormat(1, 9, self.REFERENCE)
	def setFormat(self, start, count, format):
		super(Highlighter, self).setFormat(start, count, format)
		#print('intercept! hah!')

class PreferencesDialog(QDialog):
	def __init__(self, parent):
		super(PreferencesDialog, self).__init__()
		self.parent = parent
		self.resize(600, 300)
		self.create()
	def create(self):
		# NO TABS YET -- NOT ENOUGH PREFERENCES
		#self.tabs = QTabWidget()
		hlayout = QHBoxLayout()
		self.closeButton = QPushButton('Close')
		self.closeButton.clicked.connect(self.close)
		self.generalTab = PreferenceGeneralTab(self, self.parent)
		#self.syntaxHighlightingTab = PreferenceSyntaxHighlightingTab(self, self.parent)
		#self.tabs.addTab(self.generalTab, 'General')
		#self.tabs.addTab(self.syntaxHighlightingTab, 'Syntax Highlighting')
		hlayout.addStretch()
		hlayout.addWidget(self.closeButton)
		self.layout = QVBoxLayout()
		#self.layout.addWidget(self.tabs)
		self.layout.addWidget(self.generalTab)
		self.layout.addLayout(hlayout)
		self.setLayout(self.layout)
		self.setWindowTitle('Preferences')
class PreferenceGeneralTab(QWidget):
	def __init__(self, parent, window):
		super(PreferenceGeneralTab, self).__init__(parent)
		self.parent = parent
		self.window = window
		self.create()
	def create(self):
		self.layout = QFormLayout()
		themes = ['Dark', 'Light']
		self.themeComboBox = QComboBox()
		self.themeComboBox.addItems(themes)
		self.themeComboBox.setCurrentIndex(themes.index(self.window.theme))
		self.themeComboBox.currentIndexChanged.connect(self.updateTheme)
		self.resetButton = QPushButton('Rest to default settings')
		self.resetButton.clicked.connect(self.restoreAllDefaults)
		resetButtonLayout = QHBoxLayout()
		resetButtonLayout.addStretch()
		resetButtonLayout.addWidget(self.resetButton)
		self.layout.addRow(QLabel('Style', self))
		self.layout.addRow(QLabel('Theme: '), self.themeComboBox)
		#self.layout.addStretch()
		self.layout.addRow(resetButtonLayout)
		self.setLayout(self.layout)
	@pyqtSlot()
	def updateTheme(self):
		window = self.parent.parent
		window.theme = self.themeComboBox.currentText()
		window.output.refreshStyle()
		window.editor.refreshStyle()
	@pyqtSlot()
	def restoreAllDefaults(self):
		title = 'Restore defaults for all settings?'
		text = 'Are you sure you want to restore all settings to their default values?'
		if QMessageBox.question(self, title, text) == QMessageBox.Yes:
			# reset colors <strike>(in syntax highlighting tab)</strike>in this tab (general)
			# self.parent.syntaxHighlightingTab.restoreDefaults()
			self.themeComboBox.currentText('Dark')
			self.updateTheme()	# works??

			# reset all other settings

			self.window.showProgressionAction.setChecked(self.window.DEFAULT_SHOW_PROGRESSION)
			self.window.lineWrapAction.setChecked(self.window.DEFAULT_LINE_WRAP)
			self.window.splitter.setSizes([1, 1])		# QSplitter will rescale; main point - maintain 1 : 1 ratio
"""
class PreferenceSyntaxHighlightingTab(QWidget):
	def __init__(self, parent, window):
		super(PreferenceSyntaxHighlightingTab, self).__init__(parent)
		self.window = window
		self.create()
	def create(self):
		CSS = 'background-color:{}; color:white;'
		self.layout = QVBoxLayout()

		self.buttonsLayout = QHBoxLayout()
		self.patternColorButton = QPushButton('Pattern \'/\' highlight')
		self.patternColorButton.setStyleSheet(CSS.format(self.window.patternSlashColor.name()))
		self.patternColorButton.clicked.connect(lambda: self.showColorDialog('pattern'))
		self.replacementColorButton = QPushButton('Replacement \'/\' highlight')
		self.replacementColorButton.setStyleSheet(CSS.format(self.window.replacementSlashColor.name()))
		self.replacementColorButton.clicked.connect(lambda: self.showColorDialog('replacement'))
		self.substitutionColorButton = QPushButton('Substitution \'/\' highlight')
		self.substitutionColorButton.setStyleSheet(CSS.format(self.window.substitutionSlashColor.name()))
		self.substitutionColorButton.clicked.connect(lambda: self.showColorDialog('substitution'))
		self.buttonsLayout.addWidget(self.patternColorButton)
		self.buttonsLayout.addWidget(self.replacementColorButton)
		self.buttonsLayout.addWidget(self.substitutionColorButton)

		self.sampleText = Output(self.window)	# same code; same "output" (no pun intended) as output panel; -> just pass window object in as parent
		self.sampleText.setMaximumHeight(30)
		self.sampleText.setPlainText('/ world! world!/Hello,/ world! world! world!')

		self.resetButtonLayout = QHBoxLayout()
		self.resetButton = QPushButton('Restore defaults')
		self.resetButton.clicked.connect(self.restoreDefaults)
		self.resetButtonLayout.addStretch(1)
		self.resetButtonLayout.addWidget(self.resetButton)

		self.layout.addLayout(self.buttonsLayout)
		self.layout.addWidget(self.sampleText)
		self.layout.addStretch()
		self.layout.addLayout(self.resetButtonLayout)
		self.setLayout(self.layout)
	def showColorDialog(self, rule):
		if rule == 'pattern':
			initial = self.window.patternSlashColor
		elif rule == 'replacement':
			initial = self.window.replacementSlashColor
		elif rule == 'substitution':
			initial = self.window.substitutionSlashColor
		color = QColorDialog.getColor(initial, self)
		if color.isValid():	# if a color was selected (Ok pressed)
			css = 'background-color:{}; color:white;'.format(color.name())
			if rule == 'pattern':
				self.window.patternSlashColor = color
				self.patternColorButton.setStyleSheet(css)
			elif rule == 'replacement':
				self.window.replacementSlashColor = color
				self.replacementColorButton.setStyleSheet(css)
			elif rule == 'substitution':
				self.window.substitutionSlashColor = color
				self.substitutionColorButton.setStyleSheet(css)
			self.window.refreshColors()
			self.sampleText.refreshStyle()
	@pyqtSlot()
	def restoreDefaults(self):
		css = 'background-color:{}; color:white;'

		self.window.patternSlashColor = self.window.DEFAULT_PATTERN_HIGHLIGHT
		self.patternColorButton.setStyleSheet(css.format(self.window.patternSlashColor.name()))
		self.window.replacementSlashColor = self.window.DEFAULT_REPLACEMENT_HIGHLIGHT
		self.replacementColorButton.setStyleSheet(css.format(self.window.replacementSlashColor.name()))
		self.window.substitutionSlashColor = self.window.DEFAULT_SUBSTITUTION_HIGHLIGHT
		self.substitutionColorButton.setStyleSheet(css.format(self.window.substitutionSlashColor.name()))

		self.window.refreshColors()
		self.sampleText.refreshStyle()
"""
