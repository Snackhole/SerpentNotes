import json
import os

import mistune
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QInputDialog, QMessageBox, QFileDialog, QAction, QSplitter, QApplication

from Core import MarkdownRenderers, Utility
from Core.Notebook import Notebook
from Interface.Dialogs.DemotePageDialog import DemotePageDialog
from Interface.Dialogs.EditHeaderOrFooterDialog import EditHeaderOrFooterDialog
from Interface.Dialogs.ExportErrorDialog import ExportErrorDialog
from Interface.Dialogs.FavoritesDialog import FavoritesDialog
from Interface.Dialogs.ImageManagerDialog import ImageManagerDialog
from Interface.Dialogs.NewPageDialog import NewPageDialog
from Interface.Dialogs.TemplateManagerDialog import TemplateManagerDialog
from Interface.Widgets.NotebookDisplayWidget import NotebookDisplayWidget
from Interface.Widgets.SearchWidget import SearchWidget
from Interface.Widgets.TextWidget import TextWidget
from SaveAndLoad.SaveAndOpenMixin import SaveAndOpenMixin


class MainWindow(QMainWindow, SaveAndOpenMixin):
    # Initialization Methods
    def __init__(self, ScriptName):
        super().__init__()

        # Store Parameters
        self.ScriptName = ScriptName

        # Variables
        self.CurrentZoomLevel = 0
        self.BackList = []
        self.BackMaximum = 50
        self.ForwardList = []
        self.BackNavigation = False

        # Set Up Save and Open
        self.SetUpSaveAndOpen(".ntbk", "Notebook", (Notebook,))

        # Load Favorites
        if os.path.isfile("Favorites.cfg"):
            with open("Favorites.cfg", "r") as ConfigFile:
                self.FavoritesData = self.JSONSerializer.DeserializeDataFromJSONString(ConfigFile.read())
        else:
            self.FavoritesData = {}

        # Create Notebook
        self.Notebook = Notebook()

        # Create Interface
        self.CreateInterface()
        self.show()

    def CreateInterface(self):
        # Create Icons
        self.CreateIcons()

        # Window Icon and Title
        self.setWindowIcon(self.WindowIcon)
        self.UpdateWindowTitle()

        # Toggle Read Mode Actions List
        self.ToggleReadModeActionsList = []

        # Create Notebook Display Widget
        self.NotebookDisplayWidgetInst = NotebookDisplayWidget(self.Notebook, self)
        self.NotebookDisplayWidgetInst.itemSelectionChanged.connect(self.PageSelected)

        # Create Text Widget
        self.TextWidgetInst = TextWidget(self.Notebook, self)
        self.TextWidgetInst.textChanged.connect(self.TextChanged)

        # Create Search Widget
        self.SearchWidgetInst = SearchWidget(self.Notebook, self)

        # Create and Populate Splitters
        self.NotebookAndSearchSplitter = QSplitter(Qt.Vertical)
        self.NotebookAndSearchSplitter.addWidget(self.NotebookDisplayWidgetInst)
        self.NotebookAndSearchSplitter.addWidget(self.SearchWidgetInst)
        self.NotebookAndTextSplitter = QSplitter(Qt.Horizontal)
        self.NotebookAndTextSplitter.addWidget(self.NotebookAndSearchSplitter)
        self.NotebookAndTextSplitter.addWidget(self.TextWidgetInst)
        self.NotebookAndSearchSplitter.setStretchFactor(0, 1)
        self.NotebookAndSearchSplitter.setMinimumWidth(274)
        self.NotebookAndSearchSplitter.setChildrenCollapsible(False)
        self.NotebookAndTextSplitter.setStretchFactor(1, 1)
        self.setCentralWidget(self.NotebookAndTextSplitter)

        # Create Actions
        self.CreateActions()

        # Disable Edit-Only Actions and Widgets
        for Action in self.ToggleReadModeActionsList:
            Action.setEnabled(not self.TextWidgetInst.ReadMode)

        # Create Menu Bar
        self.CreateMenuBar()

        # Create Tool Bar
        self.CreateToolBar()

        # Create Status Bar
        self.StatusBar = self.statusBar()

        # Window Setup
        self.WindowSetup()

        # Initial Focus on NotebookDisplayWidgetInst
        self.NotebookDisplayWidgetInst.setFocus()

        # Initial Selection of Root Page
        self.PageSelected(IndexPath=[0], SkipUpdatingBackAndForward=True)

        # Set Up Tab Order
        self.setTabOrder(self.NotebookDisplayWidgetInst, self.TextWidgetInst)
        self.setTabOrder(self.TextWidgetInst, self.SearchWidgetInst)
        self.setTabOrder(self.SearchWidgetInst, self.NotebookDisplayWidgetInst)

    def CreateIcons(self):
        self.WindowIcon = QIcon("Assets/SerpentNotes Icon.png")
        self.NewPageIcon = QIcon("Assets/SerpentNotes New Page Icon.png")
        self.DeletePageIcon = QIcon("Assets/SerpentNotes Delete Page Icon.png")
        self.MovePageUpIcon = QIcon("Assets/SerpentNotes Move Page Up Icon.png")
        self.MovePageDownIcon = QIcon("Assets/SerpentNotes Move Page Down Icon.png")
        self.PromotePageIcon = QIcon("Assets/SerpentNotes Promote Page Icon.png")
        self.DemotePageIcon = QIcon("Assets/SerpentNotes Demote Page Icon.png")
        self.RenamePageIcon = QIcon("Assets/SerpentNotes Rename Page Icon.png")
        self.ToggleReadModeIcon = QIcon("Assets/SerpentNotes Toggle Read Mode Icon.png")
        self.BackIcon = QIcon("Assets/SerpentNotes Back Icon.png")
        self.ForwardIcon = QIcon("Assets/SerpentNotes Forward Icon.png")
        self.ItalicsIcon = QIcon("Assets/SerpentNotes Italics Icon.png")
        self.BoldIcon = QIcon("Assets/SerpentNotes Bold Icon.png")
        self.StrikethroughIcon = QIcon("Assets/SerpentNotes Strikethrough Icon.png")
        self.BulletListIcon = QIcon("Assets/SerpentNotes Bullet List Icon.png")
        self.NumberListIcon = QIcon("Assets/SerpentNotes Number List Icon.png")
        self.QuoteIcon = QIcon("Assets/SerpentNotes Quote Icon.png")
        self.InsertLinksIcon = QIcon("Assets/SerpentNotes Insert Link(s) Icon.png")
        self.InsertExternalLinkIcon = QIcon("Assets/SerpentNotes Insert External Link Icon.png")
        self.InsertTableIcon = QIcon("Assets/SerpentNotes Insert Table Icon.png")
        self.InsertImageIcon = QIcon("Assets/SerpentNotes Insert Image Icon.png")
        self.ZoomOutIcon = QIcon("Assets/SerpentNotes Zoom Out Icon.png")
        self.ZoomInIcon = QIcon("Assets/SerpentNotes Zoom In Icon.png")
        self.FavoritesIcon = QIcon("Assets/SerpentNotes Favorites Icon.png")
        self.SearchIcon = QIcon("Assets/SerpentNotes Search Icon.png")
        self.ToggleSearchIcon = QIcon("Assets/SerpentNotes Toggle Search Icon.png")

    def CreateActions(self):
        self.NewAction = QAction("New")
        self.NewAction.setShortcut("Ctrl+Shift+N")
        self.NewAction.triggered.connect(self.NewActionTriggered)

        self.OpenAction = QAction("Open")
        self.OpenAction.setShortcut("Ctrl+O")
        self.OpenAction.triggered.connect(lambda: self.OpenActionTriggered())

        self.FavoritesAction = QAction(self.FavoritesIcon, "Favorites")
        self.FavoritesAction.setShortcut("Ctrl+Shift+O")
        self.FavoritesAction.triggered.connect(self.Favorites)

        self.SaveAction = QAction("Save")
        self.SaveAction.setShortcut("Ctrl+S")
        self.SaveAction.triggered.connect(lambda: self.SaveActionTriggered())

        self.SaveAsAction = QAction("Save As")
        self.SaveAsAction.setShortcut("Ctrl+Shift+S")
        self.SaveAsAction.triggered.connect(lambda: self.SaveActionTriggered(SaveAs=True))

        self.ExitAction = QAction("Exit")
        self.ExitAction.setShortcut("Ctrl+Q")
        self.ExitAction.triggered.connect(self.close)

        self.ToggleReadModeAction = QAction(self.ToggleReadModeIcon, "Toggle Read Mode")
        self.ToggleReadModeAction.setShortcut("Ctrl+E")
        self.ToggleReadModeAction.triggered.connect(self.ToggleReadMode)

        self.BackAction = QAction(self.BackIcon, "Back")
        self.BackAction.setShortcut("Ctrl+,")
        self.BackAction.triggered.connect(self.Back)
        self.BackAction.setEnabled(False)

        self.ForwardAction = QAction(self.ForwardIcon, "Forward")
        self.ForwardAction.setShortcut("Ctrl+.")
        self.ForwardAction.triggered.connect(self.Forward)
        self.ForwardAction.setEnabled(False)

        self.NewPageAction = QAction(self.NewPageIcon, "New Page")
        self.NewPageAction.setShortcut("Ctrl+N")
        self.NewPageAction.triggered.connect(self.NewPage)
        self.ToggleReadModeActionsList.append(self.NewPageAction)

        self.DeletePageAction = QAction(self.DeletePageIcon, "Delete Page")
        self.DeletePageAction.setShortcut("Ctrl+D")
        self.DeletePageAction.triggered.connect(self.DeletePage)
        self.ToggleReadModeActionsList.append(self.DeletePageAction)

        self.MovePageUpAction = QAction(self.MovePageUpIcon, "Move Page Up")
        self.MovePageUpAction.setShortcut("Ctrl+PgUp")
        self.MovePageUpAction.triggered.connect(lambda: self.MovePage(-1))
        self.ToggleReadModeActionsList.append(self.MovePageUpAction)

        self.MovePageDownAction = QAction(self.MovePageDownIcon, "Move Page Down")
        self.MovePageDownAction.setShortcut("Ctrl+PgDown")
        self.MovePageDownAction.triggered.connect(lambda: self.MovePage(1))
        self.ToggleReadModeActionsList.append(self.MovePageDownAction)

        self.PromotePageAction = QAction(self.PromotePageIcon, "Promote Page")
        self.PromotePageAction.setShortcut("Ctrl+Shift+PgUp")
        self.PromotePageAction.triggered.connect(self.PromotePage)
        self.ToggleReadModeActionsList.append(self.PromotePageAction)

        self.DemotePageAction = QAction(self.DemotePageIcon, "Demote Page")
        self.DemotePageAction.setShortcut("Ctrl+Shift+PgDown")
        self.DemotePageAction.triggered.connect(self.DemotePage)
        self.ToggleReadModeActionsList.append(self.DemotePageAction)

        self.RenamePageAction = QAction(self.RenamePageIcon, "Rename Page")
        self.RenamePageAction.setShortcut("Ctrl+R")
        self.RenamePageAction.triggered.connect(self.RenamePage)
        self.ToggleReadModeActionsList.append(self.RenamePageAction)

        self.ExpandAllAction = QAction("Expand All")
        self.ExpandAllAction.triggered.connect(self.NotebookDisplayWidgetInst.expandAll)

        self.CollapseAllAction = QAction("Collapse All")
        self.CollapseAllAction.triggered.connect(self.NotebookDisplayWidgetInst.collapseAll)

        self.ImageManagerAction = QAction("Image Manager")
        self.ImageManagerAction.triggered.connect(self.ImageManager)
        self.ToggleReadModeActionsList.append(self.ImageManagerAction)

        self.TemplateManagerAction = QAction("Template Manager")
        self.TemplateManagerAction.triggered.connect(self.TemplateManager)
        self.ToggleReadModeActionsList.append(self.TemplateManagerAction)

        self.EditHeaderAction = QAction("Edit Header")
        self.EditHeaderAction.triggered.connect(lambda: self.EditHeaderOrFooter("Header"))
        self.ToggleReadModeActionsList.append(self.EditHeaderAction)

        self.EditFooterAction = QAction("Edit Footer")
        self.EditFooterAction.triggered.connect(lambda: self.EditHeaderOrFooter("Footer"))
        self.ToggleReadModeActionsList.append(self.EditFooterAction)

        self.ExportHTMLAction = QAction("Export HTML Files")
        self.ExportHTMLAction.triggered.connect(self.ExportHTML)
        self.ToggleReadModeActionsList.append(self.ExportHTMLAction)

        self.ItalicsAction = QAction(self.ItalicsIcon, "Italics")
        self.ItalicsAction.setShortcut("Ctrl+I")
        self.ItalicsAction.triggered.connect(self.TextWidgetInst.Italics)
        self.ToggleReadModeActionsList.append(self.ItalicsAction)

        self.BoldAction = QAction(self.BoldIcon, "Bold")
        self.BoldAction.setShortcut("Ctrl+B")
        self.BoldAction.triggered.connect(self.TextWidgetInst.Bold)
        self.ToggleReadModeActionsList.append(self.BoldAction)

        self.StrikethroughAction = QAction(self.StrikethroughIcon, "Strikethrough")
        self.StrikethroughAction.triggered.connect(self.TextWidgetInst.Strikethrough)
        self.ToggleReadModeActionsList.append(self.StrikethroughAction)

        self.CodeSpanAction = QAction("Code Span")
        self.CodeSpanAction.triggered.connect(self.TextWidgetInst.CodeSpan)
        self.ToggleReadModeActionsList.append(self.CodeSpanAction)

        self.HeaderOneAction = QAction("Header 1")
        self.HeaderOneAction.setShortcut("Ctrl+1")
        self.HeaderOneAction.triggered.connect(lambda: self.TextWidgetInst.Header(1))
        self.ToggleReadModeActionsList.append(self.HeaderOneAction)

        self.HeaderTwoAction = QAction("Header 2")
        self.HeaderTwoAction.setShortcut("Ctrl+2")
        self.HeaderTwoAction.triggered.connect(lambda: self.TextWidgetInst.Header(2))
        self.ToggleReadModeActionsList.append(self.HeaderTwoAction)

        self.HeaderThreeAction = QAction("Header 3")
        self.HeaderThreeAction.setShortcut("Ctrl+3")
        self.HeaderThreeAction.triggered.connect(lambda: self.TextWidgetInst.Header(3))
        self.ToggleReadModeActionsList.append(self.HeaderThreeAction)

        self.HeaderFourAction = QAction("Header 4")
        self.HeaderFourAction.setShortcut("Ctrl+4")
        self.HeaderFourAction.triggered.connect(lambda: self.TextWidgetInst.Header(4))
        self.ToggleReadModeActionsList.append(self.HeaderFourAction)

        self.HeaderFiveAction = QAction("Header 5")
        self.HeaderFiveAction.setShortcut("Ctrl+5")
        self.HeaderFiveAction.triggered.connect(lambda: self.TextWidgetInst.Header(5))
        self.ToggleReadModeActionsList.append(self.HeaderFiveAction)

        self.HeaderSixAction = QAction("Header 6")
        self.HeaderSixAction.setShortcut("Ctrl+6")
        self.HeaderSixAction.triggered.connect(lambda: self.TextWidgetInst.Header(6))
        self.ToggleReadModeActionsList.append(self.HeaderSixAction)

        self.BulletListAction = QAction(self.BulletListIcon, "Bullet List")
        self.BulletListAction.triggered.connect(self.TextWidgetInst.BulletList)
        self.ToggleReadModeActionsList.append(self.BulletListAction)

        self.NumberListAction = QAction(self.NumberListIcon, "Number List")
        self.NumberListAction.triggered.connect(self.TextWidgetInst.NumberList)
        self.ToggleReadModeActionsList.append(self.NumberListAction)

        self.QuoteAction = QAction(self.QuoteIcon, "Quote")
        self.QuoteAction.triggered.connect(self.TextWidgetInst.Quote)
        self.ToggleReadModeActionsList.append(self.QuoteAction)

        self.CodeBlockAction = QAction("Code Block")
        self.CodeBlockAction.triggered.connect(self.TextWidgetInst.CodeBlock)
        self.ToggleReadModeActionsList.append(self.CodeBlockAction)

        self.HorizontalRuleAction = QAction("Horizontal Rule")
        self.HorizontalRuleAction.triggered.connect(self.TextWidgetInst.HorizontalRule)
        self.ToggleReadModeActionsList.append(self.HorizontalRuleAction)

        self.FootnoteAction = QAction("Footnote")
        self.FootnoteAction.triggered.connect(self.TextWidgetInst.Footnote)
        self.ToggleReadModeActionsList.append(self.FootnoteAction)

        self.InsertLinksAction = QAction(self.InsertLinksIcon, "Insert Link(s)")
        self.InsertLinksAction.setShortcut("Ctrl+L")
        self.InsertLinksAction.triggered.connect(self.TextWidgetInst.InsertLinks)
        self.ToggleReadModeActionsList.append(self.InsertLinksAction)

        self.InsertExternalLinkAction = QAction(self.InsertExternalLinkIcon, "Insert External Link")
        self.InsertExternalLinkAction.setShortcut("Ctrl+Shift+L")
        self.InsertExternalLinkAction.triggered.connect(self.TextWidgetInst.InsertExternalLink)
        self.ToggleReadModeActionsList.append(self.InsertExternalLinkAction)

        self.TextToLinkAction = QAction("Convert Exact Title to Link")
        self.TextToLinkAction.setShortcut("Ctrl+Alt+L")
        self.TextToLinkAction.triggered.connect(self.TextWidgetInst.TextToLink)
        self.ToggleReadModeActionsList.append(self.TextToLinkAction)

        self.InsertTableAction = QAction(self.InsertTableIcon, "Insert Table")
        self.InsertTableAction.triggered.connect(self.TextWidgetInst.InsertTable)
        self.ToggleReadModeActionsList.append(self.InsertTableAction)

        self.InsertImageAction = QAction(self.InsertImageIcon, "Insert Image")
        self.InsertImageAction.triggered.connect(self.TextWidgetInst.InsertImage)
        self.ToggleReadModeActionsList.append(self.InsertImageAction)

        self.MoveLineUpAction = QAction("Move Line Up")
        self.MoveLineUpAction.setShortcut("Ctrl+Up")
        self.MoveLineUpAction.triggered.connect(self.TextWidgetInst.MoveLineUp)
        self.ToggleReadModeActionsList.append(self.MoveLineUpAction)

        self.MoveLineDownAction = QAction("Move Line Down")
        self.MoveLineDownAction.setShortcut("Ctrl+Down")
        self.MoveLineDownAction.triggered.connect(self.TextWidgetInst.MoveLineDown)
        self.ToggleReadModeActionsList.append(self.MoveLineDownAction)

        self.DuplicateLinesAction = QAction("Duplicate Lines")
        self.DuplicateLinesAction.setShortcut("Ctrl+Shift+D")
        self.DuplicateLinesAction.triggered.connect(self.TextWidgetInst.DuplicateLines)
        self.ToggleReadModeActionsList.append(self.DuplicateLinesAction)

        self.DeleteLineAction = QAction("Delete Line")
        self.DeleteLineAction.setShortcut("Ctrl+Shift+K")
        self.DeleteLineAction.triggered.connect(self.TextWidgetInst.DeleteLine)
        self.ToggleReadModeActionsList.append(self.DeleteLineAction)

        self.ZoomOutAction = QAction(self.ZoomOutIcon, "Zoom Out")
        self.ZoomOutAction.setShortcut("Ctrl+-")
        self.ZoomOutAction.triggered.connect(self.ZoomOut)

        self.ZoomInAction = QAction(self.ZoomInIcon, "Zoom In")
        self.ZoomInAction.setShortcut("Ctrl+=")
        self.ZoomInAction.triggered.connect(self.ZoomIn)

        self.DefaultZoomAction = QAction("Default Zoom")
        self.DefaultZoomAction.setShortcut("Ctrl+0")
        self.DefaultZoomAction.triggered.connect(self.DefaultZoom)

        self.SearchAction = QAction(self.SearchIcon, "Search")
        self.SearchAction.setShortcut("Ctrl+F")
        self.SearchAction.triggered.connect(self.SearchWidgetInst.GrabFocus)

        self.ToggleSearchAction = QAction(self.ToggleSearchIcon, "Toggle Search")
        self.ToggleSearchAction.setShortcut("Ctrl+Shift+F")
        self.ToggleSearchAction.triggered.connect(self.SearchWidgetInst.ToggleVisibility)

    def CreateMenuBar(self):
        self.MenuBar = self.menuBar()

        self.FileMenu = self.MenuBar.addMenu("File")
        self.FileMenu.addAction(self.NewAction)
        self.FileMenu.addAction(self.OpenAction)
        self.FileMenu.addAction(self.FavoritesAction)
        self.FileMenu.addSeparator()
        self.FileMenu.addAction(self.SaveAction)
        self.FileMenu.addAction(self.SaveAsAction)
        self.FileMenu.addSeparator()
        self.FileMenu.addAction(self.ExitAction)

        self.EditMenu = self.MenuBar.addMenu("Edit")
        self.EditMenu.addAction(self.ToggleReadModeAction)
        self.EditMenu.addSeparator()
        self.EditMenu.addAction(self.ItalicsAction)
        self.EditMenu.addAction(self.BoldAction)
        self.EditMenu.addAction(self.StrikethroughAction)
        self.EditMenu.addAction(self.CodeSpanAction)
        self.EditMenu.addSeparator()
        self.EditMenu.addAction(self.HeaderOneAction)
        self.EditMenu.addAction(self.HeaderTwoAction)
        self.EditMenu.addAction(self.HeaderThreeAction)
        self.EditMenu.addAction(self.HeaderFourAction)
        self.EditMenu.addAction(self.HeaderFiveAction)
        self.EditMenu.addAction(self.HeaderSixAction)
        self.EditMenu.addSeparator()
        self.EditMenu.addAction(self.BulletListAction)
        self.EditMenu.addAction(self.NumberListAction)
        self.EditMenu.addAction(self.QuoteAction)
        self.EditMenu.addAction(self.CodeBlockAction)
        self.EditMenu.addSeparator()
        self.EditMenu.addAction(self.HorizontalRuleAction)
        self.EditMenu.addAction(self.FootnoteAction)
        self.EditMenu.addSeparator()
        self.EditMenu.addAction(self.InsertLinksAction)
        self.EditMenu.addAction(self.InsertExternalLinkAction)
        self.EditMenu.addAction(self.TextToLinkAction)
        self.EditMenu.addAction(self.InsertTableAction)
        self.EditMenu.addAction(self.InsertImageAction)
        self.EditMenu.addSeparator()
        self.EditMenu.addAction(self.MoveLineUpAction)
        self.EditMenu.addAction(self.MoveLineDownAction)
        self.EditMenu.addAction(self.DuplicateLinesAction)
        self.EditMenu.addAction(self.DeleteLineAction)

        self.ViewMenu = self.MenuBar.addMenu("View")
        self.ViewMenu.addAction(self.BackAction)
        self.ViewMenu.addAction(self.ForwardAction)
        self.ViewMenu.addSeparator()
        self.ViewMenu.addAction(self.SearchAction)
        self.ViewMenu.addAction(self.ToggleSearchAction)
        self.ViewMenu.addSeparator()
        self.ViewMenu.addAction(self.ZoomOutAction)
        self.ViewMenu.addAction(self.ZoomInAction)
        self.ViewMenu.addAction(self.DefaultZoomAction)
        self.ViewMenu.addSeparator()
        self.ViewMenu.addAction(self.ExpandAllAction)
        self.ViewMenu.addAction(self.CollapseAllAction)

        self.NotebookMenu = self.MenuBar.addMenu("Notebook")
        self.NotebookMenu.addAction(self.NewPageAction)
        self.NotebookMenu.addAction(self.DeletePageAction)
        self.NotebookMenu.addAction(self.RenamePageAction)
        self.NotebookMenu.addSeparator()
        self.NotebookMenu.addAction(self.MovePageUpAction)
        self.NotebookMenu.addAction(self.MovePageDownAction)
        self.NotebookMenu.addAction(self.PromotePageAction)
        self.NotebookMenu.addAction(self.DemotePageAction)
        self.NotebookMenu.addSeparator()
        self.NotebookMenu.addAction(self.ImageManagerAction)
        self.NotebookMenu.addAction(self.TemplateManagerAction)
        self.NotebookMenu.addSeparator()
        self.NotebookMenu.addAction(self.EditHeaderAction)
        self.NotebookMenu.addAction(self.EditFooterAction)
        self.NotebookMenu.addSeparator()
        self.NotebookMenu.addAction(self.ExportHTMLAction)

    def CreateToolBar(self):
        self.ToolBar = self.addToolBar("Actions")
        self.ToolBar.addAction(self.ToggleReadModeAction)
        self.ToolBar.addAction(self.BackAction)
        self.ToolBar.addAction(self.ForwardAction)
        self.ToolBar.addSeparator()
        self.ToolBar.addAction(self.NewPageAction)
        self.ToolBar.addAction(self.DeletePageAction)
        self.ToolBar.addAction(self.RenamePageAction)
        self.ToolBar.addSeparator()
        self.ToolBar.addAction(self.MovePageUpAction)
        self.ToolBar.addAction(self.MovePageDownAction)
        self.ToolBar.addAction(self.PromotePageAction)
        self.ToolBar.addAction(self.DemotePageAction)
        self.ToolBar.addSeparator()
        self.ToolBar.addAction(self.ItalicsAction)
        self.ToolBar.addAction(self.BoldAction)
        self.ToolBar.addAction(self.StrikethroughAction)
        self.ToolBar.addSeparator()
        self.ToolBar.addAction(self.BulletListAction)
        self.ToolBar.addAction(self.NumberListAction)
        self.ToolBar.addAction(self.QuoteAction)
        self.ToolBar.addSeparator()
        self.ToolBar.addAction(self.InsertLinksAction)
        self.ToolBar.addAction(self.InsertExternalLinkAction)
        self.ToolBar.addAction(self.InsertTableAction)
        self.ToolBar.addAction(self.InsertImageAction)
        self.ToolBar.addSeparator()
        self.ToolBar.addAction(self.SearchAction)
        self.ToolBar.addAction(self.ToggleSearchAction)
        self.ToolBar.addSeparator()
        self.ToolBar.addAction(self.ZoomOutAction)
        self.ToolBar.addAction(self.ZoomInAction)
        self.ToolBar.addSeparator()
        self.ToolBar.addAction(self.FavoritesAction)

    # Notebook Methods
    def UpdateNotebook(self, Notebook):
        self.Notebook = Notebook
        self.NotebookDisplayWidgetInst.Notebook = self.Notebook
        self.TextWidgetInst.Notebook = self.Notebook
        self.TextWidgetInst.Renderer.Notebook = self.Notebook
        self.SearchWidgetInst.Notebook = self.Notebook

    def PageSelected(self, IndexPath=None, SkipUpdatingBackAndForward=False):
        IndexPath = IndexPath if IndexPath is not None else self.NotebookDisplayWidgetInst.GetCurrentPageIndexPath()
        if IndexPath is not None:
            if not SkipUpdatingBackAndForward:
                self.UpdateBackAndForward()
            self.TextWidgetInst.SetCurrentPage(self.Notebook.GetPageFromIndexPath(IndexPath))

    def UpdateBackAndForward(self):
        if not self.BackNavigation and self.TextWidgetInst.ReadMode:
            PreviousPageIndexPath = self.TextWidgetInst.CurrentPage["IndexPath"]
            if self.BackList != []:
                if self.BackList[-1] != PreviousPageIndexPath:
                    self.BackList.append(PreviousPageIndexPath)
            else:
                self.BackList.append(PreviousPageIndexPath)
            if len(self.BackList) > self.BackMaximum:
                self.BackList = self.BackList[-self.BackMaximum:]
            self.ForwardList.clear()
        self.BackAction.setEnabled(len(self.BackList) > 0 and self.TextWidgetInst.ReadMode)
        self.ForwardAction.setEnabled(len(self.ForwardList) > 0 and self.TextWidgetInst.ReadMode)

    def ClearBackAndForward(self):
        self.BackList.clear()
        self.ForwardList.clear()
        self.BackAction.setEnabled(len(self.BackList) > 0 and self.TextWidgetInst.ReadMode)
        self.ForwardAction.setEnabled(len(self.ForwardList) > 0 and self.TextWidgetInst.ReadMode)

    def Back(self):
        if len(self.BackList) > 0:
            self.BackNavigation = True
            TargetPageIndexPath = self.BackList[-1]
            del self.BackList[-1]
            CurrentPageIndexPath = self.NotebookDisplayWidgetInst.GetCurrentPageIndexPath()
            self.ForwardList.append(CurrentPageIndexPath)
            self.NotebookDisplayWidgetInst.SelectTreeItemFromIndexPath(TargetPageIndexPath)
            self.BackNavigation = False

    def Forward(self):
        if len(self.ForwardList) > 0:
            self.BackNavigation = True
            TargetPageIndexPath = self.ForwardList[-1]
            del self.ForwardList[-1]
            CurrentPageIndexPath = self.NotebookDisplayWidgetInst.GetCurrentPageIndexPath()
            self.BackList.append(CurrentPageIndexPath)
            self.NotebookDisplayWidgetInst.SelectTreeItemFromIndexPath(TargetPageIndexPath)
            self.BackNavigation = False

    def NewPage(self):
        if not self.TextWidgetInst.ReadMode:
            CurrentPageIndexPath = self.NotebookDisplayWidgetInst.GetCurrentPageIndexPath()
            CurrentPage = self.Notebook.GetPageFromIndexPath(CurrentPageIndexPath)
            NewPageDialogInst = NewPageDialog(CurrentPage["Title"], self.Notebook.GetTemplateNames(), self)
            if NewPageDialogInst.NewPageAdded:
                OldLinkData = self.GetLinkData()
                self.Notebook.AddSubPage(NewPageDialogInst.NewPageName, "" if NewPageDialogInst.TemplateName == "None" else self.Notebook.GetTemplate(NewPageDialogInst.TemplateName), CurrentPageIndexPath)
                NewLinkData = self.GetLinkData()
                self.UpdateLinks(OldLinkData, NewLinkData)
                self.NotebookDisplayWidgetInst.FillFromRootPage()
                self.NotebookDisplayWidgetInst.SelectTreeItemFromIndexPath(CurrentPageIndexPath, ScrollToLastChild=True)
                self.SearchWidgetInst.RefreshSearch()
                self.UpdateUnsavedChangesFlag(True)
            self.NotebookDisplayWidgetInst.setFocus()

    def DeletePage(self):
        if not self.TextWidgetInst.ReadMode:
            CurrentPageIndexPath = self.NotebookDisplayWidgetInst.GetCurrentPageIndexPath()
            CurrentPage = self.Notebook.GetPageFromIndexPath(CurrentPageIndexPath)
            if CurrentPage["IndexPath"] == [0]:
                self.DisplayMessageBox("The root page of a notebook cannot be deleted.")
            elif self.DisplayMessageBox("Are you sure you want to delete this page?  This cannot be undone.", Icon=QMessageBox.Question, Buttons=(QMessageBox.Yes | QMessageBox.No)) == QMessageBox.Yes:
                OldLinkData = self.GetLinkData()
                self.Notebook.DeleteSubPage(CurrentPageIndexPath)
                NewLinkData = self.GetLinkData()
                self.UpdateLinks(OldLinkData, NewLinkData)
                self.NotebookDisplayWidgetInst.FillFromRootPage()
                SelectParent = False
                SelectDelta = 0
                CurrentPageSuperSubPagesLength = len(self.Notebook.GetSuperOfPageFromIndexPath(CurrentPageIndexPath)["SubPages"])
                if CurrentPageSuperSubPagesLength < 1:
                    SelectParent = True
                elif CurrentPageSuperSubPagesLength == CurrentPageIndexPath[-1]:
                    SelectDelta = -1
                self.NotebookDisplayWidgetInst.SelectTreeItemFromIndexPath(CurrentPageIndexPath, SelectParent=SelectParent, SelectDelta=SelectDelta)
                self.SearchWidgetInst.RefreshSearch()
                self.UpdateUnsavedChangesFlag(True)
            self.NotebookDisplayWidgetInst.setFocus()

    def MovePage(self, Delta):
        if not self.TextWidgetInst.ReadMode:
            CurrentPageIndexPath = self.NotebookDisplayWidgetInst.GetCurrentPageIndexPath()
            CurrentPage = self.Notebook.GetPageFromIndexPath(CurrentPageIndexPath)
            OldLinkData = self.GetLinkData()
            if CurrentPage["IndexPath"] == [0]:
                self.DisplayMessageBox("The root page of a notebook cannot be moved.")
            elif self.Notebook.MoveSubPage(CurrentPageIndexPath, Delta):
                NewLinkData = self.GetLinkData()
                self.UpdateLinks(OldLinkData, NewLinkData)
                self.NotebookDisplayWidgetInst.FillFromRootPage()
                self.NotebookDisplayWidgetInst.SelectTreeItemFromIndexPath(CurrentPageIndexPath, SelectDelta=Delta)
                self.SearchWidgetInst.RefreshSearch()
                self.UpdateUnsavedChangesFlag(True)
            self.NotebookDisplayWidgetInst.setFocus()

    def PromotePage(self):
        if not self.TextWidgetInst.ReadMode:
            CurrentPageIndexPath = self.NotebookDisplayWidgetInst.GetCurrentPageIndexPath()
            SuperOfCurrentPageIndexPath = self.Notebook.GetSuperOfPageFromIndexPath(CurrentPageIndexPath)["IndexPath"]
            if CurrentPageIndexPath == [0]:
                self.DisplayMessageBox("The root page of a notebook cannot be promoted.")
            elif SuperOfCurrentPageIndexPath == [0]:
                self.DisplayMessageBox("A page cannot be promoted to the same level as the root page.")
            else:
                CurrentPage = self.Notebook.GetPageFromIndexPath(CurrentPageIndexPath)
                OldLinkData = self.GetLinkData()
                self.Notebook.PromoteSubPage(CurrentPageIndexPath)
                NewLinkData = self.GetLinkData()
                self.UpdateLinks(OldLinkData, NewLinkData)
                self.NotebookDisplayWidgetInst.FillFromRootPage()
                self.NotebookDisplayWidgetInst.SelectTreeItemFromIndexPath(CurrentPage["IndexPath"])
                self.SearchWidgetInst.RefreshSearch()
                self.UpdateUnsavedChangesFlag(True)
            self.NotebookDisplayWidgetInst.setFocus()

    def DemotePage(self):
        if not self.TextWidgetInst.ReadMode:
            CurrentPageIndexPath = self.NotebookDisplayWidgetInst.GetCurrentPageIndexPath()
            SuperOfCurrentPage = self.Notebook.GetSuperOfPageFromIndexPath(CurrentPageIndexPath)
            if CurrentPageIndexPath == [0]:
                self.DisplayMessageBox("The root page of a notebook cannot be demoted.")
            elif len(SuperOfCurrentPage["SubPages"]) < 2:
                self.DisplayMessageBox("No valid page to demote to.")
            else:
                CurrentPage = self.Notebook.GetPageFromIndexPath(CurrentPageIndexPath)
                SiblingPages = SuperOfCurrentPage["SubPages"].copy()
                SiblingPages.remove(CurrentPage)
                SiblingPageTitles = [Sibling["Title"] for Sibling in SiblingPages]
                SiblingPageIndex = DemotePageDialog(CurrentPage, SiblingPageTitles, self).SiblingPageIndex
                if SiblingPageIndex is not None:
                    OldLinkData = self.GetLinkData()
                    self.Notebook.DemoteSubPage(CurrentPageIndexPath, SiblingPageIndex)
                    NewLinkData = self.GetLinkData()
                    self.UpdateLinks(OldLinkData, NewLinkData)
                    self.NotebookDisplayWidgetInst.FillFromRootPage()
                    self.NotebookDisplayWidgetInst.SelectTreeItemFromIndexPath(CurrentPage["IndexPath"])
                    self.SearchWidgetInst.RefreshSearch()
                    self.UpdateUnsavedChangesFlag(True)
            self.NotebookDisplayWidgetInst.setFocus()

    def RenamePage(self):
        if not self.TextWidgetInst.ReadMode:
            CurrentPageIndexPath = self.NotebookDisplayWidgetInst.GetCurrentPageIndexPath()
            CurrentPage = self.Notebook.GetPageFromIndexPath(CurrentPageIndexPath)
            NewName, OK = QInputDialog.getText(self, "Rename " + CurrentPage["Title"], "Enter a title:", text=CurrentPage["Title"])
            if OK:
                if NewName == "":
                    self.DisplayMessageBox("Page names cannot be blank.")
                else:
                    CurrentPage["Title"] = NewName
                    self.NotebookDisplayWidgetInst.FillFromRootPage()
                    self.NotebookDisplayWidgetInst.SelectTreeItemFromIndexPath(CurrentPageIndexPath)
                    self.SearchWidgetInst.RefreshSearch()
                    self.UpdateUnsavedChangesFlag(True)
            self.NotebookDisplayWidgetInst.setFocus()

    def GetLinkData(self):
        LinkData = {}
        LinkData[id(self.Notebook.RootPage)] = "](" + json.dumps(self.Notebook.RootPage["IndexPath"], indent=None) + ")"
        self.AddSubPageLinkData(self.Notebook.RootPage, LinkData)
        return LinkData

    def AddSubPageLinkData(self, CurrentPage, LinkData):
        for SubPage in CurrentPage["SubPages"]:
            LinkData[id(SubPage)] = "](" + json.dumps(SubPage["IndexPath"], indent=None) + ")"
            self.AddSubPageLinkData(SubPage, LinkData)

    def UpdateLinks(self, OldLinkData, NewLinkData):
        ReplaceQueue = []
        for PageID in NewLinkData:
            if PageID in OldLinkData:
                if NewLinkData[PageID] != OldLinkData[PageID]:
                    ReplaceStrings = (OldLinkData[PageID], "<<LINK UPDATE TOKEN" + str(PageID) + ">>", NewLinkData[PageID])
                    ReplaceQueue.append(ReplaceStrings)
        for ReplaceStrings in ReplaceQueue:
            self.SearchWidgetInst.ReplaceAllInNotebook(SearchText=ReplaceStrings[0], ReplaceText=ReplaceStrings[1], MatchCase=True, DelayTextUpdate=True)
        for ReplaceStrings in ReplaceQueue:
            self.SearchWidgetInst.ReplaceAllInNotebook(SearchText=ReplaceStrings[1], ReplaceText=ReplaceStrings[2], MatchCase=True, DelayTextUpdate=True)

    def ImageManager(self):
        if not self.TextWidgetInst.ReadMode:
            ImageManagerDialogInst = ImageManagerDialog(self.Notebook, self)
            if ImageManagerDialogInst.UnsavedChanges:
                self.UpdateUnsavedChangesFlag(True)

    def TemplateManager(self):
        if not self.TextWidgetInst.ReadMode:
            TemplateManagerDialogInst = TemplateManagerDialog(self.Notebook, self)
            if TemplateManagerDialogInst.UnsavedChanges:
                self.UpdateUnsavedChangesFlag(True)

    def EditHeaderOrFooter(self, Mode):
        if not self.TextWidgetInst.ReadMode:
            EditHeaderOrFooterDialogInst = EditHeaderOrFooterDialog(Mode, self.Notebook, self)
            if EditHeaderOrFooterDialogInst.UnsavedChanges:
                if EditHeaderOrFooterDialogInst.Mode == "Header":
                    self.Notebook.Header = EditHeaderOrFooterDialogInst.HeaderOrFooterString
                elif EditHeaderOrFooterDialogInst.Mode == "Footer":
                    self.Notebook.Footer = EditHeaderOrFooterDialogInst.HeaderOrFooterString
                self.UpdateUnsavedChangesFlag(True)

    # Text Methods
    def TextChanged(self):
        if self.TextWidgetInst.DisplayChanging or self.TextWidgetInst.ReadMode:
            return
        self.TextWidgetInst.CurrentPage["Content"] = self.TextWidgetInst.toPlainText()
        self.Notebook.SearchIndexUpToDate = False
        self.UpdateUnsavedChangesFlag(True)

    def ToggleReadMode(self):
        self.TextWidgetInst.SetReadMode(not self.TextWidgetInst.ReadMode)
        for Action in self.ToggleReadModeActionsList:
            Action.setEnabled(not self.TextWidgetInst.ReadMode)
        self.NotebookDisplayWidgetInst.setFocus() if self.TextWidgetInst.ReadMode else self.TextWidgetInst.setFocus()
        self.ClearBackAndForward()

    def ZoomOut(self):
        self.TextWidgetInst.zoomOut(1)
        self.CurrentZoomLevel -= 1

    def ZoomIn(self):
        self.TextWidgetInst.zoomIn(1)
        self.CurrentZoomLevel += 1

    def DefaultZoom(self):
        if self.CurrentZoomLevel > 0:
            self.TextWidgetInst.zoomOut(self.CurrentZoomLevel)
            self.CurrentZoomLevel = 0
        elif self.CurrentZoomLevel < 0:
            self.TextWidgetInst.zoomIn(-self.CurrentZoomLevel)
            self.CurrentZoomLevel = 0

    # Interface Methods
    def DisplayMessageBox(self, Message, Icon=QMessageBox.Information, Buttons=QMessageBox.Ok, Parent=None):
        MessageBox = QMessageBox(self if Parent is None else Parent)
        MessageBox.setWindowIcon(self.WindowIcon)
        MessageBox.setWindowTitle(self.ScriptName)
        MessageBox.setIcon(Icon)
        MessageBox.setText(Message)
        MessageBox.setStandardButtons(Buttons)
        return MessageBox.exec_()

    def FlashStatusBar(self, Status, Duration=2000):
        self.StatusBar.showMessage(Status)
        QTimer.singleShot(Duration, self.StatusBar.clearMessage)

    def UpdateWindowTitle(self):
        self.setWindowTitle(self.ScriptName + (" - [" + os.path.basename(self.CurrentOpenFileName) + "]" if self.CurrentOpenFileName != "" else "") + (" *" if self.UnsavedChanges else ""))

    # HTML Export Methods
    def ExportHTML(self):
        ExportDirectory = QFileDialog.getExistingDirectory(caption="Export HTML")
        if ExportDirectory != "":
            if len(os.listdir(ExportDirectory)) > 0:
                self.DisplayMessageBox("HTML files must be exported to an empty folder.")
                return
            ErrorList = []
            self.ExportPagesToHTML(ExportDirectory, ErrorList)
            if len(ErrorList) > 0:
                CombinedErrorString = ""
                for ErrorString in ErrorList:
                    CombinedErrorString += ErrorString + "\n\n"
                CombinedErrorString = CombinedErrorString.rstrip()
                ExportErrorDialog(CombinedErrorString, self)
            self.FlashStatusBar("Exported notebook to:  " + ExportDirectory)

    def ExportPagesToHTML(self, ExportDirectory, ErrorList):
        RootPageTitle = str(self.Notebook.RootPage["IndexPath"][-1]) + " - " + Utility.GetSafeFileNameFromPageTitle(self.Notebook.RootPage["Title"])
        HTMLExportRenderer = MarkdownRenderers.HTMLExportRenderer(self.Notebook)
        HTMLExportMarkdownParser = mistune.Markdown(renderer=HTMLExportRenderer)
        with open(os.path.join(ExportDirectory, RootPageTitle) + ".html", "w") as ExportFile:
            MarkdownText = MarkdownRenderers.ConstructMarkdownStringFromPage(self.Notebook.RootPage, self.Notebook)
            HTMLExportRenderer.CurrentPage = self.Notebook.RootPage
            HTMLText = HTMLExportMarkdownParser(MarkdownText)
            try:
                ExportFile.write(HTMLText)
            except Exception as Error:
                ErrorString = RootPageTitle + ":  " + str(Error)
                ErrorList.append(ErrorString)
        self.ExportSubPagesToHTML(ExportDirectory, self.Notebook.RootPage, HTMLExportMarkdownParser, HTMLExportRenderer, ErrorList)

    def ExportSubPagesToHTML(self, CurrentDirectory, CurrentPage, MarkdownParser, HTMLExportRenderer, ErrorList):
        CurrentPageTitle = str(CurrentPage["IndexPath"][-1]) + " - " + Utility.GetSafeFileNameFromPageTitle(CurrentPage["Title"])
        CurrentPageDirectory = os.path.join(CurrentDirectory, CurrentPageTitle)
        for SubPage in CurrentPage["SubPages"]:
            if not os.path.isdir(CurrentPageDirectory):
                os.makedirs(CurrentPageDirectory, exist_ok=True)
            SubPageTitle = str(SubPage["IndexPath"][-1]) + " - " + Utility.GetSafeFileNameFromPageTitle(SubPage["Title"])
            with open(os.path.join(CurrentPageDirectory, SubPageTitle) + ".html", "w") as ExportFile:
                MarkdownText = MarkdownRenderers.ConstructMarkdownStringFromPage(SubPage, self.Notebook)
                HTMLExportRenderer.CurrentPage = SubPage
                HTMLText = MarkdownParser(MarkdownText)
                try:
                    ExportFile.write(HTMLText)
                except Exception as Error:
                    ErrorString = SubPageTitle + ":  " + str(Error)
                    ErrorList.append(ErrorString)
            self.ExportSubPagesToHTML(CurrentPageDirectory, SubPage, MarkdownParser, HTMLExportRenderer, ErrorList)

    # Save and Open Methods
    def SaveActionTriggered(self, SaveAs=False):
        if self.Save(self.Notebook, SaveAs=SaveAs):
            self.Notebook.BuildSearchIndex()
            self.SearchWidgetInst.RefreshSearch()
            self.UpdateUnsavedChangesFlag(False)
        else:
            self.UpdateWindowTitle()

    def OpenActionTriggered(self, FilePath=None):
        NewNotebook = self.Open(self.Notebook, FilePath=FilePath)
        if NewNotebook is not None:
            self.UpdateNotebook(NewNotebook)
            self.NotebookDisplayWidgetInst.FillFromRootPage()
            self.Notebook.BuildSearchIndex()
            self.SearchWidgetInst.ClearSearch()
            self.ClearBackAndForward()
            self.UpdateUnsavedChangesFlag(False)
        else:
            self.UpdateWindowTitle()

    def Favorites(self):
        FavoritesDialogInst = FavoritesDialog(self.FavoritesData, self)
        if FavoritesDialogInst.OpenFilePath is not None:
            self.OpenActionTriggered(FavoritesDialogInst.OpenFilePath)

    def NewActionTriggered(self):
        if not self.New(self.Notebook):
            self.UpdateWindowTitle()
            return
        self.UpdateNotebook(Notebook())
        self.NotebookDisplayWidgetInst.FillFromRootPage()
        self.Notebook.BuildSearchIndex()
        self.SearchWidgetInst.ClearSearch()
        self.ClearBackAndForward()
        self.UpdateUnsavedChangesFlag(False)

    def closeEvent(self, event):
        Close = True
        if self.UnsavedChanges:
            SavePrompt = self.DisplayMessageBox("Save unsaved work before closing?", Icon=QMessageBox.Warning, Buttons=(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel))
            if SavePrompt == QMessageBox.Yes:
                if not self.Save(self.Notebook):
                    Close = False
            elif SavePrompt == QMessageBox.No:
                pass
            elif SavePrompt == QMessageBox.Cancel:
                Close = False
        if not Close:
            event.ignore()
        else:
            with open("Favorites.cfg", "w") as ConfigFile:
                ConfigFile.write(json.dumps(self.FavoritesData, indent=2))
            event.accept()

    def UpdateUnsavedChangesFlag(self, UnsavedChanges):
        self.UnsavedChanges = UnsavedChanges
        self.UpdateWindowTitle()

    # Window Management Methods
    def WindowSetup(self):
        self.Resize()
        self.Center()

    def Resize(self):
        ScreenGeometry = QApplication.primaryScreen().availableGeometry()
        Width = int(ScreenGeometry.width() * 0.5)
        Height = int(ScreenGeometry.height() * 0.75)
        self.resize(Width, Height)

    def Center(self):
        FrameGeometryRectangle = self.frameGeometry()
        DesktopCenterPoint = QApplication.primaryScreen().availableGeometry().center()
        FrameGeometryRectangle.moveCenter(DesktopCenterPoint)
        self.move(FrameGeometryRectangle.topLeft())