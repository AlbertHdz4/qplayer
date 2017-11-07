
from PyQt5.uic import loadUiType
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys

from variables import VariablesModel, VariablesProxyModel


class ControlSystemGUI(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        ui_main_window, main_window = loadUiType('control-system.ui')
        self.ui = ui_main_window()
        self.ui.setupUi(self)

        # MODELS
        self.variables_model = VariablesModel()

        # PROXY MODELS
        self.static_variables_model = VariablesProxyModel(["name","value","comment"], True, False, True)
        self.static_variables_model.setSourceModel(self.variables_model)
        self.iterator_variables_model = VariablesProxyModel(["name","value","start","stop","increment"], False, True, False)
        #self.iterator_variables_model = VariablesProxyModel(VariablesModel.variable_fields, True, True, True) # Uncomment for debug
        self.iterator_variables_model.setSourceModel(self.variables_model)

        # ADD MODELS TO VIEWS
        self.ui.static_variables_view.setModel(self.static_variables_model)
        self.ui.iterator_variables_view.setModel(self.iterator_variables_model)

        # VIEWS SETUP
        self.ui.static_variables_view.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.iterator_variables_view.header().setSectionResizeMode(QHeaderView.ResizeToContents)

        # SIGNALS
        self.ui.addVariableGroupButton.clicked.connect(self.add_variable_group)
        self.ui.addVariableButton.clicked.connect(self.add_variable)
        self.ui.static_variables_view.customContextMenuRequested.connect(self.static_variables_context_menu_requested)
        self.ui.iterator_variables_view.customContextMenuRequested.connect(self.iterator_variables_context_menu_requested)
        self.variables_model.dataChanged.connect(self.data_changed)
        self.variables_model.dataChanged.connect(self.iterator_variables_model.invalidate)

        # UTILITY VARIABLES
        self.var_idx = 0
        self.group_idx = 0

        # DUMMY DATA FOR TESTING
        self.variables_model.add_group("MOT")
        self.variables_model.add_group("Compression")
        self.variables_model.add_group("Dipole Trap")
        self.variables_model.add_group("Absorption Imaging")

        prnt = self.variables_model.index(0,0)
        self.variables_model.add_variable(prnt, name="loading_time", value="1000", comment="ms")
        self.variables_model.add_variable(prnt, name="slower_beam_pwr", value="1000", comment="W")
        self.variables_model.add_variable(prnt, name="oven_shutter_time", value="100", comment="ms")
        self.variables_model.add_variable(prnt, name="cooler_detuning", value="-20", comment="MHz")
        self.variables_model.add_variable(prnt, name="repumper_detuning", value="-20", comment="MHz")

        prnt = self.variables_model.index(2, 0)
        self.variables_model.add_variable(prnt, name="evaporation_time", value="0", start="0",stop="3000",increment="100",iterator=True)
        self.variables_model.add_variable(prnt, name="bottom_power", value="y = exp(-5*evaporation_time)\namp = 4\n= amp*y", comment="W")

        prnt = self.variables_model.index(3, 0)
        self.variables_model.add_variable(prnt, name="probe_detuning", value="-40", start="-40",stop="40",increment="5",iterator=True)

    @pyqtSlot()
    def add_variable_group(self):
        self.variables_model.add_group( "default%02d" %self.group_idx)
        self.group_idx += 1

    @pyqtSlot()
    def add_variable(self):
        selected_indexes = self.ui.static_variables_view.selectedIndexes()
        if len(selected_indexes) > 0:
            parent_idx = selected_indexes[0] # type: QModelIndex

            # We only want variables to be children of groups, not of variables so we
            # find the parent if a variable is selected
            if parent_idx.parent().isValid():
                parent_idx = parent_idx.parent()

            parent = self.static_variables_model.mapToSource(parent_idx) # type: QStandardItem
            self.variables_model.add_variable(parent, name="var%02d" % self.var_idx, iterator=False,value="0")
            self.var_idx += 1


    @pyqtSlot()
    def data_changed(self):
        print("Data changed!")

    @pyqtSlot(QPoint)
    def iterator_variables_context_menu_requested(self, pos):
        menu = QMenu()
        no_iterate_action = menu.addAction("Set as static")

        idx = self.ui.iterator_variables_view.indexAt(pos) # type: QModelIndex
        src_idx = self.iterator_variables_model.mapToSource(idx)

        if src_idx.parent().isValid(): # if a variable is selected

            action = menu.exec(self.ui.iterator_variables_view.mapToGlobal(pos)) # type: QMenu
            if action == no_iterate_action:
                iterator_idx = src_idx.parent().child(src_idx.row(),VariablesModel.variable_fields.index("iterator"))
                self.variables_model.setData(iterator_idx,Qt.Unchecked,Qt.CheckStateRole)

    @pyqtSlot(QPoint)
    def static_variables_context_menu_requested(self, pos):
        menu = QMenu()
        iterate_action = menu.addAction("Iterate")
        move_to_menu = menu.addMenu("Move to group")

        group_list = self.variables_model.get_group_list()
        move_actions = {}
        for gr_idx in range(len(group_list)):
            group_name = group_list[gr_idx]
            new_action = move_to_menu.addAction(group_name)
            move_actions[new_action] = gr_idx

        delete_action = menu.addAction("Delete variable")

        idx = self.ui.static_variables_view.indexAt(pos) # type: QModelIndex
        src_idx = self.static_variables_model.mapToSource(idx)

        if src_idx.parent().isValid(): # if a variable is selected

            action = menu.exec(self.ui.static_variables_view.mapToGlobal(pos)) # type: QMenu
            if action == iterate_action:
                iterator_idx = src_idx.parent().child(src_idx.row(),VariablesModel.variable_fields.index("iterator"))
                self.variables_model.setData(iterator_idx,Qt.Checked,Qt.CheckStateRole)
            elif action == delete_action:
                self.variables_model.removeRow(src_idx.row(),src_idx.parent())
            elif action in move_actions:
                print("Move to %s %d"%(group_list[move_actions[action]], move_actions[action]))

                taken_row = self.variables_model.itemFromIndex(src_idx.parent()).takeRow(src_idx.row())
                dest_item = self.variables_model.item(move_actions[action], 0)
                dest_item.insertRow(0,taken_row)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = ControlSystemGUI()
    myapp.show()
    sys.exit(app.exec_())

