import sys

from oasys2.widget.widget import OWWidget
from orangewidget import gui
from orangewidget.settings import Setting

from AnyQt.QtWidgets import QApplication
from AnyQt.QtCore import QRect

import oasys2.widget.gui as oasysgui
from oasys2.widget.gui import ConfirmDialog, MessageDialog

class AutomaticElement(OWWidget):
    want_main_area = 1
    is_automatic_run = Setting(True)

    MAX_WIDTH          = 1320
    MAX_HEIGHT         = 720
    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT   = 560

    def __init__(self, show_automatic_box=True):
        super().__init__()

        geom = QApplication.primaryScreen().geometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))
        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())
        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        if show_automatic_box:
            self.general_options_box = oasysgui.widgetBox(self.controlArea, "General Options", addSpace=True, orientation="horizontal", width=self.CONTROL_AREA_WIDTH-5)
            gui.checkBox(self.general_options_box, self, 'is_automatic_run', 'Automatic Execution')
            self.TABS_AREA_HEIGHT = 555
        else:
            self.TABS_AREA_HEIGHT = 615

    def call_reset_settings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:    self._reset_settings()
            except: pass

    def prompt_exception(self, exception: Exception):
        MessageDialog.message(self, str(exception), "Exception occured in OASYS", "critical")
        if self.IS_DEVELOP: raise exception

