import os
import pickle

from AnyQt.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Output

from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.widget.widget import OWWidget, OWAction
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from orangecontrib.shadow4.util.shadow4_objects import ShadowData


class BeamFileReader(OWWidget):
    name = "Shadow4 File Reader"
    description = "Tools: Shadow File Reader"
    icon = "icons/beam_file_reader.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 6
    category = "Tools"
    keywords = ["data", "file", "load", "read"]

    want_main_area = 0

    shadow_data_file_name = Setting("")

    class Outputs:
        shadow_data = Output("Shadow Data", ShadowData, default=True, auto_summary=False)

    def __init__(self):
        super().__init__()

        self.runaction = OWAction("Read Shadow4 File", self)
        self.runaction.triggered.connect(self.read_file)
        self.addAction(self.runaction)

        self.setFixedWidth(590)
        self.setFixedHeight(150)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Shadow4 File Selection", addSpace=True, orientation="vertical",
                                         width=570, height=70)

        figure_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal", width=550, height=35)

        self.le_shadow_data_file_name = oasysgui.lineEdit(figure_box, self, "shadow_data_file_name", "Shadow4 File Name",
                                                    labelWidth=120, valueType=str, orientation="horizontal")
        self.le_shadow_data_file_name.setFixedWidth(330)

        gui.button(figure_box, self, "...", callback=self.selectFile)

        button = gui.button(self.controlArea, self, "Read Shadow4 File", callback=self.read_file)
        button.setFixedHeight(45)

        gui.rubber(self.controlArea)

    def selectFile(self):
        self.le_shadow_data_file_name.setText(oasysgui.selectFileFromDialog(self, self.shadow_data_file_name, "Open Shadow4 File", file_extension_filter="Pickle Files (*.pkl)"))

    def read_file(self):
        self.setStatusMessage("")

        try:
            if congruence.checkFileName(self.shadow_data_file_name):
                with open(self.shadow_data_file_name, "rb") as f:  shadow_data = pickle.load(f)

                _, file_name = os.path.split(self.shadow_data_file_name)

                self.setStatusMessage("Current: " + file_name)

                self.Outputs.shadow_data.send(shadow_data)
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

add_widget_parameters_to_module(__name__)