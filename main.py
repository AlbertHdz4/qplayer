

from PyQt5.uic import loadUiType
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys

from variables import VariablesModel, StaticVariablesProxyModel, IteratorVariablesProxyModel


class ControlSystemGUI(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        Ui_MainWindow, MainWindow = loadUiType('control-system.ui')
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        
         
        #self.tableModel = QStandardItemModel()
        self.variablesModel = VariablesModel()
        self.staticVariablesModel = StaticVariablesProxyModel()
        self.iteratorVariablesModel = IteratorVariablesProxyModel()
        self.staticVariablesModel.setSourceModel(self.variablesModel)
        self.iteratorVariablesModel.setSourceModel(self.variablesModel)
        self.ui.variablesView.setModel(self.staticVariablesModel)
        self.ui.iteratorsView.setModel(self.iteratorVariablesModel)
        self.ui.fullView.setModel(self.variablesModel)
        #self.ui.variablesView.setSelectionBehavior(QAbstractItemView.SelectRows)
        #self.ui.variablesView.setDropIndicatorShown(True)

        #self.tableModel.setHorizontalHeaderLabels(["variable","value"])
        #root = self.tableModel.invisibleRootItem()

        #self.var_groups = []
        self.var_idx = 0
        self.group_idx = 0

        #SIGNALS
        self.ui.addVariableButton.clicked.connect(self.add_variable)
        self.ui.addVariableGroupButton.clicked.connect(self.add_variable_group)
        self.variablesModel.dataChanged.connect(self.data_changed)
        self.ui.variablesView.customContextMenuRequested.connect(self.variables_context_menu_requested)
        
        
        """
        for k in grdata:
            it = QStandardItem(k)
            root.appendRow([it,QStandardItem("s")])
            print(it)
            for j in grdata[k]:
                it.appendRow([QStandardItem(j),QStandardItem(grdata[k][j])])
                #it.appendRow(QStandardItem(grdata[k][j]))
        tableModel.setHorizontalHeaderLabels(["variables","values"]) 

        """

    @pyqtSlot()
    def add_variable_group(self):
        self.variablesModel.addGroup("default%02d"%self.group_idx)
        self.group_idx += 1

    @pyqtSlot()
    def add_variable(self):
        self.variablesModel.addVariable("var%02d"%self.var_idx,0)
        self.var_idx += 1

    @pyqtSlot()
    def data_changed(self):
        print("Data changed!")

    @pyqtSlot(QPoint)
    def variables_context_menu_requested(self, pos):
        print("menu")
        menu = QMenu()
        quitAction = menu.addAction("Quit")
        nopAction = menu.addAction("NOP")

        idx = self.ui.variablesView.indexAt(pos)
        if idx.isValid():
            print(idx.internalPointer().name)


        action = menu.exec(self.ui.variablesView.mapToGlobal(pos))
        if action == quitAction:
            print("Quit")
        elif action == nopAction:
            print("NOP")

        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = ControlSystemGUI()
    myapp.show()
    sys.exit(app.exec_())

